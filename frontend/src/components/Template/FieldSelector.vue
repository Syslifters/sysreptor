<template>
  <v-list density="compact">
    <v-list-item>
      <s-project-type-selection
        v-model="templateFieldFilterDesign"
        :query-filters="{scope: [ProjectTypeScope.GLOBAL]}"
        :additional-items="([{id: 'all', name: 'All Designs'}] as ProjectType[])"
        :disabled="disabled"
        label="Show fields of"
        variant="underlined"
      />
    </v-list-item>

    <v-list-item v-for="d in fieldDefinitionList" :key="d.id">
      <v-list-item-title class="text-body-2">{{ d.id }}</v-list-item-title>
      <template #append v-if="d.origin !== FieldOrigin.CORE">
        <s-btn-icon
          @click="toggleFieldVisible(d)"
          :icon="d.visible ? 'mdi-eye' : 'mdi-eye-off'"
          :disabled="disabled"
          size="x-small"
        />
      </template>
    </v-list-item>
  </v-list>
</template>

<script setup lang="ts">
import { FieldOrigin } from "~/utils/types";

const props = defineProps<{
  visibleFieldIds?: string[];
}>();
const disabled = computed(() => props.visibleFieldIds !== undefined);

const localSettings = useLocalSettings();
const templateStore = useTemplateStore();
const projectTypeStore = useProjectTypeStore();
useLazyAsyncData(async () => await templateStore.getFieldDefinition());

const fieldDefinitionList = computed(() => {
  if (props.visibleFieldIds !== undefined) {
    return templateStore.fieldDefinitionList.map(d => ({ ...d, visible: props.visibleFieldIds?.includes(d.id) }));
  } else {
    return templateStore.fieldDefinitionList;
  }
});
const templateFieldFilterDesign = computed({
  get: () => {
    if (disabled.value) {
      return 'all';
    } else {
      return localSettings.templateFieldFilterDesign;
    }
  },
  set: (val) => {
    if (!disabled.value) {
      localSettings.templateFieldFilterDesign = val;
    }
  },
});

watch(() => localSettings.templateFieldFilterDesign, async (val: string) => {
  if (!val) {
    localSettings.templateFieldFilterDesign = 'all';
  } else if (val === 'all') {
    localSettings.templateFieldFilterHiddenFields = [];
  } else {
    try {
      const projectType = await projectTypeStore.getById(val);
      localSettings.templateFieldFilterHiddenFields = templateStore.fieldDefinitionList.filter(d => !Object.keys(projectType.finding_fields).includes(d.id)).map(d => d.id);
    } catch (error) {
      localSettings.templateFieldFilterDesign = 'all';
    }
  }
});

function toggleFieldVisible(d: {id: string}) {
  if (localSettings.templateFieldFilterHiddenFields.includes(d.id)) {
    localSettings.templateFieldFilterHiddenFields = localSettings.templateFieldFilterHiddenFields.filter(f => f !== d.id);
  } else {
    localSettings.templateFieldFilterHiddenFields = [...localSettings.templateFieldFilterHiddenFields, d.id];
  }
}
</script>
