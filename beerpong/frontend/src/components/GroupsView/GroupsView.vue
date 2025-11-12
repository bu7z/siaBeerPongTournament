<template>
  <section class="mx-auto" style="max-width: 1400px;">
    <div class="d-flex justify-content-between align-items-center mb-4">
      <h2>Gruppenphase</h2>
      <div class="d-flex gap-2">
        <button class="btn btn-outline-light" @click="$emit('back')">Zur Startseite</button>
        <button
          class="btn btn-primary"
          :disabled="!allGroupsReadyForKO"
          @click="emitKo()"
        >
          {{ playInNeeded ? 'Play-In prüfen' : 'KO-Runde erzeugen' }}
        </button>
      </div>
    </div>

    <!-- Turnier-Info -->
    <div class="card bg-dark border-secondary mb-4 text-light">
      <div class="card-body py-3">
        <div class="row">
          <div class="col-md-4"><strong>Teilnehmer:</strong> {{ teams.length }} Teams</div>
          <div class="col-md-4"><strong>Becher pro Spiel:</strong> {{ cupsPerGame }}</div>
          <div class="col-md-4"><strong>Gruppen:</strong> {{ baseGroups.length }}</div>
        </div>
      </div>
    </div>

    <div class="row g-4">
      <div
        v-for="group in baseGroups"
        :key="group.name"
        class="col-xl-4 col-lg-6"
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
          <div class="card-body p-0">
            <div class="table-responsive">
              <table class="table table-dark table-hover mb-0">
                <thead>
                  <tr>
                    <th class="ps-3">#</th>
                    <th>Team</th>
                    <th class="text-center">P</th>
                    <th class="text-center">S</th>
                    <th class="text-center">N</th>
                    <th class="text-center">B+</th>
                    <th class="text-center">B-</th>
                    <th class="text-center">±</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="(row, idx) in getFinalStandings(group.name)"
                    :key="row.name + idx"
                    :class="getRowClass(group.name, idx)"
                  >
                    <td class="ps-3 fw-bold">{{ idx + 1 }}.</td>
                    <td class="text-truncate" style="max-width: 160px;" :title="row.name">{{ row.name }}</td>
                    <td class="text-center fw-bold">{{ row.points }}</td>
                    <td class="text-center text-success">{{ row.wins }}</td>
                    <td class="text-center text-danger">{{ row.losses }}</td>
                    <td class="text-center">{{ row.cupsFor }}</td>
                    <td class="text-center">{{ row.cupsAgainst }}</td>
                    <td class="text-center" :class="{'text-success': row.cupsDiff > 0, 'text-danger': row.cupsDiff < 0}">
                      {{ row.cupsDiff > 0 ? '+' : '' }}{{ row.cupsDiff }}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- Tiebreak-Controls -->
          <div
            v-if="shouldShowTiebreakControls(group.name)"
            class="px-3 py-2 border-top border-secondary"
          >
            <p class="text-secondary small mb-2">
              Gleichstand am Cut-Off (Top-2). Tiebreak wählen:
            </p>
            <div class="d-flex flex-wrap gap-2">
              <button
                v-if="tieCount(group.name) >= 5 && !hasActiveTiebreak(group.name)"
                class="btn btn-sm btn-outline-light"
                @click="startMiniTiebreak(group.name)"
              >
                Mini-Runde (Round-Robin)
              </button>

              <button
                v-if="tieCount(group.name) === 3 && !hasActiveTiebreak(group.name)"
                class="btn btn-sm btn-outline-light"
                @click="startRageCage(group.name)"
              >
                Rage-Cage (3 Teams)
              </button>

              <button
                v-if="tieCount(group.name) === 4 && !hasActiveTiebreak(group.name)"
                class="btn btn-sm btn-outline-light"
                @click="startRage4(group.name)"
              >
                Schnell-Tiebreak (4 Teams, 3 Spiele)
              </button>

              <button
                v-if="[3,4].includes(tieCount(group.name)) && !hasActiveTiebreak(group.name)"
                class="btn btn-sm btn-outline-secondary"
                @click="startMiniTiebreak(group.name)"
              >
                Alternativ: Mini-Runde
              </button>
            </div>
          </div>

          <!-- Mini-Runde -->
          <div
            v-if="tiebreakState[group.name]?.mode === 'mini'"
            class="px-3 pb-3 border-top border-secondary"
          >
            <p class="text-secondary small mb-2">Tiebreak-Spiele (Mini-Runde)</p>
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
              Alle Tiebreak-Spiele entscheiden – oder anderen Modus wählen.
            </p>
          </div>

          <!-- Rage-Cage (3er) -->
          <div
            v-if="tiebreakState[group.name]?.mode === 'rage'"
            class="px-3 pb-3 border-top border-secondary"
          >
            <p class="text-secondary small mb-2">Rage-Cage (3 Teams): Verlierer wählen</p>
            <div class="d-flex flex-column gap-2">
              <button
                v-for="team in tiebreakState[group.name].teams"
                :key="team"
                class="btn btn-sm text-start"
                :class="tiebreakState[group.name].loser === team ? 'btn-danger' : 'btn-outline-danger'"
                @click="setRageLoser(group.name, team)"
              >
                {{ truncateName(team) }} verliert
              </button>
            </div>
          </div>

          <!-- Rage-4 (4er-Schnell-Tiebreak) -->
          <div
            v-if="tiebreakState[group.name]?.mode === 'rage4'"
            class="px-3 pb-3 border-top border-secondary"
          >
            <p class="text-secondary small mb-2">Schnell-Tiebreak (4 Teams, 3 Spiele)</p>

            <div class="text-secondary small mb-1">Halbfinale</div>
            <div
              v-for="(sf, sIdx) in tiebreakState[group.name].bracket.semis"
              :key="group.name + '-sf-' + sIdx"
              class="d-flex gap-2 mb-2"
            >
              <button
                class="btn btn-sm flex-fill text-start text-truncate"
                :class="sf.winner === sf.a ? 'btn-success' : 'btn-outline-light'"
                @click="setRage4SemiWinner(group.name, sIdx, 'a')"
              >
                {{ truncateName(sf.a) }}
              </button>
              <span class="text-secondary">vs</span>
              <button
                class="btn btn-sm flex-fill text-start text-truncate"
                :class="sf.winner === sf.b ? 'btn-success' : 'btn-outline-light'"
                @click="setRage4SemiWinner(group.name, sIdx, 'b')"
              >
                {{ truncateName(sf.b) }}
              </button>
            </div>

            <div v-if="rage4SemisDone(group.name)" class="mt-3">
              <div class="text-secondary small mb-1">Winners-Final</div>
              <div class="d-flex gap-2 mb-2">
                <button
                  class="btn btn-sm flex-fill text-start text-truncate"
                  :class="rage4Final(group.name,'win').winner === rage4Final(group.name,'win').a ? 'btn-success' : 'btn-outline-light'"
                  @click="setRage4FinalWinner(group.name, 'win', 'a')"
                >
                  {{ truncateName(rage4Final(group.name,'win').a) }}
                </button>
                <span class="text-secondary">vs</span>
                <button
                  class="btn btn-sm flex-fill text-start text-truncate"
                  :class="rage4Final(group.name,'win').winner === rage4Final(group.name,'win').b ? 'btn-success' : 'btn-outline-light'"
                  @click="setRage4FinalWinner(group.name, 'win', 'b')"
                >
                  {{ truncateName(rage4Final(group.name,'win').b) }}
                </button>
              </div>

              <div class="text-secondary small mb-1 mt-3">Losers-Final</div>
              <div class="d-flex gap-2">
                <button
                  class="btn btn-sm flex-fill text-start text-truncate"
                  :class="rage4Final(group.name,'lose').winner === rage4Final(group.name,'lose').a ? 'btn-success' : 'btn-outline-light'"
                  @click="setRage4FinalWinner(group.name, 'lose', 'a')"
                >
                  {{ truncateName(rage4Final(group.name,'lose').a) }}
                </button>
                <span class="text-secondary">vs</span>
                <button
                  class="btn btn-sm flex-fill text-start text-truncate"
                  :class="rage4Final(group.name,'lose').winner === rage4Final(group.name,'lose').b ? 'btn-success' : 'btn-outline-light'"
                  @click="setRage4FinalWinner(group.name, 'lose', 'b')"
                >
                  {{ truncateName(rage4Final(group.name,'lose').b) }}
                </button>
              </div>

              <p v-if="!tiebreakState[group.name].resolved" class="text-secondary small mt-2">
                Winners- und Losers-Final entscheiden, um die Reihenfolge 1–4 zu fixen.
              </p>
            </div>
          </div>

          <!-- Gruppenspiele -->
          <div
            v-if="(groupMatches[group.name] || []).length"
            class="card-footer border-top border-secondary bg-dark"
          >
            <p class="text-secondary small mb-2">
              Spiele ({{ (groupMatches[group.name] || []).length }})
            </p>
            <div
              v-for="(m, idx) in groupMatches[group.name]"
              :key="group.name + idx"
              class="match-entry mb-3 p-2 border border-secondary rounded"
            >
              <div class="d-flex align-items-center justify-content-between gap-2">
                <div class="flex-fill d-flex align-items-center justify-content-between gap-2">
                  <button
                    class="btn btn-sm d-flex align-items-center gap-2"
                    :class="m.winner === m.team1 ? 'btn-success' : 'btn-outline-light'"
                    @click="incrementCups(group.name, idx, 'team1')"
                    :title="`+1 Becher für ${m.team1}`"
                  >
                    <img src="/beer-cup.svg" alt="" width="18" height="18" />
                    <span class="text-truncate" style="max-width:120px;">{{ m.team1 }}</span>
                  </button>
                  <input
                    type="number"
                    class="form-control form-control-sm cups-input"
                    style="width:70px;"
                    :value="m.cups_team1 ?? 0"
                    @input="setCups(group.name, idx, 'team1', $event.target.value)"
                    min="0"
                    :max="cupsPerGame"
                  />
                </div>
                <span class="text-secondary">vs</span>
                <div class="flex-fill d-flex align-items-center justify-content-between gap-2">
                  <input
                    type="number"
                    class="form-control form-control-sm cups-input"
                    style="width:70px;"
                    :value="m.cups_team2 ?? 0"
                    @input="setCups(groupName=group.name, matchIndex=idx, teamField='team2', value=$event.target.value)"
                    min="0"
                    :max="cupsPerGame"
                  />
                  <button
                    class="btn btn-sm d-flex align-items-center gap-2"
                    :class="m.winner === m.team2 ? 'btn-success' : 'btn-outline-light'"
                    @click="incrementCups(group.name, idx, 'team2')"
                    :title="`+1 Becher für ${m.team2}`"
                  >
                    <img src="/beer-cup.svg" alt="" width="18" height="18" />
                    <span class="text-truncate" style="max-width:120px;">{{ m.team2 }}</span>
                  </button>
                </div>
              </div>
              <div class="text-center mt-1">
                <small class="text-secondary">
                  Ergebnis: {{ m.cups_team1 || 0 }} - {{ m.cups_team2 || 0 }} Becher
                </small>
                <div v-if="m.winner" class="mt-1">
                  <small class="text-success">🏆 Sieger: {{ m.winner }}</small>
                </div>
              </div>
            </div>
          </div>
          <!-- /Gruppenspiele -->
        </div>
      </div>
    </div>

    <!-- Info -->
    <div class="mt-4 p-3 border border-secondary rounded">
      <h6>ℹ️ Tiebreak-Regeln</h6>
      <p class="mb-1 text-secondary"><strong>3 Teams:</strong> Rage-Cage oder Mini-Runde.</p>
      <p class="mb-1 text-secondary"><strong>4 Teams:</strong> Schnell-Tiebreak (2×HF, Winners- & Losers-Final).</p>
      <p class="mb-0 text-secondary"><strong>≥5 Teams:</strong> Mini-Runde.</p>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  tournament: { type: Object, required: true },
  teams: { type: Array, required: true },
  groupMatches: { type: Object, required: true },
  tiebreakState: { type: Object, default: () => ({}) }
})
const emit = defineEmits([
  'back',
  'generate-group-matches',
  'update:group-matches',
  'update:tiebreak-state',
  'create-ko'
])

