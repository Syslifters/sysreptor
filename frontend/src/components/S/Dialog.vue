<template>
  <v-dialog
    :model-value="props.modelValue"
    @update:model-value="$emit('update:modelValue', $event)"
    :max-width="props.maxWidth"
    :retain-focus="false"
  >
    <template v-if="slots.activator" #activator="{props: dialogProps}"><slot name="activator" v-bind="{props: dialogProps}" /></template>
    <template #default>
      <v-card variant="elevated">
        <v-card-title>
          <v-toolbar color="inherit" flat>
            <v-toolbar-title><slot name="title" /></v-toolbar-title>
            <v-spacer />
            <slot name="toolbar" />

            <v-btn @click="emit('update:modelValue', false)" icon>
              <v-icon icon="mdi-close" size="x-large" />
              <v-tooltip text="Cancel" activator="parent" />
            </v-btn>
          </v-toolbar>
        </v-card-title>

        <slot name="default" />
      </v-card>
    </template>
  </v-dialog>
</template>

<script setup lang="ts">
const props = withDefaults(defineProps<{
  modelValue?: boolean,
  maxWidth?: string
}>(), {
  modelValue: undefined,
  maxWidth: '50%',
});
const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void,
}>();
const slots = useSlots();
</script>
