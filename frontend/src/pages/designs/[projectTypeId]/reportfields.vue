<template>
  <v-form ref="form" class="h-100">
    <split-menu v-model="localSettings.reportFieldDefinitionMenuSize">
      <template #menu>
        <v-list
          v-model:selected="currentItemSelection"
          class="pb-0 h-100 d-flex flex-column"
        >
          <div class="flex-grow-height overflow-y-auto">
            <draggable
              v-model="reportSections"
              item-key="id"
              group="sections"
              :disabled="readonly"
            >
              <template #item="{ element: s }">
                <div>
                  <v-list-item
                    :value="s"
                    :title="s.label"
                    :ripple="false"
                    link
                    class="draggable-handle"
                  >
                    <template #prepend>
                      <v-icon icon="mdi-drag-horizontal" />
                    </template>
                    <template #append>
                      <btn-delete
                        v-if="s.fields.length === 0"
                        :delete="() => deleteSection(s)"
                        :disabled="readonly"
                        button-variant="icon"
                        size="small"
                        density="compact"
                      />
                    </template>
                  </v-list-item>

                  <v-list
                    v-model:selected="currentItemSelection"
                    class="sublist"
                    density="compact"
                  >
                    <draggable
                      :model-value="s.fields"
                      @update:model-value="updateFieldOrder(s, $event)"
                      item-key="id"
                      group="fields"
                      :disabled="readonly"
                    >
                      <template #item="{ element: f}">
                        <v-list-item :value="f" class="draggable-handle" :ripple="false" link>
                          <template #prepend>
                            <v-icon icon="mdi-drag-horizontal" />
                          </template>
                          <template #default>
                            <v-list-item-title class="text-body-2">{{ f.id }}</v-list-item-title>
                          </template>
                          <template #append>
                            <btn-delete
                              v-if="f.origin !== FieldOrigin.CORE"
                              :delete="() => deleteField(s, f)"
                              :disabled="readonly"
                              button-variant="icon"
                              size="small"
                              density="compact"
                            />
                          </template>
                        </v-list-item>
                      </template>
                    </draggable>

                    <v-list-item>
                      <s-btn-secondary
                        @click.stop="addField(s)"
                        size="x-small"
                        :disabled="readonly"
                        prepend-icon="mdi-plus"
                        text="Add Field"
                      />
                    </v-list-item>
                  </v-list>

                  <v-divider />
                </div>
              </template>
            </draggable>
          </div>

          <div>
            <v-divider class="mb-1" />
            <v-list-item>
              <s-btn-secondary
                @click.stop="addSection"
                :disabled="readonly"
                size="small"
                block
                prepend-icon="mdi-plus"
                text="Add Section"
              />
            </v-list-item>
          </div>
        </v-list>
      </template>

      <template #default>
        <edit-toolbar v-bind="toolbarAttrs" :form="$refs.form as VForm" />

        <template v-if="currentItemIsSection">
          <s-card>
            <v-card-title>Section: {{ currentItemSection!.label }}</v-card-title>
            <v-card-text>
              <v-row>
                <v-col>
                  <s-text-field
                    :model-value="currentItemSection!.id"
                    @update:model-value="updateCurrentSection('id', $event)"
                    label="Section ID"
                    :rules="rules.sectionId"
                    required
                    spellcheck="false"
                    :readonly="readonly"
                  />
                </v-col>
                <v-col>
                  <s-text-field
                    :model-value="currentItemSection!.label"
                    @update:model-value="updateCurrentSection('label', $event)"
                    label="Label"
                    required
                    spellcheck="false"
                    :readonly="readonly"
                  />
                </v-col>
              </v-row>
            </v-card-text>
          </s-card>
          <design-input-field-definition
            v-for="f in currentItemSection!.fields" :key="f.id"
            :model-value="f"
            @update:model-value="updateCurrentSectionField(f, $event)"
            :can-change-structure="![FieldOrigin.CORE, FieldOrigin.PREDEFINED].includes(f.origin as any)"
            :lang="projectType.language"
            :readonly="readonly"
            :is-object-property="true"
          />
          <s-btn-secondary
            @click.stop="addField(currentItemSection!)"
            :disabled="readonly"
            class="mt-4"
            prepend-icon="mdi-plus"
            text="Add Field"
          />
        </template>
        <template v-else-if="currentItemIsField">
          <design-input-field-definition
            :model-value="currentItemField!"
            @update:model-value="updateCurrentField"
            :can-change-structure="![FieldOrigin.CORE, FieldOrigin.PREDEFINED].includes(currentItemField!.origin as any)"
            :lang="projectType.language"
            :readonly="readonly"
          />
        </template>
      </template>
    </split-menu>
  </v-form>
</template>

<script setup lang="ts">
import Draggable from "vuedraggable";
import { omit, isEqual } from 'lodash-es';
import { VForm } from "vuetify/components";
import { uniqueName } from '@/utils/urls';
import { FieldOrigin } from "~/utils/types";

const localSettings = useLocalSettings();

const { projectType, toolbarAttrs, readonly } = useProjectTypeLockEdit(await useProjectTypeLockEditOptions({
  save: true,
  saveFields: ['report_sections', 'report_fields'],
}));

