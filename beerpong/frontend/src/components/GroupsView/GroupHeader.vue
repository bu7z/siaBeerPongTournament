<template>
  <div
    class="card-header bg-dark border-secondary d-flex justify-content-between align-items-center"
    @click="$emit('toggle')"
    style="cursor: pointer"
  >
    <div class="d-flex align-items-center gap-2">
      <span class="badge bg-secondary">Gruppe</span>
      <strong class="text-white">{{ groupName }}</strong>
    </div>
    <span class="text-light small">
      {{ expanded ? 'zuklappen' : 'aufklappen' }}
    </span>
  </div>
</template>

<script setup>
defineProps({
  groupName: { type: String, required: true },
  expanded: { type: Boolean, default: true }
})
defineEmits(['toggle'])
</script>
