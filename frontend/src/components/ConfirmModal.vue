<template>
  <transition name="fade">
    <div v-if="show" class="modal-backdrop" @click="cancel">
      <transition name="slide-up">
        <div v-if="show" class="confirm-modal" @click.stop>
          <div class="modal-content">
            <h3 class="modal-title">{{ title }}</h3>
            <p class="modal-message">{{ message }}</p>
          </div>
          <div class="modal-actions">
            <button class="ks-btn-outlined cancel-btn" @click="cancel">Abbrechen</button>
            <button class="ks-btn-filled confirm-btn" @click="confirm">{{ confirmText }}</button>
          </div>
        </div>
      </transition>
    </div>
  </transition>
</template>

<script setup>
import { defineProps, defineEmits } from 'vue';

const props = defineProps({
  show: Boolean,
  title: {
    type: String,
    default: 'Bestätigen'
  },
  message: String,
  confirmText: {
    type: String,
    default: 'Löschen'
  }
});

const emit = defineEmits(['confirm', 'cancel']);

const confirm = () => emit('confirm');
const cancel = () => emit('cancel');
</script>

<style scoped>
.modal-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.6);
  z-index: 200;
  display: flex;
  align-items: center;
  justify-content: center;
}

.confirm-modal {
  background: var(--ks-surface);
  border-radius: 16px;
  width: 90%;
  max-width: 400px;
  overflow: hidden;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3);
}

.modal-content {
  padding: 24px;
  text-align: center;
}

.modal-title {
  margin: 0 0 12px 0;
  font-size: 20px;
  color: var(--ks-text);
}

.modal-message {
  margin: 0;
  font-size: 16px;
  color: var(--ks-text-muted);
  line-height: 1.5;
}

.modal-actions {
  display: flex;
  padding: 16px;
  gap: 12px;
  background: var(--ks-surface-2);
  border-top: 1px solid var(--ks-border);
}

.cancel-btn {
  flex: 1;
  padding: 12px;
  font-size: 16px;
  min-height: 48px; /* Touch target */
}

.confirm-btn {
  flex: 1;
  padding: 12px;
  font-size: 16px;
  background: var(--ks-error);
  color: white;
  min-height: 48px; /* Touch target */
  border: none;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.slide-up-enter-active,
.slide-up-leave-active {
  transition: transform 0.2s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}
.slide-up-enter-from,
.slide-up-leave-to {
  transform: translateY(20px) scale(0.95);
}
</style>
