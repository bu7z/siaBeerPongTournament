<template>
  <div class="app-wrapper bg-dark text-light min-vh-100">
    <HeaderBar
      :has-active="!!tournament?.id"
      :tournament-name="tournamentName"
      :tournament-phase="tournamentPhase"
      @create-new="handleCreateNew"
      @open-loader="toggleLoadPanel"
    />

    <main class="container py-5">
      <!-- Landing-Info nur auf Startseite (step 0, kein Load-Dialog) -->
      <InfoPanel v-if="step === 0 && !showLoad" class="mb-4" />

      <!-- Load Panel -->
      <div
        v-if="showLoad"
        class="card bg-black border-secondary text-light mb-4"
      >
        <div
          class="card-header bg-black border-secondary d-flex justify-content-between align-items-center"
        >
          <strong>Vorhandene Turniere</strong>
          <button
            class="btn btn-sm btn-outline-light"
            @click="fetchTournamentsList"
          >
            Neu laden
          </button>
        </div>

        <div class="card-body text-light">
          <div v-if="loadingList" class="text-secondary">Lade…</div>

          <div
            v-else-if="tournamentsList.length === 0"
            class="text-secondary"
          >
            Keine Turniere vorhanden.
          </div>

          <div v-else class="list-group">
            <div
              v-for="t in tournamentsList"
              :key="t.id"
              class="list-group-item bg-black text-light border-secondary d-flex justify-content-between align-items-center"
            >
              <div>
                <div class="fw-bold text-light">
                  {{ t.name }}
                  <small class="text-secondary">(#{{ t.id }})</small>
                </div>
                <div class="small text-secondary">
                  Teams: {{ t.participant_count ?? t.participantCount }} ·
                  Modus: {{ t.mode }} · Phase:
                  {{ t.current_phase ?? t.currentPhase ?? 'group' }}
                </div>
              </div>
              <div class="d-flex gap-2">
                <button
                  class="btn btn-sm btn-success"
                  @click="loadTournament(t.id)"
                >
                  Laden
                </button>
                <button
                  class="btn btn-sm btn-outline-danger"
                  @click="deleteTournament(t.id)"
                >
                  Löschen
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Wizard (inkl. Turniername-Popup in Schritt 0) -->
      <TournamentWizard
        v-if="step === 0 || step === 1 || step === 2 || step === 3"
        :step="step"
        :tournament="tournament"
        :teams="teams"
        @update:step="step = $event"
        @update:tournament="tournament = $event"
        @update:teams="teams = $event"
        @finish="handleFinish"
        @open-load-dialog="toggleLoadPanel"
      />

      <!-- Gruppenphase -->
      <GroupsView
        v-else-if="step === 4"
        :tournament-id="tournament?.id"
        :tournament="tournament"
        :teams="teams"
        @back="step = 0"
        @create-ko="handleCreateKoFromGroups"
      />

      <!-- KO-Vorschau -->
      <KnockoutPreview
        v-else-if="step === 6"
        :teams="koPreviewTeams"
        :ko-size="targetKoSize || null"
        @cancel="handlePreviewCancel"
        @confirm="handleKoPreviewConfirm"
      />

      <!-- Play-In -->
      <PlayInView
        v-else-if="step === 7"
        :tournament-id="tournament?.id"
        :auto-qualified="pendingQualified"
        :ko-size="targetKoSize || null"
        :candidates="playInCandidates"
        :matches="playInMatches"
        :rage-cage="rageCageGroups"
        :policy-notes="policyNotes"
        @back="step = 4"
        @to-ko="handlePlayInToKo"
        @create-ko="handlePlayInToKo"
      />

      <!-- KO-Phase -->
      <KnockoutView
        v-else-if="step === 5"
        :tournament-id="tournament?.id"
        :teams="koPreviewTeams"
        :ko-size="targetKoSize || null"
        @back="handleKoBack"
        @saved="handleKoSaved"
      />
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import HeaderBar from './components/HeaderBar.vue'
import InfoPanel from './components/InfoPanel.vue'
import TournamentWizard from './components/TournamentWizard.vue'
import GroupsView from './components/GroupsView/GroupsView.vue'
import KnockoutView from './components/KnockoutView.vue'
import PlayInView from './components/PlayInView.vue'
import KnockoutPreview from './components/KnockoutPreview.vue'

const API =
  `${window.location.protocol}//${window.location.hostname}:5000` ||
  import.meta.env.VITE_API_BASE

const step = ref(0)
const showLoad = ref(false)
const loadingList = ref(false)
const tournamentsList = ref([])

const tournament = ref({
  id: null,
  name: 'Neues Turnier',
  mode: 'groups',
  participantCount: 8,
  cupsPerGame: 6,
  finaleWith10Cups: false,
  current_phase: 'group'
})
const teams = ref([])

const tournamentName = computed(
  () => tournament.value?.name ?? ('#' + (tournament.value?.id ?? ''))
)
const tournamentPhase = computed(
  () =>
    tournament.value?.current_phase ??
    tournament.value?.currentPhase ??
    'group'
)

/** KO / Play-In State */
const koPreviewTeams = ref([])
const pendingQualified = ref([])
const cameFromPlayIn = ref(false)

const targetKoSize = ref(null)
const playInMatches = ref([])
const rageCageGroups = ref([])
const policyNotes = ref([])
const playInCandidates = ref([])

function pow2KoSize(qualified) {
  const sizes = [4, 8, 16, 32, 64, 128]
  for (const k of sizes) if (k >= qualified) return k
  return qualified
}
function pairTeamsToMatches(list) {
  const out = []
  for (let i = 0; i < list.length; i += 2) {
    const t1 = list[i]
    const t2 = list[i + 1]
    if (!t1 || !t2) break
    out.push({ team1: t1, team2: t2, winner: null })
  }
  return out
}

function handleCreateNew() {
  showLoad.value = false
  // WICHTIG: Schritt 0, damit TournamentWizard die Landing-Seite mit Name-Popup zeigt
  step.value = 0
}

function toggleLoadPanel() {
  showLoad.value = !showLoad.value
  if (showLoad.value) fetchTournamentsList()
}

async function fetchTournamentsList() {
  loadingList.value = true
  try {
    const res = await fetch(`${API}/tournaments`)
    const data = await res.json()
    tournamentsList.value = Array.isArray(data) ? data : data.items ?? []
  } catch {
    tournamentsList.value = []
  } finally {
    loadingList.value = false
  }
}

async function loadTournament(id) {
  try {
    const res = await fetch(`${API}/tournaments/${id}/load-all-data`)
    if (!res.ok) throw new Error('HTTP ' + res.status)
    const data = await res.json()

    const t = data.tournament ?? {}
    tournament.value = {
      id: t.id,
      name: t.name,
      mode: t.mode ?? 'groups',
      participantCount: t.participantCount ?? t.participant_count ?? 8,
      cupsPerGame: t.cupsPerGame ?? t.cups_per_game ?? 6,
      finaleWith10Cups: t.finaleWith10Cups ?? t.finale_with_10_cups ?? false,
      current_phase: t.currentPhase ?? t.current_phase ?? 'group'
    }

    teams.value = Array.isArray(data.teams) ? data.teams : []

    const phase = tournament.value.current_phase ?? 'group'
    if (phase === 'group') {
      step.value = 4
    } else if (phase === 'playin') {
      const pi = data.playin ?? {}
      pendingQualified.value =
        pi.direct_qualified_labels ?? pi.direct_qualified ?? []
      playInMatches.value = pi.playin_matches ?? []
      rageCageGroups.value = pi.rage_cage_groups ?? []
      policyNotes.value = pi.policy_notes ?? []
      targetKoSize.value = pi.ko_size ?? null
      playInCandidates.value = pi.ranking_candidates ?? []
      cameFromPlayIn.value = true
      step.value = 7
    } else if (phase === 'ko') {
      cameFromPlayIn.value = false
      targetKoSize.value = data.ko_phase?.ko_size ?? null
      koPreviewTeams.value = []
      step.value = 5
    } else {
      step.value = 4
    }

    showLoad.value = false
  } catch (e) {
    console.error('Turnier laden fehlgeschlagen:', e)
  }
}

async function deleteTournament(id) {
  try {
    const res = await fetch(`${API}/tournaments/${id}`, { method: 'DELETE' })
    if (res.ok) {
      tournamentsList.value = tournamentsList.value.filter(t => t.id !== id)
      if (tournament.value?.id === id) {
        step.value = 0
        tournament.value = {
          id: null,
          name: 'Neues Turnier',
          mode: 'groups',
          participantCount: 8,
          cupsPerGame: 6,
          finaleWith10Cups: false,
          current_phase: 'group'
        }
        teams.value = []
        koPreviewTeams.value = []
        pendingQualified.value = []
        playInMatches.value = []
        rageCageGroups.value = []
        policyNotes.value = []
        targetKoSize.value = null
        playInCandidates.value = []
      }
    }
  } catch (e) {
    console.error('Löschen fehlgeschlagen:', e)
  }
}

async function handleFinish(finalTournament) {
  try {
    const createBody = {
      name: finalTournament.name ?? 'Neues Turnier',
      mode: 'groups',
      participantCount: Number.isFinite(+finalTournament.participantCount)
        ? +finalTournament.participantCount
        : 8,
      cupsPerGame: Number.isFinite(+finalTournament.cupsPerGame)
        ? +finalTournament.cupsPerGame
        : 6,
      finaleWith10Cups: !!finalTournament.finaleWith10Cups
    }
    const createRes = await fetch(`${API}/tournaments/create`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(createBody)
    })
    if (!createRes.ok)
      throw new Error(`create failed: HTTP ${createRes.status}`)
    const created = await createRes.json()
    const tId = created.id
    if (!tId) throw new Error('create returned no id')

    const teamList = Array.isArray(finalTournament.teams)
      ? finalTournament.teams
      : []
    if (teamList.length) {
      await fetch(`${API}/tournaments/${tId}/save-teams`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ teams: teamList })
      }).catch(() => {})
    }

    tournament.value = {
      id: tId,
      name: created.name ?? createBody.name,
      mode: created.mode ?? 'groups',
      participantCount:
        created.participantCount ?? createBody.participantCount,
      cupsPerGame: created.cupsPerGame ?? createBody.cupsPerGame,
      finaleWith10Cups:
        created.finaleWith10Cups ?? createBody.finaleWith10Cups,
      current_phase: created.currentPhase ?? 'group'
    }
    teams.value = teamList.slice()
    step.value = 4

    if (!tournamentsList.value.some(t => t.id === tId)) {
      tournamentsList.value.unshift({
        id: tId,
        name: tournament.value.name,
        mode: tournament.value.mode,
        participant_count: tournament.value.participantCount,
        current_phase: tournament.value.current_phase
      })
    }
    fetchTournamentsList().catch(() => {})
  } catch (e) {
    console.error('handleFinish failed:', e)
  }
}

