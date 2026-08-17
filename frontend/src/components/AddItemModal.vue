<script setup>
import { ref, onMounted, nextTick, computed } from 'vue';
import { searchTaxonomy, debounce } from '../utils/search';
import CategoryIcon from './CategoryIcon.vue';

// --- KATEGORIE DEFINITIONEN ---
const predefinedCategories = [
  { name: 'Obst & Gemüse', color: '#1B5E20', bg: '#C8E6C9' },
  { name: 'Brot & Backwaren', color: '#F57F17', bg: '#FFF9C4' },
  { name: 'Fleisch & Fisch', color: '#B71C1C', bg: '#FFCDD2' },
  { name: 'Milchprodukte & Tiefkühlkost', color: '#01579B', bg: '#B3E5FC' },
  { name: 'Vorratskammer', color: '#E65100', bg: '#FFE0B2' },
  { name: 'Getränke & Genussmittel', color: '#1A237E', bg: '#C5CAE9' },
  { name: 'Drogerie, Haushalt & Tierbedarf', color: '#006064', bg: '#B2EBF2' },
  { name: 'Sonstiges', color: 'var(--ks-text-muted)', bg: 'var(--ks-surface-3)' }
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
  editItem: { type: Object, default: null },
  activeItems: { type: Array, default: () => [] }
});

const emit = defineEmits(['close', 'add', 'update']);

const query = ref('');
const duplicateWarning = ref(false);
const results = ref([]);
const inputRef = ref(null);
const selectedItem = ref(null);

// Custom Amount
const showManualAmount = ref(false);
const manualQuantity = ref('');
const manualUnit = ref('');

// Active tags state
const activeTags = ref([]);
const frequentItems = ref([]);

const calculateFrequentItems = () => {
    try {
        const cachedData = localStorage.getItem('cachedLists');
        if (!cachedData) return [];
        const lists = JSON.parse(cachedData);
        const counts = {};
        const itemsMap = {};

        lists.forEach(list => {
            list.items.forEach(item => {
                const name = item.name.toLowerCase();
                counts[name] = (counts[name] || 0) + 1;
                if (!itemsMap[name]) itemsMap[name] = item;
            });
        });

        const sorted = Object.keys(counts).sort((a, b) => counts[b] - counts[a]).slice(0, 5);
        return sorted.map(name => itemsMap[name]);
    } catch (e) {
        return [];
    }
};

