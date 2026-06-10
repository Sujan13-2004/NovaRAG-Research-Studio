import urllib.request
import os

def test_arxiv_download():
    # Let's try to download a real paper: GPT-4 on Medical Challenge Problems (2303.13375)
    pdf_url = "https://arxiv.org/pdf/2303.13375.pdf"
    pdf_path = "test_arxiv.pdf"
    
    print(f"Downloading from: {pdf_url}")
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        req = urllib.request.Request(pdf_url, headers=headers)
        with urllib.request.urlopen(req, timeout=25) as response:
            content_type = response.info().get('Content-Type', '')
            print(f"Content-Type: {content_type}")
            if 'pdf' in content_type.lower():
                with open(pdf_path, 'wb') as f:
                    f.write(response.read())
                print(f"Successfully downloaded {pdf_path} (size: {os.path.getsize(pdf_path)} bytes)")
                os.remove(pdf_path)
            else:
                print("Failed: Response content type is not PDF.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_arxiv_download()
