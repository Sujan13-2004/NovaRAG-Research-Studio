with open("C:/Users/sujan/.gemini/antigravity-ide/brain/19b3bd03-c5ed-488c-9434-d56d620f34bd/.system_generated/tasks/task-534.log", "r", encoding="utf-8") as f:
    text = f.read()

import re
matches = re.findall(r'(Gemini call succeeded with model:.*|Model.*failed:.*)', text)
for m in matches:
    print(m)
