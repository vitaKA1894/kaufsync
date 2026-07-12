<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';

const route = useRoute();
const router = useRouter();
const listId = route.params.id;

const items = ref([]);
const currentList = ref(null);
const newItemName = ref('');
const errorMessage = ref('');
const successMessage = ref('');
const showShareSheet = ref(false);
const showSortSheet = ref(false);

let ws = null;
const isOnline = ref(navigator.onLine);

// --- KATEGORIE DEFINITIONEN ---
const predefinedCategories = [
  { name: 'Obst & Gemüse', color: 'var(--ks-success)', bg: 'var(--ks-success-bg)' },
  { name: 'Kühlregal', color: 'var(--ks-primary)', bg: 'var(--ks-primary-container)' },
  { name: 'Backwaren', color: 'var(--ks-warning)', bg: 'var(--ks-warning-bg)' },
  { name: 'Fleisch & Fisch', color: 'var(--ks-error)', bg: 'var(--ks-error-bg)' },
  { name: 'Getränke', color: 'var(--ks-secondary)', bg: 'rgba(194, 231, 255, 0.14)' },
  { name: 'Drogerie', color: 'var(--ks-text)', bg: 'var(--ks-surface-4)' },
  { name: 'Allgemein', color: 'var(--ks-text-muted)', bg: 'var(--ks-surface-3)' }
];

// --- MARKT SPEZIFISCHE DEFAULTS (JSON-Konfiguration) ---
const chainsConfig = {
  aldi: { marketType: "discounter", defaultOrder: ["Obst & Gemüse", "Backwaren", "Allgemein", "Getränke", "Kühlregal", "Fleisch & Fisch", "Drogerie"] },
  lidl: { marketType: "discounter", defaultOrder: ["Obst & Gemüse", "Backwaren", "Allgemein", "Getränke", "Kühlregal", "Fleisch & Fisch", "Drogerie"] },
  netto: { marketType: "discounter", defaultOrder: ["Obst & Gemüse", "Backwaren", "Allgemein", "Getränke", "Kühlregal", "Fleisch & Fisch", "Drogerie"] },
  penny: { marketType: "discounter", defaultOrder: ["Obst & Gemüse", "Backwaren", "Allgemein", "Getränke", "Kühlregal", "Fleisch & Fisch", "Drogerie"] },
  rewe: { marketType: "supermarket", defaultOrder: ["Obst & Gemüse", "Backwaren", "Allgemein", "Getränke", "Kühlregal", "Fleisch & Fisch", "Drogerie"] },
  edeka: { marketType: "supermarket", defaultOrder: ["Obst & Gemüse", "Backwaren", "Allgemein", "Getränke", "Kühlregal", "Fleisch & Fisch", "Drogerie"] },
  kaufland: { marketType: "supermarket", defaultOrder: ["Obst & Gemüse", "Backwaren", "Allgemein", "Getränke", "Kühlregal", "Fleisch & Fisch", "Drogerie"] },
  dm: { 
    marketType: "drugstore", 
    defaultOrder: ["Drogerie", "Allgemein", "Getränke", "Kühlregal", "Backwaren", "Obst & Gemüse", "Fleisch & Fisch"], 
    categoryMeta: { "Obst & Gemüse": { deprioritized: true }, "Fleisch & Fisch": { deprioritized: true }, "Backwaren": { deprioritized: true }, "Kühlregal": { deprioritized: true } } 
  },
  rossmann: { 
    marketType: "drugstore", 
    defaultOrder: ["Drogerie", "Allgemein", "Getränke", "Kühlregal", "Backwaren", "Obst & Gemüse", "Fleisch & Fisch"], 
    categoryMeta: { "Obst & Gemüse": { deprioritized: true }, "Fleisch & Fisch": { deprioritized: true }, "Backwaren": { deprioritized: true }, "Kühlregal": { deprioritized: true } } 
  },
  metro: { marketType: "wholesale", defaultOrder: ["Obst & Gemüse", "Fleisch & Fisch", "Kühlregal", "Backwaren", "Allgemein", "Getränke", "Drogerie"] },
  selgros: { marketType: "wholesale", defaultOrder: ["Obst & Gemüse", "Fleisch & Fisch", "Kühlregal", "Backwaren", "Allgemein", "Getränke", "Drogerie"] }
};

