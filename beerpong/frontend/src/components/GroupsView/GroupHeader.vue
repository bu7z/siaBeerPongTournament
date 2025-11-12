<template>
  <div class="card-header d-flex justify-content-between align-items-center">
    <span class="fw-semibold">{{ group.name }}</span>
    <button
      class="btn btn-sm btn-outline-light"
      @click="$emit('generate-matches')"
      :disabled="groupMatches.length > 0 || group.teams.length < 2"
    >
      Gruppenspiele
    </button>
  </div>
</template>

<script setup>
defineProps({
  group: { type: Object, required: true },
  groupMatches: { type: Array, required: true }
})

defineEmits(['generate-matches'])
</script>