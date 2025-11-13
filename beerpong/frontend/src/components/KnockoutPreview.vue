<template>
  <section class="mx-auto" style="max-width: 900px;">
    <div class="d-flex justify-content-between align-items-center mb-3">
      <h2>KO-Vorschau</h2>
      <button class="btn btn-outline-light" @click="$emit('cancel')">Zurück</button>
    </div>

    <div class="card bg-dark border-secondary mb-3">
      <div class="card-body">
        <div class="d-flex justify-content-between align-items-center">
          <div>
            <div class="small text-light">Teams in der KO-Phase</div>
            <div class="display-6 fw-bold text-white">{{ teams.length }}</div>
          </div>
          <div class="text-end">
            <div class="small text-light">Geplante Größe</div>
            <div class="h4 text-white">{{ koSize || inferredSize }}</div>
          </div>
        </div>
      </div>
    </div>

    <div class="card bg-dark border-secondary">
      <div class="card-header">Teilnehmer</div>
      <div class="card-body">
        <div class="d-flex flex-wrap gap-2">
          <span v-for="t in teams" :key="t" class="badge bg-secondary">{{ t }}</span>
        </div>
      </div>
    </div>

    <div class="d-flex justify-content-between mt-4">
      <button class="btn btn-outline-light" @click="$emit('cancel')">Zurück</button>
      <button class="btn btn-success" @click="confirm">KO-Phase starten</button>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'

const POW2 = [4,8,16,32,64,128]

const props = defineProps({
  teams: { type: Array, default: () => [] },
  koSize: { type: Number, default: null }
})
const emit = defineEmits(['confirm','cancel'])

const inferredSize = computed(() => {
  const n = props.teams.length
  for (const k of POW2) if (k >= n) return k
  return n
})

function confirm() {
  emit('confirm', { teams: props.teams.slice(), koSize: props.koSize || inferredSize.value })
}
</script>

<style scoped>
.badge { font-weight: 500; }
</style>