const selectedCategory = ref(predefinedCategories[6]); // Default: Allgemein
const categoryOrder = ref([]); 
const isCustomOrder = ref(false); // Flag, um zu wissen ob der User überschrieben hat

// Ermittelt anhand des Listennamens die zugehörige Kette (z.B. "dm Einkauf" -> "dm")
const currentChainKey = computed(() => {
  if (!currentList.value) return null;
  const name = currentList.value.name.toLowerCase();
  return Object.keys(chainsConfig).find(key => name.includes(key)) || null;
});

// Lädt Sortierung: Prio 1 = User Override (LocalStorage), Prio 2 = Markt-Default, Prio 3 = Fallback
const loadCategoryOrder = () => {
  const saved = localStorage.getItem(`ks_sort_${listId}`);
  if (saved) {
    categoryOrder.value = JSON.parse(saved);
    isCustomOrder.value = true;
  } else {
    isCustomOrder.value = false;
    const chainKey = currentChainKey.value;
    if (chainKey && chainsConfig[chainKey]) {
      categoryOrder.value = [...chainsConfig[chainKey].defaultOrder];
    } else {
      categoryOrder.value = predefinedCategories.map(c => c.name);
    }
  }
};

const saveCategoryOrder = () => {
  localStorage.setItem(`ks_sort_${listId}`, JSON.stringify(categoryOrder.value));
  isCustomOrder.value = true;
};

const resetCategoryOrder = () => {
  localStorage.removeItem(`ks_sort_${listId}`);
  loadCategoryOrder();
  showSortSheet.value = false;
  successMessage.value = "Sortierung auf Markt-Standard zurückgesetzt.";
  setTimeout(() => successMessage.value = '', 3000);
};

const moveCategory = (index, direction) => {
  if (direction === -1 && index > 0) {
    const temp = categoryOrder.value[index];
    categoryOrder.value[index] = categoryOrder.value[index - 1];
    categoryOrder.value[index - 1] = temp;
  } else if (direction === 1 && index < categoryOrder.value.length - 1) {
    const temp = categoryOrder.value[index];
    categoryOrder.value[index] = categoryOrder.value[index + 1];
    categoryOrder.value[index + 1] = temp;
  }
  saveCategoryOrder();
};

const updateOnlineStatus = () => {
  isOnline.value = navigator.onLine;
  if (isOnline.value) {
    processOfflineQueue();
    if (!ws || ws.readyState !== WebSocket.OPEN) setupWebSocket();
  }
};

const loadItems = async () => {
  try {
    const token = localStorage.getItem('token');
    const response = await fetch('http://localhost:8000/api/lists', {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!response.ok) throw new Error('Fehler beim Laden');
    const lists = await response.json();

    localStorage.setItem('cachedLists', JSON.stringify(lists));

    currentList.value = lists.find(l => l.id === listId);
    if (currentList.value) items.value = currentList.value.items;
  } catch (error) {
    const cachedData = localStorage.getItem('cachedLists');
    if (cachedData) {
      const lists = JSON.parse(cachedData);
      currentList.value = lists.find(l => l.id === listId);
      if (currentList.value) items.value = currentList.value.items;
    } else {
      errorMessage.value = "Offline: Konnte Liste nicht laden.";
    }
  } finally {
    // Wenn Liste geladen ist (egal ob API oder Cache), initialisiere die Sortierung
    loadCategoryOrder();
  }
};

const setupWebSocket = () => {
  if (!isOnline.value) return;
  try {
    ws = new WebSocket(`ws://localhost:8000/ws/${listId}`);
    ws.onerror = (error) => console.warn("WebSocket Fehler", error);
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.event === 'ITEM_UPDATED') {
        const incomingItem = data.payload.item;
        const index = items.value.findIndex(i => i.id === incomingItem.id);
        if (index !== -1) {
          items.value[index].status = incomingItem.status;
          items.value[index].quantity = incomingItem.quantity;
          items.value[index].name = incomingItem.name;
          // Kategorie Fallback, falls via WS nicht gesendet
          if (incomingItem.category) items.value[index].category = incomingItem.category;
        } else {
          items.value.push(incomingItem);
        }
      } else if (data.event === 'ITEM_DELETED') {
        items.value = items.value.filter(i => i.id !== data.payload.item_id);
      }
    };
  } catch (err) {
    console.warn("Konnte WebSocket nicht aufbauen:", err);
  }
};

