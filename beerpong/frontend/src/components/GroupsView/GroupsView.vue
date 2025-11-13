<template>
  <section class="mx-auto" style="max-width: 1400px;">
    <!-- Kopf -->
    <div class="d-flex justify-content-between align-items-center mb-2">
      <h2 class="mb-0">Gruppenphase</h2>
      <div class="d-flex align-items-center gap-3">
        <small v-if="saveState === 'saving'" class="text-info">Speichere…</small>
        <small v-else-if="saveState === 'saved'" class="text-success">Gespeichert</small>
        <small v-else-if="saveState === 'error'" class="text-danger">Speichern fehlgeschlagen</small>
        <button class="btn btn-outline-light" @click="$emit('back')">Zur Startseite</button>
        <button class="btn btn-outline-light" @click="reloadAll" :disabled="loading">Daten laden</button>
        <button class="btn btn-primary" :disabled="!canProceedKo" @click="goNext">
          Weiter (KO/Play-In)
        </button>
      </div>
    </div>

    <!-- Turnier-Info -->
    <div class="card bg-dark border-secondary mb-4 text-light">
      <div class="card-body py-3">
        <div class="row">
          <div class="col-md-4">
            <strong>Teilnehmer:</strong>
            {{ (tournament?.participantCount ?? tournament?.participant_count) ?? teams.length }} Teams
          </div>
          <div class="col-md-4"><strong>Becher pro Spiel:</strong> {{ cupsTarget }}</div>
          <div class="col-md-4"><strong>Gruppen (Vorschau):</strong> {{ autoGroupsPreview.length || '–' }}</div>
        </div>
        <div class="mt-2">
          <button class="btn btn-sm btn-outline-light" @click="generateGroupsFromTeams" :disabled="loading">
            Gruppen automatisch erzeugen
          </button>
          <button
            class="btn btn-sm btn-outline-secondary ms-2"
            @click="saveGroupPhase"
            :disabled="loading || renderGroups.length === 0"
          >
            Gruppenphase speichern
          </button>
        </div>
      </div>
    </div>

    <!-- Ladehinweise -->
    <div v-if="loading" class="alert alert-dark border-secondary my-3">Lade…</div>
    <div v-else-if="renderGroups.length === 0" class="alert alert-dark border-secondary my-3">
      Noch keine Gruppendaten. Klicke auf „Gruppen automatisch erzeugen“.
    </div>

    <!-- Kartenraster -->
    <div class="row g-4">
      <div v-for="group in renderGroups" :key="group.name" class="col-xl-4 col-lg-6">
        <div class="card bg-dark text-light border-secondary h-100 d-flex flex-column">
          <!-- Header -->
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
                    :class="getRowClass(idx)"
                  >
                    <td class="ps-3 fw-bold">{{ idx + 1 }}.</td>
                    <td class="text-truncate" style="max-width: 160px;" :title="row.name">
                      {{ formatTeamName(row.name, 26) }}
                      <span
                        v-if="markTiebreak(group.name, idx)"
                        class="badge bg-warning text-dark ms-1"
                        title="Teil der Tiebreak-Konstellation"
                      >
                        TB
                      </span>
                    </td>
                    <td class="text-center fw-bold">{{ row.points }}</td>
                    <td class="text-center text-success">{{ row.wins }}</td>
                    <td class="text-center text-danger">{{ row.losses }}</td>
                    <td class="text-center">{{ row.cupsFor }}</td>
                    <td class="text-center">{{ row.cupsAgainst }}</td>
                    <td
                      class="text-center"
                      :class="{
                        'text-success': row.cupsDiff > 0,
                        'text-danger': row.cupsDiff < 0
                      }"
                    >
                      {{ row.cupsDiff > 0 ? '+' : '' }}{{ row.cupsDiff }}
                    </td>
                  </tr>
                  <tr v-if="getFinalStandings(group.name).length === 0">
                    <td colspan="8" class="text-center text-light">Noch keine Daten</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <!-- Tiebreak-Hinweis (nur nach Gruppen-Abschluss) -->
            <div v-if="perGroupTiebreak[group.name]" class="p-3 border-top border-secondary small">
              <div v-if="perGroupTiebreak[group.name].type === 'RAGE_CAGE_3'" class="text-warning">
                <strong>Tiebreak:</strong> Rage Cage (exakter 3er-Gleichstand in 3er-Gruppe).
              </div>
              <div v-else-if="perGroupTiebreak[group.name].type === 'REMATCH_3_OF_4'" class="text-info">
                <strong>Tiebreak:</strong> Mini-Rematch (3 Becher) zwischen Plätzen 2–4 (4er-Gruppe).
              </div>
            </div>
          </div>

          <!-- Matches -->
          <div
            v-if="(groupMatches[group.name] || []).length"
            class="card-footer border-top border-secondary bg-dark"
          >
            <p class="text-secondary small mb-2">
              Spiele ({{ (groupMatches[group.name] || []).length }}) – Becher anklicken, um zu erhöhen.
              <span
                class="ms-2"
                :class="isGroupComplete(group.name) ? 'text-success' : 'text-warning'"
              >
                {{ isGroupComplete(group.name) ? 'Gruppe abgeschlossen' : 'Gruppe noch nicht abgeschlossen' }}
              </span>
            </p>

            <div
              v-for="(m, idx) in groupMatches[group.name]"
              :key="m.id || (group.name + '-' + idx)"
              class="match-entry mb-3 p-2 border border-secondary rounded"
            >
              <div class="d-flex align-items-center justify-content-between gap-2">
                <div class="flex-fill d-flex align-items-center justify-content-between gap-2">
                  <button
                    class="btn btn-sm d-flex align-items-center gap-2 match-team-btn"
                    :class="m.winner === m.team1 ? 'btn-success' : 'btn-outline-light'"
                    @click="incrementCups(group.name, idx, 'team1')"
                    :title="`+1 Becher für ${m.team1}`"
                  >
                    <img src="/beer-cup.svg" alt="" width="18" height="18" />
                    <span class="match-team-name">
                      {{ formatTeamName(m.team1) }}
                    </span>
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
                    class="btn btn-sm d-flex align-items-center gap-2 match-team-btn"
                    :class="m.winner === m.team2 ? 'btn-success' : 'btn-outline-light'"
                    @click="incrementCups(group.name, idx, 'team2')"
                    :title="`+1 Becher für ${m.team2}`"
                  >
                    <img src="/beer-cup.svg" alt="" width="18" height="18" />
                    <span class="match-team-name">
                      {{ formatTeamName(m.team2) }}
                    </span>
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

    <!-- Play-In/KO-Block -->
    <div class="card bg-dark border-secondary my-4" v-if="renderGroups.length">
      <div class="card-header bg-dark border-secondary d-flex align-items-center justify-content-between">
        <strong>Play-In / KO-Vorbereitung</strong>
        <div class="d-flex gap-2">
          <button class="btn btn-outline-light btn-sm" @click="recalculateTables">
            Tabellen berechnen
          </button>
          <button
            class="btn btn-success btn-sm"
            @click="computePlayInLocal"
            :disabled="teamsDone < 2"
          >
            Play-In prüfen
          </button>
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
                    <span
                      v-for="t in playInResult.direct_qualified"
                      :key="t"
                      class="badge bg-success"
                    >
                      {{ t }}
                    </span>
                    <span
                      v-if="playInResult.direct_qualified?.length === 0"
                      class="text-light"
                    >
                      –
                    </span>
                  </div>
                </div>
              </div>
            </div>

            <!-- Play-In Matches ODER Rage-Cage-Gruppen -->
            <div class="col-md-8">
              <div class="card bg-dark border-secondary h-100">
                <div class="card-body">
                  <div class="fw-bold text-white mb-2">Play-In</div>

                  <template v-if="(playInResult.playin_matches?.length || 0) > 0">
                    <div
                      v-for="(m, idx) in playInResult.playin_matches"
                      :key="m.match_id || idx"
                      class="d-flex align-items-center gap-2 mb-2"
                    >
                      <span class="badge bg-secondary flex-grow-1 text-start">{{ m.team1 }}</span>
                      <span class="text-light">vs</span>
                      <span class="badge bg-secondary flex-grow-1 text-start">{{ m.team2 }}</span>
                      <span
                        class="badge bg-dark border border-secondary"
                        :title="m.cups_per_game ? `Becher pro Spiel: ${m.cups_per_game}` : 'Standard'"
                      >
                        {{ m.cups_per_game || cupsTarget }} B.
                      </span>
                    </div>
                  </template>

                  <template v-else-if="(playInResult.rage_cage_groups?.length || 0) > 0">
                    <div
                      v-for="(rc, i) in playInResult.rage_cage_groups"
                      :key="'rc' + i"
                      class="alert alert-dark border-warning"
                    >
                      <div class="text-warning fw-bold mb-2">Rage-Cage</div>
                      <div class="d-flex flex-wrap gap-1">
                        <span v-for="t in rc.teams" :key="t" class="badge bg-secondary">
                          {{ t }}
                        </span>
                      </div>
                      <div class="small text-light mt-2">{{ rc.note }}</div>
                    </div>
                  </template>

                  <div v-else class="text-light">
                    <span v-if="(playInResult.auto_advanced?.length || 0) > 0">
                      Automatisch weiter:
                      <span
                        class="badge bg-success ms-1"
                        v-for="t in playInResult.auto_advanced"
                        :key="t"
                      >
                        {{ t }}
                      </span>
                    </span>
                    <span v-else>Kein Play-In notwendig.</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Tiebreak-Pläne (gruppenlokal) -->
          <div
            v-if="(playInResult.tiebreaks?.length || 0) > 0"
            class="card bg-dark border-secondary mt-3"
          >
            <div class="card-header bg-dark border-secondary text-light">
              <strong>Tiebreak-Pläne</strong>
            </div>
            <div class="card-body">
              <div v-for="(tb, i) in playInResult.tiebreaks" :key="i" class="mb-3">
                <div class="fw-semibold text-white mb-1">
                  {{ tb.group }}:
                  <span
                    v-if="tb.type === 'RAGE_CAGE_3'"
                    class="text-warning"
                  >
                    Rage Cage (3er-Gruppe)
                  </span>
                  <span
                    v-else-if="tb.type === 'REMATCH_3_OF_4'"
                    class="text-info"
                  >
                    Mini-Rematch (3 Becher) für Plätze 2–4
                  </span>
                </div>

                <div
                  v-if="tb.type === 'RAGE_CAGE_3'"
                  class="text-secondary small"
                >
                  Teams: {{ tb.teams.join(', ') }} → Letzter im Rage Cage = Gruppen-Letzter.
                </div>

                <div v-else-if="tb.type === 'REMATCH_3_OF_4'">
                  <div class="text-secondary small mb-2">
                    Spiele (3 Becher): jeder gegen jeden
                  </div>
                  <div class="d-flex flex-column gap-1">
                    <div
                      v-for="(m, k) in tb.rematch_matches"
                      :key="k"
                      class="d-flex align-items-center gap-2"
                    >
                      <span class="badge bg-secondary">{{ m.team1 }}</span>
                      <span class="text-light">vs</span>
                      <span class="badge bg-secondary">{{ m.team2 }}</span>
                      <span class="badge bg-dark border border-secondary">
                        {{ m.cups_per_game }} B.
                      </span>
                    </div>
                  </div>
                  <div class="text-secondary small mt-2">
                    Falls erneut exakt gleich: Rage Cage für diese drei → letzter = Platz 4;
                    danach 1 Tiebreak-Match (3 Becher) zwischen den verbleibenden zwei um Platz 2/3.
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div
            v-if="(playInResult.policy_notes?.length || 0) > 0"
            class="alert alert-dark border-secondary mt-3"
          >
            <ul class="mb-0">
              <li v-for="(n, i) in playInResult.policy_notes" :key="i">{{ n }}</li>
            </ul>
          </div>
        </div>

        <div class="d-flex justify-content-end">
          <button class="btn btn-outline-light" @click="$emit('back')">Zurück</button>
          <button
            class="btn btn-success ms-2"
            @click="goNext"
            :disabled="!canProceedKo"
          >
            Weiter (KO/Play-In)
          </button>
        </div>
      </div>
    </div>

    <!-- Info -->
    <div class="mt-4 p-3 border border-secondary rounded">
      <h6>ℹ️ Tiebreak-Regeln</h6>
      <p class="mb-1 text-secondary">
        <strong>3 Teams (exakt gleich):</strong> Rage-Cage – der Letzte wird Gruppen-Letzter.
      </p>
      <p class="mb-1 text-secondary">
        <strong>4 Teams (Plätze 2–4 exakt gleich):</strong> Mini-Rematch (3 Becher, 3 Spiele).
        Bei erneutem exaktem Gleichstand: Rage Cage um den Letzten, danach 1 Tiebreak-Match um Platz 2/3.
      </p>
      <p class="mb-0 text-secondary">
        <strong>Sonst:</strong> Standard-Sortierung: Punkte → Becher-Diff → Becher+ → Name.
      </p>
    </div>
  </section>
