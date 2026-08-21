<script setup>
import { ref, onMounted, onUnmounted, watch, computed } from 'vue';
import { useRouter } from 'vue-router';

const router = useRouter();
const shoppingLists = ref([]);
const invitations = ref([]);
const errorMessage = ref('');
const currentUser = ref(null);
const successMessage = ref('');

const showActionSheet = ref(false);
const notifications = ref([]);
const showNotifications = ref(false);
const activeModal = ref(null);

const unreadCount = computed(() => {
  return notifications.value.filter(n => !n.is_read).length;
});

const showOptionsSheet = ref(false);
const selectedListForOptions = ref(null);

const newListName = ref('');
const selectedIcon = ref(''); 
const shareCodeInput = ref('');

// --- ECHTE WIKIPEDIA LOGOS (Alphabetisch sortiert) ---
const predefinedStores = [
  { name: 'Aldi', icon: 'https://commons.wikimedia.org/wiki/Special:FilePath/ALDI_SUD.svg' },
  { name: 'dm', icon: 'https://commons.wikimedia.org/wiki/Special:FilePath/Dm_Logo.svg' },
  { name: 'Edeka', icon: 'https://commons.wikimedia.org/wiki/Special:FilePath/Logo_Edeka.svg' },
  { name: 'Kaufland', icon: 'https://commons.wikimedia.org/wiki/Special:FilePath/Kaufland_Logo.svg' },
  { name: 'Lidl', icon: 'https://commons.wikimedia.org/wiki/Special:FilePath/Lidl-Logo.svg' },
  { name: 'Metro', icon: 'https://commons.wikimedia.org/wiki/Special:FilePath/Metro_Deutschland_Logo_2024.svg' },
  { name: 'Netto', icon: 'https://commons.wikimedia.org/wiki/Special:FilePath/Netto_Logo.svg' },
  { name: 'Penny', icon: 'https://commons.wikimedia.org/wiki/Special:FilePath/Penny-Markt.svg' },
  { name: 'REWE', icon: 'https://commons.wikimedia.org/wiki/Special:FilePath/Logo_REWE.svg' },
  { name: 'Rossmann', icon: 'https://commons.wikimedia.org/wiki/Special:FilePath/Logo_rossmann_2024.svg' },
  { name: 'Selgros', icon: 'https://commons.wikimedia.org/wiki/Special:FilePath/Logo_selgros_2024.svg' }
];

const fallbackCartIcon = 'mdi-cart';

watch(newListName, (newVal) => {
  const matchedStore = predefinedStores.find(s => s.name.toLowerCase() === newVal.trim().toLowerCase());
  if (matchedStore) selectedIcon.value = matchedStore.icon;
  else selectedIcon.value = fallbackCartIcon;
});

const selectPreset = (store) => {
  newListName.value = store.name;
  selectedIcon.value = store.icon;
};

// Modals
const openActionSheet = () => showActionSheet.value = true;
const closeActionSheet = () => { showActionSheet.value = false; showOptionsSheet.value = false; };
const openModal = (mode) => { activeModal.value = mode; showActionSheet.value = false; };
const closeModal = () => { activeModal.value = null; newListName.value = ''; selectedIcon.value = fallbackCartIcon; shareCodeInput.value = ''; };

const openOptions = (list) => {
  selectedListForOptions.value = list;
  showOptionsSheet.value = true;
};

const goToProfile = () => router.push('/profile');

const wsConnections = new Map();
let userWs = null;