const search = debounce((val) => {
  if (val && val.length >= 3) {
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
  const isDuplicate = !props.editItem && props.activeItems.some(
    i => i.name.trim().toLowerCase() === item.name.trim().toLowerCase()
  );
  if (isDuplicate) {
    duplicateWarning.value = true;
    return;
  }

  proceedToDetails(item);
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

  // Custom amount overrides chip selection
  if (showManualAmount.value && (manualQuantity.value.trim() !== '' || manualUnit.value.trim() !== '')) {
      const qVal = parseFloat(manualQuantity.value.replace(',', '.'));
      quantity = !isNaN(qVal) ? qVal : 1;
      unit = manualUnit.value.trim() || 'Stk';
  } else {
      // Find quantity from active tags
      const quantTags = enhancedQuantities.value;
      const selectedQuantTag = activeTags.value.find(t => quantTags.includes(t));
      if (selectedQuantTag) {
          const parsed = parseQuantity(selectedQuantTag);
          quantity = parsed.quantity;
          unit = parsed.unit;
          // Remove it from active tags so it doesn't show up in the pills
          activeTags.value = activeTags.value.filter(t => t !== selectedQuantTag);
      }
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
        if (props.editItem) {
            // Edit Mode Init
            const editItemMapped = { ...props.editItem, category: mapLegacyCategory(props.editItem.category || 'Sonstiges') };
            selectItem(editItemMapped);

            // Re-map tags
            let tags = [];
            try { tags = typeof props.editItem.tags === 'string' ? JSON.parse(props.editItem.tags) : []; } catch(e){}
            activeTags.value = tags;

            // Re-map quantity
            if (props.editItem.quantity) {
                const combinedQty = props.editItem.unit === 'Stk'
                    ? props.editItem.quantity.toString()
                    : `${props.editItem.quantity} ${props.editItem.unit}`;

                if (enhancedQuantities.value.includes(combinedQty)) {
                    activeTags.value.push(combinedQty);
                } else {
                    showManualAmount.value = true;
                    manualQuantity.value = props.editItem.quantity.toString();
                    manualUnit.value = props.editItem.unit;
                }
            }
        } else {
            // Add Mode Init
            frequentItems.value = calculateFrequentItems().reverse();
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
      <div class="modal-content" @click.stop>

        <!-- STEP 1: Search -->
        <div v-if="!selectedItem" class="search-step">
          <div class="results-list">
            <!-- Frequent Items View -->
            <div v-if="query.length === 0 && frequentItems.length > 0">
              <p class="history-label">Häufig gekauft</p>
              <div
                v-for="item in frequentItems"
                :key="item.id"
                class="result-item"
                @click="selectItem(item)"
              >
                <CategoryIcon :name="item.name" :category="item.category" class="result-icon" :color="getCategoryDef(item.category).color" />
                <div class="result-text">{{ item.name }}</div>
                <span class="result-category" :style="{ background: getCategoryDef(item.category).bg, color: getCategoryDef(item.category).color }">{{ item.category }}</span>
              </div>
            </div>

            <!-- Search Results View -->
            <template v-else>
              <div
                v-for="item in results"
                :key="item.id"
                class="result-item"
                @click="selectItem(item)"
              >
                <CategoryIcon :name="item.name" :category="item.category" class="result-icon" :color="getCategoryDef(item.category).color" />
                <div class="result-text" v-html="highlightText(item.name, query)"></div>
                <span class="result-category" :style="{ background: getCategoryDef(item.category).bg, color: getCategoryDef(item.category).color }">{{ item.category }}</span>
              </div>

              <div v-if="query.length >= 3 && results.length === 0" class="no-results">
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
        </div>

        <!-- STEP 2: Tags Selection -->
        <div v-else class="tags-step">
           <div class="modal-header" style="justify-content: flex-start; gap: 12px;">
              <button class="ks-icon-btn" @click="selectedItem = null">
                 <svg viewBox="0 0 24 24"><path d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z"/></svg>
              </button>
              <h3 style="margin:0; font-size: 18px;">Details zu {{ selectedItem.name }}</h3>
           </div>

           <div class="tags-content">
               <!-- Numerische Quantifikatoren -->
               <div class="tag-section">
                   <p class="tag-label">Menge</p>
                   <div class="tag-group">
                       <button
                           v-for="tag in enhancedQuantities" :key="tag"
                           class="ks-chip tag-chip"
                           :class="{ active: activeTags.includes(tag) && !showManualAmount }"
                           @click="() => { showManualAmount = false; toggleTag(tag); }"
                       >
                           {{ tag }}
                       </button>
                       <button
                           class="ks-chip tag-chip"
                           :class="{ active: showManualAmount }"
                           @click="showManualAmount = !showManualAmount"
                       >
                           Manuell ✏️
                       </button>
                   </div>

                   <div v-if="showManualAmount" class="manual-amount-input mt-3" style="display: flex; gap: 8px; align-items: center;">
                       <input
                           type="text"
                           v-model="manualQuantity"
                           placeholder="Menge (z.B. 2)"
                           class="modal-input"
                           style="background: var(--ks-surface-3); font-size: 16px; padding: 10px 14px; flex: 1; min-width: 0;"
                           @keyup.enter="confirmSelection(false)"
                       />
                       <input
                           type="text"
                           v-model="manualUnit"
                           placeholder="Einheit (z.B. kg)"
                           class="modal-input"
                           style="background: var(--ks-surface-3); font-size: 16px; padding: 10px 14px; flex: 1.5; min-width: 0;"
                           @keyup.enter="confirmSelection(false)"
                       />
                       <button class="ks-icon-btn primary" style="background: var(--ks-primary); color: var(--ks-on-primary); width: 44px; height: 44px; border-radius: 12px;" @click="confirmSelection(false)">
                           <svg viewBox="0 0 24 24" style="width: 24px; height: 24px; fill: currentColor;"><path d="M9 16.2L4.8 12l-1.4 1.4L9 19 21 7l-1.4-1.4L9 16.2z"/></svg>
                       </button>
                   </div>
               </div>

               <!-- Produktspezifische Eigenschaften -->
               <div class="tag-section" v-if="selectedItem.tags.constellations?.length > 0">
                   <p class="tag-label">Ausprägung</p>
                   <div class="tag-group">
                       <button
                           v-for="tag in selectedItem.tags.constellations" :key="tag"
                           class="ks-chip tag-chip"
                           :class="{ active: activeTags.includes(tag) }"
                           @click="toggleTag(tag)"
                       >
                           {{ tag }}
                       </button>
                   </div>
               </div>

               <!-- Globale Meta Tags -->
               <div class="tag-section">
                   <p class="tag-label">Priorität</p>
                   <div class="tag-group">
                       <button
                           v-for="tag in selectedItem.tags.global_meta" :key="tag"
                           class="ks-chip tag-chip"
                           :class="{ active: activeTags.includes(tag) }"
                           @click="toggleTag(tag)"
                       >
                           {{ tag }}
                       </button>
                   </div>
               </div>
           </div>

           <div class="modal-footer">
               <button class="ks-btn-filled full-width" @click="confirmSelection(false)">
                   {{ editItem ? 'Speichern' : 'Zur Liste hinzufügen' }}
               </button>
           </div>
        </div>

      </div>
    </div>
  </transition>
</template>

<style scoped>
.modal-backdrop {
  position: fixed;
  top: 0; left: 0; width: 100%; height: 100%;
  background: rgba(0,0,0,0.6);
  z-index: 100;
  display: flex;
  align-items: flex-end;
  justify-content: center;
}

.modal-content {
  background: var(--ks-bg);
  width: 100%;
  max-width: var(--ks-page-width);
  border-radius: 20px 20px 0 0;
  padding: 16px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
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
  margin-top: auto; /* Push down to bottom */
  padding-bottom: env(safe-area-inset-bottom);
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
  max-height: 50vh;
  position: absolute;
  bottom: 100%;
  left: 0;
  right: 0;
  margin-bottom: 16px;
}

.result-item {
  display: flex;
  align-items: center;
  padding: 16px;
  background: var(--ks-surface-2);
  border-radius: 12px;
  cursor: pointer;
  transition: background 0.2s;
}
.result-item:active {
  background: var(--ks-surface-3);
}

.result-icon {
  width: 24px; height: 24px;
  margin-right: 12px;
  color: var(--ks-text-muted);
}

.result-text {
  flex: 1;
  font-size: 16px;
  color: var(--ks-text);
}

.result-category {
  font-size: 12px;
  color: var(--ks-text-muted);
  background: var(--ks-surface-4);
  padding: 4px 8px;
  border-radius: 12px;
}

.no-results {
    padding: 16px;
    text-align: center;
    color: var(--ks-text-muted);
    font-size: 14px;
}

/* Tags Step */
.tags-content {
    overflow-y: auto;
    padding-bottom: 16px;
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
}
.full-width {
    width: 100%;
    padding: 16px;
    font-size: 16px;
    font-weight: 600;
}
</style>
