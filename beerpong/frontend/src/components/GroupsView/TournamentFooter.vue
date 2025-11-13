<template>
  <div class="mt-5 text-center text-light small">
    <hr class="border-secondary opacity-25" />
    <div>Beer-Pong Turnier – Gruppen & KO © {{ year }}</div>
  </div>
</template>

<script setup>
const year = new Date().getFullYear()
</script>