const cupsPerGame = computed(() => props.tournament.cupsPerGame || 6)
const letters = ['A','B','C','D','E','F','G','H','I','J']

function groupCountByBand(n) {
  if (n <= 4) return 1
  if (n <= 8) return 2
  if (n <= 12) return 3
  if (n <= 16) return 4
  return Math.ceil(n / 4)
}

/* -------------------------
   Gruppen ROBUST mergen
   ------------------------- */
const baseGroups = computed(() => {
  const nameOf = (t, i) => typeof t === 'string' ? t : (t?.name || `Team ${i+1}`)
  const nTeams = (props.teams || []).length

  // 1) Start: aus Team-Zuordnung (group/group_name)
  const map = new Map() // groupName -> Set(teamNames)
  for (let i = 0; i < nTeams; i++) {
    const t = props.teams[i]
    const g =
      (typeof t === 'object' && (t.group || t.group_name)) ||
      null
    if (g) {
      const key = String(g)
      if (!map.has(key)) map.set(key, new Set())
      map.get(key).add(nameOf(t, i))
    }
  }

  // 2) Falls keine Team-Zuordnung vorhanden → Fallback verteilen
  if (map.size === 0) {
    const gcount = groupCountByBand(nTeams)
    for (let gi = 0; gi < gcount; gi++) {
      const gname = `Gruppe ${letters[gi] || gi + 1}`
      map.set(gname, new Set())
    }
    ;(props.teams || []).forEach((t, i) => {
      const gnames = Array.from(map.keys())
      const bucket = gnames[i % gnames.length]
      map.get(bucket).add(nameOf(t, i))
    })
  }

  // 3) Matches einmischen (Gruppen & Teams aus groupMatches sind zusätzlich gültig)
  for (const gname of Object.keys(props.groupMatches || {})) {
    if (!map.has(gname)) map.set(gname, new Set())
    for (const m of props.groupMatches[gname] || []) {
      if (m.team1) map.get(gname).add(m.team1)
      if (m.team2) map.get(gname).add(m.team2)
    }
  }

  // Ergebnis in Array-Form bringen
  const groups = Array.from(map.entries()).map(([gname, set]) => ({
    name: gname,
    teams: Array.from(set).map((nm, idx) => ({ name: nm, originalIndex: idx }))
  }))

  // Konsistente Sortierung: Gruppe A, B, C …
  groups.sort((a, b) => a.name.localeCompare(b.name, 'de'))
  return groups
})

