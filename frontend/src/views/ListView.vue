<script setup>
import { ref, onMounted, onUnmounted, computed, nextTick, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import CategoryIcon from '../components/CategoryIcon.vue';
import AddItemModal from '../components/AddItemModal.vue';
import ConfirmModal from '../components/ConfirmModal.vue';
import Sortable from 'sortablejs';

const route = useRoute();
const router = useRouter();
const listId = route.params.id;

const items = ref([]);
const currentList = ref(null);
const newItemName = ref('');
const isAddModalOpen = ref(false);
const startScanner = ref(false);
const itemToEdit = ref(null);
const errorMessage = ref('');
const showConfirmModal = ref(false);
const confirmMessage = ref('');
const confirmAction = ref(null);
const successMessage = ref('');
const showShareSheet = ref(false);
const showSortSheet = ref(false);
const showChangelogSheet = ref(false);
const sortListRef = ref(null);
let sortableInstance = null;

const searchQuery = ref('');
const searchResults = ref([]);
const isSearching = ref(false);

const changelog = ref([]);
const changelogFilter = ref('all'); // 'all', 'added', 'completed'

let ws = null;
const isOnline = ref(navigator.onLine);

// --- LONG PRESS GESTURE ---
let pressTimer = null;
let longPressTriggered = false;

const startPress = (item, event) => {
  if (event.type === 'mousedown' && event.button !== 0) return; // Only left click
  longPressTriggered = false;
  pressTimer = setTimeout(() => {
    longPressTriggered = true;
    itemToEdit.value = item;
    startScanner.value = false;
    isAddModalOpen.value = true;
  }, 500); // 500ms for long press
};

const openAddModal = () => {
    startScanner.value = false;
    isAddModalOpen.value = true;
};

const openScannerModal = () => {
    startScanner.value = true;
    isAddModalOpen.value = true;
};

const cancelPress = () => {
  if (pressTimer !== null) {
    clearTimeout(pressTimer);
    pressTimer = null;
  }
};

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

const getTagStyle = (tag) => {
  const t = tag.toLowerCase();
  if (t === 'bio') return { bg: '#E8F5E9', color: '#2E7D32' };
  if (t === 'vegan') return { bg: '#F1F8E9', color: '#33691E' };
  if (t === 'angebot' || t === 'dringend') return { bg: '#FFEBEE', color: '#C62828' };
  if (t === 'regional') return { bg: '#FFF3E0', color: '#EF6C00' };
  if (t === "wenn's passt") return { bg: '#E3F2FD', color: '#1565C0' };
  return { bg: 'var(--ks-surface-4)', color: 'var(--ks-text-muted)' };
};

const formatQuantity = (item) => {
  if (!item.quantity) return '';
  const q = item.quantity;
  const u = item.unit || 'Stk';
  // Avoid printing "1 Stk" if they chose custom units, print nicely
  const qStr = (q % 1 === 0) ? q.toString() : q.toString();
  return `${qStr} ${u}`.trim();
};

const parseTags = (tagsStr) => {
  if (!tagsStr) return [];
  try {
    return typeof tagsStr === 'string' ? JSON.parse(tagsStr) : tagsStr;
  } catch (e) {
    return [];
  }
};

// --- MARKT SPEZIFISCHE DEFAULTS (JSON-Konfiguration) ---
const chainsConfig = {
  aldi: { marketType: "discounter", defaultOrder: ["Obst & Gemüse", "Brot & Backwaren", "Fleisch & Fisch", "Milchprodukte & Tiefkühlkost", "Vorratskammer", "Getränke & Genussmittel", "Drogerie, Haushalt & Tierbedarf", "Sonstiges"] },
  lidl: { marketType: "discounter", defaultOrder: ["Obst & Gemüse", "Brot & Backwaren", "Fleisch & Fisch", "Milchprodukte & Tiefkühlkost", "Vorratskammer", "Getränke & Genussmittel", "Drogerie, Haushalt & Tierbedarf", "Sonstiges"] },
  netto: { marketType: "discounter", defaultOrder: ["Obst & Gemüse", "Brot & Backwaren", "Fleisch & Fisch", "Milchprodukte & Tiefkühlkost", "Vorratskammer", "Getränke & Genussmittel", "Drogerie, Haushalt & Tierbedarf", "Sonstiges"] },
  penny: { marketType: "discounter", defaultOrder: ["Obst & Gemüse", "Brot & Backwaren", "Fleisch & Fisch", "Milchprodukte & Tiefkühlkost", "Vorratskammer", "Getränke & Genussmittel", "Drogerie, Haushalt & Tierbedarf", "Sonstiges"] },
  rewe: { marketType: "supermarket", defaultOrder: ["Obst & Gemüse", "Brot & Backwaren", "Fleisch & Fisch", "Milchprodukte & Tiefkühlkost", "Vorratskammer", "Getränke & Genussmittel", "Drogerie, Haushalt & Tierbedarf", "Sonstiges"] },
  edeka: { marketType: "supermarket", defaultOrder: ["Obst & Gemüse", "Brot & Backwaren", "Fleisch & Fisch", "Milchprodukte & Tiefkühlkost", "Vorratskammer", "Getränke & Genussmittel", "Drogerie, Haushalt & Tierbedarf", "Sonstiges"] },
  kaufland: { marketType: "supermarket", defaultOrder: ["Obst & Gemüse", "Brot & Backwaren", "Fleisch & Fisch", "Milchprodukte & Tiefkühlkost", "Vorratskammer", "Getränke & Genussmittel", "Drogerie, Haushalt & Tierbedarf", "Sonstiges"] },
  dm: { 
    marketType: "drugstore", 
    defaultOrder: ["Drogerie, Haushalt & Tierbedarf", "Sonstiges", "Getränke & Genussmittel", "Milchprodukte & Tiefkühlkost", "Brot & Backwaren", "Obst & Gemüse", "Fleisch & Fisch"],
    categoryMeta: { "Obst & Gemüse": { deprioritized: true }, "Fleisch & Fisch": { deprioritized: true }, "Brot & Backwaren": { deprioritized: true }, "Milchprodukte & Tiefkühlkost": { deprioritized: true } }
  },
  rossmann: { 
    marketType: "drugstore", 
    defaultOrder: ["Drogerie, Haushalt & Tierbedarf", "Sonstiges", "Getränke & Genussmittel", "Milchprodukte & Tiefkühlkost", "Brot & Backwaren", "Obst & Gemüse", "Fleisch & Fisch"],
    categoryMeta: { "Obst & Gemüse": { deprioritized: true }, "Fleisch & Fisch": { deprioritized: true }, "Brot & Backwaren": { deprioritized: true }, "Milchprodukte & Tiefkühlkost": { deprioritized: true } }
  },
  metro: { marketType: "wholesale", defaultOrder: ["Obst & Gemüse", "Fleisch & Fisch", "Milchprodukte & Tiefkühlkost", "Brot & Backwaren", "Vorratskammer", "Getränke & Genussmittel", "Drogerie, Haushalt & Tierbedarf", "Sonstiges"] },
  selgros: { marketType: "wholesale", defaultOrder: ["Obst & Gemüse", "Fleisch & Fisch", "Milchprodukte & Tiefkühlkost", "Brot & Backwaren", "Vorratskammer", "Getränke & Genussmittel", "Drogerie, Haushalt & Tierbedarf", "Sonstiges"] }
};

const selectedCategory = ref(predefinedCategories[7]); // Default: Sonstiges
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

watch(showSortSheet, async (newVal) => {
  if (newVal) {
    await nextTick();
    if (sortListRef.value && !sortableInstance) {
      sortableInstance = new Sortable(sortListRef.value, {
        handle: '.drag-handle',
        animation: 150,
        onEnd: (evt) => {
          const itemEl = evt.item;
          const oldIndex = evt.oldIndex;
          const newIndex = evt.newIndex;

          const temp = categoryOrder.value[oldIndex];
          categoryOrder.value.splice(oldIndex, 1);
          categoryOrder.value.splice(newIndex, 0, temp);
          saveCategoryOrder();
        }
      });
    }
  } else {
    if (sortableInstance) {
      sortableInstance.destroy();
      sortableInstance = null;
    }
  }
});


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
    const response = await fetch('/api/lists', {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (response.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('isLoggedIn');
      router.push('/login');
      return;
    }
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
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    ws = new WebSocket(`${protocol}//${window.location.host}/ws/${listId}`);
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
          items.value[index].unit = incomingItem.unit;
          items.value[index].tags = incomingItem.tags;
          // Kategorie Fallback, falls via WS nicht gesendet
          if (incomingItem.category) items.value[index].category = incomingItem.category;
        } else {
          // If the item starts with "temp-", it's an optimistic addition
          const tempIndex = items.value.findIndex(i => i.id.startsWith('temp-') && i.name === incomingItem.name);
          if (tempIndex !== -1) {
              items.value[tempIndex] = incomingItem;
          } else {
              items.value.push(incomingItem);
          }
        }
      } else if (data.event === 'ITEM_DELETED') {
        items.value = items.value.filter(i => i.id !== data.payload.item_id);
      } else if (data.event === 'CHANGELOG_UPDATED') {
        if (showChangelogSheet.value) {
          loadChangelog();
        }
      }
    };
  } catch (err) {
    console.warn("Konnte WebSocket nicht aufbauen:", err);
  }
};

