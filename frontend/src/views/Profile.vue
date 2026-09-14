<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';

const router = useRouter();

const user = ref({
  email: '',
  display_name: '',
  is_admin: false,
  settings_push_new_items: false
});

const passwordData = ref({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
});

const successMessage = ref('');
const errorMessage = ref('');
const isLoading = ref(false);

const loadUserProfile = async () => {
  try {
    const token = localStorage.getItem('token');
    const response = await fetch('/api/users/me', {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    
    if (response.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('isLoggedIn');
      router.push('/login');
      return;
    }

    if (!response.ok) throw new Error('Profil konnte nicht geladen werden');
    
    const data = await response.json();
    user.value.email = data.email;
    user.value.display_name = data.display_name;
    user.value.is_admin = data.is_admin || false;
    user.value.settings_push_new_items = data.settings_push_new_items || false;
  } catch (error) {
    console.error(error);
  }
};

const updateProfile = async () => {
  errorMessage.value = '';
  successMessage.value = '';
  isLoading.value = true;
  
  try {
    const token = localStorage.getItem('token');
    const response = await fetch('/api/users/me', {
      method: 'PUT',
      headers: { 
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}` 
      },
      body: JSON.stringify({
        display_name: user.value.display_name,
        settings_push_new_items: user.value.settings_push_new_items
      })
    });
    
    if (!response.ok) throw new Error('Fehler beim Speichern des Profils');
    
    successMessage.value = 'Profil erfolgreich aktualisiert!';
    setTimeout(() => successMessage.value = '', 3000);
  } catch (error) {
    errorMessage.value = error.message;
  } finally {
    isLoading.value = false;
  }
};

const changePassword = async () => {
  errorMessage.value = '';
  successMessage.value = '';

  if (passwordData.value.newPassword !== passwordData.value.confirmPassword) {
    errorMessage.value = 'Die neuen Passwörter stimmen nicht überein.';
    return;
  }
  if (passwordData.value.newPassword.length < 6) {
    errorMessage.value = 'Das neue Passwort muss mindestens 6 Zeichen lang sein.';
    return;
  }

  isLoading.value = true;
  try {
    const token = localStorage.getItem('token');
    const response = await fetch('/api/users/me/password', {
      method: 'PUT',
      headers: { 
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}` 
      },
      body: JSON.stringify({ 
        old_password: passwordData.value.oldPassword,
        new_password: passwordData.value.newPassword 
      })
    });
    
    if (!response.ok) {
      const errData = await response.json();
      throw new Error(errData.detail || 'Fehler beim Ändern des Passworts');
    }
    
    successMessage.value = 'Passwort erfolgreich geändert!';
    passwordData.value = { oldPassword: '', newPassword: '', confirmPassword: '' };
    setTimeout(() => successMessage.value = '', 3000);
  } catch (error) {
    errorMessage.value = error.message;
  } finally {
    isLoading.value = false;
  }
};

const logout = () => {
  localStorage.removeItem('token');
  localStorage.removeItem('isLoggedIn');
  router.push('/login');
};

const isIos = () => {
  const userAgent = window.navigator.userAgent.toLowerCase();
  return /iphone|ipad|ipod/.test(userAgent);
};

const isStandalone = () => {
  return window.navigator.standalone || window.matchMedia('(display-mode: standalone)').matches;
};

const urlBase64ToUint8Array = (base64String) => {
  const padding = '='.repeat((4 - base64String.length % 4) % 4);
  const base64 = (base64String + padding)
    .replace(/\-/g, '+')
    .replace(/_/g, '/');

  const rawData = window.atob(base64);
  const outputArray = new Uint8Array(rawData.length);

  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i);
  }
  return outputArray;
};

const enableNotifications = async () => {
  if (isIos() && !isStandalone()) {
    alert("To receive push notifications, tap Share and select 'Add to Home Screen'.");
    return;
  }

  if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
    alert('Push Notifications werden von diesem Browser nicht unterstützt.');
    return;
  }

  try {
    const permission = await Notification.requestPermission();
    if (permission !== 'granted') {
      alert('Bitte Push-Benachrichtigungen in den Browser-Einstellungen erlauben.');
      return;
    }

    const token = localStorage.getItem('token');

    // Get public key
    const pubKeyRes = await fetch('/api/push/public-key');
    if (!pubKeyRes.ok) throw new Error('VAPID public key konnte nicht geladen werden');
    const { public_key } = await pubKeyRes.json();

    // Register/Get Service Worker
    const registration = await navigator.serviceWorker.ready;

    if (!public_key) {
      console.warn('VAPID public key is missing or null. Push notifications cannot be enabled. Please ensure VAPID keys are configured in the backend.');
      throw new Error('Push-Benachrichtigungen können nicht aktiviert werden, da der VAPID Key fehlt.');
    }

    const convertedKey = urlBase64ToUint8Array(public_key);

    // Subscribe to push manager
    const subscription = await registration.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: convertedKey
    });

    const subData = JSON.parse(JSON.stringify(subscription));

    // Send to backend
    const subRes = await fetch('/api/push/subscribe', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        endpoint: subData.endpoint,
        p256dh: subData.keys.p256dh,
        auth: subData.keys.auth
      })
    });

    if (!subRes.ok) throw new Error('Fehler beim Speichern der Push-Subscription');

    user.value.settings_push_new_items = true;
    await updateProfile(); // Save the new setting

    successMessage.value = 'Push-Benachrichtigungen erfolgreich aktiviert!';
    setTimeout(() => successMessage.value = '', 3000);
  } catch (error) {
    console.error(error);
    errorMessage.value = error.message;
  }
};

