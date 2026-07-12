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

let ws = null;
const isOnline = ref(navigator.onLine);

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
  try {
    const token = localStorage.getItem('token');
    const response = await fetch(`http://localhost:8000/api/lists/${listId}/items`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
      body: JSON.stringify({ name: newItemName.value, quantity: 1, unit: 'Stk' })
    });
    if (response.ok) newItemName.value = '';
  } catch (error) { errorMessage.value = error.message; }
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
  try {
    const token = localStorage.getItem('token');
    await fetch(`http://localhost:8000/api/items/${itemId}`, {
      method: 'DELETE',
      headers: { 'Authorization': `Bearer ${token}` }
    });
  } catch (error) {
    errorMessage.value = error.message;
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

const activeItems = computed(() => items.value.filter(i => i.status === 'active'));
const completedItems = computed(() => items.value.filter(i => i.status === 'completed'));

onMounted(() => {
  loadItems();
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
  <div class="page-shell" @click="showShareSheet = false">

    <header class="page-topbar" style="justify-content: space-between;">
      <div style="display: flex; align-items: center; gap: 12px; flex: 1; min-width: 0;">
        <button class="ks-icon-btn" @click.stop="router.push('/')" aria-label="Zurück">
          <svg viewBox="0 0 24 24"><path d="M11.175 19 4 12l7.175-7 1.425 1.4L7.85 11H20v2H7.85l4.75 4.6Z"/></svg>
        </button>
        <h1 class="list-title">{{ currentList ? currentList.name : 'Laden...' }}</h1>
      </div>
      <button v-if="currentList" class="ks-icon-btn" @click.stop="showShareSheet = !showShareSheet" aria-label="Teilen">
        <svg viewBox="0 0 24 24"><path d="M18 22q-1.25 0-2.125-.875T15 19q0-.15.025-.325.025-.175.075-.325L7.05 13.7q-.425.4-.95.65-.525.25-1.1.25-1.25 0-2.125-.875T2 11.4q0-1.25.875-2.125T5 8.4q.575 0 1.1.25.525.25.95.65l8.05-4.65q-.05-.15-.075-.325Q15 4.15 15 4q0-1.25.875-2.125T18 1q1.25 0 2.125.875T21 4q0 1.25-.875 2.125T18 7q-.575 0-1.1-.25-.525-.25-.95-.65L7.9 10.75q.05.15.075.325.025.175.025.325 0 .15-.025.325-.025.175-.075.325l8.05 4.65q.425-.4.95-.65.525-.25 1.1-.25 1.25 0 2.125.875T21 19q0 1.25-.875 2.125T18 22Z"/></svg>
      </button>
    </header>

    <transition name="scrim-fade">
      <div v-if="showShareSheet" class="ks-sheet-scrim" @click="showShareSheet = false"></div>
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

    <div class="ks-snackbar-stack">
      <div v-if="!isOnline" class="ks-snackbar ks-snackbar--warning">Offline. Änderungen werden später synchronisiert.</div>
      <transition-group name="toast">
        <div v-if="errorMessage" key="err" class="ks-snackbar ks-snackbar--error">{{ errorMessage }}</div>
        <div v-if="successMessage" key="succ" class="ks-snackbar ks-snackbar--success">{{ successMessage }}</div>
      </transition-group>
    </div>

    <section class="items-section">
      <h2 class="section-label">Zu kaufen ({{ activeItems.length }})</h2>
      <div class="ks-grid">
        <div v-for="item in activeItems" :key="item.id" class="grid-card active" @click="toggleItemStatus(item)">
          <div class="card-icon-area">
             <span class="initials">{{ getInitials(item.name) }}</span>
          </div>
          <div class="card-text-area">
            <span class="item-name">{{ item.name }}</span>
            <span class="item-meta">{{ item.quantity }} {{ item.unit }}</span>
          </div>
        </div>
      </div>
      <div v-if="activeItems.length === 0" class="empty-state">
        <svg viewBox="0 0 24 24"><path d="M9 16.2 4.8 12l-1.4 1.4L9 19 21 7l-1.4-1.4Z"/></svg>
        <p>Alles erledigt!</p>
      </div>
    </section>

    <section v-if="completedItems.length > 0" class="items-section">
      <h2 class="section-label">Erledigt</h2>
      <div class="ks-grid">
        <div v-for="item in completedItems" :key="item.id" class="grid-card completed" @click="toggleItemStatus(item)">
          <div class="card-icon-area">
             <span class="initials">{{ getInitials(item.name) }}</span>
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
</template>

<style scoped>
.list-title { margin: 0; font-size: 20px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.items-section { margin-bottom: 32px; }
.section-label {
  font-size: 14px; font-weight: 600; letter-spacing: 0.5px;
  text-transform: uppercase; color: var(--ks-text-muted);
  margin: 0 0 16px 4px;
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
  transition: transform 0.1s, opacity 0.2s;
  position: relative;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}
.grid-card:active { transform: scale(0.95); }

.grid-card.active { background: var(--ks-primary); color: var(--ks-on-primary); }
.grid-card.completed { background: var(--ks-surface-3); color: var(--ks-text-muted); opacity: 0.7; }

.card-icon-area { display: flex; align-items: center; justify-content: center; height: 50px; margin-bottom: 8px; }
.initials { font-size: 32px; font-weight: 700; opacity: 0.9; }

.card-text-area { display: flex; flex-direction: column; }
.item-name { 
  font-size: 14px; font-weight: 600; 
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; 
  overflow: hidden; line-height: 1.2;
}
.item-meta { font-size: 12px; opacity: 0.8; margin-top: 4px; }

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

.floating-input-bar {
  position: fixed;
  bottom: 24px; left: 16px; right: 16px;
  max-width: var(--ks-page-width); margin: 0 auto;
  background: var(--ks-surface-4);
  border-radius: 32px;
  padding: 6px 6px 6px 20px;
  display: flex; align-items: center;
  box-shadow: var(--ks-shadow-2);
  z-index: 40;
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

.sheet-heading { font-size: 20px; font-weight: 500; margin: 0 0 8px; color: var(--ks-text); }
.sheet-support { font-size: 14px; color: var(--ks-text-muted); margin: 0 0 20px; }

.code-box {
  width: 100%; background: var(--ks-surface-3); border: none;
  border-radius: var(--ks-radius-xs);
  padding: 16px; display: flex; align-items: center; justify-content: center; gap: 16px;
  cursor: pointer; color: var(--ks-text);
}
.code-box .code { font-size: 24px; font-family: monospace; font-weight: 700; letter-spacing: 4px; }
.code-box svg { width: 24px; height: 24px; fill: currentColor; opacity: 0.6; }
</style>