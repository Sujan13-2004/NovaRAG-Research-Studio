import os
import re
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
from flashrank import Ranker, RerankRequest
from ingest import get_chroma_client, get_collection

# Global variables for caching
_ranker = None
_papers_mapping = {}

def load_papers_mapping():
    """Loads mapping from papers.csv to resolve dynamic downloads."""
    global _papers_mapping
    _papers_mapping = {}
    try:
        import csv
        csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "papers.csv")
        if os.path.exists(csv_path):
            with open(csv_path, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    filename = row.get("pdf_filename", "").strip()
                    title = row.get("title", "").strip()
                    arxiv_id = row.get("arxiv_id", "").strip()
                    if filename:
                        _papers_mapping[filename] = {
                            "title": title,
                            "arxiv_id": arxiv_id
                        }
    except Exception as e:
        print(f"Error loading papers.csv in RAG pipeline: {e}")

def get_paper_identifiers(filename: str):
    """
    Extracts canonical title and arXiv ID for a given filename.
    Returns (normalized_title, arxiv_id).
    """
    basename = os.path.basename(filename)
    if basename in _papers_mapping:
        mapped = _papers_mapping[basename]
        title = mapped["title"]
        arxiv_id = mapped["arxiv_id"]
        return re.sub(r'[^a-z0-9]', '', title.lower()), arxiv_id

    name = basename
    name = re.sub(r'\.pdf$', '', name, flags=re.IGNORECASE)
    arxiv_match = re.match(r'^(\d{4}\.\d{4,5})[-_]?(.*)', name)
    arxiv_id = None
    if arxiv_match:
        arxiv_id = arxiv_match.group(1)
        name = arxiv_match.group(2)
    
    clean_name = name.replace('_', ' ').strip()
    clean_name = re.sub(r'^[\s\-\.]+|[\s\-\.]+$', '', clean_name)
    clean_name = re.sub(r'\s{2,}', ' ', clean_name)
    if not clean_name:
        clean_name = "untitled paper"
        
    return re.sub(r'[^a-z0-9]', '', clean_name.lower()), arxiv_id

def get_ranker():
    """Lazy initialization of the FlashRank reranker to save startup time."""
    global _ranker
    if _ranker is None:
        # Default model is ms-marco-MiniLM-L-6-v2 or similar depending on the version
        # It downloads a tiny (~15MB-30MB) model locally on the first run
        _ranker = Ranker()
    return _ranker

def clean_text(text: str) -> str:
    """Removes redundant whitespaces and newlines to optimize token usage."""
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def clean_inline_citations(summary: str, sources: list) -> str:
    """
    Cleans inline citations in the summary by replacing filename/title citations
    with bracketed ranks like [1], [2], etc.
    """
    cleaned = summary
    for src in sources:
        rank = src.get("rank", 1)
        raw_title = src.get("title", "")
        # Get filename and base title
        filename = os.path.basename(raw_title)
        filename_no_ext = re.sub(r'\.pdf$', '', filename, flags=re.IGNORECASE)
        # Clean title (e.g. replacing underscores with spaces)
        clean_title = filename_no_ext.replace('_', ' ')
        
        # Create regex patterns to find this source citation in brackets
        escaped_filename = re.escape(filename_no_ext[:30])
        escaped_title = re.escape(clean_title[:30])
        
        pattern = rf'\[\s*(?:{escaped_filename}|{escaped_title}|{re.escape(filename)})[^\]]{0,100}\]'
        cleaned = re.sub(pattern, f'[{rank}]', cleaned, flags=re.IGNORECASE)
        
    # Also clean general occurrences of multiple pages or verbose citations if any remain
    cleaned = re.sub(r'\[\s*(\d+)\s*,\s*Page\s*\d+\s*\]', r'[\1]', cleaned)
    cleaned = re.sub(r'\[\s*(\d+(?:\s*,\s*\d+)*)\s*\]', r'[\1]', cleaned)
    return cleaned


# ═══════════════════════════════════════════════════════════════════════════════
# SYSTEM PROMPTS
# ═══════════════════════════════════════════════════════════════════════════════

# System prompt for GENERAL multi-document synthesis queries
SYSTEM_PROMPT_GENERAL = (
    "You are an elite academic AI research assistant. Your task is to produce a "
    "professional research synthesis using ONLY the provided paper snippets. "
    "Do not fabricate facts or extrapolate beyond what is stated in the sources.\n\n"
    "CRITICAL GROUNDING RULES:\n"
    "- EVERY factual claim MUST include a citation [N] referencing the source number.\n"
    "- If the sources do not contain enough information to fill a section, write: "
    "'Insufficient evidence in the retrieved sources to address this area.'\n"
    "- Do NOT invent statistics, author names, method names, or results not present in the sources.\n"
    "- Do NOT discuss topics, methods, or technologies that are not mentioned in the provided sources.\n\n"
    "CRITICAL OUTPUT RULES — FOLLOW EXACTLY:\n\n"
    "1. Do ALL of your internal reasoning silently. Do NOT write any reasoning, "
    "   planning, analysis steps, chain-of-thought, or meta-commentary in your output.\n\n"
    "2. Your ENTIRE output must be a polished, professional academic research summary.\n\n"
    "3. Your output MUST begin IMMEDIATELY with the first section header below. "
    "   Do NOT write any text before the first '## Research Overview' header.\n\n"
    "4. Structure your output using EXACTLY these markdown sections in this order:\n"
    "   ## Research Overview\n"
    "   ## Methodology\n"
    "   ## Key Findings\n"
    "   ## Comparative Analysis\n"
    "   ## Future Scope\n"
    "   ## Conclusion\n"
    "   ## References\n\n"
    "5. Under '## Future Scope', discuss potential future research directions ONLY if "
    "   the sources explicitly mention them. If the sources do not discuss future work, "
    "   write: 'The retrieved sources do not explicitly discuss future research directions.'\n\n"
    "6. Cite sources in-text using bracketed numbers matching the source rank, "
    "   e.g., [1] or [1, 2]. Do not include the PDF filename, title, or 'Page X' "
    "   in the inline citation. Every claim must be cited.\n\n"
    "ABSOLUTELY FORBIDDEN in your output:\n"
    "- Phrases like 'The user wants...', 'I need to...', 'Let me...', 'My analysis...'\n"
    "- Internal labels such as 'Snippet 1', 'Snippet 2', 'Plan:', 'Step 1:'\n"
    "- Any <thinking> tags or reasoning traces\n"
    "- Any preamble, introduction of yourself, or meta-commentary\n"
    "- Bullet-point lists of your analysis steps\n"
    "- ANY claim, statistic, method name, or result not directly found in the provided sources\n\n"
    "Write in formal academic prose. Be dense, precise, and well-structured."
)

# System prompt for SINGLE-DOCUMENT summarization (uploaded PDF workflow)
SYSTEM_PROMPT_SINGLE_DOC = (
    "You are an elite academic AI research assistant. Your task is to produce a comprehensive "
    "summary of a SINGLE research paper using ONLY the provided text excerpts from that paper. "
    "Do not fabricate facts, add external knowledge, or extrapolate beyond what is stated.\n\n"
    "CRITICAL GROUNDING RULES:\n"
    "- EVERY factual claim MUST include a citation [N] referencing the specific excerpt number.\n"
    "- Summarize ONLY what the paper actually says. Do NOT add information from other papers or your training data.\n"
    "- If a section cannot be filled from the excerpts, write: "
    "'This aspect is not covered in the available excerpts.'\n"
    "- Do NOT invent statistics, author names, method names, or results not present in the excerpts.\n\n"
    "CRITICAL OUTPUT RULES — FOLLOW EXACTLY:\n\n"
    "1. Do ALL of your internal reasoning silently. Do NOT write any reasoning, "
    "   planning, analysis steps, chain-of-thought, or meta-commentary in your output.\n\n"
    "2. Your ENTIRE output must be a polished, professional academic paper summary.\n\n"
    "3. Your output MUST begin IMMEDIATELY with the first section header below. "
    "   Do NOT write any text before the first '## Research Overview' header.\n\n"
    "4. Structure your output using EXACTLY these markdown sections in this order:\n"
    "   ## Research Overview\n"
    "   ## Methodology\n"
    "   ## Key Findings\n"
    "   ## Conclusion\n"
    "   ## References\n\n"
    "5. Cite excerpts in-text using bracketed numbers matching the excerpt rank, "
    "   e.g., [1] or [1, 2]. Every claim must be cited.\n\n"
    "ABSOLUTELY FORBIDDEN in your output:\n"
    "- Phrases like 'The user wants...', 'I need to...', 'Let me...', 'My analysis...'\n"
    "- Internal labels such as 'Snippet 1', 'Snippet 2', 'Plan:', 'Step 1:'\n"
    "- Any <thinking> tags or reasoning traces\n"
    "- Any preamble, introduction of yourself, or meta-commentary\n"
    "- ANY claim, statistic, method name, or result not directly found in the provided excerpts\n\n"
    "Write in formal academic prose. Be dense, precise, and well-structured."
)

# System prompt for FACTUAL QA — short, direct answers to specific questions
SYSTEM_PROMPT_FACTUAL_QA = (
    "You are a precise academic research assistant. Your task is to answer a specific "
    "factual question using ONLY the provided source excerpts.\n\n"
    "CRITICAL RULES:\n"
    "- Give a SHORT, DIRECT answer. One or two sentences maximum.\n"
    "- If the answer is a specific value (number, percentage, name, date), return ONLY that value.\n"
    "- If the exact answer is NOT present in the provided sources, reply ONLY with: "
    "'Not stated in the document.'\n"
    "- Do NOT generate a research report, synthesis, or summary.\n"
    "- Do NOT add section headers like '## Research Overview'.\n"
    "- Do NOT add methodology, key findings, or conclusion sections.\n"
    "- Do NOT extrapolate, speculate, or infer beyond what is explicitly written.\n"
    "- Do NOT use phrases like 'Based on the sources...', 'According to...', or 'The paper discusses...'.\n"
    "- Include a citation [N] referencing the source where you found the answer.\n"
    "- If the user asked for a specific format (e.g., 'ONE LINE ONLY'), follow it exactly.\n\n"
    "EXAMPLES OF CORRECT BEHAVIOR:\n"
    "  Question: 'What accuracy did the model achieve?'\n"
    "  Answer: '94.5% [1]'\n\n"
    "  Question: 'Who is the corresponding author?'\n"
    "  Answer: 'Dr. Jane Smith, Stanford University [1]'\n\n"
    "  Question: 'What dataset was used?'\n"
    "  Answer if found: 'MIMIC-III clinical database [2]'\n"
    "  Answer if not found: 'Not stated in the document.'\n"
)

# System prompt for EVIDENCE EXTRACTION
SYSTEM_PROMPT_EVIDENCE_EXTRACTION = (
    "You are a precise academic research assistant. Your task is to extract evidence-backed facts "
    "from the provided source excerpts based on the user's query.\n\n"
    "CRITICAL RULES:\n"
    "- Extract ONLY evidence-backed facts that are directly supported by the provided excerpts.\n"
    "- Do NOT generate a research overview or summary.\n"
    "- Do NOT generate methodology, key findings, or conclusion sections.\n"
    "- Do NOT extrapolate, speculate, or infer. Only output what is explicitly stated.\n"
    "- If no evidence/facts corresponding to the query are available in the document excerpts, output ONLY: "
    "'Unsupported by document.'\n\n"
    "REQUIRED OUTPUT FORMAT:\n"
    "For each fact you extract, you MUST follow this exact format (do not add numbering, titles, or headers):\n"
    "Fact: <a concise description of the fact>\n"
    "Page: <the exact page number(s) in the source where this fact is found>\n"
    "Supporting Quote: \"<the exact direct quote from the source supporting this fact>\"\n"
    "Confidence: <High/Medium/Low>\n\n"
    "Separate multiple facts with a single empty line. Do not include any reasoning, preambles, or postambles."
)


def run_rag_query(
    query: str, 
    api_key: str = None, 
    collection_name: str = "research_papers", 
    top_k_retrieve: int = 20,
    top_n_rerank: int = 7,
    max_chunks_per_doc: int = 3,
    document_id: str = None,
    query_intent: str = "RESEARCH_SYNTHESIS",
    simulate_api_failure: bool = False
) -> dict:
    """
    Executes the retrieve-rerank-generate pipeline.
    
    Args:
        query: The user's research query.
        api_key: Gemini API key.
        collection_name: ChromaDB collection name.
        top_k_retrieve: Number of unique candidates to retrieve for reranking.
        top_n_rerank: Number of top reranked results to use as context.
        max_chunks_per_doc: Maximum chunks to keep per unique document (general mode).
        document_id: If set, restricts retrieval to this specific document only.
                     Used for "Summarize Uploaded Document" mode.
        query_intent: One of 'FACTUAL_QA', 'DOCUMENT_SUMMARY', 'RESEARCH_SYNTHESIS'.
                      Controls prompt selection and output format.
        simulate_api_failure: If True, simulates an API failure for testing.
    
    Returns:
        A dict with success status, summary, sources, and metadata.
    """
    client = get_chroma_client()
    collection = get_collection(client, collection_name)
    
    # Determine mode
    is_single_doc_mode = document_id is not None
    
    # Override defaults for single-document mode
    if is_single_doc_mode:
        top_k_retrieve = 50   # Retrieve all chunks from the document
        top_n_rerank = 12     # Use more context for single-doc summaries
        max_chunks_per_doc = 999  # No per-doc limit in single-doc mode
    
    # Initialize counts
    chunks_retrieved_count = 0
    unique_papers_count = 0
    duplicates_removed_count = 0
    
    # 1. Check if vector database has any entries
    all_docs = collection.get(limit=1)
    if not all_docs or not all_docs.get("ids"):
        return {
            "success": False,
            "status": "error",
            "message": "The research database is empty. Please upload some research papers first.",
            "query": query,
            "raw_chunks": [],
            "summary": "",
            "thinking": "",
            "chunks_retrieved_count": 0,
            "unique_papers_count": 0,
            "duplicates_removed_count": 0
        }
    
    # 2. Retrieve initial candidates (Recall phase)
    retrieval_limit = max(top_k_retrieve * 3, 50)
    
    # Build query parameters with optional metadata filtering
    query_params = {
        "query_texts": [query],
        "n_results": retrieval_limit,
    }
    
    # KEY FIX: Apply document_id filter to restrict retrieval to a single document
    if is_single_doc_mode:
        query_params["where"] = {"document_id": document_id}
    
    retrieval_results = collection.query(**query_params)
    
    # Check if we got any results
    if not retrieval_results or not retrieval_results.get("documents") or not retrieval_results["documents"][0]:
        msg = "No relevant documents could be found for your query."
        if is_single_doc_mode:
            msg = f"No chunks found for document '{document_id}'. The document may not be indexed yet."
        return {
            "success": False,
            "status": "error",
            "message": msg,
            "query": query,
            "raw_chunks": [],
            "summary": "",
            "thinking": "",
            "chunks_retrieved_count": 0,
            "unique_papers_count": 0,
            "duplicates_removed_count": 0
        }
        
    documents = retrieval_results["documents"][0]
    metadatas = retrieval_results["metadatas"][0]
    ids = retrieval_results["ids"][0]
    
    chunks_retrieved_count = len(documents)
    
    # 3. Retrieval Deduplication & Multi-Chunk Selection
    load_papers_mapping()
    
    if is_single_doc_mode:
        # SINGLE-DOCUMENT MODE: Keep all chunks from the target document (no dedup needed)
        unique_passages = []
        for doc, meta, id_ in zip(documents, metadatas, ids):
            unique_passages.append({
                "id": id_,
                "text": clean_text(doc),
                "meta": meta
            })
        unique_papers_count = 1
        duplicates_removed_count = 0
    else:
        # GENERAL QUERY MODE: Allow up to max_chunks_per_doc chunks per unique paper
        seen_doc_ids = {}  # doc_id -> count of chunks kept
        seen_titles = {}   # normalized_title -> doc_id (for cross-referencing)
        seen_arxiv_ids = {}  # arxiv_id -> doc_id
        
        unique_passages = []
        total_unique_docs = 0
        
        for doc, meta, id_ in zip(documents, metadatas, ids):
            doc_id = meta.get("document_id", "Unknown")
            filename = meta.get("title", "Unknown")
            
            norm_title, arxiv_id = get_paper_identifiers(filename)
            
            # Resolve the canonical doc key (handle cases where same paper has different doc_ids)
            canonical_key = doc_id
            if norm_title and norm_title in seen_titles:
                canonical_key = seen_titles[norm_title]
            elif arxiv_id and arxiv_id in seen_arxiv_ids:
                canonical_key = seen_arxiv_ids[arxiv_id]
            
            # Check if we've reached the per-document chunk limit
            current_count = seen_doc_ids.get(canonical_key, 0)
            if current_count >= max_chunks_per_doc:
                continue
            
            # Track this chunk
            if canonical_key not in seen_doc_ids:
                total_unique_docs += 1
            seen_doc_ids[canonical_key] = current_count + 1
            
            if norm_title:
                seen_titles[norm_title] = canonical_key
            if arxiv_id:
                seen_arxiv_ids[arxiv_id] = canonical_key
                
            unique_passages.append({
                "id": id_,
                "text": clean_text(doc),
                "meta": meta
            })
            
            # Stop once we have enough candidates for reranking
            if total_unique_docs >= top_k_retrieve:
                break
                
        unique_papers_count = total_unique_docs
        duplicates_removed_count = chunks_retrieved_count - len(unique_passages)
        
    try:
        ranker = get_ranker()
        rerank_request = RerankRequest(query=query, passages=unique_passages)
        rerank_results = ranker.rerank(rerank_request)
        # Get the top N reranked results
        reranked_passages = rerank_results[:top_n_rerank]
    except Exception as e:
        # Fallback if reranker fails for some reason: use original top_n_rerank candidates
        print(f"Reranking failed: {e}. Falling back to vector search order.")
        reranked_passages = unique_passages[:top_n_rerank]
 
    # Format the retrieved chunks for presentation
    formatted_chunks = []
    for rank, p in enumerate(reranked_passages):
        formatted_chunks.append({
            "rank": rank + 1,
            "id": p["id"],
            "text": p["text"],
            "title": p["meta"].get("title", "Unknown Document"),
            "page": p["meta"].get("page_number", "Unknown"),
            "doc_id": p["meta"].get("document_id", "Unknown")
        })
 
    # Prepare LLM Context
    source_label = "SOURCE" if not is_single_doc_mode else "EXCERPT"
    context_str = ""
    for chunk in formatted_chunks:
        context_str += f"\n--- {source_label} [{chunk['rank']}]: {chunk['title']} (Page {chunk['page']}) ---\n"
        context_str += f"{chunk['text']}\n"
 
    # 4. LLM Generation & Resiliency Fallback
    if simulate_api_failure:
        return {
            "success": False,
            "status": "fallback",
            "message": "API Failure Simulation: LLM generation is offline. Graceful degradation active.",
            "query": query,
            "raw_chunks": formatted_chunks,
            "summary": "SYSTEM WARNING: AI synthesis is offline (Simulated API Failure). Below are the raw retrieved text chunks for your query.",
            "thinking": "Chain of Thought: LLM generation was bypassed due to user-triggered simulated failure.",
            "chunks_retrieved_count": chunks_retrieved_count,
            "unique_papers_count": unique_papers_count,
            "duplicates_removed_count": duplicates_removed_count
        }
 
    gemini_key = api_key or os.getenv("GEMINI_API_KEY")
    if not gemini_key:
        return {
            "success": False,
            "status": "fallback",
            "message": "Gemini API key is not configured. Please supply a key in the settings.",
            "query": query,
            "raw_chunks": formatted_chunks,
            "summary": "SYSTEM WARNING: Gemini API Key is missing. Below are the raw retrieved text chunks for your query.",
            "thinking": "Chain of Thought: API key not provided, falling back to raw retrieved chunks.",
            "chunks_retrieved_count": chunks_retrieved_count,
            "unique_papers_count": unique_papers_count,
            "duplicates_removed_count": duplicates_removed_count
        }
 
    try:
        genai.configure(api_key=gemini_key)
        
        # Select the appropriate system prompt and user prompt based on intent
        is_factual_qa = query_intent == "FACTUAL_QA"
        is_evidence_extraction = query_intent == "EVIDENCE_EXTRACTION"
        
        if is_factual_qa:
            system_instruction = SYSTEM_PROMPT_FACTUAL_QA
            prompt = (
                f"Answer the following question using ONLY the provided sources.\n\n"
                f"QUESTION: {query}\n\n"
                f"SOURCE MATERIAL:\n{context_str}\n\n"
                f"If the exact answer is not present in the sources above, reply ONLY: "
                f"'Not stated in the document.'\n"
                f"Do NOT generate a report. Give a short, direct answer."
            )
            max_tokens = 300  # Short answers need far fewer tokens
        elif is_evidence_extraction:
            system_instruction = SYSTEM_PROMPT_EVIDENCE_EXTRACTION
            prompt = (
                f"Extract facts from the provided sources based on the query.\n\n"
                f"QUERY: {query}\n\n"
                f"SOURCE MATERIAL:\n{context_str}\n\n"
                f"If no evidence/facts corresponding to the query are available in the document excerpts, reply ONLY: "
                f"'Unsupported by document.'\n\n"
                f"For each fact, output exactly in the required format:\n"
                f"Fact:\nPage:\nSupporting Quote:\nConfidence:\n"
            )
            max_tokens = 1000
        elif is_single_doc_mode:
            system_instruction = SYSTEM_PROMPT_SINGLE_DOC
            prompt = (
                f"Produce a comprehensive summary of the following research paper.\n\n"
                f"PAPER QUERY/TOPIC: {query}\n\n"
                f"PAPER EXCERPTS (from the same document):\n{context_str}\n\n"
                f"IMPORTANT: Use ONLY the excerpts above. Do NOT add any external knowledge.\n"
                f"Begin your response IMMEDIATELY with '## Research Overview'. "
                f"Do not include any reasoning, planning, or preamble."
            )
            max_tokens = 2000
        else:
            system_instruction = SYSTEM_PROMPT_GENERAL
            prompt = (
                f"Synthesize a professional academic research summary for the following query.\n\n"
                f"QUERY: {query}\n\n"
                f"SOURCE MATERIAL:\n{context_str}\n\n"
                f"IMPORTANT: Use ONLY the sources above. Every claim must have a citation [N]. "
                f"Do NOT add any information not present in the sources.\n"
                f"Begin your response IMMEDIATELY with '## Research Overview'. "
                f"Do not include any reasoning, planning, or preamble."
            )
            max_tokens = 2000
        
        # Model fallback chain: try multiple models in order to handle per-model quota limits
        MODEL_CANDIDATES = [
            'gemini-2.0-flash',
            'gemini-2.5-flash-lite',
            'gemini-2.5-flash',
        ]
        
        response_text = None
        last_error = None
        
        for model_name in MODEL_CANDIDATES:
            try:
                model = genai.GenerativeModel(
                    model_name=model_name,
                    system_instruction=system_instruction
                )
                
                response = model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        max_output_tokens=max_tokens,
                        temperature=0.05 if (is_factual_qa or is_evidence_extraction) else 0.1
                    )
                )
                
                response_text = response.text
                print(f"Gemini API call succeeded with model: {model_name} (intent: {query_intent})")
                break  # Success — stop trying other models
                
            except Exception as model_err:
                last_error = model_err
                print(f"Model {model_name} failed: {model_err}. Trying next model...")
                continue
        
        if response_text is None:
            raise last_error
        
        # --- POST-PROCESSING ---
        summary = response_text
        
        if is_factual_qa:
            # For factual QA: minimal post-processing — just strip CoT leakage
            summary = re.sub(r'<thinking>.*?</thinking>', '', summary, flags=re.DOTALL).strip()
            summary = re.sub(r'</?thinking>', '', summary).strip()
            # Remove any accidental report headers the LLM might have added
            summary = re.sub(r'##\s*(Research Overview|Methodology|Key Findings|Conclusion|References|Comparative Analysis|Future Scope)\s*\n?', '', summary).strip()
            # Clean CoT preamble lines
            cot_line_patterns = [
                r'(?i)^\s*(?:the user wants|I need to|let me|my analysis|I will|I should|first,? I).*$',
                r'(?i)^\s*(?:based on the|according to the)\s+(?:sources|excerpts|passages|documents)',
            ]
            cleaned_lines = []
            for line in summary.split('\n'):
                if not any(re.match(p, line.strip()) for p in cot_line_patterns):
                    cleaned_lines.append(line)
            summary = '\n'.join(cleaned_lines).strip()
            summary = clean_inline_citations(summary, formatted_chunks)
            
            thinking_display = "Detected factual question. Retrieved relevant excerpts and extracted a direct answer."
        elif is_evidence_extraction:
            # For evidence extraction: minimal post-processing — just strip CoT and headers
            summary = re.sub(r'<thinking>.*?</thinking>', '', summary, flags=re.DOTALL).strip()
            summary = re.sub(r'</?thinking>', '', summary).strip()
            summary = re.sub(r'##\s*(Research Overview|Methodology|Key Findings|Conclusion|References|Comparative Analysis|Future Scope)\s*\n?', '', summary).strip()
            
            cot_line_patterns = [
                r'(?i)^\s*(?:the user wants|I need to|let me|my analysis|I will|I should|first,? I).*$',
                r'(?i)^\s*(?:based on the|according to the)\s+(?:sources|excerpts|passages|documents)',
            ]
            cleaned_lines = []
            for line in summary.split('\n'):
                if not any(re.match(p, line.strip()) for p in cot_line_patterns):
                    cleaned_lines.append(line)
            summary = '\n'.join(cleaned_lines).strip()
            
            thinking_display = "Detected evidence extraction query. Retrieved relevant excerpts and extracted evidence-backed facts."
        else:
            # For DOCUMENT_SUMMARY and RESEARCH_SYNTHESIS: full post-processing
            # 1. Remove <thinking>...</thinking> blocks
            summary = re.sub(r'<thinking>.*?</thinking>', '', summary, flags=re.DOTALL).strip()
            summary = re.sub(r'</?thinking>', '', summary).strip()
            
            # 2. Remove common CoT preamble patterns that LLMs sometimes leak
            cot_patterns = [
                r'^.*?(?=## Research Overview)',
                r'(?i)^\s*(?:the user wants|I need to|let me|my analysis|I will|I should|first,? I).*$',
                r'(?i)^\s*(?:snippet|source|passage)\s*\d+[:\.].*$',
                r'(?i)^\s*(?:plan|step \d+|analysis|internal|reasoning)[:\.].*$',
                r'(?i)^\s*(?:here is|below is|the following|I\'ve|I have).*(?:summary|synthesis|report).*$',
            ]
            
            # First: aggressively strip everything before '## Research Overview'
            overview_match = re.search(r'## Research Overview', summary)
            if overview_match:
                summary = summary[overview_match.start():]
            else:
                cleaned_lines = []
                for line in summary.split('\n'):
                    is_cot = False
                    for pattern in cot_patterns[1:]:
                        if re.match(pattern, line.strip()):
                            is_cot = True
                            break
                    if not is_cot:
                        cleaned_lines.append(line)
                summary = '\n'.join(cleaned_lines).strip()
            
            # 3. Final cleanup: remove any remaining artifacts and format citations
            summary = re.sub(r'\n{3,}', '\n\n', summary)
            summary = clean_inline_citations(summary, formatted_chunks)
            
            mode_label = "single-document summary" if is_single_doc_mode else "grounded research synthesis"
            thinking_display = (
                f"Retrieved relevant {'excerpts' if is_single_doc_mode else 'papers'}, "
                f"reranked sources, and generated a {mode_label}."
            )
 
        return {
            "success": True,
            "status": "success",
            "message": "Report generated successfully." if not (is_factual_qa or is_evidence_extraction) else ("Answer retrieved successfully." if is_factual_qa else "Evidence extracted successfully."),
            "query": query,
            "raw_chunks": formatted_chunks,
            "summary": summary,
            "thinking": thinking_display,
            "query_intent": query_intent,
            "chunks_retrieved_count": chunks_retrieved_count,
            "unique_papers_count": unique_papers_count,
            "duplicates_removed_count": duplicates_removed_count
        }
 
    except Exception as e:
        # Graceful degradation on API call failure
        print(f"Gemini API call failed: {e}")
        return {
            "success": False,
            "status": "fallback",
            "message": f"Gemini API Error: {str(e)}. Graceful degradation active.",
            "query": query,
            "raw_chunks": formatted_chunks,
            "summary": f"SYSTEM WARNING: Gemini API Call failed ({str(e)}). Below are the raw retrieved text chunks for your query.",
            "thinking": f"Chain of Thought: LLM generation failed with exception. Displaying raw retrieved context.",
            "chunks_retrieved_count": chunks_retrieved_count,
            "unique_papers_count": unique_papers_count,
            "duplicates_removed_count": duplicates_removed_count
        }
