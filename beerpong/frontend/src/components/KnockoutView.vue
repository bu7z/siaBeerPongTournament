<template>
  <section class="mx-auto" style="max-width: 1200px;">
    <div class="d-flex justify-content-between align-items-center mb-3">
      <h2>KO-Phase</h2>
      <div class="d-flex gap-2">
        <button class="btn btn-outline-light" @click="$emit('back')">Zurück</button>
        <button class="btn btn-outline-secondary" @click="loadFromServer" :disabled="loading">Laden</button>
        <button class="btn btn-primary" @click="saveToServer" :disabled="loading || roundsLocal.length===0">Speichern</button>
      </div>
    </div>

    <div class="card bg-dark border-secondary mb-3">
      <div class="card-body d-flex align-items-center justify-content-between">
        <div class="d-flex align-items-center gap-3">
          <div>
            <div class="small text-light">KO-Größe</div>
            <div class="h4 text-white mb-0">{{ koSizeComputed }}</div>
          </div>
          <div>
            <div class="small text-light">Teilnehmer</div>
            <div class="h4 text-white mb-0">{{ initialTeams.length }}</div>
          </div>
        </div>
        <div class="d-flex align-items-center gap-2">
          <div v-if="finalWinner" class="me-2">
            <span class="badge bg-success">Sieger: {{ finalWinner }}</span>
          </div>
          <button class="btn btn-sm btn-outline-light me-2" @click="seedBracket" :disabled="initialTeams.length===0">
            Neu setzen (Seeding)
          </button>
          <button class="btn btn-sm btn-outline-warning" @click="clearWinners" :disabled="roundsLocal.length===0">
            Sieger zurücksetzen
          </button>
        </div>
      </div>
    </div>

    <KnockoutBracket
      :rounds="roundsLocal"
      @set-winner="onSetWinner"
      @update:rounds="applyRounds"
    />

    <div class="text-end mt-4">
      <button class="btn btn-success" @click="saveToServer" :disabled="loading || roundsLocal.length===0">KO speichern</button>
    </div>

    <!-- Konfetti-Overlay: feuert automatisch bei finalem Gewinner -->
    <ConfettiOverlay
      :show="showConfetti"
      mode="burst"
      :durationMs="3500"
      :count="220"
      :gravity="150"
      :wind="8"
      :airFriction="0.02"
      :colors="['#ff3366','#33d1a0','#ffd166','#5ec8e2','#ffffff']"
      :shapes="['square','circle','triangle','strip']"
      :clickToClose="true"
      @close="showConfetti = false"
      @finished="showConfetti = false"
    />
  </section>
</template>

<script setup>
import { reactive, ref, computed, onMounted, watch } from 'vue'
import KnockoutBracket from './KnockoutBracket.vue'
import ConfettiOverlay from './ConfettiOverlay.vue'

const props = defineProps({
  tournamentId: { type: Number, required: true },
  teams: { type: Array, default: () => [] },   // bereits qualifizierte Teams (vom Play-In/Groups)
  koSize: { type: Number, default: null }      // gewünschte Baumgröße; falls null → berechnet
})
const emit = defineEmits(['back','saved'])

const loading = ref(false)
const roundsLocal = reactive([]) // [{ round_name, bracket_type, matches:[{team1,team2,winner}]}]
const initialTeams = computed(() => (props.teams || []).filter(Boolean))

const POW2 = [4,8,16,32,64,128]
const koSizeComputed = computed(() => {
  const s = props.koSize
  if (s) return s
  const n = initialTeams.value.length
  for (const k of POW2) if (k >= n) return k
  return n
})

/** --- Confetti --- */
const showConfetti = ref(false)
const finalWinner = computed(() => {
  if (!roundsLocal.length) return null
  const last = roundsLocal[roundsLocal.length - 1]
  if (!last?.matches?.length) return null
  const fm = last.matches[0]
  // Zeige Konfetti nur, wenn Finale ein echtes Duell (beide Teams) und Gewinner gesetzt
  if (fm?.team1 && fm?.team2 && fm?.winner) return fm.winner
  return null
})
watch(finalWinner, (v, oldV) => {
  if (v && v !== oldV) {
    // kleines Delay, damit Button-Highlight fertig rendert
    setTimeout(() => { showConfetti.value = true }, 80)
  }
})

/* --------- Seeding / Bracket-Aufbau ---------- */
function roundNameFor(totalRounds, rIdx) {
  // letztes = Finale, davor Halbfinale, etc.
  const names = ['Achtelfinale','Viertelfinale','Halbfinale','Finale']
  const idxFromEnd = totalRounds - rIdx
  return names[idxFromEnd - 1] || `Runde ${rIdx + 1}`
}

function seedPairs(teams, bracketSize) {
  // klassisches 1 vs last, 2 vs last-1 … mit BYEs
  const list = teams.slice(0, bracketSize)
  while (list.length < bracketSize) list.push(null) // BYE
  const pairs = []
  for (let i = 0; i < bracketSize / 2; i++) {
    pairs.push([list[i], list[bracketSize - 1 - i]])
  }
  return pairs
}

