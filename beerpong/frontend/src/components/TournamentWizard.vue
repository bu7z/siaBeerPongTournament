<template>
  <!-- Landing -->
  <section v-if="localStep === 0" class="text-center py-5">
    <div class="mb-4">
      <h1 class="display-4 fw-bold mb-3">Turnierhalle</h1>
      <p class="text-secondary fs-5 mb-4 mx-auto" style="max-width: 600px;">
        Erstelle in wenigen Schritten ein Beer-Pong-Turnier für euren Verein.
        Das System berechnet automatisch die optimale Gruppenaufteilung.
      </p>
    </div>
    <button class="btn btn-primary btn-lg px-5 py-3" @click="setStep(1)">
      Turnier erstellen
    </button>
  </section>

  <!-- Schritt 1: Turnierdetails -->
  <section v-else-if="localStep === 1" class="mx-auto" style="max-width: 900px;">
    <div class="mb-4">
      <h2 class="fw-bold mb-2">Turnierdetails</h2>
      <p class="text-secondary">Grundlegende Turnierdaten (max. 128 Teams)</p>
    </div>

    <div class="row g-4 mb-4">
      <!-- Teilnehmeranzahl -->
      <div class="col-md-6">
        <label class="form-label fw-semibold">Anzahl Teilnehmer</label>
        <input
          type="number"
          class="form-control form-control-lg bg-dark text-light border-secondary"
          min="2"
          max="128"
          v-model.number="localTournament.participantCount"
          placeholder="z.B. 16"
        />
        <small class="text-light d-block mt-2">
          Automatische Berechnung der optimalen Gruppenaufteilung
        </small>
      </div>

      <!-- Becher pro Spiel -->
      <div class="col-md-6">
        <label class="form-label fw-semibold">Becher pro Spiel</label>
        <select
          class="form-select form-select-lg bg-dark text-light border-secondary"
          v-model="localTournament.cupsPerGame"
        >
          <option value="6">6 Becher (Short Game)</option>
          <option value="10">10 Becher (Standard)</option>
          <option value="custom">Benutzerdefiniert</option>
        </select>
        <input
          v-if="localTournament.cupsPerGame === 'custom'"
          type="number"
          class="form-control bg-dark text-light border-secondary mt-2"
          min="1"
          max="20"
          v-model.number="localTournament.customCups"
          placeholder="Anzahl Becher"
        />
      </div>
    </div>

    <!-- Finale mit 10 Bechern Option -->
    <div class="card bg-dark border-secondary mb-4">
      <div class="card-body">
        <div class="form-check">
          <input
            class="form-check-input"
            type="checkbox"
            v-model="localTournament.finaleWith10Cups"
            id="finale10Cups"
          >
          <label class="form-check-label fw-semibold" for="finale10Cups">
            Finale mit 10 Bechern spielen
          </label>
        </div>
        <small class="text-muted d-block mt-2">
          Das Finale wird unabhängig von der Gruppenphase immer mit 10 Bechern gespielt
        </small>
      </div>
    </div>

    <!-- Turnierstruktur Vorschau -->
    <div v-if="localTournament.participantCount >= 2 && tournamentPlan" class="mb-4">
      <div class="card bg-dark border-secondary shadow-sm">
        <div class="card-header bg-dark border-bottom border-secondary py-3">
          <h5 class="mb-0 fw-bold text-white">Turnierstruktur für {{ localTournament.participantCount }} Teams</h5>
        </div>
        <div class="card-body p-4">
          
          <!-- Gruppenphase -->
          <div class="mb-4">
            <div class="d-flex align-items-center mb-3">
              <span class="badge bg-secondary text-white me-2 px-3 py-2">Gruppenphase</span>
              <span class="text-white">{{ tournamentPlan.groups.length }} Gruppen</span>
            </div>
            
            <div class="row g-2 mb-3">
              <div v-for="group in tournamentPlan.groups" :key="group.name" class="col-6 col-md-4 col-lg-3">
                <div class="card bg-dark border-secondary h-100">
                  <div class="card-body py-2 px-3 text-center">
                    <div class="fw-bold text-white">{{ group.name }}</div>
                    <small class="text-muted">{{ group.size }} Teams</small>
                  </div>
                </div>
              </div>
            </div>

            <div class="alert bg-dark border-secondary mb-0">
              <small>
                <strong class="text-white">Weiterkommen:</strong>
                <span class="text-muted">Die ersten 2 Teams jeder Gruppe</span>
              </small>
            </div>
          </div>

          <!-- KO-Phase -->
          <div class="mb-4 pt-3 border-top border-secondary">
            <div class="d-flex align-items-center mb-3">
              <span class="badge bg-secondary text-white me-2 px-3 py-2">KO-Phase</span>
              <span class="text-white">{{ getKoPhaseName(tournamentPlan.ko_size) }}</span>
            </div>
            
            <div class="card bg-dark border-secondary">
              <div class="card-body py-2 px-3">
                <div class="d-flex justify-content-between align-items-center">
                  <span class="text-muted">{{ tournamentPlan.ko_size }} Teams</span>
                  <span class="text-white">
                    <span v-if="tournamentPlan.ko_size === 4">Halbfinale → Finale</span>
                    <span v-else-if="tournamentPlan.ko_size === 6">Viertelfinale → Halbfinale → Finale</span>
                    <span v-else-if="tournamentPlan.ko_size === 8">Viertelfinale → Halbfinale → Finale</span>
                    <span v-else-if="tournamentPlan.ko_size === 12">Achtelfinale → Viertelfinale → Halbfinale → Finale</span>
                    <span v-else-if="tournamentPlan.ko_size === 16">Achtelfinale → Viertelfinale → Halbfinale → Finale</span>
                    <span v-else>Mehrere KO-Runden bis zum Finale</span>
                  </span>
                </div>
              </div>
            </div>
          </div>

          <!-- Play-In Phase -->
          <div v-if="tournamentPlan.playin_needed" class="pt-3 border-top border-secondary">
            <div class="d-flex align-items-center mb-3">
              <span class="badge bg-secondary text-white me-2 px-3 py-2">Play-In Phase</span>
              <span class="text-white">{{ tournamentPlan.playin_slots_needed }} zusätzliche Plätze</span>
            </div>

            <div class="mb-3">
              <div class="text-muted mb-2 small">Kandidaten:</div>
              <div class="d-flex flex-wrap gap-1">
                <span v-for="(candidate, index) in tournamentPlan.playin_candidates"
                      :key="index"
                      class="badge bg-secondary text-white">
                  {{ candidate.label }}
                </span>
              </div>
            </div>

            <div v-if="tournamentPlan.playin_matches && tournamentPlan.playin_matches.length > 0" class="mb-3">
              <div class="text-muted mb-2 small">Matches:</div>
              <div class="d-flex flex-column gap-2">
                <div v-for="match in tournamentPlan.playin_matches"
                     :key="match.match_id"
                     class="card bg-dark border-secondary">
                  <div class="card-body py-2 px-3">
                    <small class="text-white">
                      <strong>Match {{ match.match_id }}:</strong>
                      {{ match.team1 }} vs {{ match.team2 }}
                    </small>
                  </div>
                </div>
              </div>
            </div>

            <div v-if="tournamentPlan.direct_qualified && tournamentPlan.direct_qualified.length > 0">
              <div class="text-muted mb-2 small">Direkt qualifiziert:</div>
              <div class="d-flex flex-wrap gap-1">
                <span v-for="(team, index) in tournamentPlan.direct_qualified"
                      :key="index"
                      class="badge bg-secondary text-white">
                  {{ team.team || team.label }}
                </span>
              </div>
            </div>
          </div>

          <!-- Kein Play-In -->
          <div v-else class="pt-3 border-top border-secondary">
            <div class="alert bg-dark border-secondary mb-0">
              <small class="text-white">
                <strong>Play-In Phase:</strong>
                <span class="text-muted">Nicht benötigt – Alle Teams sind direkt qualifiziert</span>
              </small>
            </div>
          </div>

          <!-- Zusammenfassung -->
          <div class="pt-4 mt-4 border-top border-secondary">
            <div class="row g-3 text-center">
              <div class="col-6">
                <div class="card bg-dark border-secondary h-100">
                  <div class="card-body py-3">
                    <div class="display-6 fw-bold text-white mb-1">{{ tournamentPlan.groups.length }}</div>
                    <small class="text-muted">Gruppen</small>
                  </div>
                </div>
              </div>
              <div class="col-6">
                <div class="card bg-dark border-secondary h-100">
                  <div class="card-body py-3">
                    <div class="display-6 fw-bold text-white mb-1">{{ tournamentPlan.ko_size }}</div>
                    <small class="text-muted">KO-Phase</small>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Ladeanzeige -->
    <div v-else-if="localTournament.participantCount >= 2" class="card bg-dark border-secondary mb-4">
      <div class="card-body text-center py-4">
        <div class="spinner-border spinner-border-sm text-primary me-2"></div>
        <span class="text-muted">Berechne optimale Turnierstruktur...</span>
      </div>
    </div>

    <div class="d-flex justify-content-between mt-5">
      <button class="btn btn-outline-secondary px-4" @click="setStep(0)">Zurück</button>
      <button class="btn btn-primary px-5" @click="setStep(2)">Weiter</button>
    </div>
  </section>

  <!-- Schritt 2: Teams eingeben -->
  <section v-else-if="localStep === 2" class="mx-auto" style="max-width: 700px;">
    <div class="mb-4">
      <h2 class="fw-bold mb-2">Teams eingeben</h2>
      <p class="text-secondary">
        Gib die Teamnamen ein. Es werden <strong>{{ localTournament.participantCount }} Teams</strong> erwartet.
      </p>
    </div>

    <form class="card bg-dark border-secondary mb-4" @submit.prevent="addTeam">
      <div class="card-body">
        <div class="input-group input-group-lg">
          <input
            v-model="teamInput"
            type="text"
            class="form-control bg-dark text-light border-secondary"
            :class="{ 'border-warning': isTeamInputDisabled }"
            placeholder="Teamname eingeben..."
            :disabled="isTeamInputDisabled"
          />
          <button 
            class="btn px-4" 
            :class="addButtonClass"
            type="submit"
            :disabled="isTeamInputDisabled"
          >
            {{ addButtonText }}
          </button>
        </div>
        <small v-if="isTeamInputDisabled" class="text-warning mt-2 d-block">
          Maximale Team-Anzahl erreicht. Bitte entferne Teams um weitere hinzuzufügen.
        </small>
      </div>
    </form>

    <div class="card bg-dark border-secondary mb-4">
      <div class="card-header bg-dark border-bottom border-secondary d-flex justify-content-between align-items-center">
        <span class="fw-semibold text-white">Teams ({{ localTeams.length }}/{{ localTournament.participantCount }})</span>
        <span class="badge" :class="statusBadgeClass">{{ localTeams.length }} hinzugefügt</span>
      </div>
      
      <!-- Fortschrittsbalken -->
      <div class="card-body py-2 border-bottom border-secondary">
        <div class="progress" style="height: 8px;">
          <div 
            class="progress-bar" 
            :class="progressBarClass"
            :style="{ width: progressPercentage + '%' }"
            role="progressbar"
            :aria-valuenow="progressPercentage"
            aria-valuemin="0"
            aria-valuemax="100"
          ></div>
        </div>
      </div>

      <ul class="list-group list-group-flush">
        <li
          v-for="(t, idx) in localTeams"
          :key="idx"
          class="list-group-item bg-dark text-light border-secondary d-flex justify-content-between align-items-center"
        >
          <span><strong>{{ idx + 1 }}.</strong> {{ t }}</span>
          <button class="btn btn-sm btn-outline-danger" @click="removeTeam(idx)">Entfernen</button>
        </li>
        
        <!-- Platzhalter für fehlende Teams -->
        <li 
          v-for="n in emptySlotsCount" 
          :key="'empty-' + n"
          class="list-group-item bg-dark text-muted border-secondary d-flex justify-content-between align-items-center"
          style="opacity: 0.6;"
        >
          <span><strong>{{ localTeams.length + n }}.</strong> <em>Platz für Team {{ localTeams.length + n }}</em></span>
          <span class="badge bg-secondary">Noch frei</span>
        </li>
        
        <li v-if="localTeams.length === 0" class="list-group-item bg-dark text-muted text-center border-secondary py-4">
          Noch keine Teams hinzugefügt
        </li>
      </ul>
    </div>

    <div class="alert mb-4" :class="statusAlertClass">
      <div class="d-flex justify-content-between align-items-center">
        <span>{{ validationMessage }}</span>
        <span class="badge" :class="statusBadgeClass">
          {{ localTeams.length }}/{{ localTournament.participantCount }}
        </span>
      </div>
    </div>

    <div class="d-flex justify-content-between">
      <button class="btn btn-outline-secondary px-4" @click="setStep(1)">Zurück</button>
      <button class="btn btn-primary px-5" :disabled="!canContinue" @click="setStep(3)">
        {{ canContinue ? 'Weiter zur Übersicht' : 'Teams vervollständigen' }}
      </button>
    </div>
  </section>

  <!-- Schritt 3: Übersicht -->
  <section v-else-if="localStep === 3" class="mx-auto" style="max-width: 800px;">
    <div class="mb-4">
      <h2 class="fw-bold mb-2">Übersicht</h2>
      <p class="text-secondary">Überprüfe die Turniereinstellungen vor der Erstellung</p>
    </div>

    <div class="card bg-dark border-secondary mb-4 shadow-sm">
      <div class="card-header bg-dark border-bottom border-secondary">
        <h5 class="mb-0 fw-bold text-white">Turniereinstellungen</h5>
      </div>
      <div class="card-body">
        <div class="row g-3">
          <div class="col-md-6">
            <div class="d-flex justify-content-between">
              <span class="text-muted">Teilnehmer:</span>
              <strong class="text-white">{{ localTournament.participantCount }}</strong>
            </div>
          </div>
          <div class="col-md-6">
            <div class="d-flex justify-content-between">
              <span class="text-muted">Becher pro Spiel:</span>
              <strong class="text-white">{{ actualCupsPerGame }}</strong>
            </div>
          </div>
          <div class="col-md-6" v-if="localTournament.finaleWith10Cups">
            <div class="d-flex justify-content-between">
              <span class="text-muted">Finale:</span>
              <strong class="text-warning">10 Becher</strong>
            </div>
          </div>
          <div class="col-md-6">
            <div class="d-flex justify-content-between">
              <span class="text-muted">Gruppen:</span>
              <strong class="text-white">{{ calculatedGroupCount }}</strong>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Turnierstruktur -->
    <div v-if="tournamentPlan" class="card bg-dark border-secondary mb-4 shadow-sm">
      <div class="card-header bg-dark border-bottom border-secondary">
        <h5 class="mb-0 fw-bold text-white">Turnierstruktur</h5>
      </div>
      <div class="card-body">
        <div class="row g-3">
          <div class="col-6">
            <div class="text-muted small">Gruppenphase</div>
            <div class="fw-bold text-white">{{ tournamentPlan.groups.length }} Gruppen</div>
          </div>
          <div class="col-6">
            <div class="text-muted small">KO-Phase</div>
            <div class="fw-bold text-white">{{ getKoPhaseName(tournamentPlan.ko_size) }}</div>
          </div>
          <div class="col-12">
            <div class="text-muted small">Play-In</div>
            <div class="fw-bold text-white">
              <span v-if="tournamentPlan.playin_needed">{{ tournamentPlan.playin_slots_needed }} Plätze</span>
              <span v-else>Nicht benötigt</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Gruppenaufteilung -->
    <div class="card bg-dark border-secondary mb-4 shadow-sm">
      <div class="card-header bg-dark border-bottom border-secondary">
        <h5 class="mb-0 fw-bold text-white">Gruppenaufteilung</h5>
      </div>
      <div class="card-body">
        <div class="row g-3">
          <div v-for="group in previewGroups" :key="group.name" class="col-12">
            <div class="card bg-dark border-secondary">
              <div class="card-body py-2">
                <div class="fw-bold text-white mb-1">{{ group.name }}</div>
                <div class="text-muted small">{{ group.teams.join(', ') }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="d-flex justify-content-between">
      <button class="btn btn-outline-secondary px-4" @click="setStep(2)">Zurück</button>
      <button class="btn btn-success px-5" @click="emitFinish">Turnier erstellen</button>
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
const localTournament = ref({
  mode: 'groups',
  participantCount: 8,
  cupsPerGame: '6',
  finaleWith10Cups: false,
  customCups: 6,
  ...props.tournament
})
const localTeams = ref([...(props.teams || [])])
const teamInput = ref('')
const tournamentPlan = ref(null)

// Berechnete Properties für die Team-Eingabe
const isTeamInputDisabled = computed(() => {
  return localTeams.value.length >= localTournament.value.participantCount
})

const addButtonClass = computed(() => {
  return isTeamInputDisabled.value ? 'btn-warning' : 'btn-primary'
})

const addButtonText = computed(() => {
  return isTeamInputDisabled.value ? 'Maximal erreicht' : 'Hinzufügen'
})

const emptySlotsCount = computed(() => {
  return Math.max(0, localTournament.value.participantCount - localTeams.value.length)
})

const canContinue = computed(() => {
  return localTeams.value.length >= localTournament.value.participantCount
})

const validationMessage = computed(() => {
  const current = localTeams.value.length
  const max = localTournament.value.participantCount
  
  if (current === 0) {
    return 'Bitte füge Teams hinzu um fortzufahren.'
  } else if (current < max) {
    return `Noch ${max - current} Team${max - current > 1 ? 's' : ''} benötigt.`
  } else if (current === max) {
    return 'Perfekt! Alle Teams wurden hinzugefügt.'
  } else {
    return 'Zu viele Teams - bitte entferne welche.'
  }
})

const statusAlertClass = computed(() => {
  const current = localTeams.value.length
  const max = localTournament.value.participantCount
  
  if (current === 0) return 'alert-warning bg-dark border-warning'
  if (current < max) return 'alert-info bg-dark border-info'
  if (current === max) return 'alert-success bg-dark border-success'
  return 'alert-danger bg-dark border-danger'
})

const statusBadgeClass = computed(() => {
  const current = localTeams.value.length
  const max = localTournament.value.participantCount
  
  if (current === 0) return 'bg-warning text-dark'
  if (current < max) return 'bg-info'
  if (current === max) return 'bg-success'
  return 'bg-danger'
})

const progressPercentage = computed(() => {
  return (localTeams.value.length / localTournament.value.participantCount) * 100
})

const progressBarClass = computed(() => {
  const percentage = progressPercentage.value
  if (percentage < 50) return 'bg-warning'
  if (percentage < 100) return 'bg-info'
  return 'bg-success'
})

const actualCupsPerGame = computed(() => {
  if (localTournament.value.cupsPerGame === 'custom') {
    return localTournament.value.customCups || 6
  }
  return parseInt(localTournament.value.cupsPerGame)
})

watch(() => localTournament.value.participantCount, async (newCount) => {
  if (newCount >= 2 && newCount <= 128) {
    await computeTournamentPlan()
  } else {
    tournamentPlan.value = null
  }
}, { immediate: true })

async function computeTournamentPlan() {
  try {
    const response = await fetch('http://localhost:5000/compute-tournament-plan', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ participantCount: localTournament.value.participantCount })
    })
    if (response.ok) {
      const plan = await response.json()
      tournamentPlan.value = plan
    }
  } catch (error) {
    console.error('Fehler beim Laden des Turnierplans:', error)
    tournamentPlan.value = null
  }
}