/* -------------------------
   Tabelle berechnen
   ------------------------- */
const baseStandings = computed(() => {
  const out = {}
  for (const group of baseGroups.value) {
    const table = {}
    group.teams.forEach(t => table[t.name] = {
      name:t.name, points:0, wins:0, losses:0, cupsFor:0, cupsAgainst:0, cupsDiff:0, originalIndex:t.originalIndex
    })
    const matches = props.groupMatches[group.name] || []
    for (const m of matches) {
      const c1 = Number.isFinite(+m.cups_team1) ? +m.cups_team1 : 0
      const c2 = Number.isFinite(+m.cups_team2) ? +m.cups_team2 : 0
      if (table[m.team1]) { table[m.team1].cupsFor += c1; table[m.team1].cupsAgainst += c2 }
      if (table[m.team2]) { table[m.team2].cupsFor += c2; table[m.team2].cupsAgainst += c1 }
      if (m.winner) {
        if (table[m.winner]) { table[m.winner].wins += 1; table[m.winner].points += 2 }
        const loser = m.winner === m.team1 ? m.team2 : m.team1
        if (table[loser]) table[loser].losses += 1
      }
    }
    Object.values(table).forEach(r=> r.cupsDiff = r.cupsFor - r.cupsAgainst)
    const rows = Object.values(table).sort((a,b)=>{
      if (b.points!==a.points) return b.points-a.points
      if (b.cupsDiff!==a.cupsDiff) return b.cupsDiff-a.cupsDiff
      if (b.cupsFor!==a.cupsFor) return b.cupsFor-a.cupsFor
      return a.originalIndex-b.originalIndex
    })
    out[group.name] = rows
  }
  return out
})

