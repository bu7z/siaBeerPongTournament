<template>
  <div class="bracket-wrapper">
    <div class="bracket">
      <div
        v-for="(round, roundIndex) in rounds"
        :key="roundIndex"
        class="bracket-round"
        :class="`round-${roundIndex}`"
      >
        <h6 v-if="round.label" class="text-secondary mb-3">{{ round.label }}</h6>
        <div
          v-for="(match, matchIndex) in round.matches"
          :key="match.id ?? roundIndex + '-' + matchIndex"
          class="bracket-match"
        >
          <button
            class="team"
            :class="{ winner: match.winner === match.team1 }"
            @click="emitWinner(roundIndex, matchIndex, 'team1')"
            :title="match.team1 || 'offen'"
          >
            {{ truncate(match.team1) || '---' }}
          </button>
          <button
            class="team"
            :class="{ winner: match.winner === match.team2 }"
            @click="emitWinner(roundIndex, matchIndex, 'team2')"
            :title="match.team2 || 'offen'"
          >
            {{ truncate(match.team2) || '---' }}
          </button>
          <div
            v-if="roundIndex < rounds.length - 1"
            class="connector"
          ></div>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup>
const props = defineProps({
  rounds: { type: Array, required: true }
})
const emit = defineEmits(['select-winner'])
function emitWinner(roundIndex, matchIndex, team) {
  emit('select-winner', { roundIndex, matchIndex, team })
}
function truncate(name, len = 18) {
  if (!name) return ''
  return name.length > len ? name.slice(0, len - 3) + '...' : name
}
</script>
<style scoped>
.bracket-wrapper {
  overflow-x: auto;
  padding-bottom: 1rem;
}
.bracket {
  display: flex;
  gap: 3rem;
  min-height: 360px;
}
.bracket-round {
  display: flex;
  flex-direction: column;
  gap: 2rem;
  min-width: 190px;
}
.bracket-match {
  background: rgba(0, 0, 0, 0.15);
  border: 1px solid rgba(255, 255, 255, 0.04);
  border-radius: 0.75rem;
  padding: 0.6rem 0.6rem 1.4rem;
  position: relative;
  min-height: 78px;
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}
.team {
  width: 100%;
  background: #111;
  border: 1px solid rgba(255, 255, 255, 0.12);
  color: #fff;
  border-radius: 0.5rem;
  text-align: left;
  padding: 0.35rem 0.55rem;
  font-size: 0.78rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  cursor: pointer;
  position: relative;
  z-index: 2;
}
.team:hover {
  background: #171717;
}
.team.winner {
  background: #198754;
  border-color: #198754;
  color: #fff;
}
.connector {
  position: absolute;
  right: -1.5rem;
  top: 50%;
  width: 1.5rem;
  height: 2px;
  background: rgba(255, 255, 255, 0.08);
  pointer-events: none;
  z-index: 1;
}
.round-0 .bracket-match {
  margin-bottom: 1.5rem;
}
.round-1 .bracket-match {
  margin-top: 1.5rem;
  margin-bottom: 3.3rem;
}
.round-2 .bracket-match {
  margin-top: 3.2rem;
}
</style>