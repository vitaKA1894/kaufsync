import re

with open('frontend/src/components/AddItemModal.vue', 'r') as f:
    content = f.read()

# Update .modal-backdrop
backdrop_search = """.modal-backdrop {
  position: fixed;
  top: 0; left: 0; width: 100%; height: 100%;
  background: var(--ks-bg); /* Opaque background as requested */
  z-index: 100;
  display: flex;
  align-items: flex-start; /* Align top */
  justify-content: center;
}"""

backdrop_replace = """.modal-backdrop {
  position: fixed;
  top: 0; left: 0; width: 100%; height: 100%;
  background: rgba(0, 0, 0, 0.6); /* Semi-transparent background */
  z-index: 100;
  display: flex;
  align-items: flex-start; /* Align top */
  justify-content: center;
}"""

content = content.replace(backdrop_search, backdrop_replace)

# Modify .modal-content and add .is-details
content_search = """.modal-content {
  background: var(--ks-bg);
  width: 100%;
  max-width: var(--ks-page-width);
  padding: 16px;
  padding-top: max(16px, env(safe-area-inset-top));
  height: 100%;
  display: flex;
  flex-direction: column;
}"""

content_replace = """.modal-content {
  background: var(--ks-bg);
  width: 100%;
  max-width: var(--ks-page-width);
  padding: 16px;
  padding-top: max(16px, env(safe-area-inset-top));
  height: 100%;
  display: flex;
  flex-direction: column;
  transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
}

.modal-content.is-details {
  height: auto;
  max-height: 90vh;
  margin-top: auto;
  border-radius: 20px 20px 0 0;
  padding-top: 8px; /* Less padding on top since handle takes space */
}"""

content = content.replace(content_search, content_replace)

# Update class on modal-content in template
template_search = """      <div class="modal-content" @click.stop>"""
template_replace = """      <div class="modal-content" :class="{ 'is-details': selectedItem }" @click.stop>"""
content = content.replace(template_search, template_replace)


with open('frontend/src/components/AddItemModal.vue', 'w') as f:
    f.write(content)
