import re

with open('verify_cuj.py', 'r') as f:
    content = f.read()

# Fix path to backend and frontend
content = content.replace("cwd=os.path.join(os.getcwd(), 'backend')", "cwd=os.path.join(os.path.dirname(os.getcwd()), 'backend')")
content = content.replace("cwd=os.path.join(os.getcwd(), 'frontend')", "cwd=os.path.join(os.path.dirname(os.getcwd()), 'frontend')")

with open('verify_cuj.py', 'w') as f:
    f.write(content)
