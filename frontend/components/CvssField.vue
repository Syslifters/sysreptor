<template>
  <div class="d-flex">
    <div class="flex-grow-1">
      <s-text-field
        :value="value"
        @input="$emit('input', $event)"
        :rules="validCvssVector"
        :label="label"
        :disabled="disabled"
        spellcheck="false"
      />
    </div>

    <div class="flex-grow-0">
      <div class="cvss-score ml-2" :class="'level-' + levelNumber">
        <div class="cvss-score-header">{{ scoreFormatted }}</div>
        <div class="cvss-score-label">{{ levelName }}</div>
      </div>
    </div>

    <s-dialog v-model="dialogVisible" max-width="70%" scrollable>
      <template #activator="{ on, attrs }">
        <s-btn color="secondary" class="ma-3" v-bind="attrs" v-on="on">
          CVSS Editor
        </s-btn>
      </template>

      <template #title>CVSS Editor</template>
      <template #toolbar>
        <div class="cvss-score ma-3" :class="'level-' + editorLevelNumber">
          <div class="cvss-score-header">{{ editorScoreFormatted }}</div>
          <div class="cvss-score-label">{{ editorLevelName }}</div>
        </div>

        <s-tooltip :disabled="disabled">
          <template #activator="{attrs, on}">
            <s-btn @click="applyDialog" :disabled="disabled" icon x-large v-bind="attrs" v-on="on">
              <v-icon>mdi-check-bold</v-icon>
            </s-btn>
          </template>
          <span>Apply</span>
        </s-tooltip>
      </template>

      <template #default>
        <v-card-text class="pa-0">
          <s-card
            v-for="metricGroup in metricGroups"
            :key="metricGroup.name"
            outlined
            flat
            tile
          >
            <v-card-title>
              {{ metricGroup.name }}
            </v-card-title>
            <v-card-text>
              <v-row>
                <v-col
                  v-for="metricGroupCol in metricGroup.cols"
                  :key="metricGroupCol.toString()"
                >
                  <cvss-metric-input
                    v-for="m in metricGroupCol"
                    :key="m"
                    :value="parsedEditorVector[m]"
                    @input="updateMetric(m, $event)"
                    :metric="CVSS_DEFINITON[m]"
                    :disabled="disabled"
                  />
                </v-col>
              </v-row>
            </v-card-text>
          </s-card>
        </v-card-text>
      </template>
    </s-dialog>
  </div>
</template>

<script>
import CvssMetricInput from "./CvssMetricInput.vue";
import * as cvss from "@/utils/cvss.js";

export default {
  components: { CvssMetricInput },
  props: {
    value: {
      type: String,
      required: true,
    },
    label: {
      type: String,
      default: null,
      required: false,
    },
    disabled: {
      type: Boolean,
      default: false,
    }
  },
  emits: ["input"],
  data() {
    return {
      editorValue: this.value,
      dialogVisible: false,
      validCvssVector: [
        v =>
          cvss.isValidVector(v) ||
          ["", "n/a", "n.a."].includes(v) ||
          "Invalid CVSS vector",
      ],
      metricGroups: [
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
      ],
      CVSS_DEFINITON: cvss.CVSS31_DEFINITION,
    };
  },
  computed: {
    parsedEditorVector() {
      return cvss.parseVector(this.editorValue);
    },
    score() {
      return cvss.scoreFromVector(this.value);
    },
    scoreFormatted() {
      return (this.score || 0.0).toFixed(1);
    },
    levelNumber() {
      return cvss.levelNumberFromScore(this.score);
    },
    levelName() {
      return cvss.levelNameFromScore(this.score);
    },
    editorScore() {
      return cvss.scoreFromVector(this.editorValue);
    },
    editorScoreFormatted() {
      return (this.editorScore || 0.0).toFixed(1);
    },
    editorLevelNumber() {
      return cvss.levelNumberFromScore(this.editorScore);
    },
    editorLevelName() {
      return cvss.levelNameFromScore(this.editorScore);
    },
  },
  watch: {
    value(newVal) {
      this.editorValue = newVal;
    },
    dialogVisible(newVal) {
      // Reset temporary editorValue when the dialog is closed
      if (newVal) {
        this.editorValue = this.value;
      }
    }
  },
  methods: {
    updateMetric(metric, val) {
      const vector = Object.assign({}, this.parsedEditorVector);
      vector[metric] = val;
      this.editorValue = cvss.stringifyVector(vector);
    },
    cancelDialog() {
      this.dialogVisible = false;
    },
    applyDialog() {
      this.dialogVisible = false;
      this.$emit('input', this.editorValue);
    },
  },
};
</script>

<style scoped lang="scss">
.cvss-score {
  width: 8em;

  &-header {
    background-color: #dcdcdc;
    text-align: center;
    font-weight: bold;
  }

  &-label {
    text-align: center;
    padding: 0.4em;
  }

  &-bottom {
    height: 0.6em;
    background-color: #808080;
  }
}

@for $level from 1 through 5 {
  .level-#{$level} {
    .cvss-score-header {
      background-color: map-get($risk-color-levels, $level);
      color: white;
    }
    .cvss-score-label {
      color: map-get($risk-color-levels, $level);
    }
  }
}
</style>
