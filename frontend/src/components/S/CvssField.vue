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

      <template #title>
        <span v-if="availableCvssVersions.length > 1">
          <v-btn-toggle
            v-model="editorCvssVersion"
            :disabled="props.disabled"
            mandatory
            :border="true"
            color="secondary"
            density="compact"
            class="mr-2"
          >
            <v-btn 
              :value="CvssVersion.CVSS40" 
              :text="CvssVersion.CVSS40" 
              :disabled="props.disabled || !availableCvssVersions.includes(CvssVersion.CVSS40)" 
            />
            <v-btn 
              :value="CvssVersion.CVSS31" 
              :text="CvssVersion.CVSS31" 
              :disabled="props.disabled || !availableCvssVersions.includes(CvssVersion.CVSS31)" 
            />
          </v-btn-toggle>

          {{ editorCvssVersion }} Editor
        </span>
      </template>
      <template #toolbar>
        <div class="cvss-score mr-2" :class="'level-' + editorScoreInfo.levelNumber">
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
        <v-card-text v-if="editorCvssVersion === CvssVersion.CVSS40">
          <v-card v-for="metricGroup in metricGroupsCvss40" :key="metricGroup.name" variant="outlined" class="mb-2">
            <v-card-title>{{ metricGroup.name }}</v-card-title>
            <v-divider />

            <v-card-text v-for="metricSubgroup in metricGroup.subgroups" :key="metricSubgroup.metrics.join(',')" class="pt-0 pb-0">
              <v-card-subtitle v-if="metricSubgroup.name" class="text-h6 ma-2 mt-6 submetric-title">{{ metricSubgroup.name }}</v-card-subtitle>
              <s-cvss-metric-input
                v-for="m in metricSubgroup.metrics"
                :key="m"
                :model-value="parsedEditorVector.metrics[m]"
                @update:model-value="updateMetric(m, $event)"
                :metric="CVSS40_DEFINITION[m]"
                :single-line="true"
                :disabled="props.disabled"
              />
            </v-card-text>
          </v-card>
        </v-card-text>
        <v-card-text v-else>
          <v-card
            v-for="metricGroup in metricGroupsCvss31"
            :key="metricGroup.name"
            variant="outlined"
            class="mb-2"
          >
            <v-card-title>{{ metricGroup.name }}</v-card-title>
            <v-divider />
            
            <v-card-text>
              <v-row>
                <v-col
                  v-for="metricGroupCol in metricGroup.cols"
                  :key="metricGroupCol.toString()"
                >
                  <s-cvss-metric-input
                    v-for="m in metricGroupCol"
                    :key="m"
                    :model-value="parsedEditorVector.metrics[m]"
                    @update:model-value="updateMetric(m, $event)"
                    :metric="CVSS31_DEFINITION[m]"
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
import { isValidVector, scoreFromVector, levelNumberFromScore, levelNameFromScore, parseVector, stringifyVector } from "@/utils/cvss";
import { CVSS31_DEFINITION } from "@/utils/cvss/cvss3";
import { CVSS40_DEFINITION } from "@/utils/cvss/cvss4";
import { CvssVersion } from "@/utils/cvss/base";

const props = defineProps<{
  modelValue: string|null;
  label?: string;
  disabled?: boolean;
  cvssVersion?: CvssVersion|null;
  disableValidation?: boolean;
}>();
const emit = defineEmits<{
  (e: 'update:modelValue', value: string|null): void;
}>();

const localSettings = useLocalSettings();

const dialogVisible = ref(false);
const rules = computed(() => {
  if (props.disableValidation) {
    return {
      validCvssVector: [],
    };
  }
  return {
    validCvssVector: [
      (v: string|null|undefined) =>
        isValidVector(v) ||
        [undefined, null, "", "n/a", "n.a."].includes(v) ||
        "Invalid CVSS vector",
      (v: string|null|undefined) => {
        if (v && props.cvssVersion && isValidVector(v) && !v.startsWith(props.cvssVersion)) {
          return `Invalid CVSS version. Expected ${props.cvssVersion}`;
        }
        return true;
      }
    ]
  }
}); 

const editorCvssVersion = ref(CvssVersion.CVSS31);
const availableCvssVersions = ref<CvssVersion[]>([]);