function getKoPhaseName(koSize) {
  const names = {
    2: 'Finale',
    4: 'Halbfinale',
    6: 'Viertelfinale (6 Teams)',
    8: 'Viertelfinale',
    12: 'Achtelfinale (12 Teams)',
    16: 'Achtelfinale',
    24: 'Sechzehntelfinale (24 Teams)',
    32: 'Sechzehntelfinale',
    48: 'Zweiunddreißigstelfinale (48 Teams)',
    64: 'Zweiunddreißigstelfinale'
  }
  return names[koSize] || `${koSize}-Team KO-Phase`
}

const calculatedGroupCount = computed(() => {
  const count = localTournament.value.participantCount
  if (count <= 4) return 1
  if (count <= 8) return 2
  if (count <= 12) return 3
  if (count <= 16) return 4
  return Math.ceil(count / 4)
})

const previewGroups = computed(() => {
  const groups = []
  const groupCount = calculatedGroupCount.value
  const teamNames = localTeams.value.length >= localTournament.value.participantCount
    ? localTeams.value
    : Array.from({ length: localTournament.value.participantCount }, (_, i) => `Team ${i + 1}`)

  for (let i = 0; i < groupCount; i++) {
    const groupName = `Gruppe ${String.fromCharCode(65 + i)}`
    const teamsInGroup = []
    for (let j = i; j < teamNames.length; j += groupCount) {
      if (teamNames[j]) {
        teamsInGroup.push(teamNames[j])
      }
    }
    groups.push({ name: groupName, teams: teamsInGroup })
  }
  return groups
})

