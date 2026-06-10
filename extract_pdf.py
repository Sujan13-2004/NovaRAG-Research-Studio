import pypdf
import os

pdf_path = "reports/report_academic_comparison.pdf"
md_path = "reports/report_academic_comparison.md"

if not os.path.exists(pdf_path):
    print(f"Error: {pdf_path} does not exist.")
else:
    reader = pypdf.PdfReader(pdf_path)
    text_content = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        text_content.append(text)
    
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n\n".join(text_content))
    print(f"Successfully extracted text to {md_path}")