const addItem = async () => {
  if (newItemName.value.trim() === '') return;
  
  // Optimistisches Update für flüssigere UX
  const tempId = 'temp-' + Date.now();
  const newItem = {
    id: tempId,
    name: newItemName.value,
    quantity: 1,
    unit: 'Stk',
    category: selectedCategory.value.name,
    status: 'active'
  };
  
  items.value.push(newItem);
  const itemNameBackup = newItemName.value;
  newItemName.value = '';

  try {
    const token = localStorage.getItem('token');
    const response = await fetch(`http://localhost:8000/api/lists/${listId}/items`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
      body: JSON.stringify({ 
        name: itemNameBackup, 
        quantity: 1, 
        unit: 'Stk',
        category: selectedCategory.value.name 
      })
    });
    
    if (response.ok) {
      const savedItem = await response.json();
      
      // FIX: Wir entfernen das Temp-Item
      items.value = items.value.filter(i => i.id !== tempId);
      
      // Prüfen, ob der WebSocket das neue Item evtl. schon hinzugefügt hat
      const alreadyAddedViaWS = items.value.some(i => i.id === savedItem.id);
      if (!alreadyAddedViaWS) {
        items.value.push(savedItem);
      }
    } else {
      throw new Error('API Fehler');
    }
  } catch (error) { 
    items.value = items.value.filter(i => i.id !== tempId);
    errorMessage.value = "Fehler beim Hinzufügen."; 
  }
};