/* -------------------------
   Tie-Helper
   ------------------------- */
function getFinalStandings(groupName) {
  const rows = baseStandings.value[groupName] || []
  const tb = props.tiebreakState[groupName]
  if (!tb) return rows

  if (tb.mode === 'rage') {
    if (!tb.loser) return rows
    const secondPoints = rows[1]?.points ?? 0
    const top = rows.filter(r => r.points > secondPoints)
    const eqNames = rows.filter(r => r.points === secondPoints).map(r=>r.name)
    const eqRows = rows.filter(r => eqNames.includes(r.name))
    const bottom = rows.filter(r => r.points < secondPoints)
    const withoutLoser = eqRows.filter(r=> r.name !== tb.loser)
    const loserObj = eqRows.find(r=> r.name === tb.loser)
    return [...top, ...withoutLoser, loserObj, ...bottom]
  }

  if (tb.mode === 'mini') {
    const extra = {}
    tb.matches.forEach(m => { if (m.winner) extra[m.winner] = (extra[m.winner]||0)+2 })
    const enriched = rows.map(r => ({ ...r, points: r.points + (extra[r.name]||0) }))
    return enriched.sort((a,b)=>{
      if (b.points!==a.points) return b.points-a.points
      if (b.cupsDiff!==a.cupsDiff) return b.cupsDiff-a.cupsDiff
      if (b.cupsFor!==a.cupsFor) return b.cupsFor-a.cupsFor
      return a.originalIndex-b.originalIndex
    })
  }

  if (tb.mode === 'rage4') {
    const secondPoints = rows[1]?.points ?? 0
    const top = rows.filter(r => r.points > secondPoints)
    const br = tb.bracket
    if (!br.winFinal.winner || !br.loseFinal.winner) return rows
    const best = br.winFinal.winner
    const second = br.winFinal.winner === br.winFinal.a ? br.winFinal.b : br.winFinal.a
    const fourth = br.loseFinal.winner === br.loseFinal.a ? br.loseFinal.b : br.loseFinal.a
    const third = br.loseFinal.winner
    const order = [best, second, third, fourth]
    const eqSorted = order.map(n => rows.find(r => r.name === n)).filter(Boolean)
    const othersBottom = rows.filter(r => !order.includes(r.name) && r.points === secondPoints)
    const bottom = rows.filter(r => r.points < secondPoints)
    return [...top, ...eqSorted, ...othersBottom, ...bottom]
  }

  return rows
}

