<template>
  <div class="card bg-dark text-light border-secondary h-100 d-flex flex-column">
    <!-- Header -->
    <GroupHeader 
      :group="group"
      :group-matches="groupMatches"
      @generate-matches="$emit('generate-matches')"
    />

    <!-- Tabelle -->
    <GroupTable
      :standings="standings"
      :additional-play-in-teams="additionalPlayInTeams"
      @toggle-play-in="$emit('toggle-play-in', $event)"
    />

    <!-- Tiebreak-Controls -->
    <TiebreakControls
      v-if="shouldShowTiebreakControls"
      :tiebreak-state="tiebreakState"
      @start-mini-tiebreak="$emit('start-mini-tiebreak')"
      @start-rage-cage="$emit('start-rage-cage')"
    />

    <!-- Mini-Runde Tiebreak -->
    <TiebreakMini
      v-if="tiebreakState && tiebreakState.mode === 'mini'"
      :tiebreak-state="tiebreakState"
      :group-name="group.name"
      @set-mini-winner="$emit('set-mini-winner', $event.index, $event.teamName)"
    />

    <!-- Rage Cage Tiebreak -->
    <TiebreakRage
      v-if="tiebreakState && tiebreakState.mode === 'rage'"
      :tiebreak-state="tiebreakState"
      @set-rage-loser="$emit('set-rage-loser', $event.teamName)"
    />

    <!-- Gruppenspiele -->
    <GroupMatches
      v-if="groupMatches.length"
      :group-matches="groupMatches"
      :tournament="tournament"
      @update-match="$emit('update-match', $event.index, $event.match)"
      @update-cups="$emit('update-cups', $event.index, $event.teamField, $event.value)"
    />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import GroupHeader from './GroupHeader.vue'
import GroupTable from './GroupTable.vue'
import TiebreakControls from './TiebreakControls.vue'
import TiebreakMini from './TiebreakMini.vue'
import TiebreakRage from './TiebreakRage.vue'
import GroupMatches from './GroupMatches.vue'

const props = defineProps({
  group: { type: Object, required: true },
  tournament: { type: Object, required: true },
  groupMatches: { type: Array, required: true },
  tiebreakState: { type: Object, default: null },
  additionalPlayInTeams: { type: Array, default: () => [] },
  standings: { type: Array, required: true }
})

const emit = defineEmits([
  'generate-matches',
  'update-match',
  'update-cups',
  'start-mini-tiebreak',
  'start-rage-cage',
  'set-mini-winner',
  'set-rage-loser',
  'toggle-play-in'
])

const shouldShowTiebreakControls = computed(() => {
  if (!props.groupMatches.length) return false
  const allPlayed = props.groupMatches.every(m => !!m.winner)
  if (!allPlayed) return false
  
  // Vereinfachte Logik - in der Praxis müsste hier der Tiebreak-Status überprüft werden
  return props.tiebreakState && !props.tiebreakState.resolved
})
</script>