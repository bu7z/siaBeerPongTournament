<template>
  <div class="ko-bracket w-100">
    <div class="row g-3 flex-nowrap overflow-auto">
      <div
        v-for="(round, rIdx) in roundsLocal"
        :key="rIdx"
        class="col"
        style="min-width: 240px;"
      >
        <div class="card bg-dark border-secondary h-100">
          <div class="card-header bg-dark border-bottom border-secondary">
            <strong>{{ round.round_name || defaultRoundName(rIdx, roundsLocal.length) }}</strong>
          </div>

          <div class="card-body">
            <div v-for="(m, mIdx) in round.matches" :key="mIdx" class="mb-3">
              <div class="d-flex flex-column gap-1">
                <button
                  class="btn btn-sm text-start text-truncate"
                  :class="m.winner === m.team1 ? 'btn-success' : 'btn-outline-light'"
                  :disabled="!m.team1"
                  @click="pickWinner(rIdx, mIdx, m.team1)"
                >{{ m.team1 || '—' }}</button>

                <button
                  class="btn btn-sm text-start text-truncate"
                  :class="m.winner === m.team2 ? 'btn-success' : 'btn-outline-light'"
                  :disabled="!m.team2"
                  @click="pickWinner(rIdx, mIdx, m.team2)"
                >{{ m.team2 || '—' }}</button>
              </div>

              <small v-if="m.winner" class="text-success d-block mt-1">Sieger: {{ m.winner }}</small>
              <small v-else class="text-light d-block mt-1">Sieger wählen</small>
              <hr class="border-secondary opacity-25" />
            </div>

            <div v-if="!round.matches?.length" class="text-light small">Keine Spiele in dieser Runde</div>
          </div>
        </div>
      </div>
    </div>

    <div class="text-end mt-3 small text-light">
      Sieger werden automatisch in die nächste Runde propagiert.
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  rounds: { type: Array, default: () => [] }
})
const emit = defineEmits(['set-winner', 'update:rounds'])

const deepClone = (v) => JSON.parse(JSON.stringify(v ?? []))
const roundsLocal = ref(deepClone(props.rounds))

watch(() => props.rounds, (v) => {
  roundsLocal.value = deepClone(v)
}, { deep: true })

function defaultRoundName(idx, total) {
  const map = ['Achtelfinale', 'Viertelfinale', 'Halbfinale', 'Finale']
  const fromEnd = total - idx
  return map[fromEnd - 1] || `Runde ${idx + 1}`
}

function pickWinner(rIdx, mIdx, team) {
  if (!team) return
  const r = roundsLocal.value[rIdx]
  if (!r?.matches?.[mIdx]) return

  r.matches[mIdx].winner = team
  propagateForward(rIdx)

  emit('set-winner', rIdx, mIdx, team)
  emit('update:rounds', deepClone(roundsLocal.value))
}

function autoWinner(t1, t2) {
  if (t1 && !t2) return t1
  if (!t1 && t2) return t2
  return null
}

function propagateForward(startIdx) {
  for (let rr = startIdx; rr < roundsLocal.value.length - 1; rr++) {
    const cur = roundsLocal.value[rr]
    const nxt = roundsLocal.value[rr + 1]

    nxt.matches.forEach(mm => { mm.team1 = null; mm.team2 = null; mm.winner = null })

    cur.matches.forEach((m, idx) => {
      const w = m.winner || autoWinner(m.team1, m.team2)
      if (!w) return
      const tIdx = Math.floor(idx / 2)
      const pos  = (idx % 2 === 0) ? 'team1' : 'team2'
      nxt.matches[tIdx][pos] = w
    })
  }
}

/* HMR für diese Komponente deaktivieren (verhindert instance.job-Fehler beim Hot-Reload) */
if (import.meta && import.meta.hot) {
  import.meta.hot.decline()
}
</script>

<style scoped>
.ko-bracket { width: 100%; }
</style>
