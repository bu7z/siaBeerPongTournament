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

        <button
          class="btn btn-primary btn-sm mt-2"
          :disabled="miniWinners.length < 2"
          @click="finishMini"
        >
          2 Teams übernehmen
        </button>
      </div>
    </div>

    <!-- Rage -->
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

const miniWinners = computed(() => {
  const counter = {}
  miniMatches.value.forEach((m) => {
    if (!m.winner) return
    counter[m.winner] = (counter[m.winner] || 0) + 1
  })
  return Object.entries(counter)
    .sort((a, b) => b[1] - a[1])
    .map(([name]) => name)
})

function finishMini() {
  emit('done', miniWinners.value.slice(0, 2))
}

function finishRage(loser) {
  const winners = props.teams.filter((t) => t !== loser)
  emit('done', winners)
}
</script>
