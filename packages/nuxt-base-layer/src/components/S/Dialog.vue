<template>
  <v-dialog
    :model-value="props.modelValue"
    @update:model-value="emit('update:modelValue', $event)"
    :max-width="props.maxWidth"
    :retain-focus="false"
  >
    <template v-if="$slots.activator" #activator="{props: dialogProps}"><slot name="activator" v-bind="{props: dialogProps}" /></template>
    <template #default>
      <v-card variant="elevated" :density="props.density" v-bind="props.cardProps">
        <v-card-title>
          <v-toolbar color="inherit" flat :density="props.density">
            <v-toolbar-title><slot name="title" /></v-toolbar-title>
            <slot name="toolbar" />

            <s-btn-icon @click="emit('update:modelValue', false)">
              <v-icon size="x-large" icon="mdi-close" />
              <v-tooltip activator="parent" text="Cancel" />
            </s-btn-icon>
          </v-toolbar>
        </v-card-title>

        <slot name="default" />
      </v-card>
    </template>
  </v-dialog>
</template>

<script setup lang="ts">
import { VCard } from "vuetify/lib/components/index.mjs";

const props = withDefaults(defineProps<{
  modelValue?: boolean,
  maxWidth?: string
  density?: VCard['density'],
  cardProps?: any,
}>(), {
  modelValue: undefined,
  maxWidth: '50%',
  density: 'default',
  cardProps: undefined,
});
const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void,
}>();
</script>
