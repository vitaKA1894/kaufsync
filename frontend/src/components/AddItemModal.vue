<script setup>
import { ref, onMounted, nextTick, computed } from 'vue';
import { searchTaxonomy, debounce } from '../utils/search';
import CategoryIcon from './CategoryIcon.vue';
import BarcodeScanner from './BarcodeScanner.vue';

// --- KATEGORIE DEFINITIONEN ---
const predefinedCategories = [
  { name: 'Obst & Gemüse', color: '#1B5E20', bg: '#C8E6C9' },
  { name: 'Brot & Backwaren', color: '#F57F17', bg: '#FFF9C4' },
  { name: 'Fleisch & Fisch', color: '#B71C1C', bg: '#FFCDD2' },
  { name: 'Milchprodukte & Tiefkühlkost', color: '#01579B', bg: '#B3E5FC' },
  { name: 'Vorratskammer', color: '#E65100', bg: '#FFE0B2' },
  { name: 'Getränke & Genussmittel', color: '#1A237E', bg: '#C5CAE9' },
  { name: 'Drogerie, Haushalt & Tierbedarf', color: '#006064', bg: '#B2EBF2' },
  { name: 'Sonstiges', color: '#4A148C', bg: '#E1BEE7' }
];

const mapLegacyCategory = (catName) => {
  if (catName === 'Milch & Tiefkühl') return 'Milchprodukte & Tiefkühlkost';
  if (catName === 'Getränke') return 'Getränke & Genussmittel';
  if (catName === 'Drogerie & Haushalt') return 'Drogerie, Haushalt & Tierbedarf';
  return catName;
};

const getCategoryDef = (catName) => {
  const mappedCatName = mapLegacyCategory(catName);
  return predefinedCategories.find(c => c.name === mappedCatName) || predefinedCategories[7];
};

const props = defineProps({
  isOpen: Boolean,
  startWithScanner: { type: Boolean, default: false },
  editItem: { type: Object, default: null },
  activeItems: { type: Array, default: () => [] }
});

const emit = defineEmits(['close', 'add', 'update']);

