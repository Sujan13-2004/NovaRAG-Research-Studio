from test_direct_call import combined_sources
for src in combined_sources:
    text = src["text"]
    import re
    space_runs = re.findall(r' {5,}', text)
    if space_runs:
        print(f"Source: {src['title']} has runs of spaces: {[(len(run), text[max(0, text.find(run)-30):text.find(run)+len(run)+30]) for run in space_runs[:3]]}")