const processOfflineQueue = async () => {
  const queue = JSON.parse(localStorage.getItem('offlineQueue') || '[]');
  if (queue.length === 0) return;

  const token = localStorage.getItem('token');
  const remainingQueue = [];
  for (const action of queue) {
    try {
      if (action.type === 'TOGGLE_STATUS') {
        await fetch(`http://localhost:8000/api/items/${action.itemId}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
          body: JSON.stringify({ status: action.newStatus })
        });
      }
    } catch (error) {
      remainingQueue.push(action);
    }
  }
  localStorage.setItem('offlineQueue', JSON.stringify(remainingQueue));
};

const toggleItemStatus = async (item) => {
  const newStatus = item.status === 'active' ? 'completed' : 'active';
  item.status = newStatus;

  try {
    const token = localStorage.getItem('token');
    const response = await fetch(`http://localhost:8000/api/items/${item.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
      body: JSON.stringify({ status: newStatus })
    });
    if (!response.ok) throw new Error('API Fehler');
  } catch (error) {
    const queue = JSON.parse(localStorage.getItem('offlineQueue') || '[]');
    queue.push({ type: 'TOGGLE_STATUS', itemId: item.id, newStatus: newStatus });
    localStorage.setItem('offlineQueue', JSON.stringify(queue));
  }
};

const deleteItem = async (itemId) => {
  // Optimistic delete
  const previousItems = [...items.value];
  items.value = items.value.filter(i => i.id !== itemId);
  
  try {
    const token = localStorage.getItem('token');
    const response = await fetch(`http://localhost:8000/api/items/${itemId}`, {
      method: 'DELETE',
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!response.ok) throw new Error();
  } catch (error) {
    items.value = previousItems;
    errorMessage.value = "Fehler beim Löschen.";
  }
};

const copyToClipboard = async () => {
  if (!currentList.value) return;
  try {
    await navigator.clipboard.writeText(currentList.value.share_code);
    successMessage.value = "Code kopiert!";
    setTimeout(() => successMessage.value = '', 2000);
  } catch (err) {
    console.error('Kopieren fehlgeschlagen', err);
  }
};

const getInitials = (name) => {
  return name.substring(0, 2).toUpperCase();
};

const getCategoryDef = (catName) => {
  return predefinedCategories.find(c => c.name === catName) || predefinedCategories[6];
};

// Sortiert die Auswahl-Chips für die Eingabezeile nach demselben Laufweg wie die Liste
const sortedCategoryChips = computed(() => {
  return [...predefinedCategories].sort((a, b) => {
    let indexA = categoryOrder.value.indexOf(a.name);
    let indexB = categoryOrder.value.indexOf(b.name);
    if (indexA === -1) indexA = 999;
    if (indexB === -1) indexB = 999;
    return indexA - indexB;
  });
});

// Berechnete Eigenschaften für Gruppierung der Listenansicht
const groupedActiveItems = computed(() => {
  const activeItems = items.value.filter(i => i.status === 'active');
  const groups = {};
  
  activeItems.forEach(item => {
    const catName = item.category || 'Allgemein';
    if (!groups[catName]) {
      groups[catName] = { 
        name: catName, 
        def: getCategoryDef(catName), 
        items: [] 
      };
    }
    groups[catName].items.push(item);
  });

  // Sortiere die Gruppen basierend auf dem aktiven Markt-Default oder User-Override
  return Object.values(groups).sort((a, b) => {
    let indexA = categoryOrder.value.indexOf(a.name);
    let indexB = categoryOrder.value.indexOf(b.name);
    if (indexA === -1) indexA = 999;
    if (indexB === -1) indexB = 999;
    return indexA - indexB;
  });
});

const completedItems = computed(() => items.value.filter(i => i.status === 'completed'));

onMounted(() => {
  loadItems(); // loadItems ruft am Ende loadCategoryOrder() auf
  setupWebSocket();
  processOfflineQueue();
  window.addEventListener('online', updateOnlineStatus);
  window.addEventListener('offline', updateOnlineStatus);
});

onUnmounted(() => {
  if (ws) ws.close();
  window.removeEventListener('online', updateOnlineStatus);
  window.removeEventListener('offline', updateOnlineStatus);
});
</script>

<template>
  <div class="page-shell list-view-layout" @click="showShareSheet = false; showSortSheet = false;">

    <header class="page-topbar" style="justify-content: space-between;">
      <div style="display: flex; align-items: center; gap: 12px; flex: 1; min-width: 0;">
        <button class="ks-icon-btn" @click.stop="router.push('/')" aria-label="Zurück">
          <svg viewBox="0 0 24 24"><path d="M11.175 19 4 12l7.175-7 1.425 1.4L7.85 11H20v2H7.85l4.75 4.6Z"/></svg>
        </button>
        <h1 class="list-title">{{ currentList ? currentList.name : 'Laden...' }}</h1>
      </div>
      <div style="display: flex; gap: 8px;">
        <button class="ks-icon-btn" @click.stop="showSortSheet = !showSortSheet" aria-label="Kategorien sortieren">
           <svg viewBox="0 0 24 24"><path d="M3 18v-2h6v2H3Zm0-5v-2h12v2H3Zm0-5V6h18v2H3Z"/></svg>
        </button>
        <button v-if="currentList" class="ks-icon-btn" @click.stop="showShareSheet = !showShareSheet" aria-label="Teilen">
          <svg viewBox="0 0 24 24"><path d="M18 22q-1.25 0-2.125-.875T15 19q0-.15.025-.325.025-.175.075-.325L7.05 13.7q-.425.4-.95.65-.525.25-1.1.25-1.25 0-2.125-.875T2 11.4q0-1.25.875-2.125T5 8.4q.575 0 1.1.25.525.25.95.65l8.05-4.65q-.05-.15-.075-.325Q15 4.15 15 4q0-1.25.875-2.125T18 1q1.25 0 2.125.875T21 4q0 1.25-.875 2.125T18 7q-.575 0-1.1-.25-.525-.25-.95-.65L7.9 10.75q.05.15.075.325.025.175.025.325 0 .15-.025.325-.025.175-.075.325l8.05 4.65q.425-.4.95-.65.525-.25 1.1-.25 1.25 0 2.125.875T21 19q0 1.25-.875 2.125T18 22Z"/></svg>
        </button>
      </div>
    </header>

    <!-- SHARE SHEET -->
    <transition name="scrim-fade">
      <div v-if="showShareSheet || showSortSheet" class="ks-sheet-scrim" @click="showShareSheet = false; showSortSheet = false;"></div>
    </transition>

    <transition name="sheet-slide">
      <div v-if="showShareSheet" class="ks-sheet" @click.stop>
        <div class="ks-sheet__handle"></div>
        <h3 class="sheet-heading">Liste teilen</h3>
        <p class="sheet-support">Gib diesen Code an Familienmitglieder, damit sie beitreten können.</p>
        <button class="code-box" @click="copyToClipboard">
          <span class="code">{{ currentList?.share_code }}</span>
          <svg viewBox="0 0 24 24"><path d="M9 18q-.825 0-1.412-.587Q7 16.825 7 16V4q0-.825.588-1.412Q8.175 2 9 2h9q.825 0 1.413.588Q20 3.175 20 4v12q0 .825-.587 1.413Q18.825 18 18 18Zm0-2h9V4H9v12Zm-4 6q-.825 0-1.412-.587Q3 20.825 3 20V6h2v14h11v2Z"/></svg>
        </button>
      </div>
    </transition>

    <!-- SORTIER SHEET -->
    <transition name="sheet-slide">
      <div v-if="showSortSheet" class="ks-sheet" @click.stop>
        <div class="ks-sheet__handle"></div>
        <h3 class="sheet-heading">Laufweg im Supermarkt</h3>
        <p class="sheet-support">Sortiere die Kategorien, damit sie deinem Weg durch den Markt entsprechen.</p>
        
        <div class="sort-list">
          <div v-for="(catName, index) in categoryOrder" :key="catName" class="sort-item">
            <div class="sort-info">
               <span class="sort-color-dot" :style="{ background: getCategoryDef(catName).color }"></span>
               <span>{{ catName }}</span>
            </div>
            <div class="sort-actions">
              <button class="ks-icon-btn small-btn" :disabled="index === 0" @click="moveCategory(index, -1)">
                <svg viewBox="0 0 24 24"><path d="M11 19V7.825L8.4 10.4L7 9l5-5 5 5-1.4 1.4-2.6-2.575V19h-2Z"/></svg>
              </button>
              <button class="ks-icon-btn small-btn" :disabled="index === categoryOrder.length - 1" @click="moveCategory(index, 1)">
                <svg viewBox="0 0 24 24"><path d="M11 5v11.175l-2.6-2.6L7 15l5 5 5-5-1.4-1.4-2.6 2.6V5h-2Z"/></svg>
              </button>
            </div>
          </div>
        </div>

        <button class="ks-btn-filled full-width" style="margin-top: 16px;" @click="showSortSheet = false">Fertig</button>
        <button v-if="isCustomOrder" class="ks-btn-text full-width" style="margin-top: 8px; color: var(--ks-error)" @click="resetCategoryOrder">
          Auf Markt-Standard zurücksetzen
        </button>
      </div>
    </transition>

    <div class="ks-snackbar-stack">
      <div v-if="!isOnline" class="ks-snackbar ks-snackbar--warning">Offline. Änderungen werden später synchronisiert.</div>
      <transition-group name="toast">
        <div v-if="errorMessage" key="err" class="ks-snackbar ks-snackbar--error">{{ errorMessage }}</div>
        <div v-if="successMessage" key="succ" class="ks-snackbar ks-snackbar--success">{{ successMessage }}</div>
      </transition-group>
    </div>

    <!-- GRUPPIERTE AKTIVE ARTIKEL -->
    <div class="list-scroll-area">
      <template v-if="groupedActiveItems.length > 0">
        <section v-for="group in groupedActiveItems" :key="group.name" class="items-section">
          
          <div class="category-header">
            <span class="category-badge" :style="{ background: group.def.bg, color: group.def.color }">
              {{ group.name }}
            </span>
            <span class="category-count">{{ group.items.length }}</span>
          </div>

          <div class="ks-grid">
            <div v-for="item in group.items" :key="item.id" class="grid-card active" @click="toggleItemStatus(item)">
              <div class="card-icon-area" :style="{ background: group.def.bg, color: group.def.color }">
                 <span class="initials">{{ getInitials(item.name) }}</span>
              </div>
              <div class="card-text-area">
                <span class="item-name">{{ item.name }}</span>
                <span class="item-meta">{{ item.quantity }} {{ item.unit }}</span>
              </div>
            </div>
          </div>
        </section>
      </template>

      <div v-if="groupedActiveItems.length === 0 && completedItems.length === 0" class="empty-state">
        <svg viewBox="0 0 24 24"><path d="M9 16.2 4.8 12l-1.4 1.4L9 19 21 7l-1.4-1.4Z"/></svg>
        <p>Deine Liste ist leer!</p>
      </div>

      <!-- ERLEDIGTE ARTIKEL -->
      <section v-if="completedItems.length > 0" class="items-section completed-section">
        <div class="category-header">
          <span class="category-badge completed-badge">Erledigt</span>
          <span class="category-count">{{ completedItems.length }}</span>
        </div>
        
        <div class="ks-grid">
          <div v-for="item in completedItems" :key="item.id" class="grid-card completed" @click="toggleItemStatus(item)">
            <div class="card-icon-area">
               <svg viewBox="0 0 24 24" style="width: 24px; height: 24px; fill: currentColor;"><path d="M9 16.2 4.8 12l-1.4 1.4L9 19 21 7l-1.4-1.4Z"/></svg>
            </div>
            <div class="card-text-area">
              <span class="item-name">{{ item.name }}</span>
            </div>
            <button class="delete-btn" @click.stop="deleteItem(item.id)" aria-label="Löschen">
              <svg viewBox="0 0 24 24"><path d="M7 21q-.825 0-1.412-.587Q5 19.825 5 19V6H4V4h5V3h6v1h5v2h-1v13q0 .825-.587 1.413Q17.825 21 17 21Zm2-4h2V8H9Zm4 0h2V8h-2Z"/></svg>
            </button>
          </div>
        </div>
      </section>
    </div>

    <!-- FLOATING INPUT BAR MIT KATEGORIE-CHIPS -->
    <div class="input-container">
      <div class="category-selector">
        <button 
          v-for="cat in sortedCategoryChips" :key="cat.name"
          class="ks-chip"
          :class="{ 'chip-active': selectedCategory.name === cat.name }"
          :style="selectedCategory.name === cat.name ? { background: cat.bg, color: cat.color, borderColor: cat.color } : {}"
          @click="selectedCategory = cat"
        >
          {{ cat.name }}
        </button>
      </div>

      <div class="floating-input-bar">
        <input
          v-model="newItemName"
          type="text"
          placeholder="Artikel hinzufügen…"
          @keyup.enter="addItem"
        />
        <button class="add-btn" @click="addItem" aria-label="Hinzufügen">
          <svg viewBox="0 0 24 24"><path d="M11 19v-6H5v-2h6V5h2v6h6v2h-6v6Z"/></svg>
        </button>
      </div>
    </div>

  </div>
</template>

<style scoped>
/* Um Platz für die doppelte Input-Bar (Chips + Input) zu machen */
.list-view-layout {
  padding-bottom: 160px; 
}

.list-title { margin: 0; font-size: 20px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.items-section { margin-bottom: 32px; }

.category-header {
  display: flex; align-items: center; gap: 12px;
  margin-bottom: 16px; padding-left: 4px;
}

.category-badge {
  padding: 6px 12px; border-radius: var(--ks-radius-xs);
  font-size: 13px; font-weight: 700; letter-spacing: 0.5px;
  text-transform: uppercase;
}
.category-count {
  font-size: 14px; color: var(--ks-text-muted); font-weight: 500;
}

.completed-badge {
  background: var(--ks-surface-3); color: var(--ks-text-muted);
}

.ks-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
  gap: 12px;
}

.grid-card {
  display: flex; flex-direction: column;
  border-radius: var(--ks-radius-sm); padding: 12px 8px;
  cursor: pointer; text-align: center;
  transition: transform 0.1s, opacity 0.2s, background 0.2s;
  position: relative;
  background: var(--ks-surface-2);
  border: 1px solid var(--ks-border);
}
.grid-card:active { transform: scale(0.95); }
.grid-card:hover { background: var(--ks-surface-3); }

/* Erledigte Artikel Styles */
.completed-section { opacity: 0.7; }
.grid-card.completed { 
  background: transparent; 
  border-color: rgba(255,255,255,0.04);
}
.grid-card.completed .card-icon-area {
  background: var(--ks-surface-4); color: var(--ks-text-muted);
}
.grid-card.completed .item-name {
  text-decoration: line-through; color: var(--ks-text-muted); font-weight: 500;
}

.card-icon-area { 
  display: flex; align-items: center; justify-content: center; 
  height: 50px; margin-bottom: 12px; border-radius: var(--ks-radius-xs);
}
.initials { font-size: 24px; font-weight: 700; }

.card-text-area { display: flex; flex-direction: column; }
.item-name { 
  font-size: 14px; font-weight: 600; 
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; 
  overflow: hidden; line-height: 1.3; color: var(--ks-text);
}
.item-meta { font-size: 12px; color: var(--ks-text-muted); margin-top: 4px; }

.delete-btn {
  position: absolute; top: -8px; right: -8px;
  width: 32px; height: 32px; border: none; border-radius: 50%;
  background: var(--ks-surface-4); color: var(--ks-error);
  display: none; align-items: center; justify-content: center;
  box-shadow: 0 2px 4px rgba(0,0,0,0.3); cursor: pointer;
}
.delete-btn svg { width: 16px; height: 16px; fill: currentColor; }
.grid-card:hover .delete-btn { display: flex; }
@media (hover: none) { .delete-btn { display: flex; opacity: 0.8; } }

.empty-state { text-align: center; padding: 40px 0; color: var(--ks-text-muted); }
.empty-state svg { width: 40px; height: 40px; opacity: 0.5; margin-bottom: 8px; fill: currentColor; margin-inline: auto; }

/* Input Bereich mit Chips */
.input-container {
  position: fixed;
  bottom: 0; left: 0; right: 0;
  background: linear-gradient(0deg, var(--ks-bg) 70%, transparent);
  padding: 0 16px 24px;
  display: flex; flex-direction: column; gap: 12px;
  z-index: 40; pointer-events: none; /* Container ist klick-durchlässig */
}
.input-container > * { pointer-events: auto; /* Kinder sind klickbar */ }

.category-selector {
  display: flex; overflow-x: auto; gap: 8px; padding-bottom: 4px;
  -ms-overflow-style: none; scrollbar-width: none;
  max-width: var(--ks-page-width); margin: 0 auto; width: 100%;
}
.category-selector::-webkit-scrollbar { display: none; }
.ks-chip { flex-shrink: 0; transition: all 0.2s ease; cursor: pointer; }
.ks-chip.chip-active { border-width: 2px; font-weight: 600; }

.floating-input-bar {
  max-width: var(--ks-page-width); margin: 0 auto; width: 100%;
  background: var(--ks-surface-4);
  border-radius: 32px;
  padding: 6px 6px 6px 20px;
  display: flex; align-items: center;
  box-shadow: var(--ks-shadow-2);
}
.floating-input-bar input {
  flex: 1; background: transparent; border: none;
  color: var(--ks-text); font-size: 16px;
  outline: none; padding: 12px 0;
}
.floating-input-bar input::placeholder { color: var(--ks-text-muted); }
.add-btn {
  width: 46px; height: 46px; flex-shrink: 0; margin-left: 8px;
  background: var(--ks-primary); color: var(--ks-on-primary);
  border: none; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  cursor: pointer; box-shadow: 0 2px 8px var(--ks-primary-container);
}
.add-btn svg { width: 24px; height: 24px; fill: currentColor; }

/* Modal & Sheets */
.sheet-heading { font-size: 20px; font-weight: 500; margin: 0 0 8px; color: var(--ks-text); }
.sheet-support { font-size: 14px; color: var(--ks-text-muted); margin: 0 0 20px; line-height: 1.4; }

.code-box {
  width: 100%; background: var(--ks-surface-3); border: none;
  border-radius: var(--ks-radius-xs);
  padding: 16px; display: flex; align-items: center; justify-content: center; gap: 16px;
  cursor: pointer; color: var(--ks-text);
}
.code-box .code { font-size: 24px; font-family: monospace; font-weight: 700; letter-spacing: 4px; }
.code-box svg { width: 24px; height: 24px; fill: currentColor; opacity: 0.6; }

/* Sort List */
.sort-list {
  display: flex; flex-direction: column; gap: 8px;
  max-height: 50vh; overflow-y: auto;
}
.sort-item {
  display: flex; align-items: center; justify-content: space-between;
  padding: 12px 16px; background: rgba(255,255,255,0.03);
  border-radius: var(--ks-radius-xs); border: 1px solid var(--ks-border);
}
.sort-info { display: flex; align-items: center; gap: 12px; font-weight: 500; }
.sort-color-dot { width: 12px; height: 12px; border-radius: 50%; }
.sort-actions { display: flex; gap: 4px; }
.small-btn { width: 36px; height: 36px; }
.small-btn:disabled { opacity: 0.2; pointer-events: none; }
.full-width { width: 100%; }
</style>