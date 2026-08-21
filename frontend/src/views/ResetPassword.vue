<script setup>
import { ref, onMounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';

const router = useRouter();
const route = useRoute();

const formData = ref({
  password: '',
  confirmPassword: ''
});
const errorMessage = ref('');
const successMessage = ref('');
const isLoading = ref(false);

const submitForm = async () => {
  if (!formData.value.password || !formData.value.confirmPassword) {
    errorMessage.value = 'Bitte fülle alle Pflichtfelder aus.';
    return;
  }
  if (formData.value.password !== formData.value.confirmPassword) {
    errorMessage.value = 'Die Passwörter stimmen nicht überein.';
    return;
  }
  if (formData.value.password.length < 6) {
    errorMessage.value = 'Das Passwort muss mindestens 6 Zeichen lang sein.';
    return;
  }

  isLoading.value = true;
  errorMessage.value = '';
  successMessage.value = '';

  const token = route.query.token;
  const user_id = route.query.user_id;

  try {
    const response = await fetch('/api/auth/reset-password', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: user_id, token: token, new_password: formData.value.password })
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || 'Ein Fehler ist aufgetreten');
    }

    successMessage.value = 'Passwort erfolgreich zurückgesetzt! Du wirst zum Login weitergeleitet...';
    setTimeout(() => {
        router.push('/login');
    }, 3000);
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
        <h1 style="color: var(--ks-primary);">KaufSync</h1>
        <p>Neues Passwort vergeben</p>
      </div>

      <div class="ks-snackbar-stack">
        <div v-if="errorMessage" class="ks-snackbar ks-snackbar--error">{{ errorMessage }}</div>
        <div v-if="successMessage" class="ks-snackbar ks-snackbar--success">{{ successMessage }}</div>
      </div>

      <form @submit.prevent="submitForm" class="login-form">
        <div class="ks-field">
          <input type="password" v-model="formData.password" placeholder=" " id="password" required />
          <label for="password">Neues Passwort</label>
        </div>

        <div class="ks-field">
          <input type="password" v-model="formData.confirmPassword" placeholder=" " id="confirmPassword" required />
          <label for="confirmPassword">Passwort bestätigen</label>
        </div>

        <button type="submit" class="ks-btn-filled" :disabled="isLoading">
          {{ isLoading ? 'Lädt...' : 'Passwort speichern' }}
        </button>
      </form>

      <div class="toggle-section">
        <button type="button" class="ks-btn-text" @click="router.push('/login')">
          Zurück zum Login
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
  margin: 0 auto 16px auto;
}

.login-logo img {
  display: block;
  margin: 0 auto;
  max-width: 120px;
  height: auto;
}
.branding h1 { margin: 0 0 8px; font-size: 24px; font-weight: 600; }
.branding p { margin: 0; color: var(--ks-text-muted); font-size: 15px; }

.login-form { display: flex; flex-direction: column; gap: 20px; }
.toggle-section { text-align: center; margin-top: 24px; }
</style>
