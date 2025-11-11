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

  if (tied.length === 3) return tied.map(t => t.name)
  if (tied.length === 2) return tied.map(t => t.name)
  return []
}

// Zeige Tiebreak-Steuerung?
function shouldShowTiebreakControls(groupName) {
  // Wenn Gruppe nicht fertig → nichts
  if (!isGroupFullyPlayed(groupName)) return false

  const candidates = getTiebreakCandidates(groupName)
  if (!candidates.length) return false

  const tb = tiebreakState.value[groupName]
  // noch kein Tiebreak → anzeigen
  if (!tb) return true

  // Mini lief, aber Ergebnis nicht eindeutig → Rage Cage anbieten
  if (tb.mode === 'mini' && !tb.resolved) return true

  // Rage gestartet aber noch kein Verlierer → nichts zusätzlich
  if (tb.mode === 'rage' && !tb.resolved) return false

  // resolved → nichts
  return false
}

function hasActiveMini(groupName) {
  const tb = tiebreakState.value[groupName]
  return tb && tb.mode === 'mini'
}

/* Finale Anzeige unter Berücksichtigung des Tiebreaks */
function getFinalStandings(groupName) {
  // Basis
  const rows = baseStandings.value[groupName] || []
  const tb = tiebreakState.value[groupName]

  if (!tb) {
    return rows
  }

  // Rage: Verlierer nach hinten
  if (tb.mode === 'rage') {
    if (!tb.loser) return rows
    const without = rows.filter(r => r.name !== tb.loser)
    const loserObj = rows.find(r => r.name === tb.loser)
    return [...without, loserObj]
  }

  // Mini: Siege aus Tiebreak als Punkte addieren (+2 pro Sieg)
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

    const tb = tiebreakState.value[name]
    if (!tb) return false
    if (!tb.resolved) return false
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

  // Gewinner setzen
  const newMatches = current.matches.map((m, i) =>
    i === matchIndex ? { ...m, winner: teamName } : m
  )

  // prüfen, ob alle Tiebreak-Spiele entschieden sind
  const allDecided = newMatches.every(m => !!m.winner)

  // wenn alle entschieden sind → schauen, ob eindeutig
  let resolved = false
  if (allDecided) {
    const winCounter = {}
    newMatches.forEach(m => {
      winCounter[m.winner] = (winCounter[m.winner] || 0) + 1
    })

    // z.B. 3 Teams → wins = [2,1,0] → eindeutig
    const counts = Object.values(winCounter).sort((a, b) => b - a) // absteigend
    // eindeutig, wenn es nicht sowas wie 1,1,1 oder 2,2 gibt
    if (counts.length === 3) {
      // 3er mini
      if (!(counts[0] === counts[1] && counts[1] === counts[2])) {
        resolved = true
      }
    } else if (counts.length === 2) {
      // 2er mini (selten, aber möglich)
      if (counts[0] !== counts[1]) {
        resolved = true
      }
    }
    // wenn nicht resolved → bleibt false → UI zeigt weiter Rage Cage an
  }

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
  // wir geben die Tabellen (ohne Tiebreak-Zusatzdaten) nach oben;
  // App macht daraus KO
  emit('create-ko', baseStandings.value)
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
</style>
