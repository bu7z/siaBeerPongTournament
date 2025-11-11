<!-- src/App.vue -->
<template>
  <div class="app-wrapper bg-dark text-light min-vh-100">
    <!-- Header -->
    <header class="navbar navbar-dark bg-black shadow-sm px-3">
      <div class="d-flex align-items-center gap-3">
        <img src="/weiß.png" alt="Logo" class="logo-img" />
        <span class="fs-5 fw-semibold">Beer Pong Turnierverwaltung</span>
      </div>
    </header>

    <main class="container py-5">
      <!-- Landing -->
      <section v-if="step === 0" class="text-center">
        <h1 class="mb-3">Willkommen in der Turnierhalle</h1>
        <p class="text-secondary mb-4 mx-auto" style="max-width: 540px;">
          Erstelle in wenigen Schritten ein Beer-Pong-Turnier für euren Verein. 
          Wähle zuerst die Turnierform, lege Gruppen fest und trage die Teams ein. 
          Den Rest kann später das Backend übernehmen.
        </p>
        <button class="btn btn-primary btn-lg" @click="goToStep(1)">
          Turnier anlegen
        </button>
      </section>

      <!-- Schritt 1: Turnierform -->
      <section v-else-if="step === 1" class="mx-auto" style="max-width: 640px;">
        <h2 class="mb-3">Turnierform wählen</h2>
        <p class="text-secondary mb-4">Wie soll das Turnier starten?</p>

        <div class="row g-3">
          <div class="col-md-4">
            <button
              class="w-100 btn"
              :class="tournament.mode === 'groups' ? 'btn-primary' : 'btn-outline-light'"
              @click="setMode('groups')"
            >
              Gruppenphase
            </button>
          </div>
          <div class="col-md-4">
            <button
              class="w-100 btn"
              :class="tournament.mode === 'round16' ? 'btn-primary' : 'btn-outline-light'"
              @click="setMode('round16')"
            >
              Achtelfinale (16 Teams)
            </button>
          </div>
          <div class="col-md-4">
            <button
              class="w-100 btn"
              :class="tournament.mode === 'quarter' ? 'btn-primary' : 'btn-outline-light'"
              @click="setMode('quarter')"
            >
              Viertelfinale (8 Teams)
            </button>
          </div>
        </div>

        <!-- Gruppenoption nur bei Gruppenphase -->
        <div v-if="tournament.mode === 'groups'" class="mt-4">
          <label class="form-label">Anzahl Gruppen</label>
          <input
            type="number"
            class="form-control bg-dark text-light border-secondary"
            min="1"
            max="8"
            v-model.number="tournament.groupCount"
          />
          <small class="text-secondary">
            Diese Zahl wird später zum Aufteilen der Teams verwendet.
          </small>
        </div>

        <div class="d-flex justify-content-between mt-5">
          <button class="btn btn-outline-light" @click="goToStep(0)">Zurück</button>
          <button class="btn btn-primary" @click="goToStep(2)">Weiter</button>
        </div>
      </section>

      <!-- Schritt 2: Teams eingeben -->
      <section v-else-if="step === 2" class="mx-auto" style="max-width: 640px;">
        <h2 class="mb-3">Teams eingeben</h2>
        <p class="text-secondary mb-3">
          {{ teamHint }}
        </p>

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
            v-for="(t, idx) in teams"
            :key="idx"
            class="list-group-item bg-dark text-light d-flex justify-content-between align-items-center border-secondary"
          >
            {{ idx + 1 }}. {{ t }}
            <button class="btn btn-sm btn-outline-danger" @click="removeTeam(idx)">x</button>
          </li>
        </ul>

        <div
          class="alert"
          :class="canContinue ? 'alert-success' : 'alert-warning'"
        >
          {{ validationMessage }}
        </div>

        <div class="d-flex justify-content-between mt-4">
          <button class="btn btn-outline-light" @click="goToStep(1)">Zurück</button>
          <button class="btn btn-primary" :disabled="!canContinue" @click="goToStep(3)">
            Weiter
          </button>
        </div>
      </section>

      <!-- Schritt 3: Übersicht -->
      <section v-else-if="step === 3" class="mx-auto" style="max-width: 640px;">
        <h2 class="mb-3">Übersicht</h2>
        <p class="text-secondary mb-3">
          So würde das Turnier jetzt angelegt werden:
        </p>

        <div class="card bg-black border-secondary mb-3 text-light">
          <div class="card-body">
            <p class="mb-1"><strong>Modus:</strong> {{ readableMode }}</p>
            <p v-if="tournament.mode === 'groups'" class="mb-1">
              <strong>Gruppen:</strong> {{ tournament.groupCount }}
            </p>
            <p class="mb-1"><strong>Teams:</strong> {{ teams.length }}</p>
          </div>
        </div>


        <p class="text-secondary mb-4">
          Hier würdest du dann später an das Flask-Backend schicken (POST /tournaments …).
        </p>

        <div class="d-flex justify-content-between">
          <button class="btn btn-outline-light" @click="goToStep(2)">Zurück</button>
          <button class="btn btn-success" @click="finish">Fertig</button>
        </div>
      </section>
    </main>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const step = ref(0)