function buildEmptyRound(matchesCount) {
  return {
    bracket_type: 'main',
    round_name: '',
    matches: Array.from({ length: matchesCount }, () => ({ team1: null, team2: null, winner: null }))
  }
}

function seedBracket() {
  const size = koSizeComputed.value
  if (!size || size < 2) return
  const pairs = seedPairs(initialTeams.value, size)

  const rounds = []
  let currentMatches = pairs.map(p => ({ team1: p[0], team2: p[1], winner: autoWinner(p[0], p[1]) }))
  rounds.push({
    bracket_type: 'main',
    round_name: roundNameFor(Math.log2(size), 0),
    matches: currentMatches
  })

  // Folge-Runden generieren
  let m = currentMatches.length
  let roundIdx = 1
  while (m > 1) {
    m = Math.floor(m / 2)
    const r = buildEmptyRound(m)
    r.round_name = roundNameFor(Math.log2(size), roundIdx)
    rounds.push(r)
    roundIdx++
  }

  // BYE-Sieger automatisch propagieren
  propagateAll(rounds)

  roundsLocal.splice(0, roundsLocal.length, ...rounds)
}

function autoWinner(t1, t2) {
  // BYE-Logik: wenn ein Team null ist, gewinnt das andere automatisch
  if (t1 && !t2) return t1
  if (!t1 && t2) return t2
  return null
}

function propagateAll(rounds) {
  for (let r = 0; r < rounds.length - 1; r++) {
    const cur = rounds[r]
    const nxt = rounds[r + 1]
    cur.matches.forEach((m, idx) => {
      const w = m.winner || autoWinner(m.team1, m.team2)
      if (!w) return
      const tIdx = Math.floor(idx / 2)
      const pos  = (idx % 2 === 0) ? 'team1' : 'team2'
      nxt.matches[tIdx][pos] = w
      nxt.matches[tIdx].winner = (nxt.matches[tIdx].winner === w) ? w : null
    })
  }
}

/* --------- Interaktion ---------- */
function onSetWinner(rIdx, mIdx, team) {
  const r = roundsLocal[rIdx]
  if (!r?.matches?.[mIdx]) return
  r.matches[mIdx].winner = team

  // nachfolgende Runden frisch propagieren (ab rIdx)
  for (let rr = rIdx; rr < roundsLocal.length - 1; rr++) {
    const nxt = roundsLocal[rr + 1]
    nxt.matches.forEach(mm => {
      mm.team1 = null
      mm.team2 = null
      mm.winner = null
    })
    roundsLocal[rr].matches.forEach((m, idx) => {
      const w = m.winner || autoWinner(m.team1, m.team2)
      if (!w) return
      const tIdx = Math.floor(idx / 2)
      const pos  = (idx % 2 === 0) ? 'team1' : 'team2'
      roundsLocal[rr + 1].matches[tIdx][pos] = w
    })
  }
}

function clearWinners() {
  roundsLocal.forEach(r => r.matches.forEach(m => m.winner = null))
}

function applyRounds(newRounds) {
  roundsLocal.splice(0, roundsLocal.length, ...(newRounds ?? []))
}

/* --------- Backend I/O ---------- */
async function loadFromServer() {
  loading.value = true
  try {
    const res = await fetch(`http://localhost:5000/tournaments/${props.tournamentId}/load-ko-bracket`)
    if (!res.ok) throw new Error('load-ko-bracket failed')
    const data = await res.json()

    const rounds = (data?.rounds || []).map(r => ({
      bracket_type: r.bracket_type || 'main',
      round_name: r.round_name || '',
      matches: (r.matches || []).map(m => ({
        team1: m.team1 ?? null,
        team2: m.team2 ?? null,
        winner: m.winner ?? null
      }))
    }))

    if (rounds.length > 0) {
      roundsLocal.splice(0, roundsLocal.length, ...rounds)
    } else {
      // Falls leer → neu seeden
      seedBracket()
    }
  } catch (e) {
    console.error(e)
    if (roundsLocal.length === 0) seedBracket()
  } finally {
    loading.value = false
  }
}

async function saveToServer() {
  loading.value = true
  try {
    const payload = {
      rounds: roundsLocal.map(r => ({
        round_name: r.round_name || '',
        bracket_type: r.bracket_type || 'main',
        matches: r.matches.map(m => ({
          team1: m.team1 ?? null,
          team2: m.team2 ?? null,
          winner: m.winner ?? null
        }))
      }))
    }
    const res = await fetch(`http://localhost:5000/tournaments/${props.tournamentId}/save-ko-bracket`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(payload)
    })
    if (!res.ok) throw new Error('save-ko-bracket failed')
    emit('saved')

    // Optional: wenn Sieger existiert, Konfetti nochmals zeigen
    if (finalWinner.value) {
      showConfetti.value = true
    }
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await loadFromServer()
  if (roundsLocal.length === 0 && initialTeams.value.length > 0) {
    seedBracket()
  }
})
</script>

<style scoped>
/* nichts spezielles */
</style>
