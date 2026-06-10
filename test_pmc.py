import urllib.request
import urllib.parse
import json

def test_pmc():
    query = "sepsis detection AI"
    encoded_query = urllib.parse.quote(query)
    url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pmc&term={encoded_query}&retmode=json&retmax=5"
    
    print(f"Querying PMC: {url}")
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode('utf-8'))
            print("Response keys:", data.keys())
            id_list = data.get('esearchresult', {}).get('idlist', [])
            print(f"Found PMC IDs: {id_list}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_pmc()