const teams = ref([])
const teamInput = ref('')

const tournament = ref({
  mode: 'groups',    // 'groups' | 'round16' | 'quarter'
  groupCount: 4
})

function goToStep(n) {
  step.value = n
}

function setMode(m) {
  tournament.value.mode = m
  // sinnvolle defaults
  if (m === 'groups' && !tournament.value.groupCount) {
    tournament.value.groupCount = 4
  }
}

function addTeam() {
  if (!teamInput.value.trim()) return
  teams.value.push(teamInput.value.trim())
  teamInput.value = ''
}

function removeTeam(idx) {
  teams.value.splice(idx, 1)
}

const requiredTeams = computed(() => {
  if (tournament.value.mode === 'round16') return 16
  if (tournament.value.mode === 'quarter') return 8
  // bei Gruppenphase erstmal keine harte Grenze
  return null
})

const canContinue = computed(() => {
  if (requiredTeams.value) {
    return teams.value.length >= requiredTeams.value
  }
  // bei Gruppenphase: mindestens so viele Teams wie Gruppen
  return teams.value.length >= tournament.value.groupCount
})

const validationMessage = computed(() => {
  if (tournament.value.mode === 'round16') {
    return canContinue.value
      ? 'Genug Teams für ein Achtelfinale.'
      : `Es werden 16 Teams benötigt. Aktuell: ${teams.value.length}.`
  }
  if (tournament.value.mode === 'quarter') {
    return canContinue.value
      ? 'Genug Teams für ein Viertelfinale.'
      : `Es werden 8 Teams benötigt. Aktuell: ${teams.value.length}.`
  }
  // groups
  return canContinue.value
    ? `Gruppenphase ist anlegbar.`
    : `Mindestens ${tournament.value.groupCount} Teams nötig für ${tournament.value.groupCount} Gruppen.`
})

const teamHint = computed(() => {
  if (tournament.value.mode === 'round16') return 'Für ein Achtelfinale brauchst du 16 Teams.'
  if (tournament.value.mode === 'quarter') return 'Für ein Viertelfinale brauchst du 8 Teams.'
  return `Gib alle Teams ein, wir teilen später auf ${tournament.value.groupCount} Gruppen auf.`
})

const readableMode = computed(() => {
  if (tournament.value.mode === 'round16') return 'Achtelfinale'
  if (tournament.value.mode === 'quarter') return 'Viertelfinale'
  return 'Gruppenphase'
})

function finish() {
  // hier später: POST ans Backend
  // vorerst zurück zur Landing
  teams.value = []
  tournament.value = { mode: 'groups', groupCount: 4 }
  step.value = 0
}
</script>

<style scoped>
.logo-img {
  height: 42px;
  width: 42px;
  object-fit: contain;
  background: #121212;
  border-radius: 0.5rem;
  padding: 4px;
}
.app-wrapper {
  background: radial-gradient(circle at top, #1f1f1f 0%, #0d0d0d 55%, #000 100%);
}
</style>
