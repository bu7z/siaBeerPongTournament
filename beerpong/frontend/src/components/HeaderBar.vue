<template>
  <nav class="navbar navbar-dark bg-black border-bottom border-secondary">
    <div class="container">
      <span class="navbar-brand d-flex align-items-center gap-2">
        <span class="fw-bold">🏆 Turnierhalle</span>
        <small class="text-secondary">Beer-Pong</small>
      </span>

      <div class="d-flex align-items-center gap-3">
        <span v-if="hasActive" class="small text-secondary d-none d-md-inline">
          Aktives Turnier:
          <strong class="text-white">{{ tournamentName }}</strong>
          (Phase: {{ tournamentPhase }})
        </span>
        <button class="btn btn-outline-light btn-sm" @click="$emit('create-new')">
          Neues Turnier
        </button>
        <button class="btn btn-primary btn-sm" @click="$emit('open-loader')">
          Turnier laden
        </button>
      </div>
    </div>
  </nav>
</template>

<script setup>
defineProps({
  hasActive: { type: Boolean, default: false },
  tournamentName: { type: String, default: '' },
  tournamentPhase: { type: String, default: 'group' },
})
</script>

<style scoped>
.navbar { position: sticky; top: 0; z-index: 1000; }
</style>
