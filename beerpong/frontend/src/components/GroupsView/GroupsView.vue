<template>
  <section class="mx-auto" style="max-width: 1400px;">
    <div class="d-flex justify-content-between align-items-center mb-4">
      <h2 class="mb-0">Gruppenphase</h2>
      <div class="d-flex gap-2">
        <button class="btn btn-outline-light" @click="$emit('back')">Zur Startseite</button>
        <button class="btn btn-outline-light" @click="reloadAll" :disabled="loading">Daten laden</button>
        <button
          class="btn btn-primary"
          :disabled="!canProceedKo"
          @click="goNext"
        >
          Weiter (KO/Play-In)
        </button>
      </div>
    </div>

    <div class="card bg-dark border-secondary mb-4 text-light">
      <div class="card-body py-3">
        <div class="row">
          <div class="col-md-4"><strong>Teilnehmer:</strong> {{ (tournament?.participantCount ?? tournament?.participant_count) ?? teams.length }} Teams</div>
          <div class="col-md-4"><strong>Becher pro Spiel:</strong> {{ cupsTarget }}</div>
          <div class="col-md-4"><strong>Gruppen (Vorschau):</strong> {{ autoGroupsPreview.length || '–' }}</div>
        </div>
        <div class="mt-2">
          <button class="btn btn-sm btn-outline-light" @click="generateGroupsFromTeams" :disabled="loading">
            Gruppen automatisch erzeugen
          </button>
          <button class="btn btn-sm btn-outline-secondary ms-2" @click="saveGroupPhase" :disabled="loading || renderGroups.length === 0">
            Gruppenphase speichern
          </button>
        </div>
      </div>
    </div>

    <div v-if="loading" class="alert alert-dark border-secondary my-3">
      Lade…
    </div>
    <div v-if="!loading && renderGroups.length === 0" class="alert alert-dark border-secondary my-3">
      Noch keine Gruppendaten. Klicke auf „Gruppen automatisch erzeugen“.
    </div>

    <div class="row g-4">
      <div
        v-for="group in renderGroups"
        :key="group.name"
        class="col-xl-4 col-lg-6"
      >
        <div class="card bg-dark text-light border-secondary h-100 d-flex flex-column">
          <div class="card-header d-flex justify-content-between align-items-center">
            <span class="fw-semibold">{{ group.name }}</span>
            <button
              class="btn btn-sm btn-outline-light"
              @click="ensureGroupMatches(group)"
              :disabled="(groupMatches[group.name] || []).length > 0 || group.teams.length < 2"
            >
              Gruppenspiele
            </button>
          </div>

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
                    :class="getRowClass(idx)"
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
                  <tr v-if="getFinalStandings(group.name).length === 0">
                    <td colspan="8" class="text-center text-light">Noch keine Daten</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <div
            v-if="(groupMatches[group.name] || []).length"
            class="card-footer border-top border-secondary bg-dark"
          >
            <p class="text-secondary small mb-2">
              Spiele ({{ (groupMatches[group.name] || []).length }}) – Becher anklicken, um zu erhöhen.
            </p>

            <div
              v-for="(m, idx) in groupMatches[group.name]"
              :key="group.name + '-' + idx"
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
                    :max="cupsTarget"
                  />
                </div>
                <span class="text-secondary">vs</span>
                <div class="flex-fill d-flex align-items-center justify-content-between gap-2">
                  <input
                    type="number"
                    class="form-control form-control-sm cups-input"
                    style="width:70px;"
                    :value="m.cups_team2 ?? 0"
                    @input="setCups(group.name, idx, 'team2', $event.target.value)"
                    min="0"
                    :max="cupsTarget"
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
          <!-- /Matches -->
        </div>
      </div>
    </div>

    <div class="card bg-dark border-secondary my-4" v-if="renderGroups.length">
      <div class="card-header bg-dark border-secondary d-flex align-items-center justify-content-between">
        <strong>Play-In / KO-Vorbereitung</strong>
        <div class="d-flex gap-2">
          <button class="btn btn-outline-light btn-sm" @click="recalculateTables">Tabellen berechnen</button>
          <button class="btn btn-success btn-sm" @click="computePlayInLocal" :disabled="teamsDone < 2">Play-In prüfen</button>
        </div>
      </div>
      <div class="card-body">
        <div v-if="playInResult" class="mb-3">
          <div class="mb-2">
            <span class="badge bg-secondary">Ergebnis</span>
          </div>
          <div class="row g-3">
            <div class="col-md-4">
              <div class="card bg-dark border-secondary h-100">
                <div class="card-body">
                  <div class="fw-bold text-white mb-2">Direkt qualifiziert</div>
                  <div class="d-flex flex-wrap gap-1">
                    <span v-for="t in playInResult.direct_qualified" :key="t" class="badge bg-success">{{ t }}</span>
                    <span v-if="playInResult.direct_qualified?.length === 0" class="text-light">–</span>
                  </div>
                </div>
              </div>
            </div>
            <div class="col-md-8">
              <div class="card bg-dark border-secondary h-100">
                <div class="card-body">
                  <div class="fw-bold text-white mb-2">Play-In</div>
                  <div v-if="(playInResult.playin_matches?.length || 0) > 0" class="mb-2">
                    <div
                      v-for="(m, idx) in playInResult.playin_matches"
                      :key="m.match_id || idx"
                      class="d-flex align-items-center gap-2 mb-2"
                    >
                      <span class="badge bg-secondary flex-grow-1 text-start">{{ m.team1 }}</span>
                      <span class="text-light">vs</span>
                      <span class="badge bg-secondary flex-grow-1 text-start">{{ m.team2 }}</span>
                    </div>
                  </div>
                  <div v-else-if="(playInResult.rage_cage_groups?.length || 0) > 0" class="mb-2">
                    <div
                      v-for="(rc, i) in playInResult.rage_cage_groups"
                      :key="'rc'+i"
                      class="alert alert-dark border-warning"
                    >
                      <div class="text-warning fw-bold mb-2">Rage-Cage</div>
                      <div class="d-flex flex-wrap gap-1">
                        <span v-for="t in rc.teams" :key="t" class="badge bg-secondary">{{ t }}</span>
                      </div>
                      <div class="small text-light mt-2">{{ rc.note }}</div>
                    </div>
                  </div>
                  <div v-else class="text-light">Kein Play-In notwendig.</div>
                </div>
              </div>
            </div>
          </div>

          <div v-if="(playInResult.policy_notes?.length || 0) > 0" class="alert alert-dark border-secondary mt-3">
            <ul class="mb-0">
              <li v-for="(n, i) in playInResult.policy_notes" :key="i">{{ n }}</li>
            </ul>
          </div>
        </div>

        <div class="d-flex justify-content-end">
          <button class="btn btn-outline-light" @click="$emit('back')">Zurück</button>
          <button class="btn btn-success ms-2" @click="goNext" :disabled="!canProceedKo">Weiter (KO/Play-In)</button>
        </div>
      </div>
    </div>

    <div class="mt-4 p-3 border border-secondary rounded">
      <h6>ℹ️ Tiebreak-Regeln</h6>
      <p class="mb-1 text-secondary"><strong>3 Teams:</strong> Rage-Cage oder Mini-Runde.</p>
      <p class="mb-1 text-secondary"><strong>4 Teams:</strong> Schnell-Tiebreak (2×HF, Winners- & Losers-Final).</p>
      <p class="mb-0 text-secondary"><strong>≥5 Teams:</strong> Mini-Runde.</p>
    </div>
  </section>