const goBack = () => router.push('/');

onMounted(loadUserProfile);
</script>

<template>
  <div class="page-shell">
    <header class="page-topbar" style="justify-content: space-between;">
      <div style="display: flex; align-items: center; gap: 12px;">
        <button class="ks-icon-btn" @click="goBack" aria-label="Zurück">
          <svg viewBox="0 0 24 24"><path d="M11.175 19 4 12l7.175-7 1.425 1.4L7.85 11H20v2H7.85l4.75 4.6Z"/></svg>
        </button>
        <h1 style="margin: 0; font-size: 20px;">Mein Konto</h1>
      </div>
      <button class="ks-icon-btn logout-btn" @click="logout" aria-label="Logout">
        <svg viewBox="0 0 24 24"><path d="M5 21q-.825 0-1.412-.587Q3 19.825 3 19V5q0-.825.588-1.412Q4.175 3 5 3h7v2H5v14h7v2Zm11-4-1.375-1.45 2.55-2.55H9v-2h8.175l-2.55-2.55L16 7l5 5Z"/></svg>
      </button>
    </header>

    <div class="ks-snackbar-stack">
      <transition-group name="toast">
        <div v-if="errorMessage" key="err" class="ks-snackbar ks-snackbar--error">{{ errorMessage }}</div>
        <div v-if="successMessage" key="succ" class="ks-snackbar ks-snackbar--success">{{ successMessage }}</div>
      </transition-group>
    </div>

    <div class="settings-grid">
      <!-- Admin Bereich -->
      <section v-if="user.is_admin" class="page-panel settings-card">
        <h3>Admin Dashboard</h3>
        <p style="margin-top: 0; color: var(--ks-text-muted); font-size: 14px; margin-bottom: 20px;">
          Du hast Administrator-Rechte.
        </p>
        <button @click="router.push('/admin')" class="ks-btn-filled full-width" style="background: var(--ks-primary); margin-bottom: 20px;">
          Admin Dashboard öffnen
        </button>
      </section>

      <!-- Profil Info -->
      <section class="page-panel settings-card">
        <h3>Profil & Einstellungen</h3>
        
        <div class="ks-field" style="margin-bottom: 20px;">
          <input type="email" v-model="user.email" disabled placeholder=" " />
          <label>E-Mail-Adresse</label>
        </div>

        <div class="ks-field" style="margin-bottom: 20px;">
          <input type="text" v-model="user.display_name" placeholder=" " />
          <label>Anzeigename</label>
        </div>

        <button @click="updateProfile" :disabled="isLoading" class="ks-btn-filled full-width">
          Profil speichern
        </button>
      </section>

      <!-- Push Benachrichtigungen -->
      <section class="page-panel settings-card">
        <h3>Push-Benachrichtigungen</h3>

        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px;">
          <span>Neue Artikel in Listen</span>
          <label class="ks-switch">
            <input type="checkbox" v-model="user.settings_push_new_items" @change="updateProfile" />
            <span class="ks-switch-slider"></span>
          </label>
        </div>

        <button @click="enableNotifications" class="ks-btn-tonal full-width" style="margin-top: 0;">
          Benachrichtigungen aktivieren
        </button>
      </section>

      <!-- Sicherheit / Passwort -->
      <section class="page-panel settings-card">
        <h3>Sicherheit</h3>
        
        <div class="ks-field" style="margin-bottom: 20px;">
          <input type="password" v-model="passwordData.oldPassword" placeholder=" " />
          <label>Aktuelles Passwort</label>
        </div>

        <div class="ks-field" style="margin-bottom: 20px;">
          <input type="password" v-model="passwordData.newPassword" placeholder=" " />
          <label>Neues Passwort</label>
        </div>

        <div class="ks-field" style="margin-bottom: 20px;">
          <input type="password" v-model="passwordData.confirmPassword" placeholder=" " />
          <label>Passwort bestätigen</label>
        </div>

        <button @click="changePassword" :disabled="isLoading" class="ks-btn-tonal full-width">
          Passwort ändern
        </button>
      </section>
    </div>
  </div>
</template>

<style scoped>
.logout-btn { color: var(--ks-error); }
.settings-grid { display: grid; gap: 24px; max-width: 600px; margin: 0 auto; width: 100%; }

.settings-card { padding: 24px; }
.settings-card h3 { margin: 0 0 24px; font-size: 18px; font-weight: 500; color: var(--ks-primary); }

.full-width { width: 100%; margin-top: 8px; }
.ks-field input:disabled { opacity: 0.5; background: rgba(255, 255, 255, 0.02); }
</style>