<template>
  <section>
    <KnockoutPreview
      v-if="phase==='preview'"
      :teams="qualified"
      :ko-size="koSize"
      @back="$emit('back')"
      @create-bracket="onCreateBracket"
    />
    <KnockoutBracket
      v-else
      :seeded="seeded"
      :size="size"
      @back="phase='preview'"
      @finish="$emit('finish', $event)"
    />
  </section>
</template>

<script setup>
import { ref } from 'vue'
import KnockoutPreview from './KnockoutPreview.vue'
import KnockoutBracket from './KnockoutBracket.vue'

const props = defineProps({
  qualified: { type: Array, required: true },
  koSize: { type: Number, default: null }
})
const emit = defineEmits(['back','finish'])

const phase = ref('preview')
const seeded = ref([])
const size = ref(4)

function onCreateBracket(payload){
  seeded.value = payload.seeded
  size.value = payload.size
  phase.value = 'bracket'
}
</script>
