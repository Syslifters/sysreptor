<template>
  <v-form ref="form" class="h-100">
    <split-menu v-model="localSettings.reportFieldDefinitionMenuSize" :content-props="{ class: 'h-100 pa-0' }">
      <template #menu>
        <v-list
          v-model:selected="currentItemSelection"
          class="pt-0 pb-0 h-100 d-flex flex-column"
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
                      <template #item="{ element: f }">
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
        <div class="h-100 d-flex flex-column">
          <edit-toolbar v-bind="toolbarAttrs" :form="$refs.form as VForm" />

          <v-container fluid class="pt-0 flex-grow-height overflow-y-auto">
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
                v-for="f, fIdx in currentItemSection!.fields" :key="fIdx"
                :model-value="f"
                @update:model-value="updateField(f, $event)"
                :can-change-structure="![FieldOrigin.CORE, FieldOrigin.PREDEFINED].includes(f.origin as any)"
                :lang="projectType.language"
                :readonly="readonly"
                :sibling-field-ids="allReportFields.filter(rf => rf !== f).map(rf => rf.id)"
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
                @update:model-value="updateField(currentItemField!, $event)"
                :can-change-structure="![FieldOrigin.CORE, FieldOrigin.PREDEFINED].includes(currentItemField!.origin as any)"
                :lang="projectType.language"
                :readonly="readonly"
                :sibling-field-ids="allReportFields.filter(rf => rf !== currentItemField!).map(rf => rf.id)"
              />
            </template>
          </v-container>
        </div>
      </template>
    </split-menu>
  </v-form>
</template>

<script setup lang="ts">
import Draggable from "vuedraggable";
import { VForm } from "vuetify/components";
import { FieldOrigin, type ReportSectionDefinition, uniqueName } from "#imports";

const localSettings = useLocalSettings();

const { projectType, toolbarAttrs, readonly } = useProjectTypeLockEdit(await useProjectTypeLockEditOptions({
  save: true,
  saveFields: ['report_sections'],
}));

const reportSections = computed({
  get: () => projectType.value.report_sections,
  set: (val) => {
    projectType.value.report_sections = val;
    if (currentItemSection.value) {
      currentItem.value = reportSections.value.find(s => s.id === currentItemSection.value!.id)!;
    }
  }
});
const allReportFields = computed(() => reportSections.value.map(s => s.fields).flat());

const currentItem = ref<FieldDefinition|ReportSectionDefinition|null>(null);
const currentItemIsField = computed(() => allReportFields.value.includes(currentItem.value as any));
const currentItemField = computed(() => currentItemIsField.value ? currentItem.value as FieldDefinition : null);
const currentItemIsSection = computed(() => reportSections.value.includes(currentItem.value as any));
const currentItemSection = computed(() => currentItemIsSection.value ? currentItem.value as ReportSectionDefinition : null);
const currentItemSelection = computed({
  get: () => currentItem.value ? [currentItem.value] : [],
  set: (val) => { currentItem.value = (val.length > 0) ? val[0]! : null; },
});

const rules = {
  sectionId: [
    (id: string) => /^[a-zA-Z0-9_-]+$/.test(id) || 'Invalid ID format',
    (id: string) => !reportSections.value.filter(s => s !== currentItemSection.value).map(s => s.id).includes(id) || 'Section ID is not unique. This ID is already used by another section.',
  ]
};

function updateField(field: FieldDefinition, val: FieldDefinition) {
  Object.keys(field).forEach(k => delete field[k as keyof FieldDefinition]);
  Object.assign(field, val);
}
function updateFieldOrder(section: ReportSectionDefinition, fields: FieldDefinition[]) {
  section.fields = fields;
}
function addField(section: ReportSectionDefinition) {
  const fieldId = uniqueName('new_field', allReportFields.value.map(f => f.id));
  section.fields.push({
    id: fieldId,
    type: FieldDataType.STRING,
    label: 'New Field',
    required: true,
    default: 'TODO: fill field in report',
    origin: FieldOrigin.CUSTOM,
  });

  if (currentItem.value !== section) {
    currentItem.value = section.fields.find(f => f.id === fieldId)!;
  }
}
function deleteField(section: ReportSectionDefinition, field: FieldDefinition) {
  section.fields = section.fields.filter(f => f !== field);
}
function updateCurrentSection(sectionField: keyof ReportSectionDefinition, val: any) {
  if (!currentItemSection.value) {
    return;
  }
  currentItemSection.value[sectionField] = val;
}
function addSection() {
  const sectionId = uniqueName('section', projectType.value.report_sections.map(s => s.id));
  const newSection = { id: sectionId, label: 'New Section', fields: [] }
  projectType.value.report_sections.push(newSection);
  currentItem.value = newSection;
}
function deleteSection(section: ReportSectionDefinition) {
  projectType.value.report_sections = projectType.value.report_sections.filter(s => s !== section);
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
