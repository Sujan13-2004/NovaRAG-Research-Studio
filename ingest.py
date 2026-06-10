import os
import io
import hashlib
import chromadb
from chromadb.utils import embedding_functions
from pypdf import PdfReader

# Default path for persistent DB
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chroma_db")
COLLECTION_NAME = "research_papers"

def get_chroma_client(db_path=DB_PATH):
    """Initializes and returns a persistent Chroma client."""
    os.makedirs(db_path, exist_ok=True)
    return chromadb.PersistentClient(path=db_path)

def get_embedding_function():
    """Returns the sentence-transformers embedding function."""
    # We use all-MiniLM-L6-v2, which is lightweight and runs locally on CPU/GPU
    return embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )

def get_collection(client, collection_name=COLLECTION_NAME):
    """Gets or creates the document collection with the local embedding function."""
    embedding_function = get_embedding_function()
    return client.get_or_create_collection(
        name=collection_name, 
        embedding_function=embedding_function
    )

def clear_collection(client, collection_name=COLLECTION_NAME):
    """Purges the entire collection to ensure a clean database rebuild."""
    try:
        client.delete_collection(name=collection_name)
        print(f"Purged collection '{collection_name}' successfully.")
    except Exception as e:
        print(f"Collection '{collection_name}' did not exist or could not be deleted: {e}")
    # Recreate the collection
    return get_collection(client, collection_name)

def generate_doc_id(file_name, file_bytes):
    """Generates a unique document ID based on the filename and MD5 content hash."""
    base_name = os.path.splitext(file_name)[0]
    clean_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in base_name).lower()
    content_hash = hashlib.md5(file_bytes).hexdigest()[:8]
    return f"{clean_name}_{content_hash}"

def add_pdf_to_vector_store(collection, file_bytes, file_name, metadata=None):
    """
    Parses a PDF from bytes, chunks the text into 500-1000 tokens (with 100-150 tokens overlap),
    tracks the page numbers for each chunk, and upserts them into ChromaDB.
    """
    doc_id = generate_doc_id(file_name, file_bytes)
    
    # Read PDF using PyPDF
    pdf_file = io.BytesIO(file_bytes)
    reader = PdfReader(pdf_file)
    
    # Extract words with their respective page numbers
    words_with_pages = []
    for i, page in enumerate(reader.pages):
        page_num = i + 1
        text = page.extract_text()
        if text:
            # Split by whitespace, keeping word and page number
            for word in text.split():
                words_with_pages.append((word, page_num))
                
    if not words_with_pages:
        return doc_id, 0
        
    # Chunking parameters: 500-1000 tokens with 100-150 tokens overlap
    # We estimate: 1 token is roughly 0.75 words.
    # 750 tokens ≈ 562 words (midpoint between 500-1000)
    # 125 tokens ≈ 94 words (midpoint between 100-150)
    chunk_size_words = 562
    overlap_words = 94
    
    chunks = []
    start = 0
    while start < len(words_with_pages):
        end = start + chunk_size_words
        chunk_data = words_with_pages[start:end]
        if not chunk_data:
            break
            
        chunk_text = " ".join([word for word, page in chunk_data])
        
        # Determine the page numbers covered by this chunk
        pages = sorted(list(set([page for word, page in chunk_data])))
        if len(pages) == 1:
            page_str = str(pages[0])
        elif len(pages) > 1:
            page_str = f"{pages[0]}-{pages[-1]}"
        else:
            page_str = "Unknown"
            
        chunks.append({
            "text": chunk_text,
            "page_str": page_str
        })
        
        if end >= len(words_with_pages):
            break
        start += chunk_size_words - overlap_words
        
    # Prepare lists for ChromaDB ingestion
    ids = []
    documents = []
    metadatas = []
    
    for idx, chunk in enumerate(chunks):
        chunk_id = f"{doc_id}_chunk_{idx + 1}"
        ids.append(chunk_id)
        documents.append(chunk["text"].strip())
        
        # Base metadata
        chunk_meta = {
            "document_id": doc_id,
            "title": file_name,
            "page_number": chunk["page_str"],
            "source": file_name
        }
        
        # Merge extra metadata if available
        if metadata:
            for k, v in metadata.items():
                if v is not None:
                    chunk_meta[k] = v
                    
        metadatas.append(chunk_meta)
        
    if not ids:
        return doc_id, 0
        
    # Upsert chunks into ChromaDB
    collection.upsert(
        ids=ids,
        documents=documents,
        metadatas=metadatas
    )
    
    # Return document ID and total chunks count
    return doc_id, len(ids)

def delete_document(collection, document_id):
    """Deletes a document (all page chunks) from the ChromaDB collection by document_id."""
    collection.delete(where={"document_id": document_id})
    return True

def list_documents(collection):
    """
    Scans the ChromaDB collection and aggregates metadata to list unique documents
    along with their page counts.
    """
    # Fetch all items' metadata from ChromaDB
    results = collection.get(include=["metadatas"])
    metadatas = results.get("metadatas", [])
    
    unique_docs = {}
    for meta in metadatas:
        doc_id = meta.get("document_id")
        if not doc_id:
            continue
            
        page_str = meta.get("page_number", "1")
        # Extract the maximum page number from a string range like "2-3" or "4"
        max_page_in_chunk = 1
        try:
            if "-" in str(page_str):
                max_page_in_chunk = int(str(page_str).split("-")[-1])
            else:
                max_page_in_chunk = int(str(page_str))
        except ValueError:
            pass
            
        if doc_id not in unique_docs:
            unique_docs[doc_id] = {
                "document_id": doc_id,
                "title": meta.get("title", "Unknown"),
                "source": meta.get("source", "Unknown"),
                "total_pages": max_page_in_chunk
            }
        else:
            if max_page_in_chunk > unique_docs[doc_id]["total_pages"]:
                unique_docs[doc_id]["total_pages"] = max_page_in_chunk
                
    return list(unique_docs.values())
