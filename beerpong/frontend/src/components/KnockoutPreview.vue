<template>
  <section class="mx-auto" style="max-width: 700px;">
    <h2 class="mb-3">KO-Vorbereitung</h2>
    <p class="text-secondary mb-4">
      So würden die Teams in die KO-Runde übernommen werden. Fehlende Plätze wurden mit „Freilos“ ergänzt.
    </p>
    <div class="card bg-dark border-secondary mb-4">
      <div class="list-group list-group-flush">
        <div
          v-for="(name, idx) in localTeams"
          :key="idx"
          class="list-group-item bg-dark text-light border-secondary d-flex align-items-center gap-3"
        >
          <span class="badge bg-secondary">{{ idx + 1 }}</span>
          <input
            v-model="localTeams[idx]"
            type="text"
            class="form-control form-control-sm bg-dark text-light border-secondary"
          />
        </div>
      </div>
    </div>
    <div class="d-flex justify-content-between">
      <button class="btn btn-outline-light" @click="cancel">Zurück</button>
      <button class="btn btn-primary" @click="confirm">KO-Runde starten</button>
    </div>
  </section>
</template>
<script setup>
import { ref, watch } from 'vue'
const props = defineProps({
  teams: { type: Array, required: true },
  cameFromPlayIn: { type: Boolean, default: false }
})
const emit = defineEmits(['cancel', 'confirm'])
const localTeams = ref([])
function nextPowerOfTwo(n) {
  const bases = [2, 4, 8, 16]
  for (const b of bases) {
    if (n <= b) return b
  }
  return n
}
function prepare(list) {
  const cleaned = list.map(t => t?.toString().trim()).filter(Boolean)
  const target = nextPowerOfTwo(cleaned.length || 1)
  while (cleaned.length < target) {
    cleaned.push('Freilos')
  }
  localTeams.value = cleaned
}
watch(
  () => props.teams,
  (v) => prepare(v),
  { immediate: true }
)
function confirm() {
  const cleaned = localTeams.value.map(t => t.trim()).filter(Boolean)
  emit('confirm', cleaned)
}
function cancel() {
  emit('cancel', props.cameFromPlayIn)
}
</script>