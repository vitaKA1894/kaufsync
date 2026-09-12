import json

def read_confirm_selection(filepath="frontend/src/components/AddItemModal.vue"):
    with open(filepath, 'r') as f:
        content = f.read()

    import re
    # Extract the block defining confirmSelection
    match = re.search(r'const confirmSelection =.*?^};', content, re.DOTALL | re.MULTILINE)
    if match:
        print(match.group(0))

read_confirm_selection()
