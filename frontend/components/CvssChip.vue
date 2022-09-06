<template>
  <v-chip class="ma-2" :class="'risk-level-' + levelNumber" label>
    <strong class="level-name">{{ levelName }}</strong>
    <span class="score">{{ scoreFormatted }}</span>
  </v-chip>
</template>

<script>
import * as cvss from "@/utils/cvss.js";

export default {
  props: {
    value: {
      type: String,
      required: true,
    }
  },
  computed: {
    score() {
      return cvss.scoreFromVector(this.value);
    },
    scoreFormatted() {
      return (this.score || 0).toFixed(1);
    },
    levelName() {
      return cvss.levelNameFromScore(this.score);
    },
    levelNumber() {
      return cvss.levelNumberFromScore(this.score);
    }
  }
}
</script>

<style lang="scss" scoped>
@for $level from 1 through 5 {
  .risk-level-#{$level} {
    background-color: map-get($risk-color-levels, $level) !important;
    color: white !important;
    width: 7.5em;
    display: inline-block;
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
