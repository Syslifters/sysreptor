<template>
  <v-chip small class="ma-1">
    <v-icon small left>mdi-tag</v-icon> {{ value }}
  </v-chip>
</template>

<script>
export default {
  props: {
    value: {
      type: String,
      required: true,
    }
  }
}
</script>
