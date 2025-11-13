<template>
  <div>
    <div v-for="(m, idx) in matches" :key="idx" class="match-entry d-flex align-items-center justify-content-between py-2 border-bottom border-secondary">
      <span class="flex-fill text-light">{{ m.team1 ?? '—' }}</span>

      <div class="d-flex align-items-center gap-2">
        <input type="number" min="0" :max="cupsPerGame" class="form-control form-control-sm text-center" style="width: 70px;"
          v-model.number="m.cups_team1" @change="updateMatch(m)" />
        <span class="text-secondary">:</span>
        <input type="number" min="0" :max="cupsPerGame" class="form-control form-control-sm text-center" style="width: 70px;"
          v-model.number="m.cups_team2" @change="updateMatch(m)" />
      </div>

      <span class="flex-fill text-end text-light">{{ m.team2 ?? '—' }}</span>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  group: Object,
  matches: Array,
  tournamentId: Number,
  cupsPerGame: Number,
  finaleWith10: Boolean
})
const emit = defineEmits(['match-updated'])

function updateMatch(m) {
  const target = props.cupsPerGame || 6
  const a = Number(m.cups_team1 || 0)
  const b = Number(m.cups_team2 || 0)
  if (a >= target || b >= target) {
    if (a !== b) m.winner = a > b ? m.team1 : m.team2
  } else {
    m.winner = null
  }
  emit('match-updated', m)
}
</script>

<style scoped>
.match-entry input {
  background: rgba(0,0,0,0.3);
  border: 1px solid #666;
  color: #fff;
}
</style>
