<template>
  <div class="card bg-dark border-secondary shadow">
    <div class="card-header bg-secondary text-light d-flex justify-content-between align-items-center">
      <strong>{{ group.name }}</strong>
      <small class="text-light opacity-75">Teams: {{ group.teams.length }}</small>
    </div>
    <div class="card-body">
      <GroupHeader :group="group" />
      <GroupTable :standings="standings" :group="group" @tiebreak="onTiebreakDetected" />
      <GroupMatches
        :group="group"
        :matches="matches"
        :tournament-id="tournamentId"
        :cups-per-game="cupsPerGame"
        :finale-with-10="finaleWith10"
        @match-updated="(m) => $emit('match-updated', group.name, m)"
      />
      <TiebreakerMini v-if="showMiniTiebreak" class="mt-3" />
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import GroupHeader from './GroupHeader.vue'
import GroupMatches from './GroupMatches.vue'
import GroupTable from './GroupTable.vue'
import TiebreakerMini from './TiebreakMini.vue'

const props = defineProps({
  group: Object,
  matches: Array,
  standings: Array,
  tournamentId: Number,
  cupsPerGame: Number,
  finaleWith10: Boolean
})

const showMiniTiebreak = ref(false)
function onTiebreakDetected(type) {
  showMiniTiebreak.value = type === 'mini'
}
</script>
