<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';

const router = useRouter();
const logout = () => {
  localStorage.removeItem('token');
  localStorage.removeItem('isLoggedIn');
  localStorage.removeItem('status');
  router.push('/login');
};
</script>

<template>
  <div class="page-shell login-view">
    <div class="page-panel login-panel" style="text-align: center; padding: 48px 24px;">
      <h1 style="color: var(--ks-primary); margin-bottom: 16px;">Warten auf Freischaltung</h1>
      <p style="color: var(--ks-text); font-size: 16px; margin-bottom: 32px;">
        Dein Account wurde erfolgreich erstellt, muss aber noch von einem Administrator freigeschaltet werden. Bitte habe etwas Geduld.
      </p>
      <button @click="logout" class="ks-btn-filled">Zurück zum Login</button>
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
}
</style>
