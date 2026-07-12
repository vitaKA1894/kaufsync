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
    const response = await fetch(`http://localhost:8000${endpoint}`, {
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
        <div class="logo-circle">
          <svg viewBox="0 0 24 24"><path d="M7 22q-.825 0-1.412-.587Q5 20.825 5 20t.588-1.412Q6.175 18 7 18t1.413.588Q9 19.175 9 20t-.587 1.413Q7.825 22 7 22Zm10 0q-.825 0-1.412-.587Q15 20.825 15 20t.588-1.412Q16.175 18 17 18t1.413.588Q19 19.175 19 20t-.587 1.413Q17.825 22 17 22ZM6.15 6l1.4 3h9.75l1.65-3ZM5.2 4h15.35q.575 0 .875.5.3.5.025 1L18.3 10.45q-.275.5-.737.775-.463.275-1.013.275H7.15L6 13h12v2H6q-1.15 0-1.725-1.012-.575-1.013-.025-2.038L5.6 9.6 2 2h2Z"/></svg>
        </div>
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
.logo-circle {
  width: 64px; height: 64px; margin: 0 auto 16px;
  background: var(--ks-primary); color: var(--ks-on-primary);
  border-radius: 50%; display: flex; align-items: center; justify-content: center;
}
.logo-circle svg { width: 32px; height: 32px; }
.branding h1 { margin: 0 0 8px; font-size: 24px; font-weight: 600; }
.branding p { margin: 0; color: var(--ks-text-muted); font-size: 15px; }

.login-form { display: flex; flex-direction: column; gap: 20px; }
.toggle-section { text-align: center; margin-top: 24px; }
</style>