</template>

<script setup>
import { ref, computed, watchEffect } from 'vue'

/** Gemeinsame API-Base (wie in App.vue) */
const API = import.meta.env.VITE_API_BASE || 'http://localhost:5000'

/** Props aus App.vue */
const props = defineProps({
  tournamentId: { type: Number, required: true },
  tournament:   { type: Object, required: true },
  teams:        { type: Array,  required: true }, // Array<string>
})

const emit = defineEmits([
  'back',
  'create-ko',
  'update:group-matches',
])

/** Lokaler State */
const loading = ref(false)
const groupMatches = ref({})     // { "Gruppe A":[{...match}, ...], ... }
const playInResult = ref(null)   // lokales Ergebnis
const lastGroupsMeta = ref([])   // {name,size,teams[]}

/** Cups-Target */
const cupsTarget = computed(() => {
  const v = Number(props.tournament?.cupsPerGame || 6)
  return Number.isNaN(v) ? 6 : v
})

/** Anzahl Teams */
const teamsDone = computed(() => props.teams?.length || 0)

/** Clientseitige Vorschau aus übergebenen Teams */
const autoGroupsPreview = computed(() => {
  const n = props.teams.length
  const g = groupCountByBand(n)
  const names = computeGroupNames(g)
  return names.map((name, i) => {
    const inGroup = []
    for (let j = i; j < props.teams.length; j += g) inGroup.push(props.teams[j])
    return { name, teams: inGroup }
  })
})

