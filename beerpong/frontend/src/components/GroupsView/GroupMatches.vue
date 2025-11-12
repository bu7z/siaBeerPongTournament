<template>
  <div class="card-footer border-top border-secondary bg-dark">
    <p class="text-secondary small mb-2">
      Spiele ({{ localMatches.length }})
    </p>

    <div
      v-for="(m, idx) in localMatches"
      :key="(groupName || 'G') + '-' + (m.id ?? idx)"
      class="match-entry mb-3 p-2 border border-secondary rounded"
    >
      <div class="d-flex align-items-center justify-content-between gap-2">
        <!-- Team 1 -->
        <div class="d-flex align-items-center flex-fill justify-content-between">
          <span class="text-truncate" style="max-width: 120px;">{{ m.team1 }}</span>

          <button
            class="btn btn-cup"
            :disabled="isLocked(m)"
            @click="onCupClick(idx, 'team1')"
            :title="`Becher für ${m.team1}`"
          >
            <img class="cup-img" src="/beer-cup.svg" alt="" />
            <span class="cup-count">{{ m.cups_team1 ?? 0 }}</span>
          </button>
        </div>

        <span class="mx-2 text-secondary">vs</span>

        <!-- Team 2 -->
        <div class="d-flex align-items-center flex-fill justify-content-between">
          <button
            class="btn btn-cup me-2"
            :disabled="isLocked(m)"
            @click="onCupClick(idx, 'team2')"
            :title="`Becher für ${m.team2}`"
          >
            <img class="cup-img" src="/beer-cup.svg" alt="" />
            <span class="cup-count">{{ m.cups_team2 ?? 0 }}</span>
          </button>

          <span class="text-truncate" style="max-width: 120px;">{{ m.team2 }}</span>
        </div>
      </div>

      <!-- Ergebnis-Anzeige -->
      <div v-if="m.winner" class="text-center mt-1">
        <small class="text-secondary">
          Ergebnis: {{ m.cups_team1 ?? 0 }} - {{ m.cups_team2 ?? 0 }} Becher
        </small>
        <div class="mt-1">
          <small class="text-success">🏆 Sieger: {{ m.winner }}</small>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, watch, toRefs } from 'vue'

const props = defineProps({
  groupName: { type: String, required: true },
  matches: { type: Array, required: true },
  cupsPerGame: { type: Number, default: 6 }
})
const emit = defineEmits(['update:matches', 'persist'])

const state = reactive({
  localMatches: props.matches.map(m => normalizeMatch(m))
})
const { localMatches } = toRefs(state)

watch(
  () => props.matches,
  (arr) => { state.localMatches = arr.map(m => normalizeMatch(m)) },
  { deep: true }
)

function normalizeMatch(m) {
  return {
    id: m.id,
    team1: m.team1,
    team2: m.team2,
    cups_team1: Number.isFinite(m.cups_team1) ? m.cups_team1 : 0,
    cups_team2: Number.isFinite(m.cups_team2) ? m.cups_team2 : 0,
    winner: m.winner || null
  }
}

function isLocked(m) {
  // Gesperrt, wenn Limit erreicht (Sieger gesetzt)
  return !!m.winner
}

function onCupClick(matchIndex, teamKey) {
  const list = state.localMatches.slice()
  const m = { ...list[matchIndex] }
  const maxCups = props.cupsPerGame || 6

  if (m.winner) return

  if (teamKey === 'team1') {
    m.cups_team1 = clamp((m.cups_team1 || 0) + 1, 0, maxCups)
    if (m.cups_team1 >= maxCups) m.winner = m.team1
  } else {
    m.cups_team2 = clamp((m.cups_team2 || 0) + 1, 0, maxCups)
    if (m.cups_team2 >= maxCups) m.winner = m.team2
  }

  list[matchIndex] = m
  state.localMatches = list
  emit('update:matches', list)

  // Persistieren (optimistic)
  if (m.id) {
    emit('persist', m)
  }
}

function clamp(n, min, max) {
  return Math.max(min, Math.min(max, n))
}
</script>

<style scoped>
.match-entry {
  background: rgba(255, 255, 255, 0.05);
}

.btn-cup {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  border: 1px solid #6c757d;
  background: rgba(0,0,0,0.3);
  color: #fff;
  padding: 0.25rem 0.5rem;
  line-height: 1;
}
.btn-cup:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.cup-img {
  width: 16px;
  height: 16px;
  display: inline-block;
}

.cup-count {
  font-weight: 600;
  min-width: 1.25rem;
  text-align: center;
}
</style>
