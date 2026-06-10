with open("reports/test_raw.md", "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx, line in enumerate(lines):
    if len(line) > 500:
        print(f"Line {idx+1}: Length: {len(line)} | Prefix: {repr(line[:120])}")
        import collections
        counter = collections.Counter(line)
        print("Most common:", counter.most_common(5))