const handleUpdateItem = async (updatedPayload) => {
  const index = items.value.findIndex(i => i.id === updatedPayload.id);
  if (index !== -1) {
    const originalItem = { ...items.value[index] };
    items.value[index] = { ...items.value[index], ...updatedPayload };
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/items/${updatedPayload.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify(updatedPayload)
      });
      if (!response.ok) throw new Error('API Fehler');
    } catch (error) {
      items.value[index] = originalItem;
      errorMessage.value = "Offline: Konnte Artikel nicht aktualisieren.";
    }
  }
};

const handleAddItem = async (itemPayload) => {
  // Optimistisches Update
  const tempId = 'temp-' + Date.now();
  const newItem = {
    id: tempId,
    name: itemPayload.name,
    quantity: itemPayload.quantity || 1,
    unit: itemPayload.unit || 'Stk',
    category: itemPayload.category,
    tags: itemPayload.tags,
    status: 'active'
  };
  
  items.value.push(newItem);

  try {
    const token = localStorage.getItem('token');
    const response = await fetch(`/api/lists/${listId}/items`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
      body: JSON.stringify({ 
        name: itemPayload.name,
        quantity: itemPayload.quantity || 1,
        unit: itemPayload.unit || 'Stk',
        category: itemPayload.category,
        tags: itemPayload.tags
      })
    });
    
    if (response.ok) {
      const savedItem = await response.json();
      items.value = items.value.filter(i => i.id !== tempId);
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
        await fetch(`/api/items/${action.itemId}`, {
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
  if (longPressTriggered) {
    longPressTriggered = false;
    return;
  }
  const newStatus = item.status === 'active' ? 'completed' : 'active';

  // Prevent duplicate reactivation
  if (newStatus === 'active') {
    const existingActiveItem = items.value.find(
      i => i.name.toLowerCase() === item.name.toLowerCase() && i.status === 'active'
    );
    if (existingActiveItem) {
      // Highlight existing item
      const existingEl = document.getElementById(`item-${existingActiveItem.id}`);
      if (existingEl) {
        existingEl.classList.add('flash-highlight');
        setTimeout(() => existingEl.classList.remove('flash-highlight'), 1000);
      }
      return;
    }
  }

  item.status = newStatus;

  try {
    const token = localStorage.getItem('token');
    const response = await fetch(`/api/items/${item.id}`, {
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

const executeConfirmAction = async () => {
  if (confirmAction.value) {
    await confirmAction.value();
  }
  showConfirmModal.value = false;
  confirmAction.value = null;
};

const clearCompleted = async () => {
  const completedIds = completedItems.value.map(item => item.id);
  if (completedIds.length === 0) return;

  confirmMessage.value = `Möchtest du wirklich alle ${completedIds.length} erledigten Artikel löschen?`;
  confirmAction.value = async () => {
    for (const id of completedIds) {
      await deleteItem(id);
    }
  };
  showConfirmModal.value = true;
};

const confirmDeleteItem = (item) => {
  confirmMessage.value = `Möchtest du '${item.name}' wirklich löschen?`;
  confirmAction.value = async () => {
    await deleteItem(item.id);
  };
  showConfirmModal.value = true;
};

const deleteItem = async (itemId) => {
  // Optimistic delete
  const previousItems = [...items.value];
  items.value = items.value.filter(i => i.id !== itemId);
  
  try {
    const token = localStorage.getItem('token');
    const response = await fetch(`/api/items/${itemId}`, {
      method: 'DELETE',
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!response.ok) throw new Error();
  } catch (error) {
    items.value = previousItems;
    errorMessage.value = "Fehler beim Löschen.";
  }
};

const loadChangelog = async () => {
  try {
    const token = localStorage.getItem('token');
    const response = await fetch(`/api/lists/${listId}/changelog`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (response.ok) {
      changelog.value = await response.json();
    }
  } catch (error) {
    console.error("Fehler beim Laden des Changelogs", error);
  }
};

const openChangelog = () => {
  showChangelogSheet.value = true;
  loadChangelog();
};

const filteredChangelog = computed(() => {
  if (changelogFilter.value === 'added') return changelog.value.filter(log => log.action_type === 'added');
  if (changelogFilter.value === 'completed') return changelog.value.filter(log => log.action_type === 'completed');
  return changelog.value;
});

const formatChangelogTime = (dateStr) => {
  const d = new Date(dateStr + 'Z');
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) + ' Uhr';
};

const formatChangelogAction = (action) => {
  const map = {
    'added': 'hat hinzugefügt:',
    'completed': 'hat abgehakt:',
    'deleted': 'hat gelöscht:',
    'reactivated': 'hat wiederhergestellt:'
  };
  return map[action] || action;
};

const getInitial = (name) => {
  if (!name) return '?';
  return name.charAt(0).toUpperCase();
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

const searchUsers = async () => {
  if (searchQuery.value.length < 2) {
    searchResults.value = [];
    return;
  }
  isSearching.value = true;
  try {
    const token = localStorage.getItem('token');
    const response = await fetch(`/api/users/search?q=${encodeURIComponent(searchQuery.value)}`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (response.ok) {
      searchResults.value = await response.json();
    }
  } catch (error) {
    console.error('Fehler bei der Benutzersuche', error);
  } finally {
    isSearching.value = false;
  }
};

let searchTimeout;
const debouncedSearch = () => {
  clearTimeout(searchTimeout);
  searchTimeout = setTimeout(searchUsers, 300);
};

const inviteUser = async (userId) => {
  try {
    const token = localStorage.getItem('token');
    const listId = route.params.id;
    const response = await fetch(`/api/lists/${listId}/invite`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ invitee_id: userId })
    });

    if (response.ok) {
      successMessage.value = "Einladung versendet!";
      searchQuery.value = '';
      searchResults.value = [];
      setTimeout(() => successMessage.value = '', 3000);
    } else {
      const data = await response.json();
      throw new Error(data.detail || "Fehler beim Einladen");
    }
  } catch (error) {
    errorMessage.value = error.message;
    setTimeout(() => errorMessage.value = '', 3000);
  }
};

const getInitials = (name) => {
  return name.substring(0, 2).toUpperCase();
};

const getCategoryDef = (catName) => {
  return predefinedCategories.find(c => c.name === catName) || predefinedCategories[7];
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

const mapLegacyCategory = (catName) => {
  if (catName === 'Milch & Tiefkühl') return 'Milchprodukte & Tiefkühlkost';
  if (catName === 'Getränke') return 'Getränke & Genussmittel';
  if (catName === 'Drogerie & Haushalt') return 'Drogerie, Haushalt & Tierbedarf';
  return catName;
};

// Berechnete Eigenschaften für Gruppierung der Listenansicht
const groupedActiveItems = computed(() => {
  const activeItems = items.value.filter(i => i.status === 'active');
  const groups = {};
  
  activeItems.forEach(item => {
    let catName = item.category || 'Sonstiges';
    catName = mapLegacyCategory(catName);

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

const completedItems = computed(() => items.value.filter(i => i.status === 'completed').map(item => {
  let catName = item.category || 'Sonstiges';
  return { ...item, category: mapLegacyCategory(catName) };
}));

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
  <div class="page-shell list-view-layout" @click="showShareSheet = false; showSortSheet = false; showChangelogSheet = false;">

    <header class="page-topbar" style="justify-content: space-between;">
      <div style="display: flex; align-items: center; gap: 8px; flex: 1; min-width: 0;">
        <img src="/android-chrome-512x512.png" alt="KaufSync Logo" style="width: 24px; height: 24px; object-fit: contain; margin-right: 4px;">
        <button class="ks-icon-btn" @click.stop="router.push('/')" aria-label="Zurück">
          <svg viewBox="0 0 24 24"><path d="M11.175 19 4 12l7.175-7 1.425 1.4L7.85 11H20v2H7.85l4.75 4.6Z"/></svg>
        </button>
        <h1 class="list-title">{{ currentList ? currentList.name : 'Laden...' }}</h1>
      </div>
      <div style="display: flex; gap: 8px;">
        <button class="ks-icon-btn" @click.stop="openChangelog" aria-label="Aktivitätenprotokoll">
           <svg viewBox="0 0 24 24"><path d="M11.99 2C6.47 2 2 6.48 2 12s4.47 10 9.99 10C17.52 22 22 17.52 22 12S17.52 2 11.99 2zM12 20c-4.42 0-8-3.58-8-8s3.58-8 8-8 8 3.58 8 8-3.58 8-8 8zm.5-13H11v6l5.25 3.15.75-1.23-4.5-2.67z"/></svg>
        </button>
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
      <div v-if="showShareSheet || showSortSheet || showChangelogSheet" class="ks-sheet-scrim" @click="showShareSheet = false; showSortSheet = false; showChangelogSheet = false;"></div>
    </transition>

    <transition name="sheet-slide">
      <div v-if="showShareSheet" class="ks-sheet" @click.stop>
        <div class="ks-sheet__handle"></div>
        <h3 class="sheet-heading">Liste teilen</h3>

        <div class="share-section">
          <p class="section-label">Per Code einladen</p>
          <button class="code-box" @click="copyToClipboard">
            <span class="code">{{ currentList?.share_code }}</span>
            <svg viewBox="0 0 24 24"><path d="M9 18q-.825 0-1.412-.587Q7 16.825 7 16V4q0-.825.588-1.412Q8.175 2 9 2h9q.825 0 1.413.588Q20 3.175 20 4v12q0 .825-.587 1.413Q18.825 18 18 18Zm0-2h9V4H9v12Zm-4 6q-.825 0-1.412-.587Q3 20.825 3 20V6h2v14h11v2Z"/></svg>
          </button>
        </div>

        <div class="share-section mt-4">
          <p class="section-label">Benutzer suchen</p>
          <div class="search-box">
            <input
              v-model="searchQuery"
              @input="debouncedSearch"
              type="text"
              placeholder="Name oder E-Mail"
              class="search-input"
            />
          </div>

          <div v-if="searchResults.length > 0" class="search-results">
            <div v-for="user in searchResults" :key="user.id" class="user-result-item">
              <div class="user-info">
                <span class="user-name">{{ user.display_name }}</span>
                <span class="user-email">{{ user.email }}</span>
              </div>
              <button class="ks-btn-filled" @click="inviteUser(user.id)">Einladen</button>
            </div>
          </div>
          <p v-else-if="searchQuery.length >= 2 && !isSearching" class="no-results">Keine Benutzer gefunden</p>
        </div>
      </div>
    </transition>

    <!-- CHANGELOG SHEET -->
    <transition name="sheet-slide">
      <div v-if="showChangelogSheet" class="ks-sheet" @click.stop>
        <div class="ks-sheet__handle"></div>
        <div class="modal-header" style="justify-content: space-between; margin-bottom: 16px;">
            <h3 class="sheet-heading" style="margin: 0;">Aktivitäten</h3>
            <button class="close-btn ks-icon-btn" @click="showChangelogSheet = false">
                <svg viewBox="0 0 24 24"><path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/></svg>
            </button>
        </div>

        <div class="tag-group" style="margin-bottom: 16px;">
            <button class="ks-chip tag-chip" :class="{ active: changelogFilter === 'all' }" @click="changelogFilter = 'all'">Alle</button>
            <button class="ks-chip tag-chip" :class="{ active: changelogFilter === 'added' }" @click="changelogFilter = 'added'">Hinzugefügt</button>
            <button class="ks-chip tag-chip" :class="{ active: changelogFilter === 'completed' }" @click="changelogFilter = 'completed'">Abgehakt</button>
        </div>

        <div class="changelog-list" style="max-height: 50vh; overflow-y: auto;">
            <div v-for="log in filteredChangelog" :key="log.id" class="changelog-item">
                <div class="changelog-avatar">{{ getInitial(log.user_name) }}</div>
                <div class="changelog-content">
                    <div class="changelog-meta">
                        <span class="changelog-user">{{ log.user_name || 'Unbekannt' }}</span>
                        <span class="changelog-time">{{ formatChangelogTime(log.created_at) }}</span>
                    </div>
                    <div class="changelog-action">
                        {{ formatChangelogAction(log.action_type) }} <strong>{{ log.item_name }}</strong>
                    </div>
                </div>
            </div>
            <div v-if="filteredChangelog.length === 0" class="empty-state">
                Keine Aktivitäten gefunden.
            </div>
        </div>
      </div>
    </transition>

    <!-- SORTIER SHEET -->
    <transition name="sheet-slide">
      <div v-if="showSortSheet" class="ks-sheet" @click.stop>
        <div class="ks-sheet__handle"></div>
        <h3 class="sheet-heading">Laufweg im Supermarkt</h3>
        <p class="sheet-support">Sortiere die Kategorien, damit sie deinem Weg durch den Markt entsprechen.</p>
        
        <div class="sort-list" ref="sortListRef">
          <div v-for="(catName, index) in categoryOrder" :key="catName" class="sort-item" :data-id="catName" :style="{ background: getCategoryDef(catName).bg, color: getCategoryDef(catName).color, border: 'none' }">
            <div class="sort-info">
               <span>{{ catName }}</span>
            </div>
            <div class="sort-actions">
              <span class="drag-handle" style="cursor: grab; display: flex; align-items: center; justify-content: center; width: 32px; height: 32px;">
                 <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor"><path d="M3 15v-2h18v2H3Zm0-4V9h18v2H3Z"/></svg>
              </span>
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
            <div v-for="item in group.items" :key="item.id" class="grid-card active" :id="'item-' + item.id"
                 @click="toggleItemStatus(item)"
                 @mousedown="startPress(item, $event)"
                 @touchstart="startPress(item, $event)"
                 @mouseup="cancelPress"
                 @mouseleave="cancelPress"
                 @touchend="cancelPress"
                 @touchmove="cancelPress">
              <div class="card-icon-area" :style="{ background: group.def.bg, color: group.def.color }">
                 <CategoryIcon class="icon-svg" :name="item.name" :category="item.category" size="40" />
              </div>
              <div class="card-text-area">
                <span class="item-name">{{ item.name }}</span>
                <span class="item-quantity" v-if="formatQuantity(item)">{{ formatQuantity(item) }}</span>
                <div v-if="parseTags(item.tags).length > 0" class="item-tags">
                  <span
                    v-for="tag in parseTags(item.tags)"
                    :key="tag"
                    class="tag-pill"
                    :style="{ background: getTagStyle(tag).bg, color: getTagStyle(tag).color }"
                  >{{ tag }}</span>
                </div>
              </div>
            </div>
          </div>
        </section>
      </template>

      <div v-if="groupedActiveItems.length === 0 && completedItems.length === 0" class="empty-state">
        <svg viewBox="0 0 24 24"><path d="M9 16.2 4.8 12l-1.4 1.4L9 19 21 7l-1.4-1.4Z"/></svg>
        <p>Deine Liste ist leer!</p>
      </div>

      <div v-if="groupedActiveItems.length === 0 && completedItems.length > 0" class="all-done-banner text-center bg-green-100 text-green-700 p-4 rounded-xl mb-4 flex items-center justify-center gap-3" style="background-color: #d1fae5; color: #15803d; padding: 16px; border-radius: 12px; margin-bottom: 24px; display: flex; align-items: center; justify-content: center; gap: 12px;">
        <svg class="modern-check-icon w-8 h-8" style="width: 45px; height: 45px;" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/></svg>
        <span class="font-bold text-lg" style="font-weight: 700; font-size: 18px;">Alles erledigt!</span>
      </div>

      <!-- ERLEDIGTE ARTIKEL -->
      <section v-if="completedItems.length > 0" class="items-section completed-section">
        <div class="category-header" style="justify-content: space-between;">
          <div style="display: flex; align-items: center; gap: 12px;">
            <span class="category-badge completed-badge">Erledigt</span>
            <span class="category-count">{{ completedItems.length }}</span>
          </div>
          <button class="clear-completed-btn" @click="clearCompleted" aria-label="Alle erledigten löschen">
            Alle löschen <svg viewBox="0 0 24 24"><path d="M7 21q-.825 0-1.412-.587Q5 19.825 5 19V6H4V4h5V3h6v1h5v2h-1v13q0 .825-.587 1.413Q17.825 21 17 21Zm2-4h2V8H9Zm4 0h2V8h-2Z"/></svg>
          </button>
        </div>
        
        <div class="ks-grid">
          <div v-for="item in completedItems" :key="item.id" class="grid-card completed" @click="toggleItemStatus(item)">
            <div class="card-icon-area">
               <CategoryIcon class="icon-svg" :name="item.name" :category="item.category" size="40" style="opacity: 0.5;" />
            </div>
            <div class="card-text-area">
              <span class="item-name">{{ item.name }}</span>
              <span class="item-quantity" v-if="formatQuantity(item)">{{ formatQuantity(item) }}</span>
            </div>
            <button class="delete-btn" @click.stop="confirmDeleteItem(item)" aria-label="Löschen">
              <svg viewBox="0 0 24 24"><path d="M7 21q-.825 0-1.412-.587Q5 19.825 5 19V6H4V4h5V3h6v1h5v2h-1v13q0 .825-.587 1.413Q17.825 21 17 21Zm2-4h2V8H9Zm4 0h2V8h-2Z"/></svg>
            </button>
          </div>
        </div>
      </section>
    </div>

    <!-- Add Item Trigger -->
    <div class="input-container">
        <div style="display: flex; gap: 8px; width: 100%; max-width: var(--ks-page-width);">
            <button class="add-trigger-btn" @click="openAddModal" style="flex: 1;">
                <svg viewBox="0 0 24 24"><path d="M11 19v-6H5v-2h6V5h2v6h6v2h-6v6Z"/></svg>
                Neuen Artikel hinzufügen
            </button>
            <button class="add-trigger-btn barcode-trigger-btn ks-icon-btn" @click="openScannerModal" style="flex-shrink: 0; width: 56px; border-radius: 50%; padding: 0;">
                <svg viewBox="0 0 24 24" width="24" height="24" fill="currentColor"><path d="M3 4h4v2H5v2H3V4m14 0h4v4h-2V6h-2V4M3 20v-4h2v2h2v2H3m14 0v-2h2v-2h2v4h-4M5 10h2v4H5v-4m4 0h2v4H9v-4m4 0h2v4h-2v-4m4 0h2v4h-2v-4Z"/></svg>
            </button>
        </div>
    </div>

    <!-- Confirm Modal -->
    <ConfirmModal
      :show="showConfirmModal"
      title="Artikel löschen"
      :message="confirmMessage"
      confirmText="Löschen"
      @confirm="executeConfirmAction"
      @cancel="showConfirmModal = false"
    />

    <!-- Modal -->
    <AddItemModal
        :is-open="isAddModalOpen"
        :start-with-scanner="startScanner"
        :edit-item="itemToEdit"
        :active-items="items.filter(i => i.status === 'active')"
        @close="isAddModalOpen = false; itemToEdit = null; startScanner = false"
        @add="handleAddItem"
        @update="handleUpdateItem"
    />

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
.clear-completed-btn {
  background: transparent;
  border: 1px solid var(--ks-border);
  color: var(--ks-error);
  padding: 4px 10px;
  border-radius: var(--ks-radius-xs);
  font-size: 12px;
  display: flex;
  align-items: center;
  gap: 4px;
  cursor: pointer;
}
.clear-completed-btn svg { width: 14px; height: 14px; fill: currentColor; }

.ks-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
  gap: 12px;
}

.grid-card {
  display: flex; flex-direction: column;
  border-radius: var(--ks-radius-sm); padding: 12px 8px;
  cursor: pointer; text-align: center;
  transition: transform 0.1s, opacity 0.2s, background 0.2s, border-color 0.3s;
  position: relative;
  background: var(--ks-surface-2);
  border: 1px solid var(--ks-border);
}
.flash-highlight {
  animation: flash 1s ease-out;
}
@keyframes flash {
  0% { border-color: var(--ks-primary); background: var(--ks-primary-container); transform: scale(1.05); }
  100% { border-color: var(--ks-border); background: var(--ks-surface-2); transform: scale(1); }
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
.icon-svg { display: flex; align-items: center; justify-content: center; width: 45px; height: 45px; }
.icon-svg :deep(svg) { width: 100%; height: 100%; }

.item-quantity {
  font-size: 13px;
  color: var(--ks-text-muted);
  margin-top: 4px;
}

.card-text-area { display: flex; flex-direction: column; }
.item-name { 
  font-size: 14px; font-weight: 600; 
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; 
  overflow: hidden; line-height: 1.3; color: var(--ks-text);
}
.item-tags { display: flex; flex-wrap: wrap; gap: 4px; margin-top: 8px; justify-content: center; }
.tag-pill { font-size: 10px; background: var(--ks-surface-4); padding: 2px 6px; border-radius: 8px; color: var(--ks-text-muted); }

.delete-btn {
  position: absolute; top: -8px; right: -8px;
  width: 44px; height: 44px; border: none; border-radius: 50%;
  background: var(--ks-surface-4); color: var(--ks-error);
  display: flex; align-items: center; justify-content: center;
  box-shadow: 0 2px 4px rgba(0,0,0,0.3); cursor: pointer;
  z-index: 2; /* ensure it's on top of the card */
}
.delete-btn svg { width: 22px; height: 22px; fill: currentColor; }

.empty-state { text-align: center; padding: 40px 0; color: var(--ks-text-muted); }
.empty-state svg { width: 40px; height: 40px; opacity: 0.5; margin-bottom: 8px; fill: currentColor; margin-inline: auto; }

.input-container {
  position: fixed;
  bottom: 0; left: 0; right: 0;
  background: linear-gradient(0deg, var(--ks-bg) 70%, transparent);
  padding: 0 16px max(24px, env(safe-area-inset-bottom));
  display: flex; justify-content: center;
  z-index: 40; pointer-events: none;
}
.input-container > * { pointer-events: auto; }

.add-trigger-btn {
    display: flex; align-items: center; justify-content: center; gap: 8px;
    width: 100%; max-width: var(--ks-page-width);
    background: var(--ks-primary);
    color: var(--ks-on-primary);
    border: none; border-radius: 32px;
    padding: 16px; font-size: 16px; font-weight: 600;
    cursor: pointer;
    box-shadow: 0 4px 12px var(--ks-primary-container);
}
.add-trigger-btn svg { width: 24px; height: 24px; fill: currentColor; }

.barcode-trigger-btn {
    background: var(--ks-surface-2);
    color: var(--ks-text);
    border: 1px solid var(--ks-border);
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

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

/* Changelog */
.changelog-list { display: flex; flex-direction: column; gap: 12px; }
.changelog-item { display: flex; align-items: flex-start; gap: 12px; padding: 8px 0; border-bottom: 1px solid var(--ks-border); }
.changelog-item:last-child { border-bottom: none; }
.changelog-avatar { width: 32px; height: 32px; border-radius: 50%; background: var(--ks-primary); color: var(--ks-on-primary); display: flex; align-items: center; justify-content: center; font-weight: 600; font-size: 14px; flex-shrink: 0; }
.changelog-content { flex: 1; min-width: 0; }
.changelog-meta { display: flex; justify-content: space-between; align-items: center; margin-bottom: 2px; }
.changelog-user { font-weight: 600; font-size: 14px; color: var(--ks-text); }
.changelog-time { font-size: 12px; color: var(--ks-text-muted); }
.changelog-action { font-size: 14px; color: var(--ks-text); line-height: 1.4; word-break: break-word; }

/* Tags/Chips (reused from AddItemModal) */
.tag-group { display: flex; flex-wrap: wrap; gap: 8px; }
.tag-chip { padding: 8px 16px; border-radius: 20px; background: var(--ks-surface-2); border: 1px solid transparent; color: var(--ks-text); cursor: pointer; font-size: 14px; font-weight: 500; }
.tag-chip.active { background: var(--ks-primary-container); color: var(--ks-primary); border-color: var(--ks-primary); }

/* Sort List */
.sort-list {
  display: flex; flex-direction: column; gap: 8px;

}
.sort-item {
  display: flex; align-items: center; justify-content: space-between;
  padding: 12px 16px; background: rgba(255,255,255,0.03);
  border-radius: var(--ks-radius-xs); border: 1px solid var(--ks-border);
}
.sort-info { display: flex; align-items: center; gap: 12px; font-weight: 500; }
.sort-actions { display: flex; gap: 4px; }
.small-btn { width: 36px; height: 36px; }
.small-btn:disabled { opacity: 0.2; pointer-events: none; }
.full-width { width: 100%; }

.share-section { margin-top: 16px; }
.section-label { font-size: 14px; font-weight: 500; color: var(--ks-text-muted); margin-bottom: 8px; }
.mt-4 { margin-top: 24px; }
.search-box { background: var(--ks-surface-2); border-radius: 12px; padding: 4px 12px; display: flex; align-items: center; }
.search-input { width: 100%; background: transparent; border: none; padding: 12px 0; color: var(--ks-text); outline: none; }
.search-input::placeholder { color: var(--ks-text-muted); }
.search-results { margin-top: 12px; display: flex; flex-direction: column; gap: 8px; max-height: 200px; overflow-y: auto; }
.user-result-item { display: flex; align-items: center; justify-content: space-between; padding: 12px; background: var(--ks-surface-3); border-radius: 12px; }
.user-info { display: flex; flex-direction: column; flex: 1; min-width: 0; padding-right: 12px; }
.user-name { font-weight: 500; color: var(--ks-text); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.user-email { font-size: 12px; color: var(--ks-text-muted); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.no-results { color: var(--ks-text-muted); font-size: 14px; margin-top: 12px; text-align: center; }
</style>