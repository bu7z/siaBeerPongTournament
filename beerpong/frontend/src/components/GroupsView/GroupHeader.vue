<template>
  <div class="text-secondary small mb-3">
    <span class="me-3">Gruppe: <strong>{{ group.name }}</strong></span>
    <span class="me-3">Teams: {{ group.teams.length }}</span>
  </div>
</template>

<script setup>
const props = defineProps({ group: Object })
</script>
