<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';

const router = useRouter();

const isLogin = ref(true);
const formData = ref({
  email: '',
  password: '',
  displayName: ''
});
const errorMessage = ref('');
const successMessage = ref('');
const isLoading = ref(false);

const toggleMode = () => {
  isLogin.value = !isLogin.value;
  errorMessage.value = '';
  successMessage.value = '';
};

const submitForm = async () => {
  if (!formData.value.email || !formData.value.password) {
    errorMessage.value = 'Bitte fülle alle Pflichtfelder aus.';
    return;
  }
  if (!isLogin.value && !formData.value.displayName) {
    errorMessage.value = 'Bitte gib einen Anzeigenamen ein.';
    return;
  }

  isLoading.value = true;
  errorMessage.value = '';
  successMessage.value = '';

  const endpoint = isLogin.value ? '/api/auth/login' : '/api/auth/register';
  const payload = isLogin.value 
    ? { email: formData.value.email, password: formData.value.password }
    : { email: formData.value.email, password: formData.value.password, display_name: formData.value.displayName };

  try {
    const response = await fetch(`${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || 'Ein Fehler ist aufgetreten');
    }

    if (isLogin.value) {
      localStorage.setItem('token', data.access_token);
      localStorage.setItem('isLoggedIn', 'true');
      router.push('/');
    } else {
      isLogin.value = true;
      successMessage.value = 'Registrierung erfolgreich! Bitte logge dich ein.';
    }
  } catch (error) {
    errorMessage.value = error.message;
  } finally {
    isLoading.value = false;
  }
};
</script>

<template>
  <div class="page-shell login-view">
    <div class="page-panel login-panel">
      <div class="branding">
        <picture class="login-logo">
          <source srcset="/android-chrome-512x512.png" media="(-webkit-min-device-pixel-ratio: 2), (min-resolution: 192dpi)" />
          <img src="/android-chrome-192x192.png" srcset="/android-chrome-512x512.png 2x" alt="KaufSync Logo" />
        </picture>
        <h1>KaufSync</h1>
        <p>{{ isLogin ? 'Willkommen zurück!' : 'Konto erstellen' }}</p>
      </div>

      <div class="ks-snackbar-stack">
        <div v-if="errorMessage" class="ks-snackbar ks-snackbar--error">{{ errorMessage }}</div>
        <div v-if="successMessage" class="ks-snackbar ks-snackbar--success">{{ successMessage }}</div>
      </div>

      <form @submit.prevent="submitForm" class="login-form">
        <div class="ks-field" v-if="!isLogin">
          <input type="text" v-model="formData.displayName" placeholder=" " id="displayName" />
          <label for="displayName">Anzeigename</label>
        </div>

        <div class="ks-field">
          <input type="email" v-model="formData.email" placeholder=" " id="email" required />
          <label for="email">E-Mail-Adresse</label>
        </div>

        <div class="ks-field">
          <input type="password" v-model="formData.password" placeholder=" " id="password" required />
          <label for="password">Passwort</label>
        </div>

        <button type="submit" class="ks-btn-filled" :disabled="isLoading">
          {{ isLoading ? 'Lädt...' : (isLogin ? 'Einloggen' : 'Registrieren') }}
        </button>
      </form>

      <div class="toggle-section">
        <button type="button" class="ks-btn-text" @click="toggleMode">
          {{ isLogin ? 'Noch kein Konto? Registrieren' : 'Bereits registriert? Einloggen' }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.login-view {
  display: flex;
  align-items: center;
  justify-content: center;
}

.login-panel {
  width: 100%;
  max-width: 400px;
  padding: 32px 24px;
}

.branding { text-align: center; margin-bottom: 32px; }
.login-logo {
  display: flex;
  justify-content: center;
  width: 100%;
  margin: 0 auto 16px auto; /* 16px Abstand nach unten zum h1-Titel */
}

.login-logo img {
  display: block;
  margin: 0 auto;
  /* Optionale Begrenzung, falls das Logo auf großen Screens nicht zu riesig werden soll: */
  max-width: 120px; 
  height: auto;
}
.branding h1 { margin: 0 0 8px; font-size: 24px; font-weight: 600; }
.branding p { margin: 0; color: var(--ks-text-muted); font-size: 15px; }

.login-form { display: flex; flex-direction: column; gap: 20px; }
.toggle-section { text-align: center; margin-top: 24px; }
</style>