const query = ref('');
const duplicateWarning = ref(false);
const results = ref([]);
const inputRef = ref(null);
const selectedItem = ref(null);


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
                const product = data.product;
                const genericName = product.generic_name_de || product.generic_name || product.product_name_de || product.product_name || '';
                const brandsStr = product.brands || '';
                let brand = '';

                if (brandsStr) {
                    brand = brandsStr.split(',')[0].trim();
                }

                // Set query to generic product name
                query.value = genericName;

                // Do taxonomy search using generic name
                const searchResults = searchTaxonomy(genericName);

                let matchingItem;
                if (searchResults && searchResults.length > 0) {
                    // Fall A: Found in taxonomy
                    matchingItem = searchResults[0];
                } else {
                    // Fall B: Not found -> "Sonstiges Produkt"
                    matchingItem = {
                        name: genericName,
                        category: 'Sonstiges',
                        tags: { quantities: [], constellations: [], global_meta: [] }
                    };
                }

                proceedToDetails(matchingItem);

                // Add brand to Ausprägung
                if (brand) {
                    manualUnit.value = brand;
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

// Custom Amount
const showManualAmount = ref(false);
const manualQuantity = ref('');
const manualUnit = ref('');
const showCategorySelector = ref(false);

// Active tags state
const activeTags = ref([]);

const search = debounce((val) => {
  if (val && val.length >= 1) {
    results.value = searchTaxonomy(val).reverse();
  } else {
    results.value = [];
  }
}, 300);

const handleInput = (e) => {
  query.value = e.target.value;
  search(query.value);
};

const enhancedQuantities = computed(() => {
    if (!selectedItem.value || !selectedItem.value.tags || !selectedItem.value.tags.quantities) {
        return ['1', '2', '3', '4'];
    }
    const productQuantities = selectedItem.value.tags.quantities;
    const base = ['1', '2', '3', '4'];
    // Merge, ensuring base numbers come first, then product quantities without duplicates
    const combined = [...base];
    for (const q of productQuantities) {
        if (!combined.includes(q)) combined.push(q);
    }
    return combined;
});

const selectItem = (item) => {
  let finalItem = item;

  if (item.aliases && query.value && query.value.trim() !== '') {
    const qLower = query.value.trim().toLowerCase();
    const nameLower = item.name.toLowerCase();

    // Only replace name if the query does not match the primary name
    if (!nameLower.includes(qLower)) {
      const matchedAlias = item.aliases.find(a => a.toLowerCase().includes(qLower));
      if (matchedAlias) {
        finalItem = { ...item, name: matchedAlias };
      }
    }
  }

  const isDuplicate = !props.editItem && props.activeItems.some(
    i => i.name.trim().toLowerCase() === finalItem.name.trim().toLowerCase()
  );
  if (isDuplicate) {
    duplicateWarning.value = true;
    return;
  }

  proceedToDetails(finalItem);
};

const proceedToDetails = (item) => {
  // normalize item for detail view if it's from history
  if (!item.tags || typeof item.tags === 'string') {
      let parsedTags = [];
      try {
          parsedTags = typeof item.tags === 'string' ? JSON.parse(item.tags) : [];
      } catch (e) {}

      // Attempt to load proper taxonomy tags if it exists, for better UX
      const taxonomyMatch = searchTaxonomy(item.name).find(t => t.name.toLowerCase() === item.name.toLowerCase());
      if (taxonomyMatch) {
          selectedItem.value = taxonomyMatch;
      } else {
          selectedItem.value = {
              ...item,
              tags: {
                  quantities: [],
                  constellations: [],
                  global_meta: parsedTags
              }
          };
      }
  } else {
      selectedItem.value = item;
  }

  activeTags.value = []; // Reset selected tags
  showManualAmount.value = false;
  manualQuantity.value = '';
  manualUnit.value = '';
};

const toggleTag = (tag) => {
  const isQuantTag = enhancedQuantities.value.includes(tag);

  if (activeTags.value.includes(tag)) {
    activeTags.value = activeTags.value.filter(t => t !== tag);
  } else {
    if (isQuantTag) {
      // Remove any existing quantity tags before adding the new one
      activeTags.value = activeTags.value.filter(t => !enhancedQuantities.value.includes(t));
    }
    activeTags.value.push(tag);
  }
};

const parseQuantity = (input) => {
    if (!input) return { quantity: 1, unit: 'Stk' };
    const str = input.toString().trim();

    // Check if it's just a number
    if (/^\d+$/.test(str)) {
        return { quantity: parseInt(str), unit: 'Stk' };
    }

    // Check for pattern like "2 6er Träger" or "300g" or "1.5 kg"
    const match = str.match(/^([\d.,]+)\s*(.*)$/);
    if (match) {
        const numStr = match[1].replace(',', '.');
        const num = parseFloat(numStr);
        if (!isNaN(num)) {
            const unit = match[2].trim() || 'Stk';
            return { quantity: num, unit: unit };
        }
    }

    // Fallback: entire string as unit, quantity 1
    return { quantity: 1, unit: str };
};

const confirmSelection = (bypassWarning = false) => {
  if (!selectedItem.value && query.value && query.value.trim() !== '') {
    // If no item selected, try to find an exact match in the taxonomy
    const qLower = query.value.trim().toLowerCase();
    const taxonomyMatch = searchTaxonomy(query.value).find(
      t => t.name.toLowerCase() === qLower || t.aliases.some(a => a.toLowerCase() === qLower)
    );
    if (taxonomyMatch) {
      selectedItem.value = taxonomyMatch;
    }
  }

  const finalName = selectedItem.value ? selectedItem.value.name : query.value;

  if (!bypassWarning && !selectedItem.value && finalName.trim() !== '') {
    const isDuplicate = !props.editItem && props.activeItems.some(i => i.name.trim().toLowerCase() === finalName.trim().toLowerCase());
    if (isDuplicate) {
      duplicateWarning.value = true;
      return;
    }
  }

  let quantity = 1;
  let unit = 'Stk';


  // Process Menge
  if (manualQuantity.value && manualQuantity.value.trim() !== '') {
      const parsed = parseQuantity(manualQuantity.value);
      quantity = parsed.quantity;
      unit = parsed.unit;
  } else {
      const quantTags = enhancedQuantities.value;
      const selectedQuantTag = activeTags.value.find(t => quantTags.includes(t));
      if (selectedQuantTag) {
          const parsed = parseQuantity(selectedQuantTag);
          quantity = parsed.quantity;
          unit = parsed.unit;
          activeTags.value = activeTags.value.filter(t => t !== selectedQuantTag);
      }
  }

  // Process Ausprägung
  if (manualUnit.value.trim() !== '') {
      activeTags.value.push(manualUnit.value.trim());
  }


  const payload = {
    name: selectedItem.value ? selectedItem.value.name : query.value,
    category: selectedItem.value ? selectedItem.value.category : 'Sonstiges',
    tags: JSON.stringify(activeTags.value),
    quantity: quantity,
    unit: unit
  };

  if (props.editItem) {
    emit('update', { id: props.editItem.id, ...payload });
  } else {
    // Only emit add if we have a valid item or query
    if (selectedItem.value || query.value.trim() !== '') {
      emit('add', payload);
    }
  }
  closeModal();
};

const closeModal = () => {
  query.value = '';
  results.value = [];
  selectedItem.value = null;
  activeTags.value = [];
  showManualAmount.value = false;
  manualQuantity.value = '';
  manualUnit.value = '';
  duplicateWarning.value = false;
  emit('close');
};

const highlightText = (text, match) => {
  if (!match) return text;
  // Escape special regex characters to prevent syntax errors
  const escapedMatch = match.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const regex = new RegExp(`(${escapedMatch})`, 'gi');
  return text.replace(regex, '<strong>$1</strong>');
};

onMounted(() => {
  if (props.isOpen) {
    nextTick(() => {
      inputRef.value?.focus();
    });
  }
});

// Watch isOpen prop to focus input when modal is opened
import { watch } from 'vue';
watch(() => props.isOpen, (newVal) => {
    if (newVal) {
        showScanner.value = props.startWithScanner;

        if (props.editItem) {
            // Edit Mode Init
            const editItemMapped = { ...props.editItem, category: mapLegacyCategory(props.editItem.category || 'Sonstiges') };
            selectItem(editItemMapped);

            // Re-map quantity
            if (props.editItem.quantity) {
                const combinedQty = props.editItem.unit === 'Stk'
                    ? props.editItem.quantity.toString()
                    : `${props.editItem.quantity} ${props.editItem.unit}`;

                if (enhancedQuantities.value.includes(combinedQty)) {
                    activeTags.value = [combinedQty];
                } else {
                    activeTags.value = [];
                    manualQuantity.value = combinedQty;
                }
            } else {
                activeTags.value = [];
            }

            // Re-map tags (Ausprägungen)
            let tags = [];
            try { tags = typeof props.editItem.tags === 'string' ? JSON.parse(props.editItem.tags) : []; } catch(e){}

            // Check if there are tags that are not in the standard constellations/meta or quantities
            tags.forEach(t => {
                if (!enhancedQuantities.value.includes(t)) {
                    // Try to see if it's a known constellation or just append it to manualUnit if it's the first unknown
                    let isKnown = false;
                    if (selectedItem.value && selectedItem.value.tags) {
                        if (selectedItem.value.tags.constellations?.includes(t)) isKnown = true;
                        if (selectedItem.value.tags.global_meta?.includes(t)) isKnown = true;
                    }
                    if (isKnown) {
                        activeTags.value.push(t);
                    } else if (manualUnit.value === '') {
                        manualUnit.value = t;
                    } else {
                        activeTags.value.push(t);
                    }
                }
            });
        } else {
            // Add Mode Init
            nextTick(() => {
                inputRef.value?.focus();
            });
        }
    } else {
        // Reset when closed
        query.value = '';
        results.value = [];
        selectedItem.value = null;
        activeTags.value = [];
        showManualAmount.value = false;
        manualQuantity.value = '';
        manualUnit.value = '';
    }
});
</script>

<template>
  <transition name="scrim-fade">
    <div v-if="isOpen" class="modal-backdrop" @click="closeModal">
      <div class="modal-content" :class="{ 'is-details': selectedItem }" @click.stop>

        <!-- STEP 1: Search -->
        <div v-if="!selectedItem" class="search-step-container" style="flex: 1; display: flex; flex-direction: column; min-height: 0;">
        <!-- Scanner View -->
        <BarcodeScanner v-if="showScanner" @close="showScanner = false" @scan="handleScan" />

        <!-- STEP 1: Search -->
        <div class="search-step" v-show="!showScanner" style="flex-direction: column-reverse;">
          <div class="results-list" style="margin-top: 16px;">
            <template v-if="query.length >= 1">
              <div class="ks-grid items-grid" style="padding: 0 4px;">
                <div
                  v-for="item in results"
                  :key="item.id"
                  class="grid-card"
                  @click="selectItem(item)"
                >
                  <div class="card-icon-area" :style="{ background: getCategoryDef(item.category).bg, color: getCategoryDef(item.category).color }">
                    <CategoryIcon class="icon-svg" :name="item.name" :category="item.category" size="64" />
                  </div>
                  <div class="card-text-area">
                    <span class="item-name" v-html="highlightText(item.name, query)"></span>
                  </div>
                </div>
              </div>

              <div v-if="query.length >= 1 && results.length === 0" class="no-results">
                  Keine Vorschläge gefunden. Drücke Enter, um "{{ query }}" als eigenen Artikel hinzuzufügen.
              </div>
            </template>
          </div>

          <div class="modal-header">
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
              </div>
            </div>
            <button class="close-btn ks-icon-btn" @click="closeModal">
                <svg viewBox="0 0 24 24"><path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/></svg>
            </button>
          </div>
        </div>
        </div>

        <!-- STEP 2: Tags Selection -->
        <div v-else class="tags-step">
           <div class="ks-sheet__handle" style="margin: 8px auto 16px auto; width: 40px; height: 4px; background: var(--ks-border); border-radius: 2px;"></div>
           <div class="modal-header" style="justify-content: space-between; align-items: center; margin-top: 0; padding-bottom: 16px;">
              <div style="display: flex; align-items: center; gap: 12px;">
                 <!-- Empty placeholder for alignment if we don't need back button, or back button if needed, wait, the design doesn't show a back button, but has 'Eis' prominently on the left. Ah, actually in the new design we don't have a back button. But let's keep selectedItem = null functionality. I'll make the title itself clickable or just remove it if not needed? Actually, the request says 'Eis' as h2 and 'Fertig' on the right. -->
                 <h2 style="margin:0; font-size: 24px; font-weight: bold;">{{ selectedItem.name }}</h2>
              </div>
              <button class="ks-btn-text" @click="confirmSelection(false)" style="font-size: 16px; font-weight: 600; padding: 0;">Fertig</button>
           </div>

           <div class="tags-content">
               <div class="manual-amount-input mb-3" style="display: flex; gap: 8px; align-items: center;">
                   <input
                       type="text"
                       v-model="manualQuantity"
                       placeholder="Menge, Beschreibung..."
                       class="modal-input"
                       style="background: var(--ks-surface-3); font-size: 16px; padding: 14px 16px; flex: 1; min-width: 0; border-radius: 8px;"
                       @keyup.enter="confirmSelection(false)"
                   />
               </div>

               <p class="history-label" style="margin-top: 16px; font-size: 16px;">Details zu {{ selectedItem.name }}</p>

               <!-- Flat List of Tags -->
               <div class="tag-group" style="margin-bottom: 24px;">
                   <!-- Quantities -->
                   <button
                       v-for="tag in enhancedQuantities" :key="'q-'+tag"
                       class="ks-chip tag-chip tag-quantity"
                       :class="{ active: activeTags.includes(tag) }"
                       @click="toggleTag(tag)"
                   >
                       {{ tag }}
                   </button>



                   <!-- Constellations -->
                   <button
                       v-for="tag in selectedItem.tags.constellations" :key="'c-'+tag"
                       class="ks-chip tag-chip tag-meta"
                       :class="{ active: activeTags.includes(tag) }"
                       @click="toggleTag(tag)"
                   >
                       {{ tag }}
                   </button>

                   <!-- Meta Tags -->
                   <button
                       v-for="tag in selectedItem.tags.global_meta?.filter(t => !['Dringend', 'Angebot', 'Wenn\'s passt'].includes(t))" :key="'m-'+tag"
                       class="ks-chip tag-chip tag-meta"
                       :class="{ active: activeTags.includes(tag) }"
                       @click="toggleTag(tag)"
                   >
                       {{ tag }}
                   </button>

                   <!-- Separator for Dringlichkeit -->
                   <div style="flex-basis: 100%; height: 0;"></div>

                   <button
                       v-for="tag in ['Dringend', 'Angebot', 'Wenn\'s passt']" :key="'u-'+tag"
                       class="ks-chip tag-chip tag-meta urgency-tag"
                       :class="{ active: activeTags.includes(tag) }"
                       @click="toggleTag(tag)"
                       style="display: flex; align-items: center; gap: 6px;"
                   >
                       <svg v-if="tag === 'Dringend'" width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M13.5 5.5c1.1 0 2-.9 2-2s-.9-2-2-2-2 .9-2 2 .9 2 2 2zM9.8 8.9L7 23h2.1l1.8-8 2.1 2v6h2v-7.5l-2.1-2 .6-3C14.8 12 16.8 13 19 13v-2c-1.9 0-3.5-1-4.3-2.4l-1-1.6c-.4-.6-1-1-1.7-1-.3 0-.5.1-.8.1L6 8.3V13h2V9.6l1.8-.7"/></svg>
                       <svg v-if="tag === 'Angebot'" width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M21.41 11.58l-9-9C12.05 2.22 11.55 2 11 2H4c-1.1 0-2 .9-2 2v7c0 .55.22 1.05.59 1.42l9 9c.36.36.86.58 1.41.58.55 0 1.05-.22 1.41-.59l7-7c.37-.36.59-.86.59-1.41 0-.55-.23-1.06-.59-1.42zM5.5 7C4.67 7 4 6.33 4 5.5S4.67 4 5.5 4 7 4.67 7 5.5 6.33 7 5.5 7z"/></svg>
                       <svg v-if="tag === 'Wenn\'s passt'" width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-7 9h-2V7h-2v5H6v2h2v5h2v-5h2v-2zm4 5h-2v-2h2v2zm0-4h-2V7h2v6z"/></svg>
                       {{ tag }}
                   </button>
               </div>

               <p class="tag-label">Einstellungen</p>
               <div class="settings-grid">
                   <button class="settings-btn" @click="showCategorySelector = true">
                       <svg viewBox="0 0 24 24"><path d="M10 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2h-8l-2-2z"/></svg>
                       <span>Kategorie ändern</span>
                   </button>
               </div>
           </div>


        </div>

        <!-- Category Selector Sheet -->
        <transition name="sheet-slide">
          <div v-if="showCategorySelector" class="ks-sheet" @click.stop style="z-index: 101;">
            <div class="ks-sheet__handle"></div>
            <h3 class="sheet-heading">Kategorie auswählen</h3>
            <div class="category-list">
              <button
                v-for="cat in predefinedCategories"
                :key="cat.name"
                class="category-list-item"
                @click="selectedItem.category = cat.name; showCategorySelector = false"
              >
                <span class="cat-color-dot" :style="{ backgroundColor: cat.color }"></span>
                <span class="cat-name">{{ cat.name }}</span>
                <svg v-if="selectedItem.category === cat.name" class="check-icon" viewBox="0 0 24 24"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg>
              </button>
            </div>
            <button class="ks-btn-text full-width mt-3" @click="showCategorySelector = false">Abbrechen</button>
          </div>
        </transition>

      </div>
    </div>
  </transition>
</template>

<style scoped>
.modal-backdrop {
  position: fixed;
  top: 0; left: 0; width: 100%; height: 100%;
  background: rgba(0, 0, 0, 0.6); /* Semi-transparent background */
  z-index: 100;
  display: flex;
  align-items: flex-start; /* Align top */
  justify-content: center;
}

.modal-content {
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
}

.search-step {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0; /* Important for flex child to scroll */
  position: relative;
}

.modal-header {
  display: flex;
  align-items: center;
  margin-bottom: 16px; /* Space below header instead of pushing down */
}

.modal-input {
  width: 100%;
  background: var(--ks-surface-2);
  border: 1px solid transparent;
  border-radius: 12px;
  padding: 14px 16px;
  font-size: 18px;
  color: var(--ks-text);
  outline: none;
  transition: border-color 0.2s;
}
.modal-input.input-error {
  border-color: #F57F17; /* Yellow border for warning */
}
.modal-input::placeholder {
  color: var(--ks-text-muted);
}

.duplicate-warning {
  font-size: 13px;
  color: #F57F17;
  margin-bottom: 6px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 4px;
}
.duplicate-bypass-btn {
  background: transparent;
  border: none;
  color: var(--ks-primary);
  font-weight: 600;
  font-size: 13px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 8px;
}
.duplicate-bypass-btn:hover {
  background: var(--ks-primary-container);
}
.mb-3 { margin-bottom: 12px; }

.close-btn {
  margin-left: 8px;
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.close-btn svg { width: 24px; height: 24px; fill: currentColor; }

.results-list {
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  gap: 8px;
  flex: 1;
  min-height: 0;
}

.ks-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(80px, 1fr));
  gap: 12px;
}