/**
 * Sichtbare Gruppen:
 * - Falls Matches vorhanden sind, UNION aus (Meta bzw. Preview) und Gruppen mit Matches.
 *   So bleiben alle Karten sichtbar, auch wenn nur eine Gruppe Matches hat.
 */
const renderGroups = computed(() => {
  const gm = groupMatches.value
  const gmKeys = Object.keys(gm)
  const meta = (lastGroupsMeta.value?.length ? lastGroupsMeta.value : autoGroupsPreview.value)

  if (gmKeys.length === 0) return meta

  const allNames = Array.from(new Set([
    ...meta.map(g => g.name),
    ...gmKeys
  ])).sort((a, b) => a.localeCompare(b, 'de'))

  return allNames.map(name => {
    const ms = gm[name] || []
    if (ms.length > 0) {
      const set = new Set()
      for (const m of ms) { if (m.team1) set.add(m.team1); if (m.team2) set.add(m.team2) }
      return { name, teams: Array.from(set) }
    } else {
      const g = meta.find(x => x.name === name)
      return { name, teams: g?.teams ?? [] }
    }
  })
})

/** Backend laden (nur per Button, kein Auto-Load beim Mount) */
async function reloadAll() {
  if (!props.tournamentId) return
  loading.value = true
  try {
    const res = await fetch(`${API}/tournaments/${props.tournamentId}/load-all-data`)
    if (!res.ok) throw new Error('load-all-data failed')
    const data = await res.json()

    const gp = data.group_phase || {}
    const mapped = {}
    let groupsList = []

    if (Array.isArray(gp.groups)) {
      groupsList = gp.groups
    }
    if (gp && gp.matches && typeof gp.matches === 'object') {
      Object.entries(gp.matches).forEach(([g, ms]) => {
        mapped[g] = normalizeMatches(ms || [])
      })
    }

    // Wenn nichts gespeichert ist, nutzen wir die Vorschau nur zur Anzeige/Meta
    if (Object.keys(mapped).length === 0 && autoGroupsPreview.value.length > 0) {
      groupsList = autoGroupsPreview.value.map(g => ({ name: g.name, size: g.teams.length, teams: g.teams }))
    }

    groupMatches.value = mapped
    lastGroupsMeta.value = groupsList
    playInResult.value = null
    emit('update:group-matches', mapped)
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

/** Speichern */
async function saveGroupPhase() {
  const groupsMeta = buildGroupsMetaFromMatches()
  const payload = {
    groups: groupsMeta,
    matches: Object.fromEntries(Object.entries(groupMatches.value).map(([g, ms]) => [g, ms])),
  }
  try {
    loading.value = true
    const res = await fetch(`${API}/tournaments/${props.tournamentId}/save-group-phase`, {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify(payload)
    })
    if (!res.ok) throw new Error('save-group-phase failed')
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

/** Gruppen automatisch erzeugen */
function generateGroupsFromTeams() {
  const preview = autoGroupsPreview.value
  const out = {}
  preview.forEach(g => {
    out[g.name] = roundRobin(g.teams).map((m, idx) => ({
      id: `${g.name}-${idx+1}`,
      group_name: g.name,
      team1: m[0],
      team2: m[1],
      cups_team1: 0,
      cups_team2: 0,
      winner: null,
      order_index: idx,
    }))
  })
  groupMatches.value = out
  playInResult.value = null
  lastGroupsMeta.value = preview.map(g => ({ name: g.name, size: g.teams.length, teams: g.teams }))
  emit('update:group-matches', out)
}

/** Gruppenspiele für EINZELNE Gruppe sicherstellen */
function ensureGroupMatches(group) {
  // Falls wir noch keine Meta haben, aus Preview ableiten (damit andere Karten sichtbar bleiben)
  if (!lastGroupsMeta.value?.length && autoGroupsPreview.value?.length) {
    lastGroupsMeta.value = autoGroupsPreview.value.map(g => ({ name: g.name, size: g.teams.length, teams: g.teams }))
  }

  const name = group.name
  if ((groupMatches.value[name] || []).length > 0) return
  const teams = group.teams || []
  const ms = roundRobin(teams).map((m, idx) => ({
    id: `${name}-${idx+1}`,
    group_name: name,
    team1: m[0],
    team2: m[1],
    cups_team1: 0,
    cups_team2: 0,
    winner: null,
    order_index: idx,
  }))
  groupMatches.value = { ...groupMatches.value, [name]: ms }
  emit('update:group-matches', groupMatches.value)
}

/** Tabellen & Play-In */
function buildTablesForAllGroups() {
  const out = {}
  for (const g of renderGroups.value.map(x => x.name)) {
    out[g] = computeGroupTable(groupMatches.value[g] || [])
  }
  return out
}
function recalculateTables() {
  buildTablesForAllGroups()
}
function computePlayInLocal() {
  const tables = buildTablesForAllGroups()
  const groupNames = Object.keys(tables)
  const directQualified = []
  const thirdPlaces = []
  const fourthPlaces = []

  for (const g of groupNames) {
    const rows = tables[g] || []
    if (rows[0]) directQualified.push(rows[0].name)
    if (rows[1]) directQualified.push(rows[1].name)
    if (rows[2]) thirdPlaces.push(rows[2])
    if (rows[3]) fourthPlaces.push(rows[3])
  }

  const qualified = directQualified.length
  const koSize = chooseKoSize(qualified)
  const slotsNeeded = Math.max(0, koSize - qualified)

  let candidates = [...thirdPlaces, ...fourthPlaces]
  candidates.sort((a, b) => {
    if (b.points !== a.points) return b.points - a.points
    if (b.cupsDiff !== a.cupsDiff) return b.cupsDiff - a.cupsDiff
    if (b.cupsFor !== a.cupsFor) return b.cupsFor - a.cupsFor
    return a.name.localeCompare(b.name, 'de')
  })

  const neededCandidates = slotsNeeded * 2
  const selected = candidates.slice(0, neededCandidates)

  const playin_matches = []
  for (let i = 0; i < selected.length; i += 2) {
    if (selected[i+1]) {
      playin_matches.push({
        match_id: i/2 + 1,
        team1: selected[i].name,
        team2: selected[i+1].name
      })
    }
  }

  const notes = []
  if (slotsNeeded > 0) {
    notes.push(`Es werden ${slotsNeeded} Play-In-Platz/Plätze benötigt, um auf ${koSize} KO-Teams zu kommen.`)
    if (selected.length < neededCandidates) {
      notes.push('Zu wenige Kandidaten vorhanden – fehlende Plätze müssen per Sonderregel (Rage-Cage o. ä.) vergeben werden.')
    }
  } else {
    notes.push('Kein Play-In nötig – alle Direktqualifizierten füllen die KO-Größe.')
  }

  playInResult.value = {
    playin_needed: slotsNeeded > 0,
    ko_size: koSize,
    direct_qualified: directQualified,
    playin_matches,
    rage_cage_groups: [],
    policy_notes: notes
  }
}

/** Weitergabe an App.vue */
const canProceedKo = computed(() => Object.keys(groupMatches.value).length > 0)
function goNext() {
  const tables = buildTablesForAllGroups()
  emit('create-ko', {
    tables,
    playIn: playInResult.value || null,
    cupsTarget: cupsTarget.value,
    koSize: playInResult.value?.ko_size
  })
}

/** Utils */
function normalizeMatches(list) {
  return (list || []).map((m, idx) => ({
    id: m.id ?? `${m.group_name || 'G'}-${idx+1}`,
    group_name: m.group_name ?? guessGroupNameFromId(m.id) ?? '',
    team1: m.team1,
    team2: m.team2,
    cups_team1: Number.isFinite(+m.cups_team1) ? +m.cups_team1 : 0,
    cups_team2: Number.isFinite(+m.cups_team2) ? +m.cups_team2 : 0,
    winner: m.winner ?? null,
    order_index: m.order_index ?? idx
  }))
}
function guessGroupNameFromId(id) {
  if (!id || typeof id !== 'string') return null
  const m = id.match(/^(Gruppe [A-Z])/)
  return m ? m[1] : null
}
function roundRobin(arr) {
  const a = (arr || []).filter(Boolean)
  const ms = []
  for (let i = 0; i < a.length; i++) {
    for (let j = i + 1; j < a.length; j++) {
      ms.push([a[i], a[j]])
    }
  }
  return ms
}
function groupCountByBand(n) {
  if (n <= 4) return 1
  if (n <= 8) return 2
  if (n <= 11) return 3
  if (n <= 16) return 4
  return Math.max(4, Math.round(n / 4.5))
}
function computeGroupNames(g) {
  return Array.from({ length: g }, (_, i) => `Gruppe ${String.fromCharCode(65 + i)}`)
}
function computeGroupTable(matches) {
  const rows = new Map()
  const ensure = (name) => {
    if (!rows.has(name)) {
      rows.set(name, { name, wins: 0, losses: 0, points: 0, cupsFor: 0, cupsAgainst: 0, cupsDiff: 0 })
    }
    return rows.get(name)
  }
  for (const m of matches) {
    if (!m.team1 || !m.team2) continue
    const a = ensure(m.team1)
    const b = ensure(m.team2)
    const c1 = Number(m.cups_team1 || 0)
    const c2 = Number(m.cups_team2 || 0)
    a.cupsFor += c1; a.cupsAgainst += c2
    b.cupsFor += c2; b.cupsAgainst += c1
    if (m.winner === m.team1) { a.wins++; b.losses++; a.points += 2 }
    else if (m.winner === m.team2) { b.wins++; a.losses++; b.points += 2 }
  }
  for (const r of rows.values()) r.cupsDiff = r.cupsFor - r.cupsAgainst
  return Array.from(rows.values()).sort((x, y) => {
    if (y.points !== x.points) return y.points - x.points
    if (y.cupsDiff !== x.cupsDiff) return y.cupsDiff - x.cupsDiff
    if (y.cupsFor !== x.cupsFor) return y.cupsFor - x.cupsFor
    return x.name.localeCompare(y.name, 'de')
  })
}
function getFinalStandings(groupName) {
  return computeGroupTable(groupMatches.value[groupName] || [])
}
function getRowClass(idx) {
  if (idx < 2) return 'table-success'
  return ''
}

/** Meta immer initialisieren, wenn noch leer und Preview vorhanden */
watchEffect(() => {
  if (!lastGroupsMeta.value?.length && autoGroupsPreview.value?.length) {
    lastGroupsMeta.value = autoGroupsPreview.value.map(g => ({ name: g.name, size: g.teams.length, teams: g.teams }))
  }
})

/** KEIN auto-reload beim Mount – nur auf Button! */
</script>

<style scoped>
.match-entry { background: rgba(255, 255, 255, 0.05); }
.cups-input { background: rgba(0, 0, 0, 0.3); border: 1px solid #6c757d; color: white; }
.cups-input:focus { background: rgba(0, 0, 0, 0.5); border-color: #0d6efd; color: white; }

.table-responsive { font-size: 0.875rem; }
.table-success { background-color: rgba(25, 135, 84, 0.15) !important; }
.table-hover tbody tr:hover { background-color: rgba(255, 255, 255, 0.075) !important; }

@media (max-width: 768px) {
  .table-responsive { font-size: 0.8rem; }
  .cups-input { width: 50px !important; }
}
</style>
