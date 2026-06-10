import os
import google.generativeai as genai
from dotenv import load_dotenv

def test():
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("[FAIL] GEMINI_API_KEY not found in environment or .env file.")
        return
        
    print(f"Loaded API key: {api_key[:6]}...{api_key[-6:] if len(api_key) > 12 else ''}")
    
    try:
        genai.configure(api_key=api_key)
        
        # Try models in order — per-model free-tier quotas may be exhausted
        for model_name in ['gemini-2.0-flash', 'gemini-2.5-flash-lite', 'gemini-2.5-flash']:
            try:
                model = genai.GenerativeModel(model_name)
                response = model.generate_content("Say 'Gemini API is online and key is working!' in exactly 10 words.")
                print(f"[PASS] Model: {model_name} | Response: {response.text.strip()}")
                return
            except Exception as model_err:
                print(f"[WARN] {model_name} failed: {model_err}")
                continue
        
        print("[FAIL] All model candidates exhausted their quotas.")
    except Exception as e:
        print(f"[FAIL] Gemini API call failed: {e}")

if __name__ == "__main__":
    test()
