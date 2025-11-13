<template>
  <div class="card bg-dark border-0">
    <div class="table-responsive">
      <table class="table table-dark align-middle mb-0">
        <thead>
          <tr>
            <th style="width: 48px;">#</th>
            <th>Team 1</th>
            <th class="text-center" style="width: 220px;">B+ Team 1</th>
            <th class="text-center" style="width: 80px;">Gewinner</th>
            <th class="text-center" style="width: 220px;">B+ Team 2</th>
            <th>Team 2</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="(m, idx) in local"
            :key="m.id ?? (groupName + '-' + idx)"
            :class="rowClass(m)"
          >
            <td class="text-light">{{ idx + 1 }}</td>

            <td class="fw-semibold text-truncate" style="max-width: 160px;" :title="m.team1">{{ m.team1 }}</td>

            <td class="text-center">
              <div class="btn-group btn-group-sm" role="group">
                <button class="btn btn-outline-light" @click="dec(idx, 'cups_team1')">−</button>
                <input
                  class="form-control form-control-sm bg-dark text-light border-secondary text-center"
                  style="width: 70px;"
                  type="number"
                  :min="0"
                  :max="cupsTarget"
                  :value="safeNum(m.cups_team1)"
                  @input="onInput(idx, 'cups_team1', $event.target.value)"
                />
                <button class="btn btn-outline-light" @click="inc(idx, 'cups_team1')">+</button>
              </div>
            </td>

            <td class="text-center">
              <span v-if="m.winner === m.team1" class="badge bg-success">T1</span>
              <span v-else-if="m.winner === m.team2" class="badge bg-success">T2</span>
              <button v-else class="btn btn-sm btn-outline-secondary" @click="decide(idx)">entscheiden</button>
            </td>

            <td class="text-center">
              <div class="btn-group btn-group-sm" role="group">
                <button class="btn btn-outline-light" @click="dec(idx, 'cups_team2')">−</button>
                <input
                  class="form-control form-control-sm bg-dark text-light border-secondary text-center"
                  style="width: 70px;"
                  type="number"
                  :min="0"
                  :max="cupsTarget"
                  :value="safeNum(m.cups_team2)"
                  @input="onInput(idx, 'cups_team2', $event.target.value)"
                />
                <button class="btn btn-outline-light" @click="inc(idx, 'cups_team2')">+</button>
              </div>
            </td>

            <td class="fw-semibold text-truncate text-end" style="max-width: 160px;" :title="m.team2">{{ m.team2 }}</td>
          </tr>

          <tr v-if="local.length === 0">
            <td colspan="6" class="text-center text-light">Keine Spiele erzeugt</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { reactive, watch, toRaw } from 'vue'

const props = defineProps({
  groupName: { type: String, required: true },
  cupsTarget: { type: Number, required: true },
  matches: { type: Array, default: () => [] }
})
const emit = defineEmits(['update:matches'])

const local = reactive(props.matches.map(normalize))

watch(() => props.matches, (v) => {
  // ersetzen (kein merge), damit Reihenfolge stabil bleibt
  while (local.length) local.pop()
  for (const m of (v || [])) local.push(normalize(m))
}, { deep: true })

function safeNum(v) {
  const n = Number(v)
  return Number.isFinite(n) ? n : 0
}

function clamp(n, min, max) {
  return Math.max(min, Math.min(max, n))
}

function normalize(m, idx = 0) {
  return {
    id: m.id ?? `${props.groupName}-${idx+1}`,
    group_name: m.group_name ?? props.groupName,
    team1: m.team1 ?? '',
    team2: m.team2 ?? '',
    cups_team1: safeNum(m.cups_team1),
    cups_team2: safeNum(m.cups_team2),
    winner: m.winner ?? null,
    order_index: m.order_index ?? idx
  }
}

function updateAndEmit() {
  // Winner-Automatismus: wer cupsTarget erreicht, gewinnt
  for (const m of local) {
    if (safeNum(m.cups_team1) >= props.cupsTarget && safeNum(m.cups_team2) < props.cupsTarget) {
      m.winner = m.team1
    } else if (safeNum(m.cups_team2) >= props.cupsTarget && safeNum(m.cups_team1) < props.cupsTarget) {
      m.winner = m.team2
    } else if (safeNum(m.cups_team1) === safeNum(m.cups_team2)) {
      // Gleichstand ohne Zielerreichung → kein Gewinner
      if (safeNum(m.cups_team1) < props.cupsTarget) m.winner = null
    }
  }
  emit('update:matches', local.map(x => ({ ...toRaw(x) })))
}

function inc(idx, field) {
  const m = local[idx]
  m[field] = clamp(safeNum(m[field]) + 1, 0, props.cupsTarget)
  updateAndEmit()
}

function dec(idx, field) {
  const m = local[idx]
  m[field] = clamp(safeNum(m[field]) - 1, 0, props.cupsTarget)
  updateAndEmit()
}

function onInput(idx, field, val) {
  const m = local[idx]
  const n = clamp(Number(val || 0), 0, props.cupsTarget)
  m[field] = Number.isFinite(n) ? n : 0
  updateAndEmit()
}

function decide(idx) {
  const m = local[idx]
  // simple decision: wer aktuell mehr hat (falls cupsTarget nicht erreicht)
  const c1 = safeNum(m.cups_team1), c2 = safeNum(m.cups_team2)
  if (c1 === c2) return // keine Änderung
  m.winner = c1 > c2 ? m.team1 : m.team2
  updateAndEmit()
}

function rowClass(m) {
  if (m.winner === m.team1) return 'table-success'
  if (m.winner === m.team2) return 'table-success'
  return ''
}
</script>

<style scoped>
.table-success {
  background-color: rgba(25, 135, 84, 0.12) !important;
}
</style>
