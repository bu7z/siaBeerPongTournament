<template>
  <table class="table table-dark table-striped table-sm align-middle mb-0">
    <thead>
      <tr>
        <th>Team</th>
        <th class="text-center">P</th>
        <th class="text-center">B+</th>
        <th class="text-center">B-</th>
        <th class="text-center">Diff</th>
      </tr>
    </thead>
    <tbody>
      <tr v-for="(t, idx) in sorted" :key="idx">
        <td>{{ t.name }}</td>
        <td class="text-center">{{ t.points }}</td>
        <td class="text-center">{{ t.cupsFor }}</td>
        <td class="text-center">{{ t.cupsAgainst }}</td>
        <td class="text-center">{{ t.cupsDiff }}</td>
      </tr>
    </tbody>
  </table>
</template>

<script setup>
import { computed, watchEffect } from 'vue'

const props = defineProps({
  standings: Array,
  group: Object
})
const emit = defineEmits(['tiebreak'])

const sorted = computed(() => {
  return [...(props.standings || [])].sort((a, b) => {
    if (b.points !== a.points) return b.points - a.points
    if (b.cupsDiff !== a.cupsDiff) return b.cupsDiff - a.cupsDiff
    if (b.cupsFor !== a.cupsFor) return b.cupsFor - a.cupsFor
    return a.name.localeCompare(b.name, 'de')
  })
})

function equalTripleByPointsDiff(a, b, c) {
  return a && b && c &&
         a.points === b.points && b.points === c.points &&
         a.cupsDiff === b.cupsDiff && b.cupsDiff === c.cupsDiff
}

watchEffect(() => {
  const s = sorted.value
  if (!Array.isArray(s) || s.length < 3) return

  if (s.length === 3) {
    const [t1, t2, t3] = s
    if (equalTripleByPointsDiff(t1, t2, t3)) {
      emit('tiebreak', { kind: 'RAGE_CAGE_3', teams: [t1.name, t2.name, t3.name] })
      return
    }
  }
  if (s.length >= 4) {
    const [, t2, t3, t4] = s
    if (equalTripleByPointsDiff(t2, t3, t4)) {
      emit('tiebreak', { kind: 'REMATCH_3_OF_4', teams: [t2.name, t3.name, t4.name] })
      return
    }
  }
  emit('tiebreak', null)
})
</script>
