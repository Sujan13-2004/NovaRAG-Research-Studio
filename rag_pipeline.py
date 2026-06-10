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
        
        pattern = rf'\[\s*(?:{escaped_filename}|{escaped_title}|{re.escape(filename)})[^\]]{{0,100}}\]'
        cleaned = re.sub(pattern, f'[{rank}]', cleaned, flags=re.IGNORECASE)
        
    # Also clean general occurrences of multiple pages or verbose citations if any remain
    cleaned = re.sub(r'\[\s*(\d+)\s*,\s*Page\s*\d+\s*\]', r'[\1]', cleaned)
    cleaned = re.sub(r'\[\s*(\d+(?:\s*,\s*\d+)*)\s*\]', r'[\1]', cleaned)
    return cleaned

def run_rag_query(
    query: str, 
    api_key: str = None, 
    collection_name: str = "research_papers", 
    top_k_retrieve: int = 15,
    top_n_rerank: int = 5,
    simulate_api_failure: bool = False
) -> dict:
    """
    Executes the retrieve-rerank-generate pipeline.
    If the API fails or simulate_api_failure is True, it performs a graceful fallback.
    """
    client = get_chroma_client()
    collection = get_collection(client, collection_name)
    
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
    # Query more results to ensure we have enough unique documents to fill top_k_retrieve after grouping
    retrieval_limit = max(top_k_retrieve * 3, 50)
    retrieval_results = collection.query(
        query_texts=[query],
        n_results=retrieval_limit
    )
    
    # Check if we got any results
    if not retrieval_results or not retrieval_results.get("documents") or not retrieval_results["documents"][0]:
        return {
            "success": False,
            "status": "error",
            "message": "No relevant documents could be found for your query.",
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
    
    # 3. Retrieval Deduplication: Group chunks by document, keep highest-scoring chunk from each unique paper
    load_papers_mapping()
    
    seen_doc_ids = set()
    seen_titles = set()
    seen_arxiv_ids = set()
    
    unique_passages = []
    
    for doc, meta, id_ in zip(documents, metadatas, ids):
        doc_id = meta.get("document_id", "Unknown")
        filename = meta.get("title", "Unknown")
        
        norm_title, arxiv_id = get_paper_identifiers(filename)
        
        # Check if we've seen this paper already
        is_duplicate = False
        if doc_id != "Unknown" and doc_id in seen_doc_ids:
            is_duplicate = True
        if norm_title and norm_title in seen_titles:
            is_duplicate = True
        if arxiv_id and arxiv_id in seen_arxiv_ids:
            is_duplicate = True
            
        if is_duplicate:
            continue
            
        # Add to seen sets
        if doc_id != "Unknown":
            seen_doc_ids.add(doc_id)
        if norm_title:
            seen_titles.add(norm_title)
        if arxiv_id:
            seen_arxiv_ids.add(arxiv_id)
            
        unique_passages.append({
            "id": id_,
            "text": clean_text(doc),
            "meta": meta
        })
        
        # Keep up to top_k_retrieve unique candidates for reranking
        if len(unique_passages) >= top_k_retrieve:
            break
            
    unique_papers_count = len(unique_passages)
    duplicates_removed_count = chunks_retrieved_count - unique_papers_count
        
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
    context_str = ""
    for chunk in formatted_chunks:
        context_str += f"\n--- SOURCE [{chunk['rank']}]: {chunk['title']} (Page {chunk['page']}) ---\n"
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
        
        # Define advanced system instruction for academic paper summarizer
        system_instruction = (
            "You are an elite academic AI research assistant. Your task is to produce a "
            "professional research synthesis using ONLY the provided paper snippets. "
            "Do not fabricate facts or extrapolate beyond what is stated in the sources.\n\n"
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
            "5. Under the '## Future Scope' section, you MUST explicitly discuss potential future research directions, explicitly including exactly these topics: Federated Learning, Multi-modal AI, Explainable AI, Privacy-Preserving Healthcare Systems, and Large Biomedical Foundation Models.\n\n"
            "6. Cite sources in-text using bracketed numbers matching the source rank, e.g., [1] or [1, 2]. Do not include the PDF filename, title, or 'Page X' in the inline citation. Every claim must be cited.\n\n"
            "ABSOLUTELY FORBIDDEN in your output:\n"
            "- Phrases like 'The user wants...', 'I need to...', 'Let me...', 'My analysis...'\n"
            "- Internal labels such as 'Snippet 1', 'Snippet 2', 'Plan:', 'Step 1:'\n"
            "- Any <thinking> tags or reasoning traces\n"
            "- Any preamble, introduction of yourself, or meta-commentary\n"
            "- Bullet-point lists of your analysis steps\n\n"
            "Write in formal academic prose. Be dense, precise, and well-structured."
        )
        
        prompt = (
            f"Synthesize a professional academic research summary for the following query.\n\n"
            f"QUERY: {query}\n\n"
            f"SOURCE MATERIAL:\n{context_str}\n\n"
            f"Begin your response IMMEDIATELY with '## Research Overview'. "
            f"Do not include any reasoning, planning, or preamble."
        )
        
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
                        max_output_tokens=2000,
                        temperature=0.2
                    )
                )
                
                response_text = response.text
                print(f"Gemini API call succeeded with model: {model_name}")
                break  # Success — stop trying other models
                
            except Exception as model_err:
                last_error = model_err
                print(f"Model {model_name} failed: {model_err}. Trying next model...")
                continue
        
        if response_text is None:
            raise last_error
        
        # --- POST-PROCESSING: Strip ALL chain-of-thought leakage ---
        summary = response_text
        
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
        
        thinking_display = (
            "Retrieved relevant papers, reranked sources, and generated "
            "a grounded research synthesis."
        )
 
        return {
            "success": True,
            "status": "success",
            "message": "Report generated successfully.",
            "query": query,
            "raw_chunks": formatted_chunks,
            "summary": summary,
            "thinking": thinking_display,
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