/** Ergebnis aus Gruppenphase → ggf. Play-In oder KO-Preview */
function handleCreateKoFromGroups({ tables, playIn, cupsTarget, koSize }) {
  const topTwos = Object.values(tables ?? {}).flatMap(rows =>
    rows.slice(0, 2).map(r => r.name)
  )
  const qualifiedBase = Array.from(new Set(topTwos))
  pendingQualified.value = [...qualifiedBase]

  targetKoSize.value = koSize ?? playIn?.ko_size ?? null
  playInCandidates.value = playIn?.ranking_candidates ?? []
  playInMatches.value = playIn?.playin_matches ?? []
  rageCageGroups.value = playIn?.rage_cage_groups ?? []
  policyNotes.value = playIn?.policy_notes ?? []

  const needPlayIn = !!playIn?.playin_needed
  if (!needPlayIn) {
    const autoAdd = playIn?.auto_advanced ?? []
    koPreviewTeams.value = [...pendingQualified.value, ...autoAdd]
    step.value = 6
    return
  }

  if (
    playInMatches.value.length > 0 ||
    rageCageGroups.value.length > 0 ||
    (playInCandidates.value?.length || 0) > 0
  ) {
    step.value = 7
  } else {
    koPreviewTeams.value = pendingQualified.value.slice()
    step.value = 6
  }
}

