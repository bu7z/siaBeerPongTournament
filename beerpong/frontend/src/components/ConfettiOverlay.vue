<template>
  <transition name="fade">
    <div v-if="show" class="confetti-overlay" @click.self="onBackdropClick">
      <canvas ref="canvasEl" class="confetti-canvas"></canvas>

      <button
        v-if="clickToClose"
        class="btn btn-sm btn-outline-light close-btn"
        @click="$emit('close')"
      >
        Schließen
      </button>
    </div>
  </transition>
</template>

<script setup>
import { ref, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'

/**
 * Props
 */
const props = defineProps({
  show: { type: Boolean, default: false },
  mode: { type: String, default: 'burst' }, // 'burst' | 'rain'
  durationMs: { type: Number, default: 3000 },
  count: { type: Number, default: 180 },
  gravity: { type: Number, default: 160 },   // px/s²
  wind: { type: Number, default: 8 },        // px/s
  airFriction: { type: Number, default: 0.02 },
  colors: {
    type: Array,
    default: () => ['#ff3366','#33d1a0','#ffd166','#5ec8e2','#ffffff']
  },
  shapes: {
    type: Array,
    default: () => ['square','circle','triangle','strip']
  },
  clickToClose: { type: Boolean, default: true }
})
const emit = defineEmits(['close','finished'])

/**
 * State
 */
const canvasEl = ref(null)
let ctx = null
let rafId = null
let lastTs = 0
let startTs = 0
let pieces = []
let stopped = false
let dpr = 1

/**
 * Helpers
 */
function rand(min, max) { return min + Math.random() * (max - min) }
function pick(arr) { return arr[Math.floor(Math.random() * arr.length)] }

function sizeCanvasToElement() {
  const c = canvasEl.value
  if (!c) return
  const rect = c.getBoundingClientRect()
  dpr = Math.max(1, window.devicePixelRatio || 1)

  // physische Bitmap-Größe
  c.width = Math.max(1, Math.floor(rect.width * dpr))
  c.height = Math.max(1, Math.floor(rect.height * dpr))

  // Zeichen-Kontext skalieren, damit wir in CSS-Pixeln rechnen können
  ctx = c.getContext('2d')
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
}

function spawnPieces(mode) {
  const c = canvasEl.value
  if (!c) return []
  const rect = c.getBoundingClientRect()
  const w = rect.width
  const h = rect.height
  const list = []
  const N = Math.max(1, props.count)

  for (let i = 0; i < N; i++) {
    const shape = pick(props.shapes)
    const color = pick(props.colors)
    const size = rand(6, 14)

    if (mode === 'rain') {
      // Start oben, fallen nach unten
      list.push({
        x: Math.random() * w,
        y: rand(-h * 0.6, -20),
        vx: props.wind + rand(-15, 15),
        vy: rand(60, 140),
        ax: 0,
        ay: props.gravity,
        rot: rand(0, Math.PI * 2),
        vr: rand(-3, 3),         // rad/s
        size,
        life: 1,
        color,
        shape
      })
    } else {
      // 'burst' – zentrierter/oberer Ausstoß
      const originX = w * 0.5 + rand(-w * 0.1, w * 0.1)
      const originY = h * 0.32 + rand(-h * 0.06, h * 0.06)
      const angle = rand(-Math.PI - 0.5, -0.5) // nach oben links/rechts
      const speed = rand(120, 360)
      list.push({
        x: originX,
        y: originY,
        vx: Math.cos(angle) * speed + props.wind,
        vy: Math.sin(angle) * speed,
        ax: 0,
        ay: props.gravity,
        rot: rand(0, Math.PI * 2),
        vr: rand(-4, 4),
        size,
        life: 1,
        color,
        shape
      })
    }
  }
  return list
}

function drawPiece(p) {
  ctx.save()
  ctx.translate(p.x, p.y)
  ctx.rotate(p.rot)
  ctx.fillStyle = p.color
  ctx.strokeStyle = p.color

  const s = p.size

  switch (p.shape) {
    case 'circle':
      ctx.beginPath()
      ctx.arc(0, 0, s * 0.5, 0, Math.PI * 2)
      ctx.fill()
      break
    case 'triangle':
      ctx.beginPath()
      ctx.moveTo(-s * 0.6, s * 0.5)
      ctx.lineTo(0, -s * 0.6)
      ctx.lineTo(s * 0.6, s * 0.5)
      ctx.closePath()
      ctx.fill()
      break
    case 'strip':
      ctx.fillRect(-s * 0.9, -s * 0.18, s * 1.8, s * 0.36)
      break
    default: // 'square'
      ctx.fillRect(-s/2, -s/2, s, s)
  }

  ctx.restore()
}

function step(ts) {
  if (stopped) return
  if (!lastTs) lastTs = ts
  if (!startTs) startTs = ts
  const dt = Math.min(0.06, (ts - lastTs) / 1000) // s, capped
  lastTs = ts

  const c = canvasEl.value
  const rect = c.getBoundingClientRect()
  const w = rect.width
  const h = rect.height

  ctx.clearRect(0, 0, w, h)

  // Update
  const drag = Math.max(0, Math.min(1, props.airFriction))
  for (const p of pieces) {
    // simple Luftwiderstand
    p.vx *= (1 - drag * dt)
    p.vy *= (1 - drag * dt)

    // Beschleunigung
    p.vx += p.ax * dt
    p.vy += p.ay * dt

    // Position
    p.x += p.vx * dt
    p.y += p.vy * dt
    p.rot += p.vr * dt

    // Lebenszeit optisch (nur für 'burst' sinnvoll)
    if (props.mode === 'burst') {
      const age = (ts - startTs) / props.durationMs
      p.life = Math.max(0, 1 - age)
    }

    // Wrap bei Rain (oben neu rein)
    if (props.mode === 'rain') {
      if (p.y > h + 24) {
        p.y = -24
        p.x = Math.random() * w
        p.vy = rand(60, 140)
        p.vx = props.wind + rand(-15, 15)
      }
    }
  }

  // Zeichnen
  for (const p of pieces) {
    if (p.life <= 0) continue
    drawPiece(p)
  }

  // Stop-Bedingung
  const elapsed = ts - startTs
  let done = false
  if (props.mode === 'rain') {
    done = elapsed >= props.durationMs
  } else {
    // burst: wenn Dauer vorbei und alle unter dem View oder ausgeblendet
    const allGone = pieces.every(p => p.y > h + 40 || p.life <= 0)
    done = elapsed >= props.durationMs && allGone
  }

  if (done) {
    stopLoop()
    emit('finished')
    return
  }

  rafId = requestAnimationFrame(step)
}

function startLoop() {
  if (!canvasEl.value) return
  stopped = false
  lastTs = 0
  startTs = 0
  rafId = requestAnimationFrame(step)
}

function stopLoop() {
  stopped = true
  if (rafId) {
    cancelAnimationFrame(rafId)
    rafId = null
  }
}

async function startConfetti() {
  await nextTick()              // sicherstellen, dass Overlay gerendert ist
  sizeCanvasToElement()         // Canvas korrekt dimensionieren (inkl. DPR)
  pieces = spawnPieces(props.mode)
  startLoop()
}

function teardownConfetti() {
  stopLoop()
  if (ctx) {
    const c = canvasEl.value
    if (c) {
      const rect = c.getBoundingClientRect()
      ctx.clearRect(0, 0, rect.width, rect.height)
    }
  }
  pieces = []
}

/**
 * Event handlers
 */
function onBackdropClick() {
  if (props.clickToClose) emit('close')
}

/**
 * Lifecycle
 */
function onResize() {
  if (!canvasEl.value || !props.show) return
  // Canvas neu skalieren, Content bleibt „fließend“
  sizeCanvasToElement()
}

onMounted(() => {
  window.addEventListener('resize', onResize, { passive: true })
  if (props.show) startConfetti()
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  teardownConfetti()
})

watch(() => props.show, (v) => {
  if (v) {
    teardownConfetti() // sauber neu starten
    startConfetti()
  } else {
    teardownConfetti()
  }
})
</script>

<style scoped>
.confetti-overlay {
  position: fixed;
  inset: 0;
  z-index: 2000;
  background: rgba(0,0,0,0.35);
  backdrop-filter: blur(1px);
}
.confetti-canvas {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  display: block; /* wichtig, damit clientWidth/Height stimmen */
}
.close-btn {
  position: absolute;
  top: 16px;
  right: 16px;
}
.fade-enter-active, .fade-leave-active { transition: opacity .18s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
