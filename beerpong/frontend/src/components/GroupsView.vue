<template>
  <section class="mx-auto" style="max-width: 1100px;">
    <div class="d-flex justify-content-between align-items-center mb-4">
      <h2>Gruppenphase</h2>
      <div class="d-flex gap-2">
        <button class="btn btn-outline-light" @click="$emit('back')">Zur Startseite</button>
        <button
          class="btn btn-primary"
          :disabled="!allGroupsReadyForKO"
          @click="emitKo()"
        >
          {{ playInNeeded ? 'Play-In starten' : 'KO-Runde erzeugen' }}
        </button>
      </div>
    </div>
    <p class="text-secondary mb-4">
      Es wurden {{ tournament.groupCount }} Gruppen angelegt. Die Teams wurden der Reihe nach aufgeteilt.
    </p>
    <div class="row g-4">
      <div
        v-for="group in baseGroups"
        :key="group.name"
        class="col-md-3"
      >
        <div class="card bg-dark text-light border-secondary h-100 d-flex flex-column">
          <!-- Header -->
          <div class="card-header d-flex justify-content-between align-items-center">
            <span class="fw-semibold">{{ group.name }}</span>
            <button
              class="btn btn-sm btn-outline-light"
              @click="$emit('generate-group-matches', group)"
              :disabled="(groupMatches[group.name] || []).length > 0 || group.teams.length < 2"
            >
              Gruppenspiele
            </button>
          </div>
          <!-- Tabelle -->
          <ul class="list-group list-group-flush">
            <li
              v-for="(row, idx) in getFinalStandings(group.name)"
              :key="row.name + idx"
              class="list-group-item bg-dark text-light border-secondary d-flex justify-content-between align-items-center"
              :class="getRowClass(group.name, idx)"
              :title="row.name"
            >
              <span class="text-truncate" style="max-width: 7rem;">
                {{ idx + 1 }}. {{ truncateName(row.name, 32) }}
              </span>
              <span class="badge bg-secondary">
                {{ row.points }}P
              </span>
              <button
                v-if="canSelectForPlayIn(group.name, idx)"
                class="btn btn-sm btn-outline-warning ms-2"
                @click="togglePlayInSelection(row.name)"
              >
                {{ isSelectedForPlayIn(row.name) ? 'Entfernen' : 'Zu Play-In' }}
              </button>
            </li>
          </ul>
          <!-- Tiebreak-Start (nur wenn noch keiner läuft / nicht eindeutig) -->
          <div
            v-if="shouldShowTiebreakControls(group.name)"
            class="px-3 py-2 border-top border-secondary"
          >
            <p class="text-secondary small mb-2">Kein eindeutiger 1./2. Platz. Tiebreak:</p>
            <div class="d-flex gap-2">
              <!-- Mini nur anbieten, wenn noch keiner lief -->
              <button
                v-if="!hasActiveMini(group.name)"
                class="btn btn-sm btn-outline-light"
                @click="startMiniTiebreak(group.name)"
              >
                Mini-Runde
              </button>
              <!-- Rage Cage immer anbieten, wenn noch nicht entschieden -->
              <button class="btn btn-sm btn-outline-light" @click="startRageCage(group.name)">
                Rage Cage
              </button>
            </div>
          </div>
          <!-- Mini-Runde -->
          <div
            v-if="tiebreakState[group.name] && tiebreakState[group.name].mode === 'mini'"
            class="px-3 pb-3 border-top border-secondary"
          >
            <p class="text-secondary small mb-2">Tiebreak-Spiele</p>
            <div
              v-for="(m, idx) in tiebreakState[group.name].matches"
              :key="group.name + '-tb-' + idx"
              class="d-flex gap-2 mb-2"
            >
              <button
                class="btn btn-sm flex-fill text-start text-truncate"
                :class="m.winner === m.team1 ? 'btn-success' : 'btn-outline-light'"
                @click="setMiniWinner(group.name, idx, m.team1)"
              >
                {{ truncateName(m.team1) }}
              </button>
              <span class="text-secondary">vs</span>
              <button
                class="btn btn-sm flex-fill text-start text-truncate"
                :class="m.winner === m.team2 ? 'btn-success' : 'btn-outline-light'"
                @click="setMiniWinner(group.name, idx, m.team2)"
              >
                {{ truncateName(m.team2) }}
              </button>
            </div>
            <p v-if="!tiebreakState[group.name].resolved" class="text-secondary small">
              Alle Tiebreak-Spiele entscheiden – oder Rage Cage verwenden.
            </p>
          </div>
          <!-- Rage Cage -->
          <div
            v-if="tiebreakState[group.name] && tiebreakState[group.name].mode === 'rage'"
            class="px-3 pb-3 border-top border-secondary"
          >
            <p class="text-secondary small mb-2">Rage-Cage: Verlierer wählen</p>
            <div class="d-flex flex-column gap-2">
              <button
                v-for="team in tiebreakState[group.name].teams"
                :key="team"
                class="btn btn-sm text-start"
                :class="tiebreakState[group.name].loser === team ? 'btn-danger' : 'btn-outline-danger'"
                @click="setRageLoser(group.name, team)"
              >
                {{ truncateName(team) }} hat verloren
              </button>
            </div>
          </div>
          <!-- Normale Spiele -->
          <div
            v-if="(groupMatches[group.name] || []).length"
            class="card-body border-top border-secondary mt-auto"
          >
            <p class="text-secondary small mb-2">
              Spiele ({{ (groupMatches[group.name] || []).length }})
            </p>
            <div
              v-for="(m, idx) in groupMatches[group.name]"
              :key="group.name + idx"
              class="d-flex gap-2 mb-2"
            >
              <button
                class="btn btn-sm flex-fill text-start text-truncate"
                :class="m.winner === m.team1 ? 'btn-success' : 'btn-outline-light'"
                @click="setGroupWinner(group.name, idx, m.team1)"
              >
                {{ truncateName(m.team1) }}
              </button>
              <span class="text-secondary">vs</span>
              <button
                class="btn btn-sm flex-fill text-start text-truncate"
                :class="m.winner === m.team2 ? 'btn-success' : 'btn-outline-light'"
                @click="setGroupWinner(group.name, idx, m.team2)"
              >
                {{ truncateName(m.team2) }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
    <p class="text-secondary mt-4">
      Nächster Schritt: {{ playInNeeded ? 'Play-In mit den markierten Teams' : 'KO-Runde aus den Erst-/Zweitplatzierten' }} bilden.
    </p>
  </section>
</template>
<script setup>
import { computed } from 'vue'
const props = defineProps({
  tournament: { type: Object, required: true },
  teams: { type: Array, required: true },
  groupMatches: { type: Object, required: true },
  tiebreakState: { type: Object, default: () => ({}) },
  additionalPlayInTeams: { type: Array, default: () => [] }
})
const emit = defineEmits(['generate-group-matches', 'back', 'update:group-matches', 'create-ko', 'update:tiebreak-state', 'update:additional-play-in-teams'])
const groupLetters = ['A','B','C','D','E','F','G','H']
/* Basis-Gruppen */
const baseGroups = computed(() => {
  if (props.tournament.mode !== 'groups') return []
  const count = props.tournament.groupCount
  const groups = Array.from({ length: count }, () => [])
  props.teams.forEach((teamName, idx) => {
    const groupIndex = idx % count
    groups[groupIndex].push({ name: teamName, originalIndex: groups[groupIndex].length })
  })
  return groups.map((teamsInGroup, idx) => ({
    name: `Gruppe ${groupLetters[idx] ?? idx + 1}`,
    teams: teamsInGroup
  }))
})
/* Grund-Tabelle (ohne Tiebreak) */
const baseStandings = computed(() => {
  const out = {}
  for (const g of baseGroups.value) {
    const gname = g.name
    const table = {}
    g.teams.forEach(t => {
      table[t.name] = {
        name: t.name,
        points: 0,
        wins: 0,
        losses: 0,
        originalIndex: t.originalIndex
      }
    })
    const matches = props.groupMatches[gname] || []
    matches.forEach(m => {
      if (!m.winner) return
      const loser = m.winner === m.team1 ? m.team2 : m.team1
      table[m.winner].wins += 1
      table[m.winner].points += 2
      if (table[loser]) table[loser].losses += 1
    })
    const rows = Object.values(table).sort((a, b) => {
      if (b.points !== a.points) return b.points - a.points
      return a.originalIndex - b.originalIndex
    })
    out[gname] = rows
  }
  return out
})
/* Finale Tabelle (mit Tiebreak) */
const finalStandings = computed(() => {
  const out = {}
  for (const g of baseGroups.value) {
    out[g.name] = getFinalStandings(g.name)
  }
  return out
})
function isGroupFullyPlayed(groupName) {
  const matches = props.groupMatches[groupName] || []
  if (!matches.length) return false
  return matches.every(m => !!m.winner)
}
// Erweiterte Tiebreak-Kandidaten (nun auch für Platz 2-4)
function getTiebreakCandidates(groupName) {
  const rows = baseStandings.value[groupName] || []
  if (rows.length < 3 || !isGroupFullyPlayed(groupName)) return []
  const secondPoints = rows[1].points
  const tied = rows.filter(r => r.points === secondPoints)
  if (tied.length > 2) return tied.map(t => t.name) // Wenn mehr als 2 gleich, Tiebreaker
  return []
}
// Zeige Tiebreak-Steuerung?
function shouldShowTiebreakControls(groupName) {
  if (!isGroupFullyPlayed(groupName)) return false
  const candidates = getTiebreakCandidates(groupName)
  if (!candidates.length) return false
  const tb = props.tiebreakState[groupName]
  if (!tb) return true
  if (tb.mode === 'mini' && !tb.resolved) return true
  if (tb.mode === 'rage' && !tb.resolved) return false
  return false
}
function hasActiveMini(groupName) {
  const tb = props.tiebreakState[groupName]
  return tb && tb.mode === 'mini'
}
/* Finale Anzeige unter Berücksichtigung des Tiebreaks */
function getFinalStandings(groupName) {
  const rows = baseStandings.value[groupName] || []
  const tb = props.tiebreakState[groupName]
  if (!tb) return rows
  if (tb.mode === 'rage') {
    if (!tb.loser) return rows
    // Neu: Korrekte Handhabung des Losers – schiebe ihn ans Ende der tied Gruppe
    const candidates = getTiebreakCandidates(groupName)
    const secondPoints = rows[1].points
    const top = rows.filter(r => r.points > secondPoints)
    const bottom = rows.filter(r => r.points < secondPoints)
    const tied = rows.filter(r => candidates.includes(r.name))
    const withoutLoser = tied.filter(r => r.name !== tb.loser).sort((a, b) => a.originalIndex - b.originalIndex)
    const loserObj = tied.find(r => r.name === tb.loser)
    return [...top, ...withoutLoser, loserObj, ...bottom]
  }
  if (tb.mode === 'mini') {
    // wins aus tiebreak zählen
    const extraPoints = {}
    tb.matches.forEach(m => {
      if (!m.winner) return
      extraPoints[m.winner] = (extraPoints[m.winner] || 0) + 2
    })
    const enriched = rows.map(r => ({
      ...r,
      points: r.points + (extraPoints[r.name] || 0)
    }))
    // sortieren wie gewohnt
    return enriched.sort((a, b) => {
      if (b.points !== a.points) return b.points - a.points
      return a.originalIndex - b.originalIndex
    })
  }
  return rows
}
/* KO-Button Bedingung */
const allGroupsReadyForKO = computed(() => {
  // alle Gruppenspiele fertig?
  const allPlayed = baseGroups.value.every(g => isGroupFullyPlayed(g.name))
  if (!allPlayed) return false
  // alle Gruppen, die Gleichstand hatten, müssen wirklich aufgelöst sein
  for (const g of baseGroups.value) {
    const name = g.name
    const candidates = getTiebreakCandidates(name)
    if (!candidates.length) continue
    const tb = props.tiebreakState[name]
    if (!tb) return false
    if (!tb.resolved) return false
  }
  return true
})
/* Play-In Needed */
const playInNeeded = computed(() => {
  let hasLeftovers = false
  for (const g of baseGroups.value) {
    const rows = getFinalStandings(g.name)
    if (rows.length > 2) hasLeftovers = true
  }
  return hasLeftovers
})
function getRowClass(groupName, idx) {
  if (idx < 2) return 'bg-success-subtle' // Qualified
  if (playInNeeded.value) return 'bg-warning-subtle' // Potenziell Play-In
  return ''
}
function canSelectForPlayIn(groupName, idx) {
  return playInNeeded.value && idx >= 1 // Ab Platz 2, falls Tie
}
function isSelectedForPlayIn(teamName) {
  return props.additionalPlayInTeams.includes(teamName)
}
function togglePlayInSelection(teamName) {
  let updated = [...props.additionalPlayInTeams]
  const idx = updated.indexOf(teamName)
  if (idx > -1) {
    updated.splice(idx, 1)
  } else {
    updated.push(teamName)
  }
  emit('update:additional-play-in-teams', updated)
}
/* Aktionen */
function setGroupWinner(groupName, matchIndex, teamName) {
  const updated = { ...props.groupMatches }
  const list = updated[groupName]?.map((m, i) =>
    i === matchIndex ? { ...m, winner: teamName } : m
  ) || []
  updated[groupName] = list
  emit('update:group-matches', updated)
}
function startMiniTiebreak(groupName) {
  const candidates = getTiebreakCandidates(groupName)
  const matches = []
  for (let i = 0; i < candidates.length; i++) {
    for (let j = i + 1; j < candidates.length; j++) {
      matches.push({
        team1: candidates[i],
        team2: candidates[j],
        winner: null
      })
    }
  }
  const newState = {
    ...props.tiebreakState,
    [groupName]: {
      mode: 'mini',
      teams: candidates,
      matches,
      resolved: false
    }
  }
  emit('update:tiebreak-state', newState)
}
function startRageCage(groupName) {
  const candidates = getTiebreakCandidates(groupName)
  const newState = {
    ...props.tiebreakState,
    [groupName]: {
      mode: 'rage',
      teams: candidates,
      loser: null,
      resolved: false
    }
  }
  emit('update:tiebreak-state', newState)
}
function setMiniWinner(groupName, matchIndex, teamName) {
  const current = props.tiebreakState[groupName]
  if (!current) return
  const newMatches = current.matches.map((m, i) =>
    i === matchIndex ? { ...m, winner: teamName } : m
  )
  const allDecided = newMatches.every(m => !!m.winner)
  let resolved = false
  if (allDecided) {
    const winCounter = {}
    newMatches.forEach(m => {
      winCounter[m.winner] = (winCounter[m.winner] || 0) + 1
    })
    const counts = Object.values(winCounter).sort((a, b) => b - a)
    // Für clear top 2: counts[1] > counts[2] (wenn exists)
    if (counts.length < 3 || counts[1] > counts[2]) {
      resolved = true
    }
  }
  const newState = {
    ...props.tiebreakState,
    [groupName]: {
      ...current,
      matches: newMatches,
      resolved
    }
  }
  emit('update:tiebreak-state', newState)
}
function setRageLoser(groupName, teamName) {
  const current = props.tiebreakState[groupName]
  if (!current) return
  const newState = {
    ...props.tiebreakState,
    [groupName]: {
      ...current,
      loser: teamName,
      resolved: true
    }
  }
  emit('update:tiebreak-state', newState)
}
function emitKo() {
  emit('create-ko', finalStandings.value)
}
/* Helper */
function truncateName(name, len = 40) {
  if (!name) return ''
  return name.length > len ? name.slice(0, len - 3) + '...' : name
}
</script>
<style scoped>
.list-group-item {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.list-group-item.bg-success-subtle {
  background-color: rgba(25, 135, 84, 0.1) !important;
}
.list-group-item.bg-warning-subtle {
  background-color: rgba(255, 193, 7, 0.1) !important;
}
</style>