function handlePlayInToKo(payload) {
  const finalList = payload?.qualified ?? []
  koPreviewTeams.value = finalList.slice()
  targetKoSize.value =
    payload?.koSize ?? pow2KoSize(koPreviewTeams.value.length)
  step.value = 6
}

async function handleKoPreviewConfirm({ teams: finalTeams, koSize }) {
  koPreviewTeams.value = finalTeams.slice()
  targetKoSize.value = koSize ?? pow2KoSize(finalTeams.length)
  step.value = 5
  try {
    if (tournament.value?.id) {
      const matches = pairTeamsToMatches(finalTeams)
      await fetch(`${API}/tournaments/${tournament.value.id}/save-ko-bracket`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          rounds: [
            {
              round_name:
                finalTeams.length === 8
                  ? 'Viertelfinale'
                  : finalTeams.length === 4
                    ? 'Halbfinale'
                    : 'KO',
              bracket_type: 'main',
              matches
            }
          ]
        })
      })
      await fetch(`${API}/tournaments/${tournament.value.id}/update`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ currentPhase: 'ko' })
      })
      tournament.value.current_phase = 'ko'
    }
  } catch (e) {
    console.warn('KO speichern/Phase setzen fehlgeschlagen:', e)
  }
}

function handlePreviewCancel() {
  step.value = cameFromPlayIn.value ? 7 : 4
}
function handleKoBack() {
  step.value = cameFromPlayIn.value ? 6 : 4
}
function handleKoSaved() {
  /* noop */
}

onMounted(() => {
  fetchTournamentsList().catch(() => {})
})
</script>

<style scoped>
.app-wrapper {
  background: radial-gradient(
    circle at top,
    #1f1f1f 0%,
    #0d0d0d 55%,
    #000 100%
  );
}

.list-group-item.bg-black:hover {
  background-color: #111 !important;
}
</style>
