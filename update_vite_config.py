import re

with open('frontend/vite.config.js', 'r') as f:
    content = f.read()

replacement = """
export default defineConfig({
  optimizeDeps: {
    exclude: ['@undecaf/zbar-wasm']
  },
  plugins: ["""

content = content.replace("export default defineConfig({\n  plugins: [", replacement.strip() + "\n")

with open('frontend/vite.config.js', 'w') as f:
    f.write(content)
