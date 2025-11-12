<template>
  <div class="mt-4 p-3 border border-secondary rounded">
    <h6>ℹ️ Turnier-Information</h6>
    <p class="mb-1 text-secondary">
      <strong>Wertung:</strong> 2 Punkte pro Sieg, 0 Punkte pro Niederlage
    </p>
    <p class="mb-1 text-secondary">
      <strong>Tie-Breaker:</strong> 1. Punkte → 2. Becher-Differenz → 3. Direkter Vergleich
    </p>
    <p class="mb-0 text-secondary" v-if="playInNeeded">
      <strong>Nächster Schritt:</strong> Play-In mit markierten Teams aus Platz 3+
    </p>
    <p class="mb-0 text-secondary" v-else>
      <strong>Nächster Schritt:</strong> KO-Runde mit den Erst- und Zweitplatzierten
    </p>
  </div>
</template>

<script setup>
defineProps({
  playInNeeded: { type: Boolean, default: false }
})
</script>