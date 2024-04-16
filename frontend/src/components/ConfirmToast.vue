<template>
  <div class="t-container">
    <span>{{ props.message }}</span>
    <button 
      @click="confirm"
      class="v-btn v-btn--density-default v-btn--size-default v-btn--variant-text"
    >
      <span class="v-btn__overlay" />
      <span class="v-btn__underlay" />
      <span class="v-btn__content">{{ props.buttonText }}</span>
    </button>
  </div>
</template>

<script setup lang="ts">
const props = withDefaults(defineProps<{
  message: string;
  buttonText?: string;
}>(), {
  buttonText: 'Confirm',
});
const emit = defineEmits(['confirm', 'closeToast']);

function confirm() {
  emit('confirm');
  emit('closeToast');
}
</script>

<style scoped>
.t-container {
  width: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
