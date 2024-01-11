<template>
  <v-select
    :model-value="props.modelValue"
    @update:model-value="emit('update:modelValue', $event)"
    v-model:menu="menuVisible"
    :items="props.items"
    :disabled="props.disabled"
    :readonly="props.readonly"
    multiple chips 
    :closable-chips="!props.readonly"
    density="compact"
    variant="solo"
    hide-details="auto"
    menu-icon=""
    @click.stop
    @mousedown.stop
    @mouseup.stop
    @focus.stop
    class="select-roles"
  >
    <template #chip="{item, props: chipProps}">
      <v-chip
        size="small"
        @click="menuVisible = true"
        v-bind="chipProps"
      >
        {{ item.title }}
      </v-chip>
    </template>
    <template #append-inner>
      <v-chip size="small" @click="menuVisible = true">
        <v-icon size="small" icon="mdi-plus" />
      </v-chip>
    </template>
  </v-select>
</template>

<script setup lang="ts">
const props = defineProps<{
  modelValue: string[];
  items: string[];
  disabled?: boolean;
  readonly?: boolean;
}>();
const emit = defineEmits<{
  (e: 'update:modelValue', value: string[]): void;
}>();

const menuVisible = ref(false);
</script>

<style lang="scss" scoped>
.select-roles:deep() {
  width: max-content;

  .v-field {
    box-shadow: none;
  }
  .v-field__input {
    padding: 0;
    min-height: 0;
  }

  input {
    display: none;
  }

  .v-chip {
    margin: 0.2em 0.2em 0 0 !important;

    &:not(.v-chip--disabled) {
      cursor: pointer;
    }
  }
}
</style>