watch(
  () => props.step,
  (v) => (localStep.value = v)
)

function setStep(v) {
  localStep.value = v
  emit('update:step', v)
}

function addTeam() {
  // Verhindere Hinzufügen wenn Maximum erreicht
  if (isTeamInputDisabled.value) {
    return
  }
  
  if (!teamInput.value.trim()) return
  
  localTeams.value.push(teamInput.value.trim())
  teamInput.value = ''
  emit('update:teams', [...localTeams.value])
}

function removeTeam(idx) {
  localTeams.value.splice(idx, 1)
  emit('update:teams', [...localTeams.value])
}

function emitFinish() {
  const finalTournament = {
    ...localTournament.value,
    cupsPerGame: actualCupsPerGame.value,
    finaleWith10Cups: localTournament.value.finaleWith10Cups
  }
  emit('update:tournament', finalTournament)
  emit('update:teams', [...localTeams.value])
  emit('finish')
}
</script>

<style scoped>
/* ---------- Kontrast-Fixes für Dark-UI ---------- */

/* Helleres "muted"/"secondary" in dunklen Cards, Alerts, Headers */
.card.bg-dark :is(.text-muted, .text-secondary),
.alert.bg-dark :is(.text-muted, .text-secondary),
.card-header.bg-dark :is(.text-muted, .text-secondary) {
  color: rgba(255, 255, 255, 0.78) !important;
}

