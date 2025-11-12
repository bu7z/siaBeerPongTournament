<template>
  <div class="card bg-dark border-secondary mb-4 text-light">
    <div class="card-body py-3">
      <div class="row">
        <div class="col-md-3">
          <strong>Teilnehmer:</strong> {{ teams.length }} Teams
        </div>
        <div class="col-md-3">
          <strong>Becher pro Spiel:</strong> {{ tournament.cupsPerGame || 6 }}
        </div>
        <div class="col-md-3">
          <strong>Gruppen:</strong> {{ baseGroups.length }} (automatisch)
        </div>
        <div class="col-md-3" v-if="tournament.finaleWith10Cups">
          <strong>Finale:</strong> 10 Becher
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  teams: { type: Array, required: true },
  tournament: { type: Object, required: true },
  baseGroups: { type: Array, required: true }
})
</script>