<template>
  <v-list density="compact" class="pb-0 h-100 d-flex flex-column">
    <v-list-item class="pl-2 pr-2 pt-0">
      <s-project-type-selection
        v-model="templateFieldFilterDesign"
        :query-filters="{scope: [ProjectTypeScope.GLOBAL]}"
        :additional-items="([{id: 'all', name: 'All Designs'}] as ProjectType[])"
        :disabled="disabled"
        label="Show fields of"
        variant="underlined"
      />
    </v-list-item>

    <div class="flex-grow-1 overflow-y-auto">
      <v-hover v-for="d in fieldDefinitionList" :key="d.id">
        <template #default="{ isHovering, props: hoverProps }">
          <v-list-item 
            @click="toggleFieldVisible(d)"
            link
            :class="{'item-disabled': !d.visible}" 
            v-bind="hoverProps"
          >
            <v-list-item-title class="text-body-2">{{ d.id }}</v-list-item-title>
            <template #append v-if="d.origin !== FieldOrigin.CORE && isHovering">
              <s-btn-icon
                :icon="d.visible ? 'mdi-eye' : 'mdi-eye-off'"
                :disabled="disabled"
                size="x-small"
              />
            </template>
          </v-list-item>
        </template>
      </v-hover>
    </div>
  </v-list>
</template>

<script setup lang="ts">
import { FieldOrigin, type ProjectType, type TemplateFieldDefinition } from "~/utils/types";

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
    } catch {
      design = null;
    }
  }
  templateStore.setDesignFilter({ design, clear: true });
});

function toggleFieldVisible(d: TemplateFieldDefinition) {
  if (disabled.value || d.origin === FieldOrigin.CORE) {
    return;
  }

  if (localSettings.templateFieldFilterHiddenFields.includes(d.id)) {
    localSettings.templateFieldFilterHiddenFields = localSettings.templateFieldFilterHiddenFields.filter(f => f !== d.id);
  } else {
    localSettings.templateFieldFilterHiddenFields = [...localSettings.templateFieldFilterHiddenFields, d.id];
  }
}
</script>

<style scoped lang="scss">
.item-disabled {
  opacity: var(--v-disabled-opacity);
}
</style>
