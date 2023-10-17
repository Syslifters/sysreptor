<template>
  <v-list density="compact">
    <v-list-item>
      <s-project-type-selection
        v-model="localSettings.templateFieldFilterDesign"
        label="Show fields of"
        :query-filters="{scope: ['global']}"
        variant="underlined"
        :additional-items="[{id: 'all', name: 'All Designs'}] as ProjectType[]"
      />
    </v-list-item>

    <v-list-item v-for="d in templateStore.fieldDefinitionList" :key="d.id">
      <v-list-item-title class="text-body-2">{{ d.id }}</v-list-item-title>
      <template #append v-if="d.origin !== FieldOrigin.CORE">
        <s-btn
          @click="toggleFieldVisible(d)"
          :icon="d.visible ? 'mdi-eye' : 'mdi-eye-off'"
          size="x-small"
        />
      </template>
    </v-list-item>
  </v-list>
</template>

<script setup lang="ts">
import { FieldOrigin, ProjectType } from "~/utils/types";

const localSettings = useLocalSettings();
const templateStore = useTemplateStore();
const projectTypeStore = useProjectTypeStore();
useLazyAsyncData(async () => await templateStore.getFieldDefinition());

watch(() => localSettings.templateFieldFilterDesign, async (val: string) => {
  if (val === 'all') {
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
