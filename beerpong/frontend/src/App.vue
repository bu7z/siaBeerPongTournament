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
        :tiebreak-state="tiebreakState"
        :additional-play-in-teams="additionalPlayInTeams"
        @generate-group-matches="generateMatchesForGroup"
        @update:group-matches="groupMatches = $event"
        @update:tiebreak-state="tiebreakState = $event"
        @update:additional-play-in-teams="additionalPlayInTeams = $event"
        @back="step = 0"
        @create-ko="createKnockoutFromGroups"
      />
      <!-- KO-Vorschau -->
      <KnockoutPreview
        v-else-if="step === 6"
        :teams="koPreviewTeams"
        :came-from-play-in="cameFromPlayIn"
        @cancel="handlePreviewCancel"
        @confirm="handleKoPreviewConfirm"
      />
      <!-- Play-In -->
      <PlayInView
        v-else-if="step === 7"
        :teams="pendingPlayIn"
        :qualified-count="pendingQualified.length"
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
import { ref, inject, onMounted, onBeforeUnmount } from 'vue'
import HeaderBar from './components/HeaderBar.vue'
import TournamentWizard from './components/TournamentWizard.vue'
import GroupsView from './components/GroupsView.vue'
import KnockoutView from './components/KnockoutView.vue'
import PlayInView from './components/PlayInView.vue'
import KnockoutPreview from './components/KnockoutPreview.vue'
const socket = inject('socket')
const step = ref(0)
const teams = ref([])
const tournament = ref({
  mode: 'groups',
  groupCount: 4,
})
const groupMatches = ref({})
const knockoutMatches = ref([])
const koPreviewTeams = ref([])
// Sonderfall Play-In
const pendingQualified = ref([]) // Direkte Qualis
const pendingPlayIn = ref([]) // Play-In Teams (dynamisch)
const cameFromPlayIn = ref(false)
const tiebreakState = ref({})
const additionalPlayInTeams = ref([]) // Zusätzliche manuell selektierte Teams für Play-In
// --------------------
// Socket Hooks
// --------------------
onMounted(() => {
  if (!socket) return
  socket.on('group_matches_updated', (payload) => {
    groupMatches.value = payload || {}
  })
  socket.on('match_updated', ({ group, match }) => {
    const current = { ...groupMatches.value }
    const list = current[group] ? [...current[group]] : []
    let idx = list.findIndex(m => m.id && match.id && m.id === match.id)
    if (idx === -1) {
      idx = list.findIndex(m => m.team1 === match.team1 && m.team2 === match.team2)
    }
    if (idx !== -1) {
      list[idx] = { ...list[idx], ...match }
    } else {
      list.push(match)
    }
    current[group] = list
    groupMatches.value = current
  })
})
onBeforeUnmount(() => {
  if (!socket) return
  socket.off('group_matches_updated')
  socket.off('match_updated')
})
// --------------------
// Wizard fertig
// --------------------
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
// --------------------
// Matchgenerierung
// --------------------
function generateRoundRobin(teamsArr) {
  const matches = []
  for (let i = 0; i < teamsArr.length; i++) {
    for (let j = i + 1; j < teamsArr.length; j++) {
      matches.push({
        team1: teamsArr[i],
        team2: teamsArr[j],
        winner: null,
      })
    }
  }
  return matches
}
function generateMatchesForGroup(group) {
  const names = group.teams.map((t) => (typeof t === 'string' ? t : t.name))
  const matches = generateRoundRobin(names)
  groupMatches.value = {
    ...groupMatches.value,
    [group.name]: matches,
  }
}
// --------------------
// KO-Erzeugung aus Gruppen (dynamisch)
// --------------------
function createKnockoutFromGroups(standingsByGroup) {
  const qualified = []
  const leftovers = []
  Object.keys(standingsByGroup).forEach((g) => {
    const rows = standingsByGroup[g] || []
    // Top 2 immer qualified
    if (rows[0]) qualified.push(rows[0].name)
    if (rows[1]) qualified.push(rows[1].name)
    // Leftovers: Ab Platz 3
    for (let i = 2; i < rows.length; i++) {
      if (rows[i]) leftovers.push(rows[i].name)
    }
  })
  // Zusätzliche manuell selektierte hinzufügen
  leftovers.push(...additionalPlayInTeams.value)
  // Entferne Duplikate (falls nötig)
  const uniqueLeftovers = [...new Set(leftovers)]
  // Wenn leftovers > 0, gehe zu Play-In
  if (uniqueLeftovers.length > 0) {
    pendingQualified.value = qualified
    pendingPlayIn.value = uniqueLeftovers
    cameFromPlayIn.value = true
    step.value = 7
    return
  }
  // Andernfalls direkt zur Preview
  koPreviewTeams.value = qualified
  cameFromPlayIn.value = false
  step.value = 6
}
function handlePlayInDone(winners) {
  koPreviewTeams.value = [...pendingQualified.value, ...winners]
  step.value = 6
}
function handleKoPreviewConfirm(finalTeams) {
  knockoutMatches.value = pairTeamsToMatches(finalTeams)
  step.value = 5
}
function handlePreviewCancel(toPlayIn) {
  step.value = toPlayIn ? 7 : 4
}
// --------------------
// KO-Helfer
// --------------------
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
      winner: null,
    })
  }
  return matches
}
function handleKoBack() {
  if (tournament.value.mode === 'groups') {
    step.value = 6
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