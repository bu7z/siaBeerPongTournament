<template>
  <section class="mx-auto" style="max-width: 900px;">
    <div class="d-flex justify-content-between align-items-center mb-3">
      <h2>KO-Phase – Übersicht</h2>
      <button class="btn btn-outline-light" @click="$emit('back')">Zurück</button>
    </div>

    <div class="card bg-dark border-secondary mb-3">
      <div class="card-body">
        <div class="row g-3">
          <div class="col-md-6">
            <div class="text-muted small">Teilnehmer KO-Phase</div>
            <div class="display-6 fw-bold text-white">{{ teams.length }}</div>
          </div>
          <div class="col-md-6">
            <div class="text-muted small">Zielgröße</div>
            <div class="display-6 fw-bold text-white">{{ targetSize }}</div>
          </div>
        </div>
      </div>
    </div>

    <div class="card bg-dark border-secondary mb-3">
      <div class="card-header"><strong>Seeding (automatisch)</strong></div>
      <div class="card-body">
        <ol class="mb-0">
          <li v-for="(t,i) in seeded" :key="i" class="text-white">{{ t }}</li>
        </ol>
      </div>
    </div>

    <div class="d-flex justify-content-between">
      <button class="btn btn-outline-light" @click="$emit('back')">Zurück</button>
      <button class="btn btn-primary" :disabled="seeded.length !== targetSize" @click="proceed">
        Bracket erzeugen
      </button>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  teams: { type: Array, required: true },
  koSize: { type: Number, default: null } // optional
})
const emit = defineEmits(['back','create-bracket'])

const targetSize = computed(() => {
  if (props.koSize) return props.koSize
  // nächste 2er-Potenz >= teams.length
  let n = 1
  while (n < props.teams.length) n <<= 1
  return n
})

const seeded = computed(() => {
  // einfache deterministische Sortierung (Name) – kann später durch Elo/Ranking ersetzt werden
  return [...props.teams].sort((a,b)=>String(a).localeCompare(String(b))).slice(0, targetSize.value)
})

function proceed(){
  emit('create-bracket', { seeded: seeded.value, size: targetSize.value })
}
</script>
