<template>
  <transition name="fade">
    <div v-if="show" class="confetti-overlay" @click.self="onBackdropClick">
      <!-- Canvas Layer (Konfetti) -->
      <canvas ref="canvasEl" class="confetti-canvas"></canvas>

      <!-- Content Layer -->
      <div class="content-layer">
        <!-- 1) Sieger-Banner (erste N Sekunden) -->
        <div v-if="showWinnerPhase" class="winner-banner">
          <div class="winner-title">Gewinner</div>
          <div class="winner-name">{{ winnerName || '—' }}</div>
        </div>

        <!-- 2) Bracket-Ansicht (nach Sieger-Phase) -->
        <div v-else class="bracket-wrapper">
          <div class="bracket-header">
            <div class="title">KO-Phase</div>
            <div class="subtitle">
              {{ displayRounds.length }} Runde(n) ·
              <span v-if="totalTeams">{{ totalTeams }} Team(s)</span>
            </div>
          </div>

          <div class="bracket-scroll">
            <div class="bracket">
              <div
                v-for="(round, rIdx) in displayRounds"
                :key="rIdx"
                class="bracket-round"
              >
                <div class="round-name">{{ round.round_name || 'Runde' }}</div>
                <div class="round-matches">
                  <div
                    v-for="(m, mIdx) in (round.matches || [])"
                    :key="(m.id || mIdx) + '-' + rIdx"
                    class="match"
                  >
                    <div class="team-row" :class="teamClass(m, 'team1')">
                      <span class="team-name">{{ m.team1 || '—' }}</span>
                      <span class="score">{{ printScore(m.cups_team1) }}</span>
                    </div>
                    <div class="team-row" :class="teamClass(m, 'team2')">
                      <span class="team-name">{{ m.team2 || '—' }}</span>
                      <span class="score">{{ printScore(m.cups_team2) }}</span>
                    </div>
                    <!-- Pokal/Winner-Chip entfernt -->
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Optional: keine Daten -->
          <div v-if="displayRounds.length === 0" class="no-data">
            Keine KO-Daten vorhanden.
          </div>
        </div>
      </div>

      <!-- Close -->
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
import { ref, watch, onMounted, onBeforeUnmount, nextTick, computed } from 'vue'

/* Props */
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
  clickToClose: { type: Boolean, default: true },

  // Sieger & KO-Phase
  winnerName: { type: String, default: '' },
  // [{ round_name, bracket_type, matches:[{team1,team2,cups_team1,cups_team2,winner}]}]
  rounds: { type: Array, default: () => [] },

  // Winner-Banner Dauer
  winnerDurationMs: { type: Number, default: 10000 }
})
const emit = defineEmits(['close','finished'])

/* State */
const canvasEl = ref(null)
let ctx = null
let rafId = null
let lastTs = 0
let startTs = 0
let pieces = []
let stopped = false
let dpr = 1

const showWinnerPhase = ref(true)
let winnerTimer = null

/* Anzeige-Reihenfolge: Platz 3 vor Finale, Finale ganz rechts */
const displayRounds = computed(() => {
  const src = Array.isArray(props.rounds) ? props.rounds.slice() : []
  if (src.length === 0) return []

  const main = src.filter(r => (r.bracket_type || 'main') !== 'placement')
  const placement = src.filter(r => (r.bracket_type || 'main') === 'placement')

  if (main.length === 0) return src

  // Finale ist die letzte Main-Runde
  const finalRound = main[main.length - 1]
  const preFinal = main.slice(0, -1)

  // Platz 3 (falls vorhanden) direkt VOR das Finale setzen
  const out = [...preFinal, ...placement, finalRound]
  return out
})

/* Teams zählen aus erster Main-Runde */
const totalTeams = computed(() => {
  const firstMain = displayRounds.value.find(r => (r.bracket_type || 'main') !== 'placement')
  if (!firstMain) return 0
  const matches = firstMain.matches || []
  const s = new Set()
  for (const m of matches) {
    if (m?.team1) s.add(m.team1)
    if (m?.team2) s.add(m.team2)
  }
  return s.size
})

/* Konfetti-Helpers */
function rand(min, max) { return min + Math.random() * (max - min) }
function pick(arr) { return arr[Math.floor(Math.random() * arr.length)] }

