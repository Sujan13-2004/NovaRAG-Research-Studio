import urllib.request
import urllib.parse
import json
import os
import sys

# Set standard output encoding to utf-8 if possible
if sys.stdout.encoding != 'utf-8':
    try:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
    except Exception:
        pass

def safe_print(text):
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode('ascii', errors='ignore').decode('ascii'))

def test_pmc_download():
    query = "sepsis detection AI AND \"open access\"[filter]"
    encoded_query = urllib.parse.quote(query)
    search_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pmc&term={encoded_query}&retmode=json&retmax=5"
    
    safe_print(f"Searching PMC: {search_url}")
    try:
        req = urllib.request.Request(search_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as response:
            search_data = json.loads(response.read().decode('utf-8'))
            pmids = search_data.get('esearchresult', {}).get('idlist', [])
            safe_print(f"Found PMC IDs: {pmids}")
            
            if not pmids:
                safe_print("No open access articles found.")
                return
                
            pmcid = pmids[0]
            summary_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pmc&id={pmcid}&retmode=json"
            safe_print(f"Fetching summary: {summary_url}")
            
            with urllib.request.urlopen(urllib.request.Request(summary_url, headers={'User-Agent': 'Mozilla/5.0'}), timeout=15) as sum_resp:
                sum_data = json.loads(sum_resp.read().decode('utf-8'))
                result = sum_data.get('result', {}).get(pmcid, {})
                title = result.get('title')
                authors = ", ".join([a.get('name') for a in result.get('authors', [])])
                pubdate = result.get('pubdate')
                year = pubdate.split()[0] if pubdate else "Unknown"
                safe_print(f"Title: {title}")
                safe_print(f"Authors: {authors}")
                safe_print(f"Year: {year}")
                
            # Attempt to download PDF
            pdf_url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{pmcid}/pdf/"
            safe_print(f"Downloading PDF from: {pdf_url}")
            
            pdf_path = f"PMC{pmcid}.pdf"
            dl_req = urllib.request.Request(pdf_url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
            with urllib.request.urlopen(dl_req, timeout=20) as pdf_resp:
                content_type = pdf_resp.info().get('Content-Type', '')
                safe_print(f"Content-Type: {content_type}")
                if 'pdf' in content_type.lower():
                    with open(pdf_path, 'wb') as f:
                        f.write(pdf_resp.read())
                    safe_print(f"Successfully downloaded {pdf_path} (size: {os.path.getsize(pdf_path)} bytes)")
                    os.remove(pdf_path)
                else:
                    safe_print(f"Not a PDF, response content type was: {content_type}")
                    
    except Exception as e:
        safe_print(f"Error: {e}")

if __name__ == "__main__":
    test_pmc_download()
