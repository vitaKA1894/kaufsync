<template>
  <div class="app-shell">
    <div class="app-shell__glow app-shell__glow--one"></div>
    <div class="app-shell__glow app-shell__glow--two"></div>
    <router-view />
  </div>
</template>

<style scoped>
.app-shell {
  position: relative;
  min-height: 100svh;
  overflow: hidden;
}

.app-shell__glow {
  position: fixed;
  inset: auto;
  pointer-events: none;
  filter: blur(72px);
  opacity: 0.32;
  z-index: 0;
}

.app-shell__glow--one {
  top: -120px;
  left: -60px;
  width: 320px;
  height: 320px;
  background: radial-gradient(circle, rgba(168, 199, 250, 0.34) 0%, rgba(168, 199, 250, 0) 72%);
}

.app-shell__glow--two {
  right: -80px;
  bottom: 60px;
  width: 280px;
  height: 280px;
  background: radial-gradient(circle, rgba(194, 231, 255, 0.18) 0%, rgba(194, 231, 255, 0) 72%);
}
</style>