function isGroupFullyPlayed(groupName) {
  const matches = props.groupMatches[groupName] || []
  if (!matches.length) return false
  return matches.every(m => !!m.winner)
}

function getTieCandidates(groupName) {
  const rows = baseStandings.value[groupName] || []
  if (rows.length < 3 || !isGroupFullyPlayed(groupName)) return []
  const secondPoints = rows[1]?.points ?? 0
  const tied = rows.filter(r => r.points === secondPoints).map(r=>r.name)
  return tied.length >= 2 ? tied : []
}

function tieCount(groupName) {
  return getTieCandidates(groupName).length
}

function shouldShowTiebreakControls(groupName) {
  const tie = getTieCandidates(groupName)
  if (!tie.length) return false
  const tb = props.tiebreakState[groupName]
  if (!tb) return true
  if (tb.mode === 'mini' && !tb.resolved) return true
  if (tb.mode === 'rage' && !tb.resolved) return true
  if (tb.mode === 'rage4' && !tb.resolved) return true
  return false
}

function hasActiveTiebreak(groupName) {
  return !!props.tiebreakState[groupName]
}

/* KO-Button Logik */
const allGroupsReadyForKO = computed(() => {
  const allPlayed = baseGroups.value.every(g => isGroupFullyPlayed(g.name))
  if (!allPlayed) return false
  for (const g of baseGroups.value) {
    const tie = getTieCandidates(g.name)
    if (!tie.length) continue
    const tb = props.tiebreakState[g.name]
    if (!tb || !tb.resolved) return false
  }
  return true
})