const setupWebSockets = () => {
  const isOnline = navigator.onLine;
  if (!isOnline) return;

  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';

  if (currentUser.value && !userWs) {
    try {
      userWs = new WebSocket(`${protocol}//${window.location.host}/ws/user/${currentUser.value.id}`);
      userWs.onerror = (error) => console.warn("User WebSocket Fehler", error);
      userWs.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.event === 'LIST_UPDATED') {
          loadLists();
        }
      };
    } catch (err) {
      console.warn("Konnte User WebSocket nicht aufbauen", err);
    }
  }


  shoppingLists.value.forEach(list => {
    if (!wsConnections.has(list.id)) {
      try {
        const ws = new WebSocket(`${protocol}//${window.location.host}/ws/${list.id}`);
        ws.onerror = (error) => console.warn(`WebSocket Fehler für Liste ${list.id}`, error);
        ws.onmessage = (event) => {
          const data = JSON.parse(event.data);

          if (data.event === 'ITEM_UPDATED') {
            const incomingItem = data.payload.item;
            const targetList = shoppingLists.value.find(l => l.id === list.id);
            if (targetList && targetList.items) {
              const index = targetList.items.findIndex(i => i.id === incomingItem.id);
              if (index !== -1) {
                targetList.items[index].status = incomingItem.status;
                targetList.items[index].quantity = incomingItem.quantity;
                targetList.items[index].name = incomingItem.name;
                targetList.items[index].unit = incomingItem.unit;
                targetList.items[index].tags = incomingItem.tags;
                if (incomingItem.category) targetList.items[index].category = incomingItem.category;
              } else {
                targetList.items.push(incomingItem);
              }
            }
          } else if (data.event === 'ITEM_DELETED') {
            const targetList = shoppingLists.value.find(l => l.id === list.id);
            if (targetList && targetList.items) {
              targetList.items = targetList.items.filter(i => i.id !== data.payload.item_id);
            }
          }
        };
        wsConnections.set(list.id, ws);
      } catch (err) {
        console.warn(`Konnte WebSocket für Liste ${list.id} nicht aufbauen:`, err);
      }
    }
  });
};

const closeWebSockets = () => {
  wsConnections.forEach((ws) => {
    ws.close();
  });
  wsConnections.clear();
  if (userWs) {
    userWs.close();
    userWs = null;
  }
};

const updateOnlineStatus = () => {
  if (navigator.onLine) {
    setupWebSockets();
  }
};

const loadNotifications = async () => {
  try {
    const token = localStorage.getItem('token');
    if (!token) return;
    const response = await fetch('/api/notifications', { headers: { 'Authorization': `Bearer ${token}` } });
    if (response.ok) {
      notifications.value = await response.json();
    }
  } catch (err) {
    console.error('Fehler beim Laden der Benachrichtigungen:', err);
  }
};

const markNotificationRead = async (id, action_url) => {
  try {
    const token = localStorage.getItem('token');
    await fetch(`/api/notifications/${id}/read`, {
      method: 'PATCH',
      headers: { 'Authorization': `Bearer ${token}` }
    });

    // Update local state
    const notif = notifications.value.find(n => n.id === id);
    if (notif) notif.is_read = true;

    if (action_url) {
      router.push(action_url);
    }
  } catch (err) {
    console.error('Fehler beim Aktualisieren der Benachrichtigung:', err);
  }
};

const loadLists = async () => {
  try {
    const token = localStorage.getItem('token');
    const response = await fetch('/api/lists', { headers: { 'Authorization': `Bearer ${token}` } });
    if (response.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('isLoggedIn');
      router.push('/login');
      return;
    }
    if (!response.ok) throw new Error('Fehler beim Laden');
    const data = await response.json();
    shoppingLists.value = data;
    setupWebSockets();
  } catch (error) {
    if (error?.message?.includes('eingeloggt')) router.push('/login');
  }
};

const loadInvitations = async () => {
  try {
    const token = localStorage.getItem('token');
    const response = await fetch('/api/invitations', { headers: { 'Authorization': `Bearer ${token}` } });
    if (!response.ok) throw new Error('Fehler beim Laden von Einladungen');
    const data = await response.json();
    invitations.value = data;
  } catch (error) {
    console.error(error);
  }
};

