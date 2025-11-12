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
            <th scope="col" class="pe-3">Play-In</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="(row, idx) in standings"
            :key="row.name + idx"
            :class="getRowClass(idx)"
          >
            <td class="ps-3 fw-bold">{{ idx + 1 }}.</td>
            <td class="text-truncate" style="max-width: 120px;" :title="row.name">
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
            <td class="pe-3">
              <button
                v-if="canSelectForPlayIn(idx)"
                class="btn btn-sm"
                :class="isSelectedForPlayIn(row.name) ? 'btn-warning' : 'btn-outline-warning'"
                @click="$emit('toggle-play-in', row.name)"
              >
                {{ isSelectedForPlayIn(row.name) ? '✓' : '+' }}
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  standings: { type: Array, required: true },
  additionalPlayInTeams: { type: Array, default: () => [] }
})

const emit = defineEmits(['toggle-play-in'])

const playInNeeded = computed(() => props.standings.length > 2)

function getRowClass(idx) {
  if (idx < 2) return 'table-success'
  if (playInNeeded.value) return 'table-warning'
  return ''
}

function canSelectForPlayIn(idx) {
  return playInNeeded.value && idx >= 2
}

function isSelectedForPlayIn(teamName) {
  return props.additionalPlayInTeams.includes(teamName)
}
</script>

<style scoped>
.table-success {
  background-color: rgba(25, 135, 84, 0.15) !important;
}

.table-warning {
  background-color: rgba(255, 193, 7, 0.15) !important;
}
</style>