</template>

<script setup>
import { ref, computed, onBeforeUnmount, onMounted, watch } from 'vue'

/** API-Base */
const API =
  `${window.location.protocol}//${window.location.hostname}:5001` || import.meta.env.VITE_API_BASE

/** Props */
const props = defineProps({
  tournamentId: { type: Number, required: true },
  tournament: { type: Object, required: true },
  teams: { type: Array, required: true }
})
const emit = defineEmits(['back', 'create-ko', 'update:group-matches'])

/** State */
const loading = ref(false)
const groupMatches = ref({}) // { "Gruppe A":[{...}], ... }
const groupStandingsSrv = ref({}) // { "Gruppe A":[{...}], ... }
const lastGroupsMeta = ref([]) // { name, size, teams[] }
const playInResult = ref(null)

/** pro Gruppe erkannter Tiebreak (nur nach Gruppen-Abschluss) */
const perGroupTiebreak = ref({}) // { "Gruppe A": {type:'RAGE_CAGE_3'| 'REMATCH_3_OF_4', ... } }

/** Save-Status + Timer */
const saveState = ref('idle')
let autosaveTimer = null
const AUTOSAVE_MS = 400

/** Derived */
const cupsTarget = computed(() => {
  const v = Number(props.tournament?.cupsPerGame || 6)
  return Number.isNaN(v) ? 6 : v
})
const teamsDone = computed(() => props.teams?.length || 0)

