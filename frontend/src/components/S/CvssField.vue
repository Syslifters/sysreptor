<template>
  <div class="d-flex">
    <div class="flex-grow-width">
      <s-text-field
        :model-value="props.modelValue"
        @update:model-value="emit('update:modelValue', $event)"
        :rules="rules.validCvssVector"
        :label="props.label"
        :disabled="props.disabled"
        spellcheck="false"
      />
    </div>

    <div class="flex-grow-0">
      <div class="cvss-score ml-2" :class="'level-' + scoreInfo.levelNumber">
        <div class="cvss-score-header">{{ scoreInfo.scoreFormatted }}</div>
        <div class="cvss-score-label">{{ scoreInfo.levelName }}</div>
      </div>
    </div>

    <s-dialog v-model="dialogVisible" max-width="70%" scrollable>
      <template #activator="{ props: dialogProps }">
        <s-btn color="secondary" class="ma-3" text="CVSS Editor" v-bind="dialogProps" />
      </template>

      <template #title>CVSS Editor</template>
      <template #toolbar>
        <div class="cvss-score" :class="'level-' + editorScoreInfo.levelNumber">
          <div class="cvss-score-header">{{ editorScoreInfo.scoreFormatted }}</div>
          <div class="cvss-score-label">{{ editorScoreInfo.levelName }}</div>
        </div>

        <s-btn
          @click="applyDialog"
          :disabled="props.disabled"
          variant="text"
          icon
        >
          <v-icon size="x-large">mdi-check-bold</v-icon>
          <s-tooltip activator="parent" :disabled="props.disabled" text="Apply" />
        </s-btn>
      </template>

      <template #default>
        <v-card-text class="pa-0">
          <v-card
            v-for="metricGroup in metricGroups"
            :key="metricGroup.name"
            flat
          >
            <v-divider />
            <v-card-title>{{ metricGroup.name }}</v-card-title>
            <v-card-text>
              <v-row>
                <v-col
                  v-for="metricGroupCol in metricGroup.cols"
                  :key="metricGroupCol.toString()"
                >
                  <s-cvss-metric-input
                    v-for="m in metricGroupCol"
                    :key="m"
                    :model-value="parsedEditorVector[m]"
                    @update:model-value="updateMetric(m, $event)"
                    :metric="cvssDefinition[m]"
                    :disabled="props.disabled"
                  />
                </v-col>
              </v-row>
            </v-card-text>
          </v-card>
        </v-card-text>
      </template>
    </s-dialog>
  </div>
</template>

<script setup lang="ts">
import * as cvss from "@/utils/cvss";

const props = defineProps<{
  modelValue: string|null;
  label?: string;
  disabled?: boolean;
}>();
const emit = defineEmits<{
  (e: 'update:modelValue', value: string|null): void;
}>();

const dialogVisible = ref(false);
const rules = {
  validCvssVector: [(v: string|null|undefined) =>
    cvss.isValidVector(v) ||
    [undefined, null, "", "n/a", "n.a."].includes(v) ||
    "Invalid CVSS vector",
  ]
}

const editorValue = ref(props.modelValue);
watch(() => props.modelValue, () => { editorValue.value = props.modelValue; });
watch(dialogVisible, (newVal) => {
  // Reset temporary editorValue when the dialog is closed
  if (newVal) {
    editorValue.value = props.modelValue;
  }
});

function cvssInfo(vector: string|null) {
  const score = cvss.scoreFromVector(vector);
  return {
    score,
    scoreFormatted: (score || 0.0).toFixed(1),
    levelNumber: cvss.levelNumberFromScore(score),
    levelName: cvss.levelNameFromScore(score),
  }
}

const parsedEditorVector = computed(() => cvss.parseVector(editorValue.value));
const editorScoreInfo = computed(() => cvssInfo(editorValue.value));
const scoreInfo = computed(() => cvssInfo(props.modelValue));

const metricGroups = [
  {
    name: "Base Score",
    cols: [
      ["AV", "AC", "PR", "UI"],
      ["S", "C", "I", "A"],
    ],
  },
  {
    name: "Temporal Score",
    cols: [["E", "RL", "RC"]],
  },
  {
    name: "Environmental Score",
    cols: [
      ["CR", "IR", "AR"],
      ["MAV", "MAC", "MPR", "MUI", "MS", "MC", "MI", "MA"],
    ],
  },
];
const cvssDefinition = cvss.CVSS31_DEFINITION;

function updateMetric(metric: string, val: any) {
  editorValue.value = cvss.stringifyVector({ ...parsedEditorVector.value, [metric]: val });
}

function applyDialog() {
  dialogVisible.value = false;
  emit('update:modelValue', editorValue.value);
}
</script>

<style scoped lang="scss">
@use "@/assets/settings" as settings;

.cvss-score {
  width: 8em;
  display: flex;
  flex-direction: column;

  &-header {
    background-color: #dcdcdc;
    text-align: center;
    font-weight: bold;
  }

  &-label {
    text-align: center;
    //padding: 0.4em;
  }

  &-bottom {
    height: 0.6em;
    background-color: #808080;
  }
}

@for $level from 1 through 5 {
  .level-#{$level} {
    .cvss-score-header {
      background-color: map-get(settings.$risk-color-levels, $level);
      color: white;
    }
    .cvss-score-label {
      color: map-get(settings.$risk-color-levels, $level);
    }
  }
}
</style>
