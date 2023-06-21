<template>
  <s-tooltip :disabled="!value.name">
    <template #activator="{ on }">
      <v-chip v-bind="$attrs" v-on="{...on, ...$listeners}" small class="ma-1" :class="{'text--secondary': imported}">
        <template v-if="imported">
          <v-icon small left class="text--secondary">mdi-account-cancel</v-icon>
          {{ value.name }}
        </template>
        <template v-else>
          <v-icon small left>mdi-account</v-icon>
          {{ value.username }}
        </template>
      </v-chip>
    </template>
    <template #default>
      <span v-if="imported">{{ value.name }} (imported)</span>
      <span v-else>{{ value.name }}</span>
    </template>
  </s-tooltip>
</template>

<script>
export default {
  props: {
    value: {
      type: Object,
      required: true,
    },
    imported: {
      type: Boolean,
      default: false,
    }
  }
}
</script>