function sizeCanvasToElement() {
  const c = canvasEl.value
  if (!c) return
  const rect = c.getBoundingClientRect()
  dpr = Math.max(1, window.devicePixelRatio || 1)
  c.width = Math.max(1, Math.floor(rect.width * dpr))
  c.height = Math.max(1, Math.floor(rect.height * dpr))
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
      list.push({
        x: Math.random() * w, y: rand(-h * 0.6, -20),
        vx: props.wind + rand(-15, 15), vy: rand(60, 140),
        ax: 0, ay: props.gravity, rot: rand(0, Math.PI * 2), vr: rand(-3, 3),
        size, life: 1, color, shape
      })
    } else {
      const originX = w * 0.5 + rand(-w * 0.1, w * 0.1)
      const originY = h * 0.32 + rand(-h * 0.06, h * 0.06)
      const angle = rand(-Math.PI - 0.5, -0.5)
      const speed = rand(120, 360)
      list.push({
        x: originX, y: originY,
        vx: Math.cos(angle) * speed + props.wind, vy: Math.sin(angle) * speed,
        ax: 0, ay: props.gravity, rot: rand(0, Math.PI * 2), vr: rand(-4, 4),
        size, life: 1, color, shape
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
  const s = p.size
  switch (p.shape) {
    case 'circle':
      ctx.beginPath(); ctx.arc(0, 0, s * 0.5, 0, Math.PI * 2); ctx.fill(); break
    case 'triangle':
      ctx.beginPath()
      ctx.moveTo(-s * 0.6, s * 0.5); ctx.lineTo(0, -s * 0.6); ctx.lineTo(s * 0.6, s * 0.5)
      ctx.closePath(); ctx.fill(); break
    case 'strip':
      ctx.fillRect(-s * 0.9, -s * 0.18, s * 1.8, s * 0.36); break
    default:
      ctx.fillRect(-s/2, -s/2, s, s)
  }
  ctx.restore()
}

function step(ts) {
  if (stopped) return
  if (!lastTs) lastTs = ts
  if (!startTs) startTs = ts
  const dt = Math.min(0.06, (ts - lastTs) / 1000)
  lastTs = ts

  const c = canvasEl.value
  const rect = c.getBoundingClientRect()
  const w = rect.width
  const h = rect.height

  ctx.clearRect(0, 0, w, h)

  const drag = Math.max(0, Math.min(1, props.airFriction))
  for (const p of pieces) {
    p.vx *= (1 - drag * dt); p.vy *= (1 - drag * dt)
    p.vx += p.ax * dt; p.vy += p.ay * dt
    p.x += p.vx * dt; p.y += p.vy * dt; p.rot += p.vr * dt
    if (props.mode === 'burst') {
      const age = (ts - startTs) / props.durationMs
      p.life = Math.max(0, 1 - age)
    }
    if (props.mode === 'rain' && p.y > h + 24) {
      p.y = -24; p.x = Math.random() * w
      p.vy = rand(60, 140); p.vx = props.wind + rand(-15, 15)
    }
  }

  for (const p of pieces) if (p.life > 0) drawPiece(p)

  const elapsed = ts - startTs
  const allGone = pieces.every(p => p.y > h + 40 || p.life <= 0)
  const done = (props.mode === 'rain') ? (elapsed >= props.durationMs)
                                       : (elapsed >= props.durationMs && allGone)
  if (done) { stopLoop(); emit('finished'); return }
  rafId = requestAnimationFrame(step)
}

function startLoop() {
  if (!canvasEl.value) return
  stopped = false; lastTs = 0; startTs = 0
  rafId = requestAnimationFrame(step)
}
function stopLoop() {
  stopped = true
  if (rafId) { cancelAnimationFrame(rafId); rafId = null }
}
async function startConfetti() {
  await nextTick()
  sizeCanvasToElement()
  pieces = spawnPieces(props.mode)
  startLoop()
}
function teardownConfetti() {
  stopLoop()
  if (ctx && canvasEl.value) {
    const rect = canvasEl.value.getBoundingClientRect()
    ctx.clearRect(0, 0, rect.width, rect.height)
  }
  pieces = []
}

/* Bracket-Helpers */
function teamClass(m, key) {
  const name = key === 'team1' ? m.team1 : m.team2
  if (!name || !m.winner) return ''
  return m.winner === name ? 'win' : 'lose'
}
function printScore(v) {
  const n = Number(v)
  return Number.isFinite(n) ? n : '–'
}

/* Events */
function onBackdropClick() { if (props.clickToClose) emit('close') }

/* Lifecycle */
function onResize() {
  if (!canvasEl.value || !props.show) return
  sizeCanvasToElement()
}
function startWinnerPhaseTimer() {
  clearWinnerTimer()
  showWinnerPhase.value = true
  if (props.winnerDurationMs > 0) {
    winnerTimer = setTimeout(() => {
      showWinnerPhase.value = false
      winnerTimer = null
    }, props.winnerDurationMs)
  }
}
function clearWinnerTimer() {
  if (winnerTimer) { clearTimeout(winnerTimer); winnerTimer = null }
}

onMounted(() => {
  window.addEventListener('resize', onResize, { passive: true })
  if (props.show) { startWinnerPhaseTimer(); startConfetti() }
})
onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  teardownConfetti()
  clearWinnerTimer()
})
watch(() => props.show, (v) => {
  if (v) { teardownConfetti(); startWinnerPhaseTimer(); startConfetti() }
  else { teardownConfetti(); clearWinnerTimer() }
})
</script>

