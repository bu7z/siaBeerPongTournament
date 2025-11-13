<template>
  <div class="card bg-dark border-secondary">
    <GroupHeader
      :group-name="groupName"
      :expanded="expandedLocal"
      @toggle="expandedLocal = !expandedLocal"
    />

    <div v-show="expandedLocal">
      <!-- Tabelle (aus Matches berechnet) -->
      <GroupTable :group-name="groupName" :matches="matchesLocal" />

      <div class="px-3 pt-2">
        <small class="text-light">
          Klicke auf +/−, um Becher anzupassen. Das Team, das zuerst
          <strong class="text-white">{{ cupsTarget }}</strong> erreicht, gewinnt automatisch.
          Zahlen sind direkt editierbar.
        </small>
      </div>

      <!-- Match-Editor -->
      <GroupMatches
        class="mt-2"
        :group-name="groupName"
        :cups-target="cupsTarget"
        :matches="matchesLocal"
        @update:matches="updateMatches"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import GroupHeader from './GroupHeader.vue'
import GroupMatches from './GroupMatches.vue'
import GroupTable from './GroupTable.vue'

const props = defineProps({
  groupName: { type: String, required: true },
  cupsTarget: { type: Number, required: true },
  matches: { type: Array, default: () => [] },
  expanded: { type: Boolean, default: true }
})
const emit = defineEmits(['update:matches', 'update:expanded'])

const expandedLocal = ref(!!props.expanded)
const matchesLocal = ref([...(props.matches || [])])

watch(() => props.matches, (v) => {
  matchesLocal.value = [...(v || [])]
}, { deep: true })

watch(() => expandedLocal.value, (v) => {
  emit('update:expanded', v)
})

function updateMatches(ms) {
  matchesLocal.value = [...ms]
  emit('update:matches', matchesLocal.value)
}
</script>
