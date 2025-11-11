<template>
  <!-- Landing -->
  <section v-if="localStep === 0" class="text-center">
    <h1 class="mb-3">Willkommen in der Turnierhalle 🏟️</h1>
    <p class="text-secondary mb-4 mx-auto" style="max-width: 540px;">
      Erstelle in wenigen Schritten ein Beer-Pong-Turnier für euren Verein.
      Wähle zuerst die Turnierform, lege Gruppen fest und trage die Teams ein.
    </p>
    <button class="btn btn-primary btn-lg" @click="setStep(1)">Turnier anlegen</button>
  </section>

  <!-- Schritt 1 -->
  <section v-else-if="localStep === 1" class="mx-auto" style="max-width: 640px;">
    <h2 class="mb-3">Turnierform wählen</h2>
    <p class="text-secondary mb-4">Wie soll das Turnier starten?</p>

    <div class="row g-3">
      <div class="col-md-4">
        <button
          class="w-100 btn"
          :class="localTournament.mode === 'groups' ? 'btn-primary' : 'btn-outline-light'"
          @click="setMode('groups')"
        >
          Gruppenphase
        </button>
      </div>
      <div class="col-md-4">
        <button
          class="w-100 btn"
          :class="localTournament.mode === 'round16' ? 'btn-primary' : 'btn-outline-light'"
          @click="setMode('round16')"
        >
          Achtelfinale
        </button>
      </div>
      <div class="col-md-4">
        <button
          class="w-100 btn"
          :class="localTournament.mode === 'quarter' ? 'btn-primary' : 'btn-outline-light'"
          @click="setMode('quarter')"
        >
          Viertelfinale
        </button>
      </div>
    </div>

    <div v-if="localTournament.mode === 'groups'" class="mt-4">
      <label class="form-label">Anzahl Gruppen</label>
      <input
        type="number"
        class="form-control bg-dark text-light border-secondary"
        min="1"
        max="8"
        v-model.number="localTournament.groupCount"
      />
      <small class="text-secondary">Diese Zahl wird später zum Aufteilen der Teams verwendet.</small>
    </div>

    <div class="d-flex justify-content-between mt-5">
      <button class="btn btn-outline-light" @click="setStep(0)">Zurück</button>
      <button class="btn btn-primary" @click="setStep(2)">Weiter</button>
    </div>
  </section>

  <!-- Schritt 2 -->
  <section v-else-if="localStep === 2" class="mx-auto" style="max-width: 640px;">
    <h2 class="mb-3">Teams eingeben</h2>
    <p class="text-secondary mb-3">{{ teamHint }}</p>

    <form class="d-flex gap-2 mb-3" @submit.prevent="addTeam">
      <input
        v-model="teamInput"
        type="text"
        class="form-control bg-dark text-light border-secondary"
        placeholder="Teamname"
      />
      <button class="btn btn-primary" type="submit">Hinzufügen</button>
    </form>

    <ul class="list-group list-group-flush mb-3 bg-dark">
      <li
        v-for="(t, idx) in localTeams"
        :key="idx"
        class="list-group-item bg-dark text-light d-flex justify-content-between align-items-center border-secondary"
      >
        {{ idx + 1 }}. {{ t }}
        <button class="btn btn-sm btn-outline-danger" @click="removeTeam(idx)">x</button>
      </li>
    </ul>

    <div class="alert" :class="canContinue ? 'alert-success' : 'alert-warning'">
      {{ validationMessage }}
    </div>

    <div class="d-flex justify-content-between mt-4">
      <button class="btn btn-outline-light" @click="setStep(1)">Zurück</button>
      <button class="btn btn-primary" :disabled="!canContinue" @click="setStep(3)">Weiter</button>
    </div>
  </section>

  <!-- Schritt 3 -->
  <section v-else-if="localStep === 3" class="mx-auto" style="max-width: 640px;">
    <h2 class="mb-3">Übersicht</h2>
    <p class="text-secondary mb-3">So würde das Turnier jetzt angelegt werden:</p>

    <div class="card bg-dark border-secondary mb-3 text-light">
      <div class="card-body">
        <p class="mb-1"><strong>Modus:</strong> {{ readableMode }}</p>
        <p v-if="localTournament.mode === 'groups'" class="mb-1">
          <strong>Gruppen:</strong> {{ localTournament.groupCount }}
        </p>
        <p class="mb-1"><strong>Teams:</strong> {{ localTeams.length }}</p>
      </div>
    </div>

    <p class="text-secondary mb-4">
      Hier würdest du später an das Flask-Backend schicken.
    </p>

    <div class="d-flex justify-content-between">
      <button class="btn btn-outline-light" @click="setStep(2)">Zurück</button>
      <button class="btn btn-success" @click="emitFinish">Fertig</button>
    </div>
  </section>
</template>

<script setup>
import { computed, ref, watch } from 'vue'

const props = defineProps({
  step: Number,
  tournament: Object,
  teams: Array,
})
const emit = defineEmits(['update:step', 'update:tournament', 'update:teams', 'finish'])

const localStep = ref(props.step ?? 0)
const localTournament = ref({ ...props.tournament })
const localTeams = ref([...(props.teams || [])])
const teamInput = ref('')

watch(
  () => props.step,
  (v) => (localStep.value = v)
)

function setStep(v) {
  localStep.value = v
  emit('update:step', v)
}

function setMode(m) {
  localTournament.value.mode = m
  if (m === 'groups' && !localTournament.value.groupCount) {
    localTournament.value.groupCount = 4
  }
  emit('update:tournament', { ...localTournament.value })
}

function addTeam() {
  if (!teamInput.value.trim()) return
  localTeams.value.push(teamInput.value.trim())
  teamInput.value = ''
  emit('update:teams', [...localTeams.value])
}

function removeTeam(idx) {
  localTeams.value.splice(idx, 1)
  emit('update:teams', [...localTeams.value])
}

const requiredTeams = computed(() => {
  if (localTournament.value.mode === 'round16') return 16
  if (localTournament.value.mode === 'quarter') return 8
  return null
})

const canContinue = computed(() => {
  if (requiredTeams.value) return localTeams.value.length >= requiredTeams.value
  return localTeams.value.length >= localTournament.value.groupCount
})

const validationMessage = computed(() => {
  if (localTournament.value.mode === 'round16')
    return canContinue.value
      ? 'Genug Teams für ein Achtelfinale.'
      : `Es werden 16 Teams benötigt. Aktuell: ${localTeams.value.length}.`
  if (localTournament.value.mode === 'quarter')
    return canContinue.value
      ? 'Genug Teams für ein Viertelfinale.'
      : `Es werden 8 Teams benötigt. Aktuell: ${localTeams.value.length}.`
  return canContinue.value
    ? 'Gruppenphase ist anlegbar.'
    : `Mindestens ${localTournament.value.groupCount} Teams nötig.`
})

const teamHint = computed(() => {
  if (localTournament.value.mode === 'round16') return 'Für ein Achtelfinale brauchst du 16 Teams.'
  if (localTournament.value.mode === 'quarter') return 'Für ein Viertelfinale brauchst du 8 Teams.'
  return `Gib alle Teams ein, wir teilen später auf ${localTournament.value.groupCount} Gruppen auf.`
})

const readableMode = computed(() => {
  if (localTournament.value.mode === 'round16') return 'Achtelfinale'
  if (localTournament.value.mode === 'quarter') return 'Viertelfinale'
  return 'Gruppenphase'
})

function emitFinish() {
  // sync state raus
  emit('update:tournament', { ...localTournament.value })
  emit('update:teams', [...localTeams.value])
  emit('finish')
}
</script>