<style scoped>
/* Overlay */
.confetti-overlay {
  position: fixed;
  inset: 0;
  z-index: 2000;
  background: rgba(0,0,0,0.40);
  backdrop-filter: blur(2px);
}

/* Canvas */
.confetti-canvas {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  display: block;
  pointer-events: none;
}

/* Content */
.content-layer {
  position: absolute;
  inset: 0;
  display: grid;
  place-items: center;
  padding: 24px;
}

/* Winner Banner */
.winner-banner {
  text-align: center;
  color: #fff;
  text-shadow: 0 4px 22px rgba(0,0,0,0.5);
  max-width: min(92vw, 1200px);
  padding: 24px 16px;
  border-radius: 16px;
  background: linear-gradient(180deg, rgba(0,0,0,0.55) 0%, rgba(0,0,0,0.35) 60%, rgba(0,0,0,0.15) 100%);
  border: 1px solid rgba(255,255,255,0.18);
}
.winner-title {
  font-size: clamp(24px, 3.8vw, 36px);
  letter-spacing: 0.06em;
  opacity: 0.9;
  margin-bottom: 8px;
}
.winner-name {
  /* Responsive, bricht nie über den Viewport hinaus */
  font-size: clamp(34px, 8vw, 96px);
  font-weight: 800;
  line-height: 1.06;
  word-break: break-word;
  overflow-wrap: anywhere;
  hyphens: auto;
  margin: 0 auto;
}

/* Bracket */
.bracket-wrapper {
  width: 100%;
  max-width: 1400px;
  color: #fff;
}
.bracket-header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-bottom: 12px;
}
.bracket-header .title { font-size: clamp(18px, 2.4vw, 30px); font-weight: 700; }
.bracket-header .subtitle { opacity: 0.8; font-size: 14px; }

.bracket-scroll {
  max-height: min(70vh, 680px);
  overflow: auto;
  padding: 12px;
  border-radius: 12px;
  background: rgba(0,0,0,0.35);
  border: 1px solid rgba(255,255,255,0.12);
}

/* Runden als Spalten (Finale ganz rechts, weil displayRounds so sortiert ist) */
.bracket {
  display: grid;
  grid-auto-flow: column;
  grid-auto-columns: minmax(220px, 1fr);
  gap: 16px;
  min-width: 100%;
}
.bracket-round { display: flex; flex-direction: column; gap: 12px; }
.round-name { font-weight: 700; opacity: 0.9; }
.round-matches { display: flex; flex-direction: column; gap: 12px; }

/* Matches */
.match {
  position: relative;
  background: rgba(255,255,255,0.06);
  border: 1px solid rgba(255,255,255,0.18);
  border-radius: 12px;
  padding: 10px 12px;
}
.team-row {
  display: flex; align-items: center; justify-content: space-between;
  gap: 8px; padding: 6px 8px; border-radius: 8px;
}
.team-row + .team-row { margin-top: 6px; }

.team-name {
  max-width: 70%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.score { font-weight: 700; min-width: 28px; text-align: right; }

/* Sieger/Verlierer */
.team-row.win {
  background: rgba(0, 180, 90, 0.22);
  border: 1px solid rgba(0, 180, 90, 0.45);
}
.team-row.lose { opacity: 0.8; }

/* No Data */
.no-data { text-align: center; opacity: 0.85; margin-top: 12px; font-size: 14px; }

/* Close */
.close-btn { position: absolute; top: 16px; right: 16px; }

/* Transition */
.fade-enter-active, .fade-leave-active { transition: opacity .18s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

/* Responsive */
@media (max-width: 768px) {
  .bracket { grid-auto-columns: minmax(200px, 1fr); }
}
</style>