const playInNeeded = computed(() => {
  let leftover = false
  for (const g of baseGroups.value) {
    const rows = getFinalStandings(g.name)
    if (rows.length > 2) leftover = true
  }
  return leftover
})

/* UI-Styling */
function getRowClass(groupName, idx) {
  if (idx < 2) return 'table-success'
  if (playInNeeded.value) return 'table-warning'
  return ''
}

/* Becher-Interaktion */
function setCups(groupName, matchIndex, teamField, value) {
  const updated = { ...props.groupMatches }
  const list = [...(updated[groupName] || [])]
  const m = { ...list[matchIndex] }
  const v = Math.max(0, Math.min(cupsPerGame.value, parseInt(value) || 0))
  m[`cups_${teamField}`] = v
  const a = Number.isFinite(+m.cups_team1) ? +m.cups_team1 : 0
  const b = Number.isFinite(+m.cups_team2) ? +m.cups_team2 : 0
  if (a >= cupsPerGame.value || b >= cupsPerGame.value) {
    m.winner = a > b ? m.team1 : m.team2
  } else {
    m.winner = null
  }
  list[matchIndex] = m
  updated[groupName] = list
  emit('update:group-matches', updated)
}

function incrementCups(groupName, matchIndex, teamField) {
  const updated = { ...props.groupMatches }
  const list = [...(updated[groupName] || [])]
  const m = { ...list[matchIndex] }
  const key = `cups_${teamField}`
  m[key] = Math.min(cupsPerGame.value, (parseInt(m[key]) || 0) + 1)
  const a = Number.isFinite(+m.cups_team1) ? +m.cups_team1 : 0
  const b = Number.isFinite(+m.cups_team2) ? +m.cups_team2 : 0
  if (a >= cupsPerGame.value || b >= cupsPerGame.value) {
    m.winner = a > b ? m.team1 : m.team2
  } else if (a === b) {
    m.winner = null
  }
  list[matchIndex] = m
  updated[groupName] = list
  emit('update:group-matches', updated)
}

/* Tiebreak: Mini */
function startMiniTiebreak(groupName) {
  const cands = getTieCandidates(groupName)
  const matches = []
  for (let i=0;i<cands.length;i++) {
    for (let j=i+1;j<cands.length;j++) {
      matches.push({ team1:cands[i], team2:cands[j], winner:null })
    }
  }
  const newState = { ...props.tiebreakState, [groupName]: { mode:'mini', teams:cands, matches, resolved:false } }
  emit('update:tiebreak-state', newState)
}
function setMiniWinner(groupName, matchIndex, teamName) {
  const current = props.tiebreakState[groupName]; if (!current) return
  const newMatches = current.matches.map((m,i)=> i===matchIndex ? { ...m, winner:teamName } : m)
  const allDecided = newMatches.every(m=>!!m.winner)
  let resolved = false
  if (allDecided) {
    const counter = {}
    newMatches.forEach(m=>{ counter[m.winner]=(counter[m.winner]||0)+1 })
    const counts = Object.values(counter).sort((a,b)=>b-a)
    if (counts.length < 3 || counts[1] > counts[2]) resolved = true
  }
  const newState = { ...props.tiebreakState, [groupName]: { ...current, matches:newMatches, resolved } }
  emit('update:tiebreak-state', newState)
}

/* Tiebreak: Rage (3er) */
function startRageCage(groupName) {
  const cands = getTieCandidates(groupName)
  const newState = { ...props.tiebreakState, [groupName]: { mode:'rage', teams:cands, loser:null, resolved:false } }
  emit('update:tiebreak-state', newState)
}
function setRageLoser(groupName, teamName) {
  const current = props.tiebreakState[groupName]; if (!current) return
  const newState = { ...props.tiebreakState, [groupName]: { ...current, loser:teamName, resolved:true } }
  emit('update:tiebreak-state', newState)
}