.grid-card {
  display: flex; flex-direction: column;
  border-radius: var(--ks-radius-sm); padding: 8px 4px;
  cursor: pointer; text-align: center;
  transition: transform 0.1s, opacity 0.2s, background 0.2s, border-color 0.3s;
  position: relative;
  background: var(--ks-surface-2);
  border: 1px solid var(--ks-border);
}
.grid-card:active { transform: scale(0.95); }
.grid-card:hover { background: var(--ks-surface-3); }

.card-icon-area {
  display: flex; align-items: center; justify-content: center;
  height: 64px; margin-bottom: 12px; border-radius: var(--ks-radius-xs);
}
.icon-svg { display: flex; align-items: center; justify-content: center; width: 64px; height: 64px; }
.icon-svg :deep(svg) { width: 100%; height: 100%; }

.card-text-area { display: flex; flex-direction: column; }
.item-name {
  font-size: 12px; font-weight: 600;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;
  overflow: hidden; line-height: 1.2; color: var(--ks-text);
}

.no-results {
    padding: 16px;
    text-align: center;
    color: var(--ks-text-muted);
    font-size: 14px;
}

/* Tags Step */
.tags-step {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
}

.tags-content {
    overflow-y: auto;
    padding-bottom: 16px;
    flex: 1;
    min-height: 0;
}
.tag-section {
    margin-bottom: 24px;
}
.tag-label {
    font-size: 14px;
    font-weight: 500;
    color: var(--ks-text-muted);
    margin-bottom: 12px;
}
.tag-group {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
}
.tag-chip {
    padding: 10px 16px;
    border-radius: 20px;
    background: var(--ks-surface-2);
    border: 1px solid transparent;
    color: var(--ks-text);
}
.tag-chip.active {
    background: var(--ks-primary-container);
    color: var(--ks-primary);
    border-color: var(--ks-primary);
}
.tag-meta {
    background: var(--ks-surface-3); /* Slightly different background for meta tags */
}
.settings-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
}
.settings-btn {
    background: var(--ks-surface-2);
    border: none;
    border-radius: 12px;
    padding: 16px;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
    color: var(--ks-text);
    cursor: pointer;
    font-size: 13px;
    font-weight: 500;
}
.settings-btn svg { width: 24px; height: 24px; fill: currentColor; }

.category-list {
  display: flex; flex-direction: column; gap: 4px; max-height: 40vh; overflow-y: auto; margin-top: 12px;
}
.category-list-item {
  display: flex; align-items: center; padding: 12px 16px;
  background: var(--ks-surface-2); border: none; border-radius: 12px;
  cursor: pointer; color: var(--ks-text); font-size: 16px; text-align: left;
}
.cat-color-dot { width: 12px; height: 12px; border-radius: 50%; margin-right: 12px; }
.cat-name { flex: 1; }
.check-icon { width: 20px; height: 20px; fill: var(--ks-primary); }

.history-label {
    font-size: 14px;
    font-weight: 600;
    color: var(--ks-text-muted);
    margin: 8px 0 12px 4px;
}
.mt-3 {
    margin-top: 12px;
}
.modal-footer {
    padding-top: 16px;
    padding-bottom: env(safe-area-inset-bottom);
    margin-top: auto;
    background: var(--ks-bg);
}
.full-width {
    width: 100%;
    padding: 16px;
    font-size: 16px;
    font-weight: 600;
}
</style>
