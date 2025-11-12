<template>
  <div class="px-3 pb-3 border-top border-secondary">
    <p class="text-secondary small mb-2">Rage-Cage: Verlierer wählen</p>
    <div class="d-flex flex-column gap-2">
      <button
        v-for="team in tiebreakState.teams"
        :key="team"
        class="btn btn-sm text-start"
        :class="tiebreakState.loser === team ? 'btn-danger' : 'btn-outline-danger'"
        @click="$emit('set-rage-loser', { teamName: team })"
      >
        {{ truncateName(team) }} hat verloren
      </button>
    </div>
  </div>
</template>

<script setup>
defineProps({
  tiebreakState: { type: Object, required: true }
})

defineEmits(['set-rage-loser'])

function truncateName(name, len = 40) {
  if (!name) return ''
  return name.length > len ? name.slice(0, len - 3) + '...' : name
}
</script>