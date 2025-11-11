<template>
  <section class="mx-auto" style="max-width: 1200px;">
    <div class="d-flex justify-content-between align-items-center mb-4">
      <h2>KO-Phase</h2>
      <button class="btn btn-outline-light" @click="$emit('back')">Zurück</button>
    </div>

    <p class="text-secondary mb-4">
      Klicke auf ein Team, um es als Sieger zu markieren. Die nächste Runde wird automatisch gefüllt.
    </p>

    <KnockoutBracket
      :rounds="rounds"
      @select-winner="handleSelectWinner"
    />
  </section>
</template>

<script setup>
import { ref, computed } from 'vue'
import KnockoutBracket from './KnockoutBracket.vue'

const props = defineProps({
  matches: { type: Array, required: true }
})

const emit = defineEmits(['back'])

const internalRounds = ref(buildInitialRounds(props.matches))
const rounds = computed(() => internalRounds.value)

function buildInitialRounds(firstRoundMatches) {
  const rounds = []
  rounds.push({
    label: labelForCount(firstRoundMatches.length),
    matches: firstRoundMatches.map((m, idx) => ({
      id: m.id ?? `r0-${idx}`,
      team1: m.team1,
      team2: m.team2,
      winner: m.winner ?? null
    }))
  })

  let len = firstRoundMatches.length
  while (len > 1) {
    len = Math.floor(len / 2)
    rounds.push({
      label: labelForCount(len),
      matches: Array.from({ length: len }, (_, i) => ({
        id: `auto-${len}-${i}`,
        team1: null,
        team2: null,
        winner: null
      }))
    })
  }
  return rounds
}

function labelForCount(n) {
  if (n === 1) return 'Finale'
  if (n === 2) return 'Halbfinale'
  if (n === 4) return 'Viertelfinale'
  if (n === 8) return 'Achtelfinale'
  return 'KO-Runde'
}

function handleSelectWinner({ roundIndex, matchIndex, team }) {
  const copy = JSON.parse(JSON.stringify(internalRounds.value))
  const match = copy[roundIndex].matches[matchIndex]
  const winnerName = team === 'team1' ? match.team1 : match.team2
  match.winner = winnerName

  const next = copy[roundIndex + 1]
  if (next) {
    const target = Math.floor(matchIndex / 2)
    if (matchIndex % 2 === 0) {
      next.matches[target].team1 = winnerName
    } else {
      next.matches[target].team2 = winnerName
    }
  }

  internalRounds.value = copy
}
</script>
