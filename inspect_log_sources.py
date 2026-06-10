with open("C:/Users/sujan/.gemini/antigravity-ide/brain/19b3bd03-c5ed-488c-9434-d56d620f34bd/.system_generated/tasks/task-456.log", "r", encoding="utf-8") as f:
    text = f.read()

import re
match = re.search(r'Total unique papers selected across 3 domains:.*', text)
if match:
    start = match.start()
    print(text[start:start+2500])
