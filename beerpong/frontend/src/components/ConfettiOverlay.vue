<template>
  <div class="confetti-overlay">
    <div
      v-for="n in 40"
      :key="n"
      class="confetti-piece"
      :style="pieceStyle(n)"
    ></div>
  </div>
</template>

<script setup>
function pieceStyle(n) {
  const left = Math.random() * 100
  const delay = Math.random() * 1.5
  const duration = 2.5 + Math.random() * 1
  const rotate = Math.floor(Math.random() * 360)
  const colors = ['#ffffff', '#0d6efd', '#198754', '#ffc107', '#e83e8c']
  const color = colors[n % colors.length]

  return {
    left: left + 'vw',
    animationDelay: delay + 's',
    animationDuration: duration + 's',
    background: color,
    transform: `rotate(${rotate}deg)`
  }
}
</script>

<style scoped>
.confetti-overlay {
  position: fixed;
  inset: 0;
  pointer-events: none;
  overflow: hidden;
  z-index: 9999;
}
.confetti-piece {
  position: absolute;
  top: -12px;
  width: 10px;
  height: 18px;
  opacity: 0.9;
  border-radius: 2px;
  animation-name: confetti-fall;
  animation-timing-function: linear;
}
@keyframes confetti-fall {
  0% {
    transform: translateY(0) rotate(0deg);
  }
  100% {
    transform: translateY(110vh) rotate(180deg);
  }
}
</style>
