<template>
  <section class="mx-auto" style="max-width: 900px;">
    <div class="d-flex justify-content-between align-items-center mb-3">
      <h2>Play-In</h2>
      <button class="btn btn-outline-light" @click="onBack">Zurück</button>
    </div>

    <div class="card bg-dark border-secondary mb-3">
      <div class="card-body">
        <div class="row g-3 align-items-center">
          <div class="col-md">
            <div class="mb-2"><strong>Bereits qualifiziert:</strong></div>
            <div class="d-flex flex-wrap gap-2">
              <span v-for="t in baseAutoQualified" :key="t" class="badge bg-success">{{ t }}</span>
              <span v-if="baseAutoQualified.length === 0" class="text-muted">–</span>
            </div>
          </div>
          <div class="col-md-auto text-end">
            <div class="small text-muted">Benötigte zusätzliche Plätze</div>
            <div class="display-6 fw-bold text-white">{{ slotsNeededText }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Rage-Cage -->
    <div v-for="(rc, idx) in rageCage" :key="'rc'+idx" class="card bg-dark border-warning mb-3">
      <div class="card-header border-warning"><strong>Rage-Cage (1 Team scheidet aus)</strong></div>
      <div class="card-body">
        <div class="d-flex flex-wrap gap-2 mb-3">
          <span v-for="t in rc.teams" :key="t" class="badge bg-secondary">{{ t }}</span>
        </div>
        <div class="small text-secondary mb-2">{{ rc.note || 'Exakter 3er-Gleichstand am Cut-Off' }}</div>
        <div class="d-flex flex-wrap gap-2">
          <button
            v-for="t in rc.teams"
            :key="'btn'+t"
            class="btn btn-sm"
            :class="rageLosers[idx] === t ? 'btn-danger' : 'btn-outline-danger'"
            @click="markRageLoser(idx, t)"
          >
            {{ t }} verliert
          </button>
        </div>
      </div>
    </div>

    <!-- Play-In Matches -->
    <div v-if="matches.length" class="card bg-dark border-secondary mb-3">
      <div class="card-header"><strong>Play-In-Spiele</strong></div>
      <div class="card-body">
        <div v-for="m in matches" :key="m.match_id" class="d-flex align-items-center gap-2 mb-2">
          <button
            class="btn btn-sm flex-fill"
            :class="winners[m.match_id] === m.team1 ? 'btn-success' : 'btn-outline-light'"
            @click="setWinner(m.match_id, m.team1)"
          >
            {{ m.team1 }}
          </button>
          <span class="text-secondary">vs</span>
          <button
            class="btn btn-sm flex-fill"
            :class="winners[m.match_id] === m.team2 ? 'btn-success' : 'btn-outline-light'"
            @click="setWinner(m.match_id, m.team2)"
          >
            {{ m.team2 }}
          </button>
        </div>
      </div>
    </div>

    <!-- Hinweise -->
    <div v-if="policyNotes && policyNotes.length" class="alert alert-dark border-secondary">
      <ul class="mb-0">
        <li v-for="(n,i) in policyNotes" :key="i">{{ n }}</li>
      </ul>
    </div>

    <div class="d-flex justify-content-between mt-4">
      <button class="btn btn-outline-light" @click="onBack">Zurück</button>
      <button class="btn btn-success" :disabled="!canContinue" @click="finalize">
        In KO-Phase übernehmen
      </button>
    </div>
  </section>
</template>

<script setup>
import { reactive, computed } from 'vue'

const props = defineProps({
  autoQualified: { type: Array, default: () => [] },
  koSize: { type: Number, default: null },
  slotsNeeded: { type: Number, required: true },     // ← MUSS vom Backend kommen
  matches: { type: Array, default: () => [] },       // [{match_id, team1, team2}]
  rageCage: { type: Array, default: () => [] },      // [{teams:[...], note}]
  policyNotes: { type: Array, default: () => [] }
})
const emit = defineEmits(['back','to-ko','create-ko'])

const baseAutoQualified = computed(() => props.autoQualified)

const slotsNeededText = computed(() => String(props.slotsNeeded))

const winners = reactive({})
const rageLosers = reactive({})

function setWinner(matchId, teamLabel){ winners[matchId] = teamLabel }
function markRageLoser(rcIndex, teamLabel){ rageLosers[rcIndex] = teamLabel }

const canContinue = computed(()=>{
  // Wenn SlotsNeeded 0 wäre, würden wir hier gar nicht landen.
  const rageOk = props.rageCage.every((_,i)=> !!rageLosers[i])
  const matchesOk = props.matches.every(m => !!winners[m.match_id])
  return rageOk && matchesOk
})

function onBack(){ emit('back') }

function finalize(){
  const rageQualified = []
  props.rageCage.forEach((rc, idx)=>{
    const loser = rageLosers[idx]
    rc.teams.forEach(t => { if (t !== loser) rageQualified.push(t) })
  })
  const matchQualified = props.matches.map(m => winners[m.match_id]).filter(Boolean)

  const payload = {
    qualified: [...baseAutoQualified.value, ...rageQualified, ...matchQualified],
    koSize: props.koSize || null
  }
  emit('to-ko', payload)
  emit('create-ko', payload) // alias
}
</script>

<style scoped>
.badge { font-weight: 500; }
</style>
