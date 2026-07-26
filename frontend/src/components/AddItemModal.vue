<script setup>
import { ref, onMounted, nextTick } from 'vue';
import { searchTaxonomy, debounce } from '../utils/search';
import CategoryIcon from './CategoryIcon.vue';

const props = defineProps({
  isOpen: Boolean
});

const emit = defineEmits(['close', 'add']);

const query = ref('');
const results = ref([]);
const inputRef = ref(null);
const selectedItem = ref(null);

// Active tags state
const activeTags = ref([]);

const search = debounce((val) => {
  if (val && val.length >= 3) {
    results.value = searchTaxonomy(val);
  } else {
    results.value = [];
  }
}, 300);

const handleInput = (e) => {
  query.value = e.target.value;
  search(query.value);
};

const selectItem = (item) => {
  selectedItem.value = item;
  activeTags.value = []; // Reset selected tags
};

const toggleTag = (tag) => {
  if (activeTags.value.includes(tag)) {
    activeTags.value = activeTags.value.filter(t => t !== tag);
  } else {
    activeTags.value.push(tag);
  }
};

const confirmSelection = () => {
  if (!selectedItem.value) {
    // Custom item without tags
    if (query.value.trim() !== '') {
        emit('add', {
            name: query.value,
            category: 'Sonstiges',
            tags: JSON.stringify(activeTags.value)
        });
    }
  } else {
    emit('add', {
      name: selectedItem.value.name,
      category: selectedItem.value.category,
      tags: JSON.stringify(activeTags.value)
    });
  }
  closeModal();
};

const closeModal = () => {
  query.value = '';
  results.value = [];
  selectedItem.value = null;
  activeTags.value = [];
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
        nextTick(() => {
            inputRef.value?.focus();
        });
    } else {
        // Reset when closed
        query.value = '';
        results.value = [];
        selectedItem.value = null;
        activeTags.value = [];
    }
});
</script>

<template>
  <transition name="scrim-fade">
    <div v-if="isOpen" class="modal-backdrop" @click="closeModal">
      <div class="modal-content" @click.stop>

        <!-- STEP 1: Search -->
        <div v-if="!selectedItem" class="search-step">
          <div class="modal-header">
            <input
              ref="inputRef"
              v-model="query"
              @input="handleInput"
              type="text"
              class="modal-input"
              placeholder="Artikel suchen..."
              @keyup.enter="confirmSelection"
            />
            <button class="close-btn ks-icon-btn" @click="closeModal">
                <svg viewBox="0 0 24 24"><path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/></svg>
            </button>
          </div>

          <div class="results-list">
            <div
              v-for="item in results"
              :key="item.id"
              class="result-item"
              @click="selectItem(item)"
            >
              <CategoryIcon :name="item.name" :category="item.category" class="result-icon" />
              <div class="result-text" v-html="highlightText(item.name, query)"></div>
              <span class="result-category">{{ item.category }}</span>
            </div>

            <div v-if="query.length >= 3 && results.length === 0" class="no-results">
                Keine Vorschläge gefunden. Drücke Enter, um "{{ query }}" als eigenen Artikel hinzuzufügen.
            </div>
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
               <div class="tag-section" v-if="selectedItem.tags.quantities?.length > 0">
                   <p class="tag-label">Menge</p>
                   <div class="tag-group">
                       <button
                           v-for="tag in selectedItem.tags.quantities" :key="tag"
                           class="ks-chip tag-chip"
                           :class="{ active: activeTags.includes(tag) }"
                           @click="toggleTag(tag)"
                       >
                           {{ tag }}
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
               <button class="ks-btn-filled full-width" @click="confirmSelection">Zur Liste hinzufügen</button>
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

.modal-header {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
}

.modal-input {
  flex: 1;
  background: var(--ks-surface-2);
  border: none;
  border-radius: 12px;
  padding: 14px 16px;
  font-size: 18px;
  color: var(--ks-text);
  outline: none;
}
.modal-input::placeholder {
  color: var(--ks-text-muted);
}

.close-btn {
  margin-left: 8px;
}
.close-btn svg { width: 24px; height: 24px; fill: currentColor; }

.results-list {
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  gap: 8px;
  padding-bottom: env(safe-area-inset-bottom);
}

.result-item {
  display: flex;
  align-items: center;
  padding: 12px;
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
