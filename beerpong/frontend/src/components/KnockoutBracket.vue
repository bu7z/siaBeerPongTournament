<template>
  <section class="mx-auto" style="max-width: 1100px;">
    <div class="d-flex justify-content-between align-items-center mb-3">
      <h2>KO-Phase – Bracket</h2>
      <button class="btn btn-outline-light" @click="$emit('back')">Zurück</button>
    </div>

    <div class="row g-4">
      <!-- Viertelfinale -->
      <div class="col-md-4">
        <div class="card bg-dark border-secondary h-100">
          <div class="card-header"><strong>Viertelfinale</strong></div>
          <div class="card-body">
            <div v-for="(m, i) in qf" :key="'qf'+i" class="d-flex gap-2 mb-2">
              <button class="btn btn-sm flex-fill"
                      :class="m.winner===m.a?'btn-success':'btn-outline-light'"
                      @click="setWinner('qf', i, m.a)">{{ m.a }}</button>
              <span class="text-secondary">vs</span>
              <button class="btn btn-sm flex-fill"
                      :class="m.winner===m.b?'btn-success':'btn-outline-light'"
                      @click="setWinner('qf', i, m.b)">{{ m.b }}</button>
            </div>
          </div>
        </div>
      </div>

      <!-- Halbfinale -->
      <div class="col-md-4">
        <div class="card bg-dark border-secondary h-100">
          <div class="card-header"><strong>Halbfinale</strong></div>
          <div class="card-body">
            <div v-for="(m, i) in sf" :key="'sf'+i" class="d-flex gap-2 mb-2">
              <button class="btn btn-sm flex-fill"
                      :class="m.winner===m.a?'btn-success':'btn-outline-light'"
                      @click="setWinner('sf', i, m.a)">{{ m.a }}</button>
              <span class="text-secondary">vs</span>
              <button class="btn btn-sm flex-fill"
                      :class="m.winner===m.b?'btn-success':'btn-outline-light'"
                      @click="setWinner('sf', i, m.b)">{{ m.b }}</button>
            </div>
          </div>
        </div>
      </div>

      <!-- Finale -->
      <div class="col-md-4">
        <div class="card bg-dark border-secondary h-100">
          <div class="card-header"><strong>Finale</strong></div>
          <div class="card-body">
            <div v-for="(m, i) in fi" :key="'fi'+i" class="d-flex gap-2 mb-2">
              <button class="btn btn-sm flex-fill"
                      :class="m.winner===m.a?'btn-success':'btn-outline-light'"
                      @click="setWinner('fi', i, m.a)">{{ m.a }}</button>
              <span class="text-secondary">vs</span>
              <button class="btn btn-sm flex-fill"
                      :class="m.winner===m.b?'btn-success':'btn-outline-light'"
                      @click="setWinner('fi', i, m.b)">{{ m.b }}</button>
            </div>
            <div v-if="fi.length && fi[0].winner" class="text-center mt-3">
              <div class="h5 text-success">🏆 Sieger: {{ fi[0].winner }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="d-flex justify-content-end mt-3">
      <button class="btn btn-success" :disabled="!finalWinner" @click="$emit('finish', finalWinner)">
        Turnier abschließen
      </button>
    </div>
  </section>
</template>

<script setup>
import { reactive, computed, watchEffect } from 'vue'

const props = defineProps({
  seeded: { type: Array, required: true }, // Länge: 8 (oder 4)
  size:   { type: Number, required: true } // 4 oder 8 (aktuell)
})
const emit = defineEmits(['back','finish'])

const state = reactive({
  qf: [],
  sf: [],
  fi: []
})

function buildPairs(list){
  const pairs = []
  for(let i=0;i<list.length;i+=2){
    pairs.push({ a:list[i], b:list[i+1], winner:null })
  }
  return pairs
}

watchEffect(()=>{
  const s = props.seeded.slice(0, props.size)
  if (props.size === 8){
    // Seeding 1-8 (klassisch 1-8, 4-5, 3-6, 2-7)
    const order = [0,7,3,4,2,5,1,6].map(i => s[i])
    state.qf = buildPairs(order)
    state.sf = buildPairs(['?', '?', '?', '?'])
    state.fi = buildPairs(['?', '?'])
  } else if (props.size === 4){
    const order = [0,3,1,2].map(i => s[i])
    state.qf = [] // kein QF
    state.sf = buildPairs(order)
    state.fi = buildPairs(['?', '?'])
  } else {
    // Fallback: behandle wie 4
    const order = [0,3,1,2].map(i => s[i] ?? '?')
    state.qf = []
    state.sf = buildPairs(order)
    state.fi = buildPairs(['?', '?'])
  }
})

function setWinner(round, idx, team){
  const r = state[round]
  r[idx].winner = team
  if (round === 'qf'){
    // map qf winners -> sf
    const w = state.qf.map(m => m.winner || '?')
    state.sf = buildPairs([w[0], w[1], w[2], w[3]])
  }
  if (round === 'sf'){
    const w = state.sf.map(m => m.winner || '?')
    state.fi = buildPairs([w[0], w[1]])
  }
}

const finalWinner = computed(()=> state.fi[0]?.winner || null)

const qf = computed(()=> state.qf)
const sf = computed(()=> state.sf)
const fi = computed(()=> state.fi)
</script>
