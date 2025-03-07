<template>
  <s-card class="mt-4 mb-4">
    <v-card-title>Finding Grouping</v-card-title>
    <v-card-text>
      <p>
        Group findings by following field in reports:
      </p>

      <v-row dense>
        <v-col cols="6">
          <s-select
            :model-value="modelValue?.[0]?.field"
            @update:model-value="modelValue = $event ? [{field: $event, order: modelValue?.[0]?.order || SortOrder.ASC}] : null"
            label="Field"
            hint="Group finding by field in report. Empty: do not group findings (default)"
            :items="availableFindingFields"
            :readonly="props.readonly"
            clearable
            class="mt-2"
          />
        </v-col>
        <v-col cols="6">
          <s-select
            :model-value="modelValue?.[0]?.order"
            @update:model-value="modelValue = $event ? [{field: modelValue![0]!.field, order: $event}] : null"
            label="Order of groups"
            hint="Order groups in ascending/descending order. Findings in groups are ordered according to finding ordering definition."
            :items="[SortOrder.ASC, SortOrder.DESC]"
            :readonly="props.readonly"
            :disabled="!modelValue?.[0]?.field"
            class="mt-2"
          />
        </v-col>
      </v-row>
    </v-card-text>
  </s-card>
</template>

<script setup lang="ts">
import { FieldDataType, type FindingOrderingDefinition, SortOrder } from '#imports';

const modelValue = defineModel<FindingOrderingDefinition[]|null>();

const props = defineProps<{
  projectType: ProjectType;
  readonly?: boolean;
}>();

const findingFields = computed(() => {
  return props.projectType.finding_fields
    .filter(f => ![FieldDataType.LIST, FieldDataType.OBJECT, FieldDataType.USER, FieldDataType.MARKDOWN, FieldDataType.JSON].includes(f.type));
});
const availableFindingFields = computed(() => {
  return [{ value: null as string|null, title: '---'}].concat(findingFields.value.map(f => ({ value: f.id, title: f.id })));
});

</script>