const reportSections = computed({
  get: () => projectType.value.report_sections
    .map(s => ({
      ...s,
      fields: s.fields.map(f => ({ id: f, ...projectType.value.report_fields[f] }))
    } as ReportSectionDefinitionWithFieldDefinition)),
  set: (val) => {
    projectType.value.report_sections = val.map(s => ({ ...s, fields: s.fields.map(f => f.id) }));
    if (currentItemSection.value) {
      currentItem.value = reportSections.value.find(s => s.id === currentItemSection.value!.id)!;
    }
  }
})
const reportFields = computed(() => reportSections.value.map(s => s.fields).flat());

const currentItem = ref<FieldDefinitionWithId|ReportSectionDefinitionWithFieldDefinition|null>(null);
const currentItemIsField = computed(() => reportFields.value.some(f => isEqual(f, currentItem.value)));
const currentItemIsSection = computed(() => currentItem.value && !currentItemIsField.value && reportSections.value.some(s => s.id === currentItem.value!.id));
const currentItemSelection = computed({
  get: () => currentItem.value ? [currentItem.value] : [],
  set: (val) => {
    currentItem.value = (val.length > 0) ? val[0] : null;
  }
});
const currentItemSection = computed(() => currentItemIsSection ? currentItem.value as ReportSectionDefinitionWithFieldDefinition : null);
const currentItemField = computed(() => currentItemIsField ? currentItem.value as FieldDefinitionWithId : null);

const rules = {
  sectionId: [
    (id: string) => /^[a-zA-Z0-9_-]+$/.test(id) || 'Invalid ID',
  ]
};

function updateField(field: FieldDefinitionWithId, val: FieldDefinitionWithId) {
  // Update field order in section
  const section = projectType.value.report_sections.find(s => s.fields.includes(field.id));
  if (!section) {
    return;
  }
  const oldIdx = section.fields.indexOf(field.id);
  if (oldIdx !== -1) {
    section.fields[oldIdx] = val.id;
  } else {
    section.fields.push(val.id);
  }

  // Update field definition
  delete projectType.value.report_fields[field.id];
  projectType.value.report_fields[val.id] = omit(val, ['id']);
}
function updateCurrentSectionField(field: FieldDefinitionWithId, val: FieldDefinitionWithId) {
  const sectionId = currentItem.value!.id;
  updateField(field, val);

  currentItem.value = reportSections.value.find(s => s.id === sectionId)!;
}
function updateCurrentField(val: FieldDefinitionWithId) {
  updateField(currentItem.value as FieldDefinitionWithId, val);

  currentItem.value = reportFields.value.find(f => f.id === val.id) || null;
}
function updateFieldOrder(section: ReportSectionDefinitionWithFieldDefinition, fields: FieldDefinitionWithId[]) {
  const ptSection = projectType.value.report_sections.find(s => s.id === section.id)!;
  ptSection.fields = fields.map(f => f.id);
  if (currentItemField.value) {
    currentItem.value = reportFields.value.find(f => f.id === currentItemField.value!.id)!;
  }
}
function addField(section: ReportSectionDefinitionWithFieldDefinition) {
  const ptSection = projectType.value.report_sections.find(s => s.id === section.id)!;
  const fieldId = uniqueName('new_field', Object.keys(projectType.value.report_fields));
  projectType.value.report_fields[fieldId] = {
    type: FieldDataType.STRING,
    label: 'New Field',
    required: true,
    default: 'TODO: fill field in report',
    origin: FieldOrigin.CUSTOM,
  };
  ptSection.fields.push(fieldId);

  if (currentItemIsSection.value && section.id === currentItem.value?.id) {
    currentItem.value = reportSections.value.find(s => s.id === section.id)!;
  } else {
    currentItem.value = reportSections.value.find(s => s.id === section.id)!.fields.find(f => f.id === fieldId)!;
  }
}
function deleteField(section: ReportSectionDefinitionWithFieldDefinition, field: FieldDefinitionWithId) {
  const ptSection = projectType.value.report_sections.find(s => s.id === section.id)!;
  ptSection.fields = ptSection.fields.filter(f => f !== field.id);
  delete projectType.value.report_fields[field.id];
}
function updateCurrentSection(sectionField: string, val: any) {
  const ptSection = projectType.value.report_sections.find(s => s.id === currentItem.value!.id)!;
  // @ts-ignore
  ptSection[sectionField] = val;
  currentItem.value = reportSections.value.find(s => s.id === ptSection.id)!;
}
function addSection() {
  const sectionId = uniqueName('section', projectType.value.report_sections.map(s => s.id));
  projectType.value.report_sections.push({ id: sectionId, label: 'New Section', fields: [] });
  currentItem.value = reportSections.value.find(s => s.id === sectionId)!;
}
function deleteSection(section: ReportSectionDefinitionWithFieldDefinition) {
  projectType.value.report_sections = projectType.value.report_sections.filter(s => s.id !== section.id);
}
</script>

<style lang="scss" scoped>
.sublist {
  margin-left: 1em;
  padding-top: 0;
  padding-bottom: 0;
}

.draggable-handle {
  cursor: grab;
}

:deep(.v-list-item__prepend) {
  .v-list-item__spacer {
    width: 0.5em;
  }
}
</style>
