import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET

NAMESPACES = {'atom': 'http://www.w3.org/2005/Atom'}

def test_id_query():
    # Real papers: GPT-4 clinical (2303.13375), Med-PaLM (2305.09617), ClinicalNLP (2306.01768)
    id_list = "2303.13375,2305.09617,2306.01768"
    url = f"https://export.arxiv.org/api/query?id_list={id_list}"
    
    print(f"Querying arXiv by ID: {url}")
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as response:
            xml_data = response.read()
            
        root = ET.fromstring(xml_data)
        entries = root.findall('atom:entry', NAMESPACES)
        print(f"Found {len(entries)} entries.")
        for entry in entries:
            title_node = entry.find('atom:title', NAMESPACES)
            title = title_node.text.strip().replace('\n', ' ') if title_node is not None else "Untitled"
            print(f"- Title: {title}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_id_query()
