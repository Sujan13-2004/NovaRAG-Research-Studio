from rag_pipeline import clean_inline_citations
import os

with open("reports/test_raw.md", "r", encoding="utf-8") as f:
    raw_text = f.read()

# Recreate combined_sources from list_db_papers to get titles
sources = [
  {"rank": 1, "title": "2409.00974_Enhancing_Privacy_in_Federated_Learning__Secure_Aggregation_.pdf"},
  {"rank": 2, "title": "2306.14483_Medical_Federated_Model_with_Mixture_of_Personalized_and_Sha.pdf"},
  {"rank": 3, "title": "2211.07893_Federated_Learning_for_Healthcare_Domain_-_Pipeline__Applica.pdf"},
  {"rank": 4, "title": "2306.17188_Decentralized_Healthcare_Systems_with_Federated_Learning_and.pdf"},
  {"rank": 5, "title": "2403.04130_An_Explainable_AI_Framework_for_Artificial_Intelligence_of_M.pdf"},
  {"rank": 6, "title": "2604.16340_How_Can_Explainable_Artificial_Intelligence_Improve_Trust_an.pdf"},
  {"rank": 7, "title": "2412.01829_Explainable_Artificial_Intelligence_for_Medical_Applications.pdf"},
  {"rank": 8, "title": "2305.07511_eXplainable_Artificial_Intelligence_on_Medical_Images__A_Sur.pdf"},
  {"rank": 9, "title": "2303.13375_Capabilities_of_GPT-4_on_Medical_Challenge_Problems.pdf"}
]

cleaned_text = clean_inline_citations(raw_text, sources)
print(f"Original length: {len(raw_text)}")
print(f"Cleaned length: {len(cleaned_text)}")
if len(cleaned_text) > 50000:
    print("CITATIONS CLEANING INTRODUCED SPACES!")
else:
    print("Citations cleaning is fine.")