const editorValue = ref(props.modelValue);
watch(() => props.modelValue, () => { editorValue.value = props.modelValue; });
watch(dialogVisible, (newVal) => {
  // Reset temporary editorValue when the dialog is opened
  if (newVal) {
    editorValue.value = props.modelValue;

    editorCvssVersion.value = parseVector(editorValue.value).version || props.cvssVersion || localSettings.cvssVersion;
    if (![CvssVersion.CVSS40, CvssVersion.CVSS31].includes(editorCvssVersion.value)) {
      editorCvssVersion.value = CvssVersion.CVSS31;
    }

    if (props.cvssVersion) {
      availableCvssVersions.value = [props.cvssVersion, editorCvssVersion.value];
    } else {
      availableCvssVersions.value = [CvssVersion.CVSS40, CvssVersion.CVSS31];
    }
  }
});
watch(editorCvssVersion, (newValue, oldValue) => {
  localSettings.cvssVersion = newValue;

  // Migrate metrics when changing CVSS versions
  const prevMetrics = { ...parsedEditorVector.value.metrics };
  if (newValue === CvssVersion.CVSS40 && oldValue === CvssVersion.CVSS31) {
    updateMetric('VC', prevMetrics.C);
    updateMetric('VI', prevMetrics.I);
    updateMetric('VA', prevMetrics.A);
  } else if (newValue === CvssVersion.CVSS31 && oldValue === CvssVersion.CVSS40) {
    updateMetric('C', prevMetrics.VC);
    updateMetric('I', prevMetrics.VI);
    updateMetric('A', prevMetrics.VA);
    updateMetric('S', ([parsedEditorVector.value.metrics.SC, parsedEditorVector.value.metrics.SI, parsedEditorVector.value.metrics.SA].some((v?: string) => v && v !== 'N')) ? 'C' : 'U');
  }
});

function cvssInfo(vector: string|null) {
  const score = scoreFromVector(vector);
  return {
    score,
    scoreFormatted: (score || 0.0).toFixed(1),
    levelNumber: levelNumberFromScore(score),
    levelName: levelNameFromScore(score),
  }
}

const parsedEditorVector = computed(() => parseVector(editorValue.value, editorCvssVersion.value));
const editorScoreInfo = computed(() => cvssInfo(editorValue.value));
const scoreInfo = computed(() => cvssInfo(props.modelValue));

const metricGroupsCvss31 = [
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
const metricGroupsCvss40 = [
  {
    name: 'Base Metrics',
    subgroups: [
      {
        name: 'Exploitability Metrics',
        metrics: ['AV', 'AC', 'AT', 'PR', 'UI'],
      },
      {
        name: 'Vulnerable System Impact Metrics',
        metrics: ['VC', 'VI', 'VA'],
      },
      {
        name: 'Subsequent System Impact Metrics',
        metrics: ['SC', 'SI', 'SA'],
      }
    ]
  },
  {
    name: 'Supplemental Metrics',
    subgroups: [
      {
        name: null,
        metrics: ['S', 'AU', 'R', 'V', 'RE', 'U'],
      }
    ]
  },
  {
    name: 'Environmental (Modified Base Metrics)',
    subgroups: [
      {
        name: 'Exploitability Metrics',
        metrics: ['MAV', 'MAC', 'MAT', 'MPR', 'MUI'],
      },
      {
        name: 'Vulnerable System Impact Metrics',
        metrics: ['MVC', 'MVI', 'MVA'],
      },
      {
        name: 'Subsequent System Impact Metrics',
        metrics: ['MSC', 'MSI', 'MSA'],
      }
    ]
  },
  {
    name: 'Environmental (Security Requirements)',
    subgroups: [
      {
        name: null,
        metrics: ['CR', 'IR', 'AR'],
      },
    ],
  },
  {
    name: 'Threat Metrics',
    subgroups: [
      {
        name: null,
        metrics: ['E'],
      }
    ]
  }
];

function updateMetric(metric: string, val: any) {
  editorValue.value = stringifyVector({ version: editorCvssVersion.value, metrics: { ...parsedEditorVector.value.metrics, [metric]: val } });
}

function applyDialog() {
  dialogVisible.value = false;
  emit('update:modelValue', editorValue.value);
}
</script>

<style scoped lang="scss">
@use "@/assets/settings" as settings;
@use "@/assets/vuetify" as vuetify;

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

.metric-group-header {
  background-color: #808080;
}

.submetric-title {
  @media #{map-get(vuetify.$display-breakpoints, 'lg-and-up')} {
    padding-left: 15em !important;
  }
}
</style>
