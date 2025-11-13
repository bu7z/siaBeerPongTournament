<template>
  <div class="card-body p-0">
    <div class="table-responsive">
      <table class="table table-dark table-hover mb-0">
        <thead>
          <tr>
            <th scope="col" class="ps-3">#</th>
            <th scope="col">Team</th>
            <th scope="col" class="text-center">P</th>
            <th scope="col" class="text-center">S</th>
            <th scope="col" class="text-center">N</th>
            <th scope="col" class="text-center">B+</th>
            <th scope="col" class="text-center">B-</th>
            <th scope="col" class="text-center">±</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="(row, idx) in standings"
            :key="row.name + idx"
            :class="getRowClass(idx)"
          >
            <td class="ps-3 fw-bold">{{ idx + 1 }}.</td>
            <td class="text-truncate" style="max-width: 160px;" :title="row.name">
              {{ row.name }}
            </td>
            <td class="text-center fw-bold">{{ row.points }}</td>
            <td class="text-center text-success">{{ row.wins }}</td>
            <td class="text-center text-danger">{{ row.losses }}</td>
            <td class="text-center">{{ row.cupsFor }}</td>
            <td class="text-center">{{ row.cupsAgainst }}</td>
            <td class="text-center" :class="{'text-success': row.cupsDiff > 0, 'text-danger': row.cupsDiff < 0}">
              {{ row.cupsDiff > 0 ? '+' : '' }}{{ row.cupsDiff }}
            </td>
          </tr>
          <tr v-if="standings.length === 0">
            <td colspan="8" class="text-center text-light">Noch keine Daten</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  groupName: { type: String, required: true },
  matches: { type: Array, default: () => [] }
})

const standings = computed(() => {
  const rows = new Map()
  const ensure = (name) => {
    if (!rows.has(name)) {
      rows.set(name, { name, wins: 0, losses: 0, points: 0, cupsFor: 0, cupsAgainst: 0, cupsDiff: 0 })
    }
    return rows.get(name)
  }
  for (const m of props.matches) {
    if (!m?.team1 || !m?.team2) continue
    const a = ensure(m.team1)
    const b = ensure(m.team2)
    const c1 = Number.isFinite(+m.cups_team1) ? +m.cups_team1 : 0
    const c2 = Number.isFinite(+m.cups_team2) ? +m.cups_team2 : 0
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
})

function getRowClass(idx) {
  if (idx < 2) return 'table-success'
  return ''
}
</script>

<style scoped>
.table-success {
  background-color: rgba(25, 135, 84, 0.15) !important;
}
</style>
