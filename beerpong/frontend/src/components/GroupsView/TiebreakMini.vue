<template>
  <div class="px-3 pb-3 border-top border-secondary">
    <p class="text-secondary small mb-2">Tiebreak-Spiele</p>
    <div
      v-for="(m, idx) in tiebreakState.matches"
      :key="groupName + '-tb-' + idx"
      class="d-flex gap-2 mb-2"
    >
      <button
        class="btn btn-sm flex-fill text-start text-truncate"
        :class="m.winner === m.team1 ? 'btn-success' : 'btn-outline-light'"
        @click="$emit('set-mini-winner', { index: idx, teamName: m.team1 })"
      >
        {{ truncateName(m.team1) }}
      </button>
      <span class="text-secondary">vs</span>
      <button
        class="btn btn-sm flex-fill text-start text-truncate"
        :class="m.winner === m.team2 ? 'btn-success' : 'btn-outline-light'"
        @click="$emit('set-mini-winner', { index: idx, teamName: m.team2 })"
      >
        {{ truncateName(m.team2) }}
      </button>
    </div>
    <p v-if="!tiebreakState.resolved" class="text-secondary small">
      Alle Tiebreak-Spiele entscheiden – oder Rage Cage verwenden.
    </p>
  </div>
</template>

<script setup>
defineProps({
  tiebreakState: { type: Object, required: true },
  groupName: { type: String, required: true }
})

defineEmits(['set-mini-winner'])

function truncateName(name, len = 40) {
  if (!name) return ''
  return name.length > len ? name.slice(0, len - 3) + '...' : name
}
</script>