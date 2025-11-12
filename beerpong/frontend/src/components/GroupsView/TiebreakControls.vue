<template>
  <div class="px-3 py-2 border-top border-secondary">
    <p class="text-secondary small mb-2">Kein eindeutiger 1./2. Platz. Tiebreak:</p>
    <div class="d-flex gap-2">
      <button
        v-if="!tiebreakState || tiebreakState.mode !== 'mini'"
        class="btn btn-sm btn-outline-light"
        @click="$emit('start-mini-tiebreak')"
      >
        Mini-Runde
      </button>
      <button class="btn btn-sm btn-outline-light" @click="$emit('start-rage-cage')">
        Rage Cage
      </button>
    </div>
  </div>
</template>

<script setup>
defineProps({
  tiebreakState: { type: Object, default: null }
})

defineEmits(['start-mini-tiebreak', 'start-rage-cage'])
</script>