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
import { FieldOrigin, type ProjectType } from "~/utils/types";

const props = defineProps<{
  fieldDefinitionList?: TemplateFieldDefinition[];
}>();
const disabled = computed(() => props.fieldDefinitionList !== undefined);

const localSettings = useLocalSettings();
const projectTypeStore = useProjectTypeStore();
const templateStore = useTemplateStore();
useLazyAsyncData(async () => await templateStore.getFieldDefinition());

const fieldDefinitionList = computed(() => props.fieldDefinitionList || templateStore.fieldDefinitionList);

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
  let design = null;
  if (!val || val === 'all') {
    design = null;
  } else {
    try {
      design = await projectTypeStore.getById(val);
    } catch (error) {
      design = null;
    }
  }
  templateStore.setDesignFilter({ design, clear: true });
});

function toggleFieldVisible(d: {id: string}) {
  if (localSettings.templateFieldFilterHiddenFields.includes(d.id)) {
    localSettings.templateFieldFilterHiddenFields = localSettings.templateFieldFilterHiddenFields.filter(f => f !== d.id);
  } else {
    localSettings.templateFieldFilterHiddenFields = [...localSettings.templateFieldFilterHiddenFields, d.id];
  }
}
</script>
