<template>
  <section class="mx-auto" style="max-width: 700px;">
    <div class="d-flex justify-content-between align-items-center mb-4">
      <h2>Play-In / Zusatzrunde</h2>
      <button class="btn btn-outline-light" @click="$emit('cancel')">Zurück</button>
    </div>

    <p class="text-secondary mb-3">
      Es fehlen noch Teams für ein vollständiges KO. Diese 3 Teams spielen die letzten 2 Plätze aus.
    </p>

    <div class="mb-3">
      <button class="btn btn-sm btn-outline-light me-2" @click="startMini">3er-Mini-Runde</button>
      <button class="btn btn-sm btn-outline-light" @click="startRage">Rage Cage</button>
    </div>

    <!-- Mini-Runde -->
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

        <!-- Fall 1: klarer Ausgang -->
        <button
          v-if="miniClearlyDecided"
          class="btn btn-primary btn-sm mt-2"
          @click="finishMini"
        >
          2 Teams übernehmen
        </button>

        <!-- Fall 2: unentschieden → Rage zwischen den betroffenen -->
        <div v-else-if="miniAllDecided" class="mt-3">
          <p class="text-secondary small mb-2">
            Mini-Runde war unentschieden. Rage Cage zwischen:
          </p>
          <div class="d-flex flex-column gap-2">
            <button
              v-for="t in miniTieTeams"
              :key="t"
              class="btn btn-sm btn-outline-danger text-start"
              @click="finishMiniRage(t)"
            >
              {{ t }} war letzter
            </button>
          </div>
        </div>

        <!-- Fall 3: noch nicht alle Mini-Spiele entschieden -->
        <p v-else class="text-secondary small mt-2">
          Alle Mini-Spiele wählen oder Rage Cage starten.
        </p>
      </div>
    </div>

    <!-- Rage direkt -->
    <div v-if="rageMode" class="card bg-dark border-secondary">
      <div class="card-body">
        <p class="text-secondary small mb-2">Rage Cage – wer war letzter?</p>
        <div class="d-flex flex-column gap-2">
          <button
            v-for="t in teams"
            :key="t"
            class="btn btn-sm btn-outline-danger text-start"
            @click="finishRage(t)"
          >
            {{ t }} war letzter
          </button>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  teams: { type: Array, required: true } // genau 3
})

const emit = defineEmits(['cancel', 'done'])

const miniMatches = ref([])
const rageMode = ref(false)

function startMini() {
  rageMode.value = false
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
  rageMode.value = true
}

function setMiniWinner(idx, name) {
  miniMatches.value = miniMatches.value.map((m, i) =>
    i === idx ? { ...m, winner: name } : m
  )
}

/**
 * Hilfswerte aus der Mini-Runde
 */

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
  // array aus { name, wins }
  return Object.entries(counter).map(([name, wins]) => ({ name, wins }))
})

// war die Mini-Runde eindeutig?
const miniClearlyDecided = computed(() => {
  if (!miniAllDecided.value) return false

  const stats = [...miniStats.value].sort((a, b) => b.wins - a.wins)
  const first = stats[0]
  const second = stats[1]
  const third = stats[2]

  // Fall: 2,1,0 → eindeutig
  if (first.wins > second.wins && second.wins > third.wins) return true

  // Fall: 2,1,1 → 1. klar, aber 2./3. gleich → nicht eindeutig
  if (first.wins > second.wins && second.wins === third.wins) return false

  // Fall: 1,1,1 → nicht eindeutig
  if (first.wins === second.wins) return false

  return false
})

// welche Teams müssen bei Unentschieden Rage spielen?
const miniTieTeams = computed(() => {
  if (!miniAllDecided.value) return []
  const stats = [...miniStats.value].sort((a, b) => b.wins - a.wins)
  const firstWins = stats[0].wins
  const topGroup = stats.filter(s => s.wins === firstWins)

  // mehrere auf Platz 1 → alle in Rage
  if (topGroup.length > 1) {
    return topGroup.map(s => s.name)
  }

  // Platz 1 eindeutig, aber Platz 2 mehrfach
  const secondWins = stats[1].wins
  const secondGroup = stats.filter(s => s.wins === secondWins)
  if (secondGroup.length > 1) {
    return secondGroup.map(s => s.name)
  }

  return []
})

function finishMini() {
  // wir wissen: miniClearlyDecided = true
  const stats = [...miniStats.value].sort((a, b) => b.wins - a.wins)
  const winners = [stats[0].name, stats[1].name]
  emit('done', winners)
}

function finishMiniRage(loser) {
  // wir bekommen einen Loser aus der Gleichstandsgruppe
  const winners = props.teams.filter(t => t !== loser)
  emit('done', winners)
}

function finishRage(loser) {
  const winners = props.teams.filter((t) => t !== loser)
  emit('done', winners)
}
</script>
