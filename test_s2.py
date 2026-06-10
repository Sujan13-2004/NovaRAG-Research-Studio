import urllib.request
import urllib.parse
import json
import time

def test_s2():
    query = "cardiovascular risk prediction AI"
    encoded_query = urllib.parse.quote(query)
    url = f"https://api.semanticscholar.org/graph/v1/paper/search?query={encoded_query}&limit=5&fields=title,authors,year,abstract,externalIds,openAccessPdf"
    
    print(f"Querying Semantic Scholar: {url}")
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode('utf-8'))
            print(f"Found {len(data.get('data', []))} results.")
            for paper in data.get('data', []):
                title = paper.get('title')
                year = paper.get('year')
                oa = paper.get('openAccessPdf')
                print(f"Title: {title} ({year})")
                print(f"  OpenAccess: {oa}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_s2()
