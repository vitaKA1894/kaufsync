import re

with open('frontend/src/components/AddItemModal.vue', 'r') as f:
    content = f.read()

# 1. Import BarcodeScanner
content = content.replace("import CategoryIcon from './CategoryIcon.vue';", "import CategoryIcon from './CategoryIcon.vue';\nimport BarcodeScanner from './BarcodeScanner.vue';")

# 2. Add scanner state and logic
scanner_code = """
// Scanner State
const showScanner = ref(false);

const handleScan = async (barcode) => {
    showScanner.value = false;

    try {
        const response = await fetch(`https://world.openfoodfacts.org/api/v3/product/${barcode}`, {
            headers: {
                'User-Agent': 'Kaufsync/1.0 (deine@email.de)'
            }
        });

        if (response.ok) {
            const data = await response.json();
            if (data.product) {
                const productName = data.product.product_name || '';
                const brands = data.product.brands || '';

                // Set query to product name
                query.value = productName;

                // Do taxonomy search
                const searchResults = searchTaxonomy(productName);

                let matchingItem;
                if (searchResults && searchResults.length > 0) {
                    // Fall A: Found in taxonomy
                    matchingItem = searchResults[0];
                } else {
                    // Fall B: Not found -> "Sonstiges Produkt"
                    matchingItem = {
                        name: productName,
                        category: 'Sonstiges',
                        tags: { quantities: [], constellations: [], global_meta: [] }
                    };
                }

                proceedToDetails(matchingItem);

                // Add brand to Ausprägung
                if (brands) {
                    manualUnit.value = brands;
                }
            }
        } else {
            console.warn("Product not found or API error:", response.status);
            // Optionally could show a message here
        }
    } catch (e) {
        console.error("Error fetching barcode info:", e);
    }
};
"""
content = content.replace("// Custom Amount", scanner_code + "\n// Custom Amount")

# 3. Update the modal UI
search_step_ui = """<div class="search-step" v-show="!showScanner">"""
content = content.replace("""<div v-if="!selectedItem" class="search-step">""", """<div v-if="!selectedItem" class="search-step-container" style="flex: 1; display: flex; flex-direction: column; min-height: 0;">\n        <!-- Scanner View -->\n        <BarcodeScanner v-if="showScanner" @close="showScanner = false" @scan="handleScan" />\n\n        <!-- STEP 1: Search -->\n        """ + search_step_ui)


input_header = """<div class="modal-header">
            <div style="flex: 1; display: flex; flex-direction: column; position: relative;">
              <div v-if="duplicateWarning" class="duplicate-warning">
                Dieser Artikel steht bereits auf der Liste.
                <button class="duplicate-bypass-btn" @click="proceedToDetails(results.find(r => r.name.toLowerCase() === query.toLowerCase()) || {name: query})">Trotzdem hinzufügen</button>
              </div>
              <div style="display: flex; gap: 8px; align-items: center;">
                <input
                  ref="inputRef"
                  v-model="query"
                  @input="handleInput($event); duplicateWarning = false;"
                  type="text"
                  class="modal-input"
                  :class="{ 'input-error': duplicateWarning }"
                  placeholder="Artikel suchen..."
                  @keyup.enter="confirmSelection(false)"
                />
                <button class="ks-icon-btn barcode-btn" @click="showScanner = true" style="flex-shrink: 0; border-radius: 50%; width: 48px; height: 48px; background: var(--ks-surface-2); display: flex; align-items: center; justify-content: center; border: 1px solid transparent;">
                    <svg viewBox="0 0 24 24" width="24" height="24" fill="currentColor"><path d="M3 4h4v2H5v2H3V4m14 0h4v4h-2V6h-2V4M3 20v-4h2v2h2v2H3m14 0v-2h2v-2h2v4h-4M5 10h2v4H5v-4m4 0h2v4H9v-4m4 0h2v4h-2v-4m4 0h2v4h-2v-4Z"/></svg>
                </button>
              </div>
            </div>
            <button class="close-btn ks-icon-btn" @click="closeModal">
                <svg viewBox="0 0 24 24"><path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/></svg>
            </button>
          </div>
        </div>"""

import re
# We need to replace the specific modal-header part. It is the second occurrence of <div class="modal-header">.
# Let's use string manipulation.
content = content.replace("""<div class="modal-header">
            <div style="flex: 1; display: flex; flex-direction: column; position: relative;">
              <div v-if="duplicateWarning" class="duplicate-warning">
                Dieser Artikel steht bereits auf der Liste.
                <button class="duplicate-bypass-btn" @click="proceedToDetails(results.find(r => r.name.toLowerCase() === query.toLowerCase()) || {name: query})">Trotzdem hinzufügen</button>
              </div>
              <input
                ref="inputRef"
                v-model="query"
                @input="handleInput($event); duplicateWarning = false;"
                type="text"
                class="modal-input"
                :class="{ 'input-error': duplicateWarning }"
                placeholder="Artikel suchen..."
                @keyup.enter="confirmSelection(false)"
              />
            </div>
            <button class="close-btn ks-icon-btn" @click="closeModal">
                <svg viewBox="0 0 24 24"><path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/></svg>
            </button>
          </div>
        </div>""", input_header + "\n        </div>")

# Close the new container div we added before the tags step
content = content.replace("""<!-- STEP 2: Tags Selection -->""", """<!-- STEP 2: Tags Selection -->""")


with open('frontend/src/components/AddItemModal.vue', 'w') as f:
    f.write(content)
