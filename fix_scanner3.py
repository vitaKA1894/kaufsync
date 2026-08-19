import re

with open('frontend/src/components/BarcodeScanner.vue', 'r') as f:
    content = f.read()

# Fix the decode() call
content = content.replace("const code = results[0].decode;", "const code = typeof results[0].decode === 'function' ? results[0].decode() : results[0].decode;")

with open('frontend/src/components/BarcodeScanner.vue', 'w') as f:
    f.write(content)