const respondToInvitation = async (inviteId, action) => {
  try {
    const token = localStorage.getItem('token');
    const response = await fetch(`/api/invitations/${inviteId}/respond?action=${action}`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` }
    });

    if (!response.ok) throw new Error('Fehler beim Antworten auf die Einladung');

    successMessage.value = action === 'accept' ? 'Einladung angenommen' : 'Einladung abgelehnt';
    setTimeout(() => successMessage.value = '', 3000);

    await loadInvitations();
    if (action === 'accept') {
      await loadLists();
    }
  } catch (error) {
    errorMessage.value = error.message;
    setTimeout(() => errorMessage.value = '', 3000);
  }
};

const createNewList = async () => {
  if (!newListName.value.trim()) return;
  errorMessage.value = '';
  try {
    const token = localStorage.getItem('token');
    const finalIcon = selectedIcon.value || fallbackCartIcon;
    
    const response = await fetch('/api/lists', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
      body: JSON.stringify({ name: newListName.value.trim(), icon_name: finalIcon })
    });
    if (!response.ok) throw new Error();
    const created = await response.json();
    shoppingLists.value.push(created);
    closeModal();
  } catch { errorMessage.value = "Liste konnte nicht erstellt werden."; }
};

const joinList = async () => {
  if (!shareCodeInput.value.trim()) return;
  try {
    const token = localStorage.getItem('token');
    const response = await fetch('/api/lists/join', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
      body: JSON.stringify({ share_code: shareCodeInput.value.trim() })
    });
    if (!response.ok) throw new Error();
    const joined = await response.json();
    shoppingLists.value.push(joined);
    successMessage.value = `Beigetreten: ${joined.name}`;
    closeModal();
    setTimeout(() => successMessage.value = '', 3000);
  } catch { errorMessage.value = "Code ungültig oder Fehler beim Beitreten."; }
};

const getInitial = (name) => {
  if (!name) return '?';
  return name.charAt(0).toUpperCase();
};

const deleteList = async () => {
  if (!selectedListForOptions.value) return;
  try {
    const token = localStorage.getItem('token');
    const response = await fetch(`/api/lists/${selectedListForOptions.value.id}`, {
      method: 'DELETE',
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!response.ok) throw new Error();
    
    shoppingLists.value = shoppingLists.value.filter(l => l.id !== selectedListForOptions.value.id);
    successMessage.value = "Liste entfernt.";
    closeActionSheet();
    setTimeout(() => successMessage.value = '', 3000);
  } catch {
    errorMessage.value = "Fehler beim Löschen.";
  }
};

const sortedShoppingLists = computed(() => {
  return [...shoppingLists.value].sort((a, b) => {
    return (a.name || '').localeCompare(b.name || '');
  });
});

const getBannerUrl = (name) => {
  if (!name) return '/banners/Generic_Banner.jpeg';
  const nameLower = name.toLowerCase();
  if (nameLower.includes('aldi')) return '/banners/ALDI_Banner.jpeg';
  if (nameLower.includes('dm')) return '/banners/DM_Banner.jpeg';
  if (nameLower.includes('edeka')) return '/banners/Edeka_Banner.jpeg';
  if (nameLower.includes('kaufland')) return '/banners/Kaufland_Banner.jpeg';
  if (nameLower.includes('lidl')) return '/banners/LIDL_Banner.jpeg';
  if (nameLower.includes('metro')) return '/banners/Metro_Banner.jpeg';
  if (nameLower.includes('mueller') || nameLower.includes('müller')) return '/banners/Mueller_Banner.jpeg';
  if (nameLower.includes('netto')) return '/banners/Netto_Banner.jpeg';
  if (nameLower.includes('penny')) return '/banners/Penny_Banner.jpeg';
  if (nameLower.includes('rewe')) return '/banners/Rewe_Banner.jpeg';
  if (nameLower.includes('rossmann')) return '/banners/Rossmann_Banner.jpeg';
  if (nameLower.includes('selgros')) return '/banners/Selgros_Banner.jpeg';

  // Format normally for generic matching attempts (capitalize first letter if needed, but let fallback handle the rest)
  const formatted = name.charAt(0).toUpperCase() + name.slice(1);
  return `/banners/${formatted}_Banner.jpeg`;
};

const getActiveCount = (list) => {
  if (!list || !list.items) return 0;
  return list.items.filter(i => i.status === 'active').length;
};

const handleImageError = (event) => {
  event.target.src = '/banners/Generic_Banner.jpeg';
};

const loadUserProfile = async () => {
  try {
    const token = localStorage.getItem('token');
    const response = await fetch('/api/users/me', { headers: { 'Authorization': `Bearer ${token}` } });
    if (!response.ok) throw new Error('Fehler beim Laden des Profils');
    currentUser.value = await response.json();
    loadNotifications();
    setupWebSockets();
  } catch (error) {
    console.error(error);
  }
};

onMounted(() => {
  loadLists();
  loadInvitations();
  loadUserProfile();
  loadNotifications();
  window.addEventListener('online', updateOnlineStatus);
  window.addEventListener('offline', updateOnlineStatus);
});

onUnmounted(() => {
  closeWebSockets();
  window.removeEventListener('online', updateOnlineStatus);
  window.removeEventListener('offline', updateOnlineStatus);
});
</script>

<template>
  <div class="page-shell" @click="closeActionSheet">

    <header class="page-topbar" style="justify-content: space-between;">
      <div style="display: flex; align-items: center; gap: 8px;">
        <img src="/android-chrome-512x512.png" alt="Logo" style="height: 48px; object-fit: contain;" />
        <h1 style="margin: 0; font-size: 22px;">Meine Listen</h1>
      </div>
      <div style="display: flex; align-items: center; gap: 4px;">
        <div style="position: relative;">
          <button class="ks-icon-btn profile-btn" @click.stop="showNotifications = true" aria-label="Benachrichtigungen">
            <svg viewBox="0 0 24 24"><path d="M12 22c1.1 0 2-.9 2-2h-4c0 1.1.89 2 2 2zm6-6v-5c0-3.07-1.64-5.64-4.5-6.32V4c0-.83-.67-1.5-1.5-1.5s-1.5.67-1.5 1.5v.68C7.63 5.36 6 7.92 6 11v5l-2 2v1h16v-1l-2-2z"/></svg>
            <span v-if="unreadCount > 0" class="ks-badge">{{ unreadCount }}</span>
          </button>
        </div>
        <button class="ks-icon-btn profile-btn" @click.stop="goToProfile" aria-label="Profil">
          <div v-if="currentUser" class="member-avatar creator" style="width: 32px; height: 32px; font-size: 14px;">
            {{ getInitial(currentUser.display_name) }}
          </div>
          <svg v-else viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 4c1.93 0 3.5 1.57 3.5 3.5S13.93 13 12 13s-3.5-1.57-3.5-3.5S10.07 6 12 6zm0 14c-2.03 0-4.43-.82-6.14-2.88C7.55 15.8 9.68 15 12 15s4.45.8 6.14 2.12C16.43 19.18 14.03 20 12 20z"/></svg>
        </button>
      </div>
    </header>

    <div v-if="showNotifications" class="ks-modal-overlay" @click.self="showNotifications = false">
      <div class="ks-modal" style="max-height: 80vh; overflow-y: auto;">
        <h2>Benachrichtigungen</h2>
        <div v-if="notifications.length === 0" style="padding: 16px; text-align: center; color: var(--ks-text-muted);">
          Keine neuen Benachrichtigungen
        </div>
        <div v-else style="display: flex; flex-direction: column; gap: 12px; margin-top: 16px;">
          <div v-for="notif in notifications" :key="notif.id" style="padding: 12px; border-radius: 8px; background: var(--ks-surface-2); display: flex; flex-direction: column; gap: 4px;" :style="{ opacity: notif.is_read ? 0.6 : 1 }">
            <div style="font-weight: 600; font-size: 14px;">{{ notif.title }}</div>
            <div style="font-size: 14px;">{{ notif.body }}</div>
            <div v-if="!notif.is_read" style="align-self: flex-end; margin-top: 8px;">
                <button @click="markNotificationRead(notif.id, notif.action_url)" class="ks-btn-text" style="font-size: 13px; padding: 4px 8px;">Gelesen</button>
            </div>
          </div>
        </div>
        <div style="margin-top: 24px; text-align: right;">
            <button class="ks-btn-text" @click="showNotifications = false">Schließen</button>
        </div>
      </div>
    </div>

    <div class="ks-snackbar-stack">
      <transition-group name="toast">
        <div v-if="errorMessage" key="err" class="ks-snackbar ks-snackbar--error">{{ errorMessage }}</div>
        <div v-if="successMessage" key="succ" class="ks-snackbar ks-snackbar--success">{{ successMessage }}</div>
      </transition-group>
    </div>

    <!-- Einladungen anzeigen -->
    <div v-if="invitations.length > 0" class="invitations-section">
      <h3 class="section-title">Einladungen</h3>
      <div class="list-stack">
        <div v-for="invite in invitations" :key="invite.id" class="page-panel list-card invite-card">
          <div class="card-leading">
            <div class="card-icon-circle secondary-icon">
              <svg viewBox="0 0 24 24"><path d="M22 6c0-1.1-.9-2-2-2H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6zm-2 0l-8 5-8-5h16zm0 12H4V8l8 5 8-5v10z"/></svg>
            </div>
            <div class="invite-info">
              <span class="card-title">{{ invite.list_name }}</span>
              <span class="invite-sender">von {{ invite.inviter_name }}</span>
            </div>
          </div>
          <div class="invite-actions">
            <button class="ks-icon-btn action-btn accept" @click.stop="respondToInvitation(invite.id, 'accept')" aria-label="Annehmen">
              <svg viewBox="0 0 24 24"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg>
            </button>
            <button class="ks-icon-btn action-btn decline" @click.stop="respondToInvitation(invite.id, 'decline')" aria-label="Ablehnen">
              <svg viewBox="0 0 24 24"><path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/></svg>
            </button>
          </div>
        </div>
      </div>
    </div>

    <h3 v-if="invitations.length > 0 && shoppingLists.length > 0" class="section-title mt-4">Meine Listen</h3>

    <div class="list-stack">
      <button 
        v-for="list in sortedShoppingLists" :key="list.id"
        class="page-panel banner-card"
        @click="router.push(`/list/${list.id}`)"
        @contextmenu.prevent="openOptions(list)"
      >
        <img :src="getBannerUrl(list.name)" class="banner-img" @error="handleImageError" alt="Banner Background" />
        <div class="banner-overlay"></div>
        <div class="banner-content">
          <div class="banner-leading">
            <span class="banner-title">{{ list.name }}</span>
            <div class="banner-left-bottom">
              <div class="item-count-badge">
                {{ getActiveCount(list) }} Artikel
              </div>
              <div class="member-indicators" v-if="list.creator || (list.members && list.members.length > 0)">
                <div class="member-avatar creator" v-if="list.creator" :title="list.creator.display_name">
                  {{ getInitial(list.creator.display_name) }}
                </div>
                <div class="member-avatar" v-for="member in list.members" :key="member.id" :title="member.display_name">
                  {{ getInitial(member.display_name) }}
                </div>
              </div>
            </div>
          </div>
          <div class="options-trigger banner-options" @click.stop="openOptions(list)">
            <svg viewBox="0 0 24 24" style="width:24px;height:24px;fill:#ffffff;"><path d="M12 8c1.1 0 2-.9 2-2s-.9-2-2-2-2 .9-2 2 .9 2 2 2zm0 2c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm0 6c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2z"/></svg>
          </div>
        </div>
      </button>
    </div>

    <div v-if="shoppingLists.length === 0" class="empty-state">
      <p>Noch keine Listen vorhanden</p>
    </div>

    <div class="ks-fab-bar">
      <button class="ks-fab" @click.stop="openActionSheet">
        <svg viewBox="0 0 24 24"><path d="M11 19v-6H5v-2h6V5h2v6h6v2h-6v6Z"/></svg>
        Liste erstellen / beitreten
      </button>
    </div>

    <transition name="scrim-fade">
      <div v-if="showActionSheet || showOptionsSheet" class="ks-sheet-scrim" @click="closeActionSheet"></div>
    </transition>

    <transition name="sheet-slide">
      <div v-if="showActionSheet && !showOptionsSheet" class="ks-sheet" @click.stop>
        <div class="ks-sheet__handle"></div>
        <button class="sheet-item" @click="openModal('create')">
          <span class="sheet-icon primary"><svg viewBox="0 0 24 24"><path d="M11 19v-6H5v-2h6V5h2v6h6v2h-6v6Z"/></svg></span>
          <div class="sheet-text">
            <span class="sheet-title">Neue Liste erstellen</span>
          </div>
        </button>
        <button class="sheet-item" @click="openModal('join')">
          <span class="sheet-icon secondary">
            <svg viewBox="0 0 24 24"><path d="M12.65 10A5.99 5.99 0 0 0 7 6c-3.31 0-6 2.69-6 6s2.69 6 6 6a5.99 5.99 0 0 0 5.65-4H17v4h4v-4h2v-4H12.65zM7 14c-1.1 0-2-.9-2-2s.9-2 2-2 2 .9 2 2-.9 2-2 2z"/></svg>
          </span>
          <div class="sheet-text">
            <span class="sheet-title">Per Code beitreten</span>
          </div>
        </button>
      </div>
    </transition>

    <transition name="sheet-slide">
      <div v-if="showOptionsSheet" class="ks-sheet" @click.stop>
        <div class="ks-sheet__handle"></div>
        <div style="padding: 0 12px 16px;">
          <h3 style="margin: 0; font-size: 16px; color: var(--ks-text-muted);">{{ selectedListForOptions?.name }}</h3>
        </div>
        <button class="sheet-item" @click="deleteList" style="color: var(--ks-error);">
          <span class="sheet-icon" style="background: var(--ks-error-bg);"><svg viewBox="0 0 24 24"><path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/></svg></span>
          <div class="sheet-text">
            <span class="sheet-title">Liste löschen / verlassen</span>
          </div>
        </button>
      </div>
    </transition>

    <transition name="dialog-fade">
      <div v-if="activeModal" class="ks-dialog-scrim" @click.self="closeModal">
        <div class="ks-dialog">
          
          <template v-if="activeModal === 'create'">
            <h2 style="margin: 0 0 16px; font-size: 20px;">Wähle Supermarkt</h2>
            
            <div class="preset-grid">
              <button 
                v-for="store in predefinedStores" 
                :key="store.name"
                class="preset-btn"
                :class="{ 'active': newListName.toLowerCase() === store.name.toLowerCase() }"
                @click="selectPreset(store)"
              >
                <div class="store-svg-container">
                  <img :src="store.icon" :alt="store.name" />
                </div>
                <span>{{ store.name }}</span>
              </button>
            </div>

            <div class="ks-field" style="margin-bottom: 24px;">
              <input v-model="newListName" type="text" placeholder=" " @keyup.enter="createNewList" />
              <label>Oder eigenen Namen eingeben</label>
            </div>
            <div class="ks-btn-row">
              <button class="ks-btn-text" @click="closeModal">Abbrechen</button>
              <button class="ks-btn-filled" @click="createNewList">Erstellen</button>
            </div>
          </template>

          <template v-else-if="activeModal === 'join'">
            <h2 style="margin: 0 0 20px; font-size: 20px;">Code einlösen</h2>
            <div class="ks-field" style="margin-bottom: 24px;">
              <input v-model="shareCodeInput" type="text" maxlength="6" placeholder=" " class="code-input" @keyup.enter="joinList" />
              <label>6-stelliger Code</label>
            </div>
            <div class="ks-btn-row">
              <button class="ks-btn-text" @click="closeModal">Abbrechen</button>
              <button class="ks-btn-filled" @click="joinList">Beitreten</button>
            </div>
          </template>
          
        </div>
      </div>
    </transition>

  </div>
</template>

<style scoped>
.list-stack { display: flex; flex-direction: column; gap: 12px; }

.list-card {
  padding: 16px; display: flex; align-items: center; justify-content: space-between;
  cursor: pointer; text-align: left; transition: filter 0.15s; border-radius: 16px; position: relative;
}
.list-card:hover { filter: brightness(1.1); }

.banner-card {
  position: relative;
  overflow: hidden;
  border-radius: 16px;
  cursor: pointer;
  text-align: left;
  border: none;
  background: transparent;
  padding: 0;
  min-height: 120px;
  margin: 0 -8px; /* Slightly wider */
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  display: flex;
}
.banner-card:hover .banner-img { transform: scale(1.05); }

.banner-img {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s ease;
  z-index: 0;
}

.banner-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(to right, rgba(0,0,0,0.85) 0%, rgba(0,0,0,0.4) 50%, rgba(0,0,0,0.1) 100%);
  z-index: 1;
}

.banner-content {
  position: relative;
  z-index: 2;
  display: flex;
  justify-content: space-between;
  align-items: stretch;
  width: 100%;
  padding: 16px;
}

.banner-leading {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.banner-title {
  color: #ffffff;
  font-size: 22px;
  font-weight: 700;
  text-shadow: 0 2px 4px rgba(0,0,0,0.5);
  margin-bottom: 12px;
}

.banner-left-bottom {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.item-count-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.6);
  color: #fff;
  border-radius: 20px;
  padding: 4px 12px;
  font-size: 13px;
  font-weight: 500;
  backdrop-filter: blur(4px);
  width: max-content;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.banner-options {
  align-self: flex-start;
  background: rgba(0,0,0,0.3);
  backdrop-filter: blur(4px);
  margin: 0;
}
.banner-options:hover { background: rgba(0,0,0,0.5); }


.card-leading { display: flex; align-items: center; gap: 16px; min-width: 0; }

.card-icon-circle {
  width: 42px; height: 42px; border-radius: 50%;
  background: var(--ks-surface-3); color: var(--ks-primary);
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
  overflow: hidden;
}
.card-icon-circle.has-image { background: #ffffff; border: 1px solid var(--ks-border); }
.card-icon-circle svg { width: 22px; height: 22px; }
.store-logo-img { width: 100%; height: 100%; object-fit: contain; padding: 4px; }

.card-title { font-size: 17px; font-weight: 500; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.ks-badge {
    position: absolute;
    top: 4px;
    right: 4px;
    background: var(--ks-error, #F44336);
    color: white;
    font-size: 10px;
    font-weight: 700;
    min-width: 16px;
    height: 16px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 0 4px;
}

.profile-btn { padding: 4px; display: flex; align-items: center; justify-content: center; }
.member-indicators { display: flex; align-items: center; }
.member-avatar { width: 20px; height: 20px; border-radius: 50%; background: var(--ks-surface-4); color: var(--ks-text); display: flex; align-items: center; justify-content: center; font-size: 10px; font-weight: bold; border: 1.5px solid var(--ks-surface-1); margin-left: -6px; }
.member-avatar:first-child { margin-left: 0; }
.member-avatar.creator { background: var(--ks-primary); color: var(--ks-on-primary); }

.options-trigger {
  padding: 8px; margin: -8px; border-radius: 50%; display: flex; align-items: center; justify-content: center;
}
.options-trigger:hover { background: rgba(255,255,255,0.05); }

/* --- 5 LOGOS WIEDERHERGESTELLT --- */
.preset-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 12px 6px;
  margin-bottom: 24px;
  max-height: 280px;
  /* Scrollen verhindern, falls möglich */
  overflow: visible; 
  padding: 4px;
}
.preset-grid::-webkit-scrollbar { display: none; }

.preset-btn {
  display: flex; flex-direction: column; align-items: center; gap: 8px;
  background: transparent; border: 2px solid transparent; border-radius: 12px;
  padding: 6px 2px; cursor: pointer; width: 100%;
  transition: all 0.2s ease;
}

.store-svg-container {
  /* Größe 50px für die breitere Ansicht */
  width: 50px; height: 50px; background: white; border-radius: 12px; padding: 6px; 
  box-shadow: 0 4px 10px rgba(0,0,0,0.2); display: flex; align-items: center; justify-content: center;
}
.store-svg-container img { width: 100%; height: 100%; object-fit: contain; }

.preset-btn span { font-size: 12px; color: var(--ks-text-soft); text-align: center; word-break: break-word; line-height: 1.2; }
.preset-btn:hover { background: rgba(255,255,255,0.06); }
.preset-btn.active { background: var(--ks-primary-container); border-color: var(--ks-primary); }
.preset-btn.active span { color: var(--ks-primary); font-weight: 600; }
/* --------------------------------------- */

.empty-state { text-align: center; margin-top: 60px; color: var(--ks-text-muted); }

.sheet-item {
  width: 100%; background: transparent; border: none; padding: 16px 12px;
  display: flex; align-items: center; gap: 16px; text-align: left;
  color: var(--ks-text); border-radius: 12px; cursor: pointer;
}
.sheet-item:hover { background: rgba(255,255,255,0.06); }

.sheet-icon {
  width: 44px; height: 44px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.sheet-icon svg { width: 24px; height: 24px; fill: currentColor; }
.sheet-icon.primary { background: var(--ks-primary); color: var(--ks-on-primary); }
.sheet-icon.secondary { background: var(--ks-secondary); color: var(--ks-on-secondary); }

.sheet-text { display: flex; flex-direction: column; }
.sheet-title { font-size: 16px; font-weight: 500; }
.code-input { text-transform: uppercase; letter-spacing: 3px; font-weight: 600; }

.section-title { font-size: 18px; font-weight: 600; margin: 16px 0 8px; color: var(--ks-text); }
.mt-4 { margin-top: 16px; }

.invite-card { cursor: default; }
.invite-card:hover { filter: none; }
.secondary-icon { background: var(--ks-secondary-container); color: var(--ks-secondary); }
.invite-info { display: flex; flex-direction: column; }
.invite-sender { font-size: 13px; color: var(--ks-text-muted); }

.invite-actions { display: flex; gap: 8px; }
.action-btn { width: 36px; height: 36px; border-radius: 50%; display: flex; align-items: center; justify-content: center; }
.action-btn.accept { background: var(--ks-primary-container); color: var(--ks-primary); }
.action-btn.decline { background: var(--ks-error-bg); color: var(--ks-error); }
.action-btn:hover { filter: brightness(0.9); }
</style>