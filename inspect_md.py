with open("reports/report_academic_comparison.md", "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx in range(29, len(lines)):
    line = lines[idx]
    if len(line) > 500:
        print(f"Line {idx+1}: Length: {len(line)} | Start: {repr(line[:150])} ... End: {repr(line[-150:])}")
    else:
        print(f"Line {idx+1}: Length: {len(line)} | Content: {repr(line)}")