/* Standardtext innerhalb dunkler Cards klarer darstellen */
.card.bg-dark,
.card-header.bg-dark,
.alert.bg-dark {
  color: #f8f9fa; /* nahe text-light */
}

/* Placeholders gut lesbar auf Dark */
.form-control.bg-dark::placeholder,
.form-select.bg-dark::placeholder {
  color: rgba(255, 255, 255, 0.55);
  opacity: 1;
}

/* Inputs/Selects Text und Border auf Dark */
.form-control.bg-dark,
.form-select.bg-dark {
  color: #f8f9fa;
  border-color: #6c757d;
}
.form-control.bg-dark:focus,
.form-select.bg-dark:focus {
  border-color: #8a97a6;
  box-shadow: 0 0 0 0.2rem rgba(138, 151, 166, 0.25);
}

/* Badges */
.badge.bg-secondary { color: #fff !important; }

/* Spinner-Text in Ladekarte */
.card.bg-dark .spinner-border + span.text-muted {
  color: rgba(255, 255, 255, 0.78) !important;
}

/* ---------- Visuelle Feinheiten ---------- */
.card { transition: all 0.2s ease; }
.card:hover { box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3); }

.form-control:focus,
.form-select:focus { transition: box-shadow .2s ease, border-color .2s ease; }

.btn { transition: transform 0.2s ease; }
.btn:hover { transform: translateY(-1px); }

.badge { font-weight: 500; padding: 0.4em 0.8em; }

.list-group-item { transition: background-color 0.2s ease; }
.list-group-item:hover { background-color: #2a2e35 !important; }

/* Fortschrittsbalken Styling */
.progress {
  background-color: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
  overflow: hidden;
}

.progress-bar {
  transition: width 0.3s ease;
}

/* Platzhalter für Teams */
.list-group-item[style*="opacity: 0.6"]:hover {
  background-color: rgba(255, 255, 255, 0.05) !important;
}
</style>