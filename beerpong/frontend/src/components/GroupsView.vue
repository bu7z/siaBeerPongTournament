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
          KO-Runde erzeugen
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
              :title="row.name"
            >
              <span class="text-truncate" style="max-width: 7rem;">
                {{ idx + 1 }}. {{ truncateName(row.name, 32) }}
              </span>
              <span class="badge bg-secondary">
                {{ row.points }}P
              </span>
            </li>
          </ul>

          <!-- Tiebreak-Start -->
          <div
            v-if="shouldShowTiebreakControls(group.name)"
            class="px-3 py-2 border-top border-secondary"
          >
            <p class="text-secondary small mb-2">Kein eindeutiger 1./2. Platz. Tiebreak:</p>
            <div class="d-flex gap-2">
              <button class="btn btn-sm btn-outline-light" @click="startMiniTiebreak(group.name)">Mini-Runde</button>
              <button class="btn btn-sm btn-outline-light" @click="startRageCage(group.name)">Rage Cage</button>
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
              Alle Tiebreak-Spiele entscheiden.
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
      Nächster Schritt: KO-Runde aus den Erst-/Zweitplatzierten bilden.
    </p>
  </section>
</template>

<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
  tournament: { type: Object, required: true },
  teams: { type: Array, required: true },
  groupMatches: { type: Object, required: true }
})

const emit = defineEmits(['generate-group-matches', 'back', 'update:group-matches', 'create-ko'])

const groupLetters = ['A','B','C','D','E','F','G','H']

// pro Gruppe: { mode, teams, matches, loser, resolved }
const tiebreakState = ref({})

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

function isGroupFullyPlayed(groupName) {
  const matches = props.groupMatches[groupName] || []
  if (!matches.length) return false
  return matches.every(m => !!m.winner)
}

// Welche Teams sind wirklich punktgleich und müssen tie-breaken?
function getTiebreakCandidates(groupName) {
  const rows = baseStandings.value[groupName] || []
  if (rows.length !== 3) return []
  if (!isGroupFullyPlayed(groupName)) return []

  const pts2 = rows[1].points
  const tied = rows.filter(r => r.points === pts2)

  // alle 3 haben gleich viele
  if (tied.length === 3) return tied.map(t => t.name)

  // nur Platz 2 und 3 gleich
  if (tied.length === 2) return tied.map(t => t.name)

  return []
}

function shouldShowTiebreakControls(groupName) {
  const candidates = getTiebreakCandidates(groupName)
  if (!candidates.length) return false
  const tb = tiebreakState.value[groupName]
  if (tb && tb.resolved === false) return false
  if (tb && tb.resolved === true) return false
  return true
}

/* Finale Anzeige unter Berücksichtigung des Tiebreaks */
function getFinalStandings(groupName) {
  const rows = baseStandings.value[groupName] || []
  const tb = tiebreakState.value[groupName]
  if (!tb || tb.resolved === false) {
    return rows
  }

  // rage: loser nach hinten
  if (tb.mode === 'rage' && tb.loser) {
    const without = rows.filter(r => r.name !== tb.loser)
    const loserObj = rows.find(r => r.name === tb.loser)
    return [...without, loserObj]
  }

  // mini: sortiere betroffene nach ihren Siegen
  if (tb.mode === 'mini') {
    const wins = {}
    tb.matches.forEach(m => {
      if (!m.winner) return
      wins[m.winner] = (wins[m.winner] || 0) + 1
    })

    const affectedNames = tb.teams
    const unaffected = rows.filter(r => !affectedNames.includes(r.name))
    const affected = rows.filter(r => affectedNames.includes(r.name))

    const sortedAffected = affected.sort((a, b) => {
      const wa = wins[a.name] || 0
      const wb = wins[b.name] || 0
      if (wb !== wa) return wb - wa
      return a.originalIndex - b.originalIndex
    })

    // wir müssen wieder nach Punkten sortieren, aber innerhalb der betroffenen die neue Reihenfolge beibehalten
    return [...unaffected, ...sortedAffected].sort((a, b) => {
      if (b.points !== a.points) return b.points - a.points
      const ai = sortedAffected.findIndex(x => x.name === a.name)
      const bi = sortedAffected.findIndex(x => x.name === b.name)
      if (ai !== -1 && bi !== -1) return ai - bi
      return a.originalIndex - b.originalIndex
    })
  }

  return rows
}

/* KO-Button Bedingung */
const allGroupsReadyForKO = computed(() => {
  // normale Spiele komplett?
  const allPlayed = baseGroups.value.every(g => isGroupFullyPlayed(g.name))
  if (!allPlayed) return false

  // alle Gruppen, die Tiebreak brauchen, müssen resolved sein
  for (const g of baseGroups.value) {
    const c = getTiebreakCandidates(g.name)
    if (c.length) {
      const tb = tiebreakState.value[g.name]
      if (!tb || tb.resolved === false) return false
    }
  }
  return true
})

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
  tiebreakState.value = {
    ...tiebreakState.value,
    [groupName]: {
      mode: 'mini',
      teams: candidates,
      matches,
      resolved: false
    }
  }
}

function startRageCage(groupName) {
  const candidates = getTiebreakCandidates(groupName)
  tiebreakState.value = {
    ...tiebreakState.value,
    [groupName]: {
      mode: 'rage',
      teams: candidates,
      loser: null,
      resolved: false
    }
  }
}

function setMiniWinner(groupName, matchIndex, teamName) {
  const current = tiebreakState.value[groupName]
  if (!current) return
  const newMatches = current.matches.map((m, i) =>
    i === matchIndex ? { ...m, winner: teamName } : m
  )
  const resolved = newMatches.every(m => !!m.winner)
  tiebreakState.value = {
    ...tiebreakState.value,
    [groupName]: {
      ...current,
      matches: newMatches,
      resolved
    }
  }
}

function setRageLoser(groupName, teamName) {
  const current = tiebreakState.value[groupName]
  if (!current) return
  tiebreakState.value = {
    ...tiebreakState.value,
    [groupName]: {
      ...current,
      loser: teamName,
      resolved: true
    }
  }
}

function emitKo() {
  emit('create-ko', baseStandings.value)
}
</script>

<style scoped>
.list-group-item {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
