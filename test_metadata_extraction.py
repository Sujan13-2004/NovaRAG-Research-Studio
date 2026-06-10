import os
import urllib.request
from pypdf import PdfReader
import google.generativeai as genai
import json
from dotenv import load_dotenv

load_dotenv()

def extract_metadata_with_gemini(pdf_path):
    print("Reading PDF text...")
    reader = PdfReader(pdf_path)
    first_pages_text = ""
    for i in range(min(2, len(reader.pages))):
        text = reader.pages[i].extract_text()
        if text:
            first_pages_text += text + "\n"
            
    print(f"Extracted {len(first_pages_text)} characters.")
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY not found in environment.")
        return None
        
    genai.configure(api_key=api_key)
    
    prompt = (
        "Extract the following academic paper metadata from the text below.\n"
        "Return ONLY a raw JSON object with the keys 'title', 'authors', 'year', 'abstract'.\n"
        "Do not include markdown tags like ```json or ```. Return pure JSON.\n\n"
        f"TEXT FROM PAPER:\n{first_pages_text[:4000]}"
    )
    
    print("Calling Gemini model...")
    # Using gemini-2.0-flash since it is supported on the environment
    model = genai.GenerativeModel('gemini-2.0-flash')
    response = model.generate_content(
        prompt,
        generation_config=genai.types.GenerationConfig(
            temperature=0.1,
            response_mime_type="application/json"
        )
    )
    
    try:
        metadata = json.loads(response.text)
        return metadata
    except Exception as e:
        print(f"Failed to parse JSON: {e}")
        print(f"Raw response: {response.text}")
        return None

def main():
    pdf_url = "https://arxiv.org/pdf/2303.13375.pdf"
    pdf_path = "test_extraction.pdf"
    
    print(f"Downloading {pdf_url}...")
    headers = {'User-Agent': 'Mozilla/5.0'}
    req = urllib.request.Request(pdf_url, headers=headers)
    with urllib.request.urlopen(req, timeout=20) as resp:
        with open(pdf_path, 'wb') as f:
            f.write(resp.read())
            
    try:
        metadata = extract_metadata_with_gemini(pdf_path)
        print("\n--- EXTRACTED METADATA ---")
        print(json.dumps(metadata, indent=2))
    finally:
        if os.path.exists(pdf_path):
            os.remove(pdf_path)

if __name__ == "__main__":
    main()
