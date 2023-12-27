<template>
  <v-chip class="ma-2" :class="'risk-level-' + levelNumber" label>
    <strong class="level-name">{{ levelName }}</strong>
    <span class="score" v-if="props.riskScore !== null">{{ scoreFormatted }}</span>
  </v-chip>
</template>

<script setup lang="ts">
import capitalize from "lodash/capitalize";
import { RiskLevel } from "@/utils/types";
import { levelNameFromScore, levelNumberFromLevelName, scoreFromVector } from "~/utils/cvss";

const props = withDefaults(defineProps<{
  value?: string|null;
  riskScore?: number|null;
  riskLevel?: RiskLevel|null;
}>(), {
  value: null,
  riskScore: null,
  riskLevel: null,
});
const score = computed(() => {
  if (props.riskScore !== null) {
    return props.riskScore;
  }
  return scoreFromVector(props.value);
});
const scoreFormatted = computed(() => (score.value || 0).toFixed(1));
const levelName = computed(() => {
  if (props.riskLevel) {
    return capitalize(props.riskLevel);
  }
  return levelNameFromScore(score.value);
});
const levelNumber = computed(() => levelNumberFromLevelName(levelName.value));
</script>

<style lang="scss" scoped>
@use "@/assets/settings.scss" as settings;

@for $level from 1 through 5 {
  .risk-level-#{$level} {
    background-color: map-get(settings.$risk-color-levels, $level) !important;
    color: white !important;
    width: 7.7em;
    min-width: 7.7em;
    text-align: center;

    :deep(.v-chip__content) {
      width: 100%;
    }

    .level-name {
      margin-right: auto;
    }
    .score {
      margin-left: auto;
    }
  }
}
</style>
