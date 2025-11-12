<template>
  <section class="mx-auto" style="max-width: 700px;">
    <div class="d-flex justify-content-between align-items-center mb-4">
      <h2>Play-In / Zusatzrunde</h2>
      <button class="btn btn-outline-light" @click="$emit('cancel')">Zurück</button>
    </div>
    <p class="text-secondary mb-3">
      Diese Teams sind in die Play-In-Runde gekommen: {{ teams.join(', ') }}.
      <br>
      Es fehlen noch Teams für ein vollständiges KO. Wähle, wie viele Teams weiterkommen sollen:
    </p>
    <div class="mb-3">
      <input
        type="number"
        class="form-control bg-dark text-light border-secondary"
        v-model="advanceCount"
        min="1"
        :max="teams.length - 1"
        placeholder="Anzahl weiterkommender Teams"
      />
    </div>
    <div class="mb-3" v-if="advanceCount">
      <button class="btn btn-sm btn-outline-light me-2" @click="startMini">Mini-Runde</button>
      <button class="btn btn-sm btn-outline-light" @click="startRage">Rage Cage</button>
    </div>
    <!-- Mini-Runde (dynamisch für beliebige Team-Anzahl) -->
    <div v-if="miniMatches.length" class="card bg-dark border-secondary mb-3">
      <div class="card-body">
        <p class="text-secondary small mb-2">Mini-Runde (Sieger wählen)</p>
        <div
          v-for="(m, idx) in miniMatches"
          :key="idx"
          class="d-flex gap-2 mb-2"
        >
          <button
            class="btn btn-sm flex-fill text-start"
            :class="m.winner === m.team1 ? 'btn-success' : 'btn-outline-light'"
            @click="setMiniWinner(idx, m.team1)"
          >
            {{ m.team1 }}
          </button>
          <span class="text-secondary">vs</span>
          <button
            class="btn btn-sm flex-fill text-start"
            :class="m.winner === m.team2 ? 'btn-success' : 'btn-outline-light'"
            @click="setMiniWinner(idx, m.team2)"
          >
            {{ m.team2 }}
          </button>
        </div>
        <button
          v-if="miniClearlyDecided"
          class="btn btn-primary btn-sm mt-2"
          @click="finishMini"
        >
          {{ advanceCount }} Teams übernehmen
        </button>
        <div v-else-if="miniAllDecided" class="mt-3">
          <p class="text-secondary small mb-2">
            Mini-Runde war unentschieden. Rage Cage zwischen:
          </p>
          <div class="d-flex flex-column gap-2">
            <button
              v-for="t in miniTieTeams"
              :key="t"
              class="btn btn-sm btn-outline-danger text-start"
              :class="selectedMiniRageLoser === t ? 'btn-danger' : 'btn-outline-danger'"
              @click="setMiniRageLoser(t)"
            >
              {{ t }} war letzter
            </button>
          </div>
          <button
            v-if="selectedMiniRageLoser"
            class="btn btn-primary btn-sm mt-2"
            @click="finishMiniRage(selectedMiniRageLoser)"
          >
            {{ advanceCount }} Teams übernehmen
          </button>
        </div>
        <p v-else class="text-secondary small mt-2">
          Alle Mini-Spiele wählen oder Rage Cage starten.
        </p>
      </div>
    </div>
    <!-- Rage direkt (dynamisch) -->
    <div v-if="rageMode" class="card bg-dark border-secondary">
      <div class="card-body">
        <p class="text-secondary small mb-2">Rage Cage – wer war letzter?</p>
        <div class="d-flex flex-column gap-2">
          <button
            v-for="t in teams"
            :key="t"
            class="btn btn-sm btn-outline-danger text-start"
            :class="selectedRageLoser === t ? 'btn-danger' : 'btn-outline-danger'"
            @click="setRageLoser(t)"
          >
            {{ t }} war letzter
          </button>
        </div>
        <button
          v-if="selectedRageLoser"
          class="btn btn-primary btn-sm mt-2"
          @click="finishRage(selectedRageLoser)"
        >
          {{ advanceCount }} Teams übernehmen
        </button>
      </div>
    </div>
  </section>
</template>
<script setup>
import { ref, computed } from 'vue'
const props = defineProps({
  teams: { type: Array, required: true },
  qualifiedCount: { type: Number, default: 0 } // Für Kontext, wie viele schon qualified
})
const emit = defineEmits(['cancel', 'done'])
const miniMatches = ref([])
const rageMode = ref(false)
const selectedMiniRageLoser = ref(null)
const selectedRageLoser = ref(null)
const advanceCount = ref(2) // Default 2, aber dynamisch
function startMini() {
  rageMode.value = false
  selectedMiniRageLoser.value = null
  const arr = props.teams
  const matches = []
  for (let i = 0; i < arr.length; i++) {
    for (let j = i + 1; j < arr.length; j++) {
      matches.push({
        team1: arr[i],
        team2: arr[j],
        winner: null
      })
    }
  }
  miniMatches.value = matches
}
function startRage() {
  miniMatches.value = []
  selectedRageLoser.value = null
  rageMode.value = true
}
function setMiniWinner(idx, name) {
  miniMatches.value = miniMatches.value.map((m, i) =>
    i === idx ? { ...m, winner: name } : m
  )
}
function setMiniRageLoser(loser) {
  selectedMiniRageLoser.value = loser
}
function setRageLoser(loser) {
  selectedRageLoser.value = loser
}
const miniAllDecided = computed(() =>
  miniMatches.value.length > 0 &&
  miniMatches.value.every(m => !!m.winner)
)
const miniStats = computed(() => {
  const counter = {}
  props.teams.forEach(t => { counter[t] = 0 })
  miniMatches.value.forEach((m) => {
    if (!m.winner) return
    counter[m.winner] = (counter[m.winner] || 0) + 1
  })
  return Object.entries(counter).map(([name, wins]) => ({ name, wins }))
})
const miniClearlyDecided = computed(() => {
  if (!miniAllDecided.value) return false
  const stats = [...miniStats.value].sort((a, b) => b.wins - a.wins)
  // Überprüfen, ob die Top N (advanceCount) eindeutig sind
  if (stats.length < advanceCount.value + 1) return false
  return stats[advanceCount.value - 1].wins > stats[advanceCount.value].wins
})
const miniTieTeams = computed(() => {
  if (!miniAllDecided.value) return []
  const stats = [...miniStats.value].sort((a, b) => b.wins - a.wins)
  const thresholdWins = stats[advanceCount.value - 1].wins
  return stats.filter(s => s.wins === thresholdWins).map(s => s.name)
})
function finishMini() {
  const stats = [...miniStats.value].sort((a, b) => b.wins - a.wins)
  const winners = stats.slice(0, advanceCount.value).map(s => s.name)
  emit('done', winners)
}
function finishMiniRage(loser) {
  // Für Tie, entferne Loser und nimm die Top
  const remaining = miniTieTeams.value.filter(t => t !== loser)
  const winners = [...miniStats.value]
    .sort((a, b) => b.wins - a.wins)
    .slice(0, advanceCount.value - (miniTieTeams.value.length - remaining.length))
    .map(s => s.name)
    .concat(remaining.slice(0, advanceCount.value - winners.length))
  emit('done', winners)
  selectedMiniRageLoser.value = null
}
function finishRage(loser) {
  const winners = props.teams.filter((t) => t !== loser).slice(0, advanceCount.value)
  emit('done', winners)
  selectedRageLoser.value = null
}
</script>