/* Tiebreak: Rage-4 */
function startRage4(groupName) {
  const rows = baseStandings.value[groupName] || []
  const secondPoints = rows[1]?.points ?? 0
  const seeded = rows.filter(r => r.points === secondPoints).map(r => r.name)
  const semis = [
    { a: seeded[0], b: seeded[3], winner: null },
    { a: seeded[1], b: seeded[2], winner: null }
  ]
  const newState = {
    ...props.tiebreakState,
    [groupName]: {
      mode: 'rage4',
      bracket: {
        semis,
        winFinal: { a: null, b: null, winner: null },
        loseFinal: { a: null, b: null, winner: null }
      },
      resolved: false
    }
  }
  emit('update:tiebreak-state', newState)
}
function rage4SemisDone(groupName) {
  const tb = props.tiebreakState[groupName]
  return !!tb && tb.mode==='rage4' && tb.bracket.semis.every(sf => !!sf.winner)
}
function rage4Final(groupName, which) {
  const tb = props.tiebreakState[groupName]
  if (!tb || tb.mode !== 'rage4') return { a:null, b:null, winner:null }
  return which === 'win' ? tb.bracket.winFinal : tb.bracket.loseFinal
}
function setRage4SemiWinner(groupName, semiIndex, side) {
  const tb = props.tiebreakState[groupName]; if (!tb || tb.mode!=='rage4') return
  const semis = tb.bracket.semis.map((sf, i)=>{
    if (i!==semiIndex) return sf
    const winner = side==='a' ? sf.a : sf.b
    return { ...sf, winner }
  })
  let { winFinal, loseFinal } = tb.bracket
  if (semis.every(sf=>!!sf.winner)) {
    const w1 = semis[0].winner, w2 = semis[1].winner
    const l1 = semis[0].winner === semis[0].a ? semis[0].b : semis[0].a
    const l2 = semis[1].winner === semis[1].a ? semis[1].b : semis[1].a
    winFinal = { a: w1, b: w2, winner: (winFinal.winner && [w1,w2].includes(winFinal.winner)) ? winFinal.winner : null }
    loseFinal = { a: l1, b: l2, winner: (loseFinal.winner && [l1,l2].includes(loseFinal.winner)) ? loseFinal.winner : null }
  }
  const newState = {
    ...props.tiebreakState,
    [groupName]: {
      mode: 'rage4',
      bracket: { semis, winFinal, loseFinal },
      resolved: !!(winFinal.winner && loseFinal.winner)
    }
  }
  emit('update:tiebreak-state', newState)
}
function setRage4FinalWinner(groupName, which, side) {
  const tb = props.tiebreakState[groupName]; if (!tb || tb.mode!=='rage4') return
  const br = tb.bracket
  const f = which==='win' ? br.winFinal : br.loseFinal
  if (!f.a || !f.b) return
  const winner = side==='a' ? f.a : f.b
  const newWin = which==='win' ? { ...br.winFinal, winner } : br.winFinal
  const newLose = which==='lose' ? { ...br.loseFinal, winner } : br.loseFinal
  const newState = {
    ...props.tiebreakState,
    [groupName]: { mode:'rage4', bracket:{ semis:br.semis, winFinal:newWin, loseFinal:newLose }, resolved: !!(newWin.winner && newLose.winner) }
  }
  emit('update:tiebreak-state', newState)
}

/* KO starten */
function emitKo() {
  const final = {}
  for (const g of baseGroups.value) final[g.name] = getFinalStandings(g.name)
  emit('create-ko', final)
}

/* Helper */
function truncateName(name, len = 40) {
  if (!name) return ''
  return name.length > len ? name.slice(0, len - 3) + '...' : name
}
</script>

<style scoped>
.match-entry { background: rgba(255, 255, 255, 0.05); }
.cups-input { background: rgba(0, 0, 0, 0.3); border: 1px solid #6c757d; color: white; }
.cups-input:focus { background: rgba(0, 0, 0, 0.5); border-color: #0d6efd; color: white; }
.table-responsive { font-size: 0.875rem; }
.table-success { background-color: rgba(25, 135, 84, 0.15) !important; }
.table-warning { background-color: rgba(255, 193, 7, 0.15) !important; }
.table-hover tbody tr:hover { background-color: rgba(255, 255, 255, 0.075) !important; }
@media (max-width: 768px) {
  .table-responsive { font-size: 0.8rem; }
  .cups-input { width: 50px !important; }
}
</style>
