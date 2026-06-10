import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET

NAMESPACES = {'atom': 'http://www.w3.org/2005/Atom'}

def test_simple_query():
    query_str = 'all:sepsis AND all:detection'
    encoded_query = urllib.parse.quote(query_str)
    url = f"https://export.arxiv.org/api/query?search_query={encoded_query}&max_results=5"
    
    print(f"Querying arXiv with simple query: {url}")
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
    test_simple_query()
