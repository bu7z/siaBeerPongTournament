<!-- App.vue -->
<template>
  <div class="app-wrapper bg-dark text-light min-vh-100">
    <HeaderBar />

    <main class="container py-5">
      <!-- Wizard -->
      <TournamentWizard
        v-if="step === 0 || step === 1 || step === 2 || step === 3"
        :step="step"
        :tournament="tournament"
        :teams="teams"
        @update:step="step = $event"
        @update:tournament="tournament = $event"
        @update:teams="teams = $event"
        @finish="handleFinish"
      />

      <!-- Gruppenphase -->
      <GroupsView
        v-else-if="step === 4"
        :tournament="tournament"
        :teams="teams"
        :group-matches="groupMatches"
        @generate-group-matches="generateMatchesForGroup"
        @update:group-matches="groupMatches = $event"
        @back="step = 0"
        @create-ko="createKnockoutFromGroups"
      />

      <!-- KO-Vorschau (zeigt Teams, füllt auf, optional editierbar) -->
      <KnockoutPreview
        v-else-if="step === 6"
        :teams="koPreviewTeams"
        @cancel="step = 4"
        @confirm="handleKoPreviewConfirm"
      />

      <!-- Play-In / Loser-Bracket (3 Teams → 2 weiter) -->
      <PlayInView
        v-else-if="step === 7"
        :teams="pendingPlayIn"
        @cancel="step = 4"
        @done="handlePlayInDone"
      />

      <!-- KO-Phase -->
      <KnockoutView
        v-else-if="step === 5"
        :matches="knockoutMatches"
        @back="handleKoBack"
      />
    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import HeaderBar from './components/HeaderBar.vue'
import TournamentWizard from './components/TournamentWizard.vue'
import GroupsView from './components/GroupsView.vue'
import KnockoutView from './components/KnockoutView.vue'
import PlayInView from './components/PlayInView.vue'
import KnockoutPreview from './components/KnockoutPreview.vue'

const step = ref(0)
const teams = ref([])

const tournament = ref({
  mode: 'groups', // 'groups' | 'round16' | 'quarter'
  groupCount: 4
})

// gruppenspiele
const groupMatches = ref({})

// KO-Matches
const knockoutMatches = ref([])

// KO-Vorschau
const koPreviewTeams = ref([])

// Sonderfall 3×3 -> 6 sichere + 3 dritte
const pendingQualified = ref([])
const pendingPlayIn = ref([])

function handleFinish() {
  if (tournament.value.mode === 'groups') {
    step.value = 4
    return
  }

  if (tournament.value.mode === 'quarter') {
    knockoutMatches.value = buildKoFromTeams(teams.value, 8)
    step.value = 5
    return
  }

  if (tournament.value.mode === 'round16') {
    knockoutMatches.value = buildKoFromTeams(teams.value, 16)
    step.value = 5
    return
  }

  step.value = 0
}

function generateRoundRobin(teamsArr) {
  const matches = []
  for (let i = 0; i < teamsArr.length; i++) {
    for (let j = i + 1; j < teamsArr.length; j++) {
      matches.push({
        team1: teamsArr[i],
        team2: teamsArr[j],
        winner: null
      })
    }
  }
  return matches
}

function generateMatchesForGroup(group) {
  // falls group.teams Objekte enthält → auf Namen mappen
  const names = group.teams.map(t => typeof t === 'string' ? t : t.name)
  const matches = generateRoundRobin(names)
  groupMatches.value = {
    ...groupMatches.value,
    [group.name]: matches
  }
}

// kommt aus GroupsView mit den berechneten Tabellen
function createKnockoutFromGroups(standingsByGroup) {
  const qualified = []
  const leftovers = []

  Object.keys(standingsByGroup).forEach((g) => {
    const rows = standingsByGroup[g] || []
    if (rows[0]) qualified.push(rows[0].name)
    if (rows[1]) qualified.push(rows[1].name)
    if (rows[2]) leftovers.push(rows[2].name)
  })

  // Sonderfall: 6 sichere + 3 dritte
  if (qualified.length === 6 && leftovers.length === 3) {
    pendingQualified.value = qualified
    pendingPlayIn.value = leftovers
    step.value = 7
    return
  }

  // Standard: wir gehen in eine Vorschau und füllen dort auf
  koPreviewTeams.value = [...qualified, ...leftovers]
  step.value = 6
}

function handlePlayInDone(winners) {
  // winners = 2 Namen aus PlayInView
  koPreviewTeams.value = [...pendingQualified.value, ...winners]
  step.value = 6
}

function handleKoPreviewConfirm(finalTeams) {
  knockoutMatches.value = pairTeamsToMatches(finalTeams)
  step.value = 5
}

function buildKoFromTeams(allTeams, needed) {
  const trimmed = allTeams.slice(0, needed)
  return pairTeamsToMatches(trimmed)
}

function pairTeamsToMatches(list) {
  const matches = []
  for (let i = 0; i < list.length; i += 2) {
    const t1 = list[i]
    const t2 = list[i + 1]
    if (!t1 || !t2) break
    matches.push({
      team1: t1,
      team2: t2,
      winner: null
    })
  }
  return matches
}

function handleKoBack() {
  if (tournament.value.mode === 'groups') {
    step.value = 4
  } else {
    step.value = 0
  }
}
</script>

<style scoped>
.app-wrapper {
  background: radial-gradient(circle at top, #1f1f1f 0%, #0d0d0d 55%, #000 100%);
}
</style>
