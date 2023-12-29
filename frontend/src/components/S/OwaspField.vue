<template>
  <v-row>
    <v-col cols="12" md="6" v-for="m in metricOWASP" :key="m">
      <v-card
        variant="outlined"
        class="mb-2"
        style="border-color: rgba(30, 30, 30, 0.12)"
      >
        <v-card-title>{{ OWASP_DEFINITION[m].name }}</v-card-title>
        <v-divider />
        <s-owasp-metric-input
          :model-value="parsedEditorVector[m]"
          @update:model-value="updateMetric(m, $event)"
          :metric="OWASP_DEFINITION[m]"
        />
      </v-card>
    </v-col>
  </v-row>
</template>

<script setup lang="ts">
import { OWASP_DEFINITION, parseVector, stringifyVector } from "@/utils/owasp";

const props = defineProps<{
  modelValue: string | null;
}>();
const emit = defineEmits<{
  (e: 'update:modelValue', value: string|null): void;
}>();

const editorValue = ref(props.modelValue);
watch(
  () => props.modelValue,
  () => {
    editorValue.value = props.modelValue;
  }
);
const parsedEditorVector = computed(() => parseVector(editorValue.value));
const metricOWASP = ["LF", "IF", "ORS"];
function updateMetric(metric: string, val: any) {
  parsedEditorVector.value[metric] = val;
  editorValue.value = stringifyVector(parsedEditorVector.value);
  emit("update:modelValue", editorValue.value);
}
</script>
<style scoped lang="scss">
@use "@/assets/settings" as settings;
@use "@/assets/vuetify" as vuetify;
</style>
