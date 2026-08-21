<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';

const router = useRouter();

const stats = ref({ lists: 0, users: 0, items: 0 });
const users = ref([]);
const errorMessage = ref('');
const successMessage = ref('');

const loadAdminData = async () => {
    try {
        const token = localStorage.getItem('token');
        const response = await fetch('/api/admin/stats', {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (response.status === 401 || response.status === 403) {
            router.push('/');
            return;
        }

        if (!response.ok) throw new Error('Fehler beim Laden der Admin-Daten');
        const data = await response.json();
        stats.value = { lists: data.lists, users: data.users, items: data.items };
        users.value = data.user_list || [];
    } catch (error) {
        errorMessage.value = error.message;
    }
};

const promoteUser = async (userId, isAdmin) => {
    try {
        const token = localStorage.getItem('token');
        const response = await fetch(`/api/admin/users/${userId}/role`, {
            method: 'PATCH',
            headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
            body: JSON.stringify({ is_admin: isAdmin })
        });

        if (!response.ok) throw new Error('Fehler beim Ändern der Rechte');
        const result = await response.json();
        successMessage.value = result.message;
        loadAdminData();
        setTimeout(() => successMessage.value = '', 3000);
    } catch (error) {
        errorMessage.value = error.message;
        setTimeout(() => errorMessage.value = '', 3000);
    }
};

const changeStatus = async (userId, status) => {
    try {
        const token = localStorage.getItem('token');
        const response = await fetch(`/api/admin/users/${userId}/status`, {
            method: 'PATCH',
            headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
            body: JSON.stringify({ status: status })
        });

        if (!response.ok) throw new Error('Fehler beim Ändern des Status');
        const result = await response.json();
        successMessage.value = result.message;
        loadAdminData();
        setTimeout(() => successMessage.value = '', 3000);
    } catch (error) {
        errorMessage.value = error.message;
        setTimeout(() => errorMessage.value = '', 3000);
    }
};

const resetPasswordLink = ref('');

const resetPassword = async (userId) => {
    try {
        const token = localStorage.getItem('token');
        const response = await fetch(`/api/admin/users/${userId}/reset-password`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (!response.ok) throw new Error('Fehler beim Generieren des Links');
        const result = await response.json();
        resetPasswordLink.value = window.location.origin + result.reset_link;
        successMessage.value = 'Passwort-Reset-Link generiert!';
        setTimeout(() => successMessage.value = '', 3000);
    } catch (error) {
        errorMessage.value = error.message;
        setTimeout(() => errorMessage.value = '', 3000);
    }
};

onMounted(() => {
    loadAdminData();
});
</script>

<template>
  <div class="page-shell">
    <header class="page-topbar">
      <div style="display: flex; align-items: center; gap: 8px; flex: 1;">
        <button class="ks-icon-btn" @click="router.push('/profile')" aria-label="Zurück">
          <svg viewBox="0 0 24 24"><path d="M11.175 19 4 12l7.175-7 1.425 1.4L7.85 11H20v2H7.85l4.75 4.6Z"/></svg>
        </button>
        <h1 class="page-title">Admin Dashboard</h1>
      </div>
    </header>

    <main class="page-content">
      <div v-if="errorMessage" class="error-card">{{ errorMessage }}</div>
      <div v-if="successMessage" class="success-card">{{ successMessage }}</div>

      <!-- Kachel-Struktur für Statistiken statt Tabellen (Mobile First) -->
      <section class="stats-section">
        <div class="stat-card">
            <span class="stat-value">{{ stats.users }}</span>
            <span class="stat-label">User</span>
        </div>
        <div class="stat-card">
            <span class="stat-value">{{ stats.lists }}</span>
            <span class="stat-label">Listen</span>
        </div>
        <div class="stat-card">
            <span class="stat-value">{{ stats.items }}</span>
            <span class="stat-label">Artikel</span>
        </div>
      </section>

      <section class="users-section">
        <h2 class="section-title">Benutzerverwaltung</h2>

        <div v-if="resetPasswordLink" class="success-card" style="margin-bottom: 16px; word-break: break-all;">
            <strong>Reset-Link:</strong> <a :href="resetPasswordLink" target="_blank">{{ resetPasswordLink }}</a>
            <button @click="resetPasswordLink = ''" class="ks-btn-text" style="padding: 4px; margin-left: 8px;">Schließen</button>
        </div>

        <div class="user-list">
            <div v-for="user in users" :key="user.id" class="user-card" style="flex-direction: column; align-items: stretch; gap: 12px;">
                <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                    <div class="user-info">
                        <span class="user-name">{{ user.display_name }}</span>
                        <span class="user-email">{{ user.email }}</span>
                        <span class="user-status" :class="user.status">Status: {{ user.status }}</span>
                    </div>
                    <div>
                        <span v-if="user.is_admin" class="admin-badge">Admin</span>
                    </div>
                </div>

                <div class="user-actions" style="display: flex; flex-wrap: wrap; gap: 8px;">
                    <button v-if="user.status === 'pending'" class="ks-btn-text" @click="changeStatus(user.id, 'active')" style="padding: 4px 8px; font-size: 12px;">Aktivieren</button>
                    <button v-if="user.status === 'active'" class="ks-btn-text" @click="changeStatus(user.id, 'locked')" style="padding: 4px 8px; font-size: 12px; color: var(--ks-error);">Sperren</button>
                    <button v-if="user.status === 'locked'" class="ks-btn-text" @click="changeStatus(user.id, 'active')" style="padding: 4px 8px; font-size: 12px;">Entsperren</button>

                    <button v-if="user.is_admin" class="ks-btn-text" @click="promoteUser(user.id, false)" style="padding: 4px 8px; font-size: 12px; color: var(--ks-error);">Admin-Rechte entziehen</button>
                    <button v-else class="ks-btn-text" @click="promoteUser(user.id, true)" style="padding: 4px 8px; font-size: 12px;">Zum Admin machen</button>

                    <button class="ks-btn-text" @click="resetPassword(user.id)" style="padding: 4px 8px; font-size: 12px;">Passwort zurücksetzen</button>
                </div>
            </div>
        </div>
      </section>
    </main>
  </div>
</template>

<style scoped>
.page-title {
    margin: 0;
    font-size: 20px;
}
.page-content {
    padding: 16px;
}
.error-card {
    background: rgba(255, 82, 82, 0.1);
    color: #ff5252;
    padding: 12px;
    border-radius: 8px;
    margin-bottom: 16px;
}
.success-card {
    background: rgba(76, 175, 80, 0.1);
    color: #4CAF50;
    padding: 12px;
    border-radius: 8px;
    margin-bottom: 16px;
}
.stats-section {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 12px;
    margin-bottom: 32px;
}
.stat-card {
    background: var(--ks-surface-2);
    border-radius: 16px;
    padding: 16px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}
.stat-value {
    font-size: 32px;
    font-weight: 700;
    color: var(--ks-primary);
    line-height: 1;
    margin-bottom: 4px;
}
.stat-label {
    font-size: 14px;
    color: var(--ks-text-muted);
}
.section-title {
    font-size: 18px;
    margin-top: 0;
    margin-bottom: 16px;
    color: var(--ks-text);
}
.user-list {
    display: flex;
    flex-direction: column;
    gap: 12px;
}
.user-card {
    background: var(--ks-surface-2);
    border-radius: 12px;
    padding: 16px;
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.user-info {
    display: flex;
    flex-direction: column;
}
.user-name {
    font-weight: 600;
    color: var(--ks-text);
}
.user-email {
    font-size: 13px;
    color: var(--ks-text-muted);
}
.user-status {
    font-size: 12px;
    margin-top: 4px;
}
.user-status.active { color: var(--ks-success, #4CAF50); }
.user-status.pending { color: var(--ks-warning, #FF9800); }
.user-status.locked { color: var(--ks-error, #F44336); }
.admin-badge {
    background: var(--ks-primary-container);
    color: var(--ks-primary);
    padding: 4px 10px;
    border-radius: 12px;
    font-size: 12px;
    font-weight: 600;
}
</style>
