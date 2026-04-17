<template>
  <div class="card bg-dark border-secondary">
    <div class="card-header bg-dark border-secondary">
      <strong>Tiebreak / Sonderfälle</strong>
    </div>
    <div class="card-body">
      <div class="text-light small mb-2">
        Tiebreaks werden automatisch über <em>Becher-Differenz</em> / <em>B+</em> / <em>Punkte</em> berücksichtigt.
        Bei einem exakten 3er-Gleichstand am Cut-Off wird <strong class="text-warning">Letzter Becher entscheidet</strong> vorgeschlagen.
      </div>
      <slot />
    </div>
  </div>
</template>

<script setup>
// rein presentational; Inhalte kommen über <slot>
</script>
