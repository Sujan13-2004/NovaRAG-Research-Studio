with open("reports/report_academic_comparison.md", "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx, line in enumerate(lines):
    print(f"Line {idx+1}: Length: {len(line)} | Prefix: {repr(line[:120])}")