/** Vorschau aus Teams (Fallback) */
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

/** Sichtbare Gruppen = Union(Meta, Matches) */
const renderGroups = computed(() => {
  const gmKeys = Object.keys(groupMatches.value)
  const meta =
    lastGroupsMeta.value?.length > 0
      ? lastGroupsMeta.value
      : autoGroupsPreview.value
  if (gmKeys.length === 0) return meta

  const allNames = Array.from(
    new Set([...meta.map(g => g.name), ...gmKeys])
  ).sort((a, b) => a.localeCompare(b, 'de'))

  return allNames.map(name => {
    const ms = groupMatches.value[name] || []
    if (ms.length > 0) {
      const set = new Set()
      for (const m of ms) {
        if (m.team1) set.add(m.team1)
        if (m.team2) set.add(m.team2)
      }
      return { name, teams: Array.from(set) }
    } else {
      const g = meta.find(x => x.name === name)
      return { name, teams: g?.teams ?? [] }
    }
  })
})

/* ---------------- Backend I/O ---------------- */

async function reloadAll() {
  if (!props.tournamentId) return
  loading.value = true
  try {
    const res = await fetch(
      `${API}/tournaments/${props.tournamentId}/load-all-data`
    )
    if (!res.ok) throw new Error('load-all-data failed')
    const data = await res.json()

    const gp = data?.group_phase?.group_phase ?? data?.group_phase ?? {}
    const srvMatches = typeof gp.matches === 'object' ? gp.matches : {}
    const srvGroups = Array.isArray(gp.groups) ? gp.groups : []

    groupStandingsSrv.value = normalizeStandingsMap(
      data?.group_standings || {}
    )

    const mapped = {}
    for (const [gName, ms] of Object.entries(srvMatches)) {
      mapped[gName] = normalizeMatches(ms || {})
    }

    const metaByName = {}
    for (const g of srvGroups) {
      metaByName[g.name] = {
        name: g.name,
        teams: Array.isArray(g.teams) ? g.teams.slice() : []
      }
    }
    for (const [gName, rows] of Object.entries(groupStandingsSrv.value)) {
      if (!metaByName[gName]) {
        metaByName[gName] = { name: gName, teams: [] }
      }
      if ((metaByName[gName].teams?.length || 0) === 0) {
        metaByName[gName].teams = rows.map(r => r.name)
      }
    }
    for (const g of autoGroupsPreview.value) {
      if (!metaByName[g.name]) {
        metaByName[g.name] = {
          name: g.name,
          teams: g.teams.slice()
        }
      } else if ((metaByName[g.name].teams?.length || 0) === 0) {
        metaByName[g.name].teams = g.teams.slice()
      }
    }
    for (const old of lastGroupsMeta.value) {
      if (!metaByName[old.name]) {
        metaByName[old.name] = {
          name: old.name,
          teams: old.teams.slice()
        }
      }
      if (
        (metaByName[old.name].teams?.length || 0) <
        (old.teams?.length || 0)
      ) {
        metaByName[old.name].teams = old.teams.slice()
      }
    }

    lastGroupsMeta.value = Object.values(metaByName)
      .map(g => ({
        name: g.name,
        teams: Array.isArray(g.teams) ? g.teams : []
      }))
      .sort((a, b) => a.name.localeCompare(b.name, 'de'))

    groupMatches.value = mapped

    // Tiebreaks neu berechnen – nur für abgeschlossene Gruppen
    perGroupTiebreak.value = computeAllTiebreaksForCompletedGroups()

    emit('update:group-matches', groupMatches.value)
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

async function saveGroupPhase() {
  const payload = {
    group_phase: {
      groups: lastGroupsMeta.value.map(g => ({
        name: g.name,
        size: g.teams.length,
        teams: g.teams
      })),
      matches: Object.fromEntries(
        Object.entries(groupMatches.value).map(([g, ms]) => [g, ms])
      )
    }
  }
  await saveGroupPhasePayload(payload)
}

async function saveGroupPhasePayload(payload) {
  if (!props.tournamentId) return
  try {
    saveState.value = 'saving'
    const res = await fetch(
      `${API}/tournaments/${props.tournamentId}/save-group-phase`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      }
    )
    if (!res.ok) throw new Error('save-group-phase failed')

    // Optimistic UI
    perGroupTiebreak.value = computeAllTiebreaksForCompletedGroups()

    saveState.value = 'saved'
    setTimeout(() => {
      if (saveState.value === 'saved') saveState.value = 'idle'
    }, 800)
  } catch (e) {
    console.error(e)
    saveState.value = 'error'
  }
}

/* Auto-Load */
onMounted(() => {
  reloadAll()
})
watch(
  () => props.tournamentId,
  () => {
    reloadAll()
  }
)

/* Debounced Full Auto-Save */
function scheduleAutoSave() {
  if (autosaveTimer) clearTimeout(autosaveTimer)
  autosaveTimer = setTimeout(() => {
    saveGroupPhase()
  }, AUTOSAVE_MS)
}
onBeforeUnmount(() => {
  if (autosaveTimer) clearTimeout(autosaveTimer)
})

/* --------------- Gruppen/Matches --------------- */

function generateGroupsFromTeams() {
  const preview = autoGroupsPreview.value
  const nextMatches = { ...groupMatches.value }
  for (const g of preview) {
    const name = g.name
    if (!nextMatches[name] || nextMatches[name].length === 0) {
      nextMatches[name] = roundRobin(g.teams).map((m, idx) => ({
        id: `${name}-${idx + 1}`,
        group_name: name,
        team1: m[0],
        team2: m[1],
        cups_team1: 0,
        cups_team2: 0,
        winner: null,
        order_index: idx
      }))
    }
  }
  groupMatches.value = nextMatches

  const metaBy = Object.fromEntries(
    lastGroupsMeta.value.map(g => [
      g.name,
      { ...g, teams: g.teams.slice() }
    ])
  )
  for (const g of preview) {
    if (!metaBy[g.name]) {
      metaBy[g.name] = { name: g.name, teams: g.teams.slice() }
    }
    if (metaBy[g.name].teams.length === 0) {
      metaBy[g.name].teams = g.teams.slice()
    }
  }
  lastGroupsMeta.value = Object.values(metaBy).sort((a, b) =>
    a.name.localeCompare(b.name, 'de')
  )

  emit('update:group-matches', groupMatches.value)
  scheduleAutoSave()
}

function ensureGroupMatches(group) {
  const name = group.name
  if ((groupMatches.value[name] || []).length > 0) return

  let teams = group.teams || []
  if (!teams?.length) {
    const meta = lastGroupsMeta.value.find(g => g.name === name)
    if (meta?.teams?.length) teams = meta.teams
  }
  if (!teams?.length) return

  const ms = roundRobin(teams).map((m, idx) => ({
    id: `${name}-${idx + 1}`,
    group_name: name,
    team1: m[0],
    team2: m[1],
    cups_team1: 0,
    cups_team2: 0,
    winner: null,
    order_index: idx
  }))

  groupMatches.value = { ...groupMatches.value, [name]: ms }
  emit('update:group-matches', groupMatches.value)
  scheduleAutoSave()
}

/* ------------ Eingabe-Handler (lokal + Autosave) ----------- */

function setCups(groupName, matchIndex, teamField, rawValue) {
  const updated = { ...groupMatches.value }
  const list = [...(updated[groupName] || [])]
  const m = { ...list[matchIndex] }

  const v = clampInt(rawValue, 0, cupsTarget.value)
  const key = teamField === 'team1' ? 'cups_team1' : 'cups_team2'
  m[key] = v

  applyWinnerRule(m)
  list[matchIndex] = m
  updated[groupName] = list
  groupMatches.value = updated
  emit('update:group-matches', updated)

  if (isGroupComplete(groupName)) {
    recomputePerGroupTiebreak(groupName)
  } else {
    clearGroupTiebreak(groupName)
  }
  scheduleAutoSave()
}

function incrementCups(groupName, matchIndex, teamKey) {
  const updated = { ...groupMatches.value }
  const list = [...(updated[groupName] || [])]
  const m = { ...list[matchIndex] }

  const field = teamKey === 'team1' ? 'cups_team1' : 'cups_team2'
  m[field] = clampInt(safeNum(m[field]) + 1, 0, cupsTarget.value)

  applyWinnerRule(m)
  list[matchIndex] = m
  updated[groupName] = list
  groupMatches.value = updated
  emit('update:group-matches', updated)

  if (isGroupComplete(groupName)) {
    recomputePerGroupTiebreak(groupName)
  } else {
    clearGroupTiebreak(groupName)
  }
  scheduleAutoSave()
}

/* --------------- Tabellen/Play-In --------------- */

function buildTablesForAllGroups() {
  const out = {}
  for (const g of renderGroups.value.map(x => x.name)) {
    out[g] = getFinalStandings(g)
  }
  return out
}
function recalculateTables() {
  for (const g of renderGroups.value.map(x => x.name)) {
    if (isGroupComplete(g)) recomputePerGroupTiebreak(g)
    else clearGroupTiebreak(g)
  }
}

function chooseKoSize(qualified) {
  const sizes = [4, 8, 16, 32, 64, 128]
  for (const k of sizes) if (k >= qualified) return k
  return qualified
}

function computePlayInLocal() {
  const tables = buildTablesForAllGroups()
  const groupNames = Object.keys(tables)
  const directQualified = []
  const thirdPlaces = []
  const fourthPlaces = []

  const tiebreakPlans = []
  const rageCageGroups = []

  const sizeByGroup = {}
  for (const g of renderGroups.value) sizeByGroup[g.name] = g.teams.length

  for (const g of groupNames) {
    const rows = tables[g] || []

    if (isGroupComplete(g)) {
      const plan = detectGroupTiebreak(g, rows)
      if (plan) {
        tiebreakPlans.push(plan)
        if (plan.type === 'RAGE_CAGE_3') {
          rageCageGroups.push({
            group: g,
            teams: plan.teams.slice(),
            note:
              '3er-Gleichstand (3er-Gruppe): Rage Cage – Letzter scheidet aus.'
          })
        }
      }
    }

    if (rows[0]) directQualified.push(rows[0].name)
    if (rows[1]) directQualified.push(rows[1].name)
    if (rows[2]) thirdPlaces.push(rows[2])
    if (rows[3]) fourthPlaces.push(rows[3])
  }

  const qualified = directQualified.length
  const koSize = chooseKoSize(qualified)
  const slotsNeeded = Math.max(0, koSize - qualified)

  const notes = []
  notes.push(
    `Es werden ${slotsNeeded} zusätzliche Platz/Plätze benötigt, um auf ${koSize} KO-Teams zu kommen.`
  )

  if (slotsNeeded === 0) {
    playInResult.value = {
      playin_needed: false,
      ko_size: koSize,
      direct_qualified: directQualified,
      auto_advanced: [],
      ranking_candidates: [],
      tiebreaks: tiebreakPlans,
      rage_cage_groups: rageCageGroups,
      policy_notes: ['Kein Play-In nötig – alle Plätze gefüllt.']
    }
    return
  }

  const allAreTrios = groupNames.every(
    g => (sizeByGroup[g] || 0) === 3
  )
  let candidateRows = []
  if (allAreTrios) {
    candidateRows = thirdPlaces.slice()
  } else {
    candidateRows = thirdPlaces.slice()
    if (candidateRows.length < slotsNeeded + 1) {
      candidateRows = candidateRows.concat(fourthPlaces)
    }
  }

  const norm = r => ({
    name: String(r?.name || ''),
    points: Number(r?.points || 0),
    cupsDiff: Number(
      (r?.cupsDiff ?? (r?.cupsFor || 0) - (r?.cupsAgainst || 0)) || 0
    ),
    cupsFor: Number(r?.cupsFor || 0)
  })
  const rankDesc = (a, b) => {
    if (b.points !== a.points) return b.points - a.points
    if (b.cupsDiff !== a.cupsDiff) return b.cupsDiff - a.cupsDiff
    if (b.cupsFor !== a.cupsFor) return b.cupsFor - a.cupsFor
    return a.name.localeCompare(b.name, 'de')
  }
  const candidates = candidateRows
    .filter(Boolean)
    .map(norm)
    .sort(rankDesc)

  if (candidates.length < slotsNeeded) {
    playInResult.value = {
      playin_needed: true,
      ko_size: koSize,
      direct_qualified: directQualified,
      ranking_candidates: candidates,
      tiebreaks: tiebreakPlans,
      rage_cage_groups: rageCageGroups,
      playin_matches: [],
      policy_notes: [
        ...notes,
        'Zu wenige Kandidaten vorhanden – bitte manuell entscheiden (Sonderverfahren).'
      ]
    }
    return
  }

  const need = slotsNeeded
  const k = need - 1
  const eq = (x, y) =>
    x &&
    y &&
    x.points === y.points &&
    x.cupsDiff === y.cupsDiff &&
    x.cupsFor === y.cupsFor
  const cutoffTie =
    need > 0 &&
    k >= 0 &&
    k < candidates.length - 1 &&
    eq(candidates[k], candidates[k + 1])

  // Kein Gleichstand am Cut-Off → automatisch weiter
  if (!cutoffTie) {
    const auto = candidates.slice(0, need).map(x => x.name)
    playInResult.value = {
      playin_needed: false,
      ko_size: koSize,
      direct_qualified: directQualified,
      auto_advanced: auto,
      ranking_candidates: candidates,
      tiebreaks: tiebreakPlans,
      rage_cage_groups: rageCageGroups,
      policy_notes: [
        ...notes,
        `Kein Gleichstand am Cut-Off → automatisch weiter: ${auto.join(', ')}.`
      ]
    }
    return
  }

  // Gleichstand am Cut-Off → Verfahren je Größe der Tie-Range
  let s = k
  let e = k + 1
  while (s - 1 >= 0 && eq(candidates[s - 1], candidates[k])) s--
  while (e + 1 < candidates.length && eq(candidates[e + 1], candidates[k]))
    e++
  const tieRange = candidates.slice(s, e + 1)

  const playin_matches = []
  const rage_cutoff_groups = []

  if (tieRange.length === 2) {
    playin_matches.push({
      match_id: 1,
      team1: tieRange[0].name,
      team2: tieRange[1].name,
      cups_per_game: 3
    })
    notes.push(
      'Exakter 2er-Gleichstand am Cut-Off → 1× 1-gegen-1 (3 Becher).'
    )
  } else if (tieRange.length === 3) {
    rage_cutoff_groups.push({
      group: 'Cut-Off',
      teams: tieRange.map(t => t.name),
      note: '3er-Gleichstand: Rage Cage – Letzter scheidet aus.'
    })
    notes.push(
      '3er-Gleichstand am Cut-Off → Rage Cage (1 Team scheidet aus).'
    )
  } else if (tieRange.length === 4) {
    for (let i = 0; i < 4; i += 2) {
      playin_matches.push({
        match_id: i / 2 + 1,
        team1: tieRange[i].name,
        team2: tieRange[i + 1].name,
        cups_per_game: 3
      })
    }
    notes.push(
      '4er-Gleichstand am Cut-Off → 2× 1-gegen-1 (3 Becher), Gewinner weiter.'
    )
  } else if (tieRange.length >= 5) {
    notes.push(
      '5er-Gleichstand am Cut-Off → „Elfmeter“-Modus empfohlen; manuelle Auswahl erforderlich.'
    )
  }

  playInResult.value = {
    playin_needed: true,
    ko_size: koSize,
    direct_qualified: directQualified,
    ranking_candidates: candidates,
    tie_range: tieRange,
    tiebreaks: tiebreakPlans,
    rage_cage_groups: [...rageCageGroups, ...rage_cutoff_groups],
    playin_matches,
    policy_notes: notes
  }
}

/** Weiter */
const canProceedKo = computed(
  () => Object.keys(groupMatches.value).length > 0
)
function goNext() {
  const tables = buildTablesForAllGroups()
  emit('create-ko', {
    tables,
    playIn: playInResult.value || null,
    cupsTarget: cupsTarget.value,
    koSize: playInResult.value?.ko_size
  })
}

/* ---------------- Utils ---------------- */

function normalizeMatches(list) {
  return (list || []).map((m, idx) => ({
    id: m.id ?? `${m.group_name || 'G'}-${idx + 1}`,
    group_name: m.group_name ?? guessGroupNameFromId(m.id) ?? '',
    team1: m.team1,
    team2: m.team2,
    cups_team1: Number.isFinite(+m.cups_team1) ? +m.cups_team1 : 0,
    cups_team2: Number.isFinite(+m.cups_team2) ? +m.cups_team2 : 0,
    winner: m.winner ?? null,
    order_index: m.order_index ?? idx
  }))
}

function normalizeStandingsMap(obj) {
  const out = {}
  for (const [g, rows] of Object.entries(obj || {})) {
    out[g] = (rows || []).map(r => ({
      name: String(r.name ?? ''),
      wins: Number.isFinite(+r.wins) ? +r.wins : 0,
      losses: Number.isFinite(+r.losses) ? +r.losses : 0,
      points: Number.isFinite(+r.points) ? +r.points : 0,
      cupsFor: Number.isFinite(+r.cupsFor) ? +r.cupsFor : 0,
      cupsAgainst: Number.isFinite(+r.cupsAgainst)
        ? +r.cupsAgainst
        : 0,
      cupsDiff: Number.isFinite(+r.cupsDiff)
        ? +r.cupsDiff
        : Number(r.cupsFor || 0) - Number(r.cupsAgainst || 0)
    }))
  }
  return out
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
    for (let j = i + 1; j < a.length; j++) ms.push([a[i], a[j]])
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

/* ----- Abschluss-Logik & Tiebreak nur bei vollständiger Gruppe ----- */

function expectedMatchCountForGroup(groupName) {
  const fromMatches = new Set()
  for (const m of groupMatches.value[groupName] || []) {
    if (m.team1) fromMatches.add(m.team1)
    if (m.team2) fromMatches.add(m.team2)
  }
  let teams = Array.from(fromMatches)
  if (teams.length === 0) {
    const meta = lastGroupsMeta.value.find(g => g.name === groupName)
    if (meta?.teams?.length) teams = meta.teams.slice()
  }
  if (teams.length === 0) {
    const preview = autoGroupsPreview.value.find(g => g.name === groupName)
    if (preview?.teams?.length) teams = preview.teams.slice()
  }
  const n = teams.length
  return n > 1 ? (n * (n - 1)) / 2 : 0
}

function isGroupComplete(groupName) {
  const ms = groupMatches.value[groupName] || []
  const expected = expectedMatchCountForGroup(groupName)
  if (ms.length < expected || expected === 0) return false
  return ms.every(m => !!m.winner)
}

function computeAllTiebreaksForCompletedGroups() {
  const next = {}
  const names = Array.from(
    new Set([
      ...Object.keys(groupMatches.value),
      ...lastGroupsMeta.value.map(g => g.name)
    ])
  )
  for (const g of names) {
    if (!isGroupComplete(g)) continue
    const rows = getFinalStandings(g)
    const plan = detectGroupTiebreak(g, rows)
    if (plan) next[g] = plan
  }
  return next
}

function getFinalStandings(groupName) {
  const matches = groupMatches.value[groupName] || []
  if (matches.length > 0) return computeGroupTable(matches)

  const srv = groupStandingsSrv.value[groupName]
  if (Array.isArray(srv) && srv.length > 0) return srv

  const meta = lastGroupsMeta.value.find(g => g.name === groupName)
  const teams = meta?.teams ?? []
  return teams.map(name => ({
    name,
    wins: 0,
    losses: 0,
    points: 0,
    cupsFor: 0,
    cupsAgainst: 0,
    cupsDiff: 0
  }))
}

function computeGroupTable(matches) {
  const rows = new Map()
  const ensure = name => {
    if (!rows.has(name)) {
      rows.set(name, {
        name,
        wins: 0,
        losses: 0,
        points: 0,
        cupsFor: 0,
        cupsAgainst: 0,
        cupsDiff: 0
      })
    }
    return rows.get(name)
  }
  for (const m of matches) {
    if (!m.team1 || !m.team2) continue
    const a = ensure(m.team1)
    const b = ensure(m.team2)
    const c1 = Number(m.cups_team1 || 0)
    const c2 = Number(m.cups_team2 || 0)
    a.cupsFor += c1
    a.cupsAgainst += c2
    b.cupsFor += c2
    b.cupsAgainst += c1
    if (m.winner === m.team1) {
      a.wins++
      b.losses++
      a.points += 2
    } else if (m.winner === m.team2) {
      b.wins++
      a.losses++
      b.points += 2
    }
  }
  for (const r of rows.values()) {
    r.cupsDiff = r.cupsFor - r.cupsAgainst
  }
  const arr = Array.from(rows.values()).sort((x, y) => {
    if (y.points !== x.points) return y.points - x.points
    if (y.cupsDiff !== x.cupsDiff) return y.cupsDiff - x.cupsDiff
    if (y.cupsFor !== x.cupsFor) return y.cupsFor - x.cupsFor
    return x.name.localeCompare(y.name, 'de')
  })
  return arr
}

function getRowClass(idx) {
  return idx < 2 ? 'table-success' : ''
}
function safeNum(v) {
  const n = Number(v)
  return Number.isFinite(n) ? n : 0
}
function clampInt(v, min, max) {
  const n = parseInt(v, 10)
  const num = Number.isFinite(n) ? n : 0
  return Math.max(min, Math.min(max, num))
}
function applyWinnerRule(m) {
  const a = safeNum(m.cups_team1)
  const b = safeNum(m.cups_team2)
  if (a >= cupsTarget.value || b >= cupsTarget.value) {
    if (a !== b) m.winner = a > b ? m.team1 : m.team2
  } else if (a === b) {
    m.winner = null
  }
}

/* ---------- Tiebreak-Erkennung ---------- */

function equalTripleByPointsDiff([r1, r2, r3]) {
  if (!r1 || !r2 || !r3) return false
  return (
    r1.points === r2.points &&
    r2.points === r3.points &&
    r1.cupsDiff === r2.cupsDiff &&
    r2.cupsDiff === r3.cupsDiff
  )
}

function detectGroupTiebreak(groupName, standings) {
  const meta = lastGroupsMeta.value.find(g => g.name === groupName)
  const size = meta?.teams?.length || standings.length

  if (size === 3 && standings.length >= 3) {
    const [t1, t2, t3] = standings
    if (equalTripleByPointsDiff([t1, t2, t3])) {
      return {
        group: groupName,
        type: 'RAGE_CAGE_3',
        teams: [t1.name, t2.name, t3.name]
      }
    }
  }

  if (size === 4 && standings.length >= 4) {
    const [t1, t2, t3, t4] = standings
    const triple = [t2, t3, t4]
    if (equalTripleByPointsDiff(triple)) {
      const pairs = [
        { team1: t2.name, team2: t3.name },
        { team1: t2.name, team2: t4.name },
        { team1: t3.name, team2: t4.name }
      ].map((m, i) => ({
        ...m,
        cups_per_game: 3,
        match_id: `${groupName}-TB-${i + 1}`
      }))
      return {
        group: groupName,
        type: 'REMATCH_3_OF_4',
        fixed_first: t1.name,
        trio: triple.map(x => x.name),
        rematch_matches: pairs,
        note: 'Plätze 2–4 exakt gleich: Mini-Rematch (3 Becher).'
      }
    }
  }
  return null
}

function recomputePerGroupTiebreak(groupName) {
  const rows = getFinalStandings(groupName)
  const plan = detectGroupTiebreak(groupName, rows)
  const next = { ...perGroupTiebreak.value }
  if (plan) next[groupName] = plan
  else delete next[groupName]
  perGroupTiebreak.value = next
}

function clearGroupTiebreak(groupName) {
  if (!perGroupTiebreak.value[groupName]) return
  const next = { ...perGroupTiebreak.value }
  delete next[groupName]
  perGroupTiebreak.value = next
}

function markTiebreak(groupName, idxInSortedTable) {
  const tb = perGroupTiebreak.value[groupName]
  if (!tb) return false
  if (tb.type === 'RAGE_CAGE_3') return true
  if (tb.type === 'REMATCH_3_OF_4')
    return idxInSortedTable >= 1 && idxInSortedTable <= 3
  return false
}

/** Teamnamen kürzen */
function formatTeamName(name, maxChars = 5) {
  const s = String(name || '').trim()
  if (s.length <= maxChars) return s
  if (maxChars <= 3) return s.slice(0, maxChars)
  return s.slice(0, maxChars - 1) + '…'
}
</script>

<style scoped>
.match-entry {
  background: rgba(255, 255, 255, 0.05);
}

.cups-input {
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid #6c757d;
  color: white;
}
.cups-input:focus {
  background: rgba(0, 0, 0, 0.5);
  border-color: #0d6efd;
  color: white;
}

.match-team-btn {
  flex: 1 1 auto;
}

.match-team-name {
  display: inline-block;
  max-width: 150px;
  font-size: 0.9rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.table-responsive {
  font-size: 0.875rem;
}
.table-success {
  background-color: rgba(25, 135, 84, 0.15) !important;
}
.table-hover tbody tr:hover {
  background-color: rgba(255, 255, 255, 0.075) !important;
}

@media (max-width: 768px) {
  .table-responsive {
    font-size: 0.8rem;
  }
  .cups-input {
    width: 50px !important;
  }
  .match-team-name {
    max-width: 100px;
    font-size: 0.8rem;
  }
}
</style>
