with open("reports/test_raw.md", "r", encoding="utf-8") as f:
    lines = f.readlines()

print(f"Total lines: {len(lines)}")
for idx in range(74, len(lines)):
    print(f"Line {idx+1}: {repr(lines[idx])}")
