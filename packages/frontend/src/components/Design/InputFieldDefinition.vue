<template>
  <s-card class="mt-4" :class="{'field-highlight-nested1': props.nestingLevel % 2 === 0, 'field-highlight-nested2': props.nestingLevel % 2 === 1}">
    <v-card-text>
      <v-row v-if="!props.isListItem">
        <v-col>
          <s-text-field
            :model-value="props.modelValue.id"
            @update:model-value="updateProperty('id', $event)"
            :rules="rules.id"
            :disabled="!props.canChangeStructure"
            :readonly="props.readonly"
            label="ID"
            hint="Used to access this field in report templates"
            required
            spellcheck="false"
          />
        </v-col>
        <v-col>
          <s-select
            :model-value="props.modelValue.type"
            @update:model-value="updateType($event)"
            :items="Object.values(FieldDataType).filter(t => !([FieldDataType.JSON] as FieldDataType[]).includes(t))"
            :disabled="!props.canChangeStructure"
            :readonly="props.readonly"
            label="Data Type"
            hint="Data type of this field. Controls the allowed values and input form."
            required
          />
        </v-col>

        <v-col>
          <s-text-field
            :model-value="props.modelValue.label"
            @update:model-value="updateProperty('label', $event)"
            :readonly="props.readonly"
            label="Label"
            hint="Friendly name used in input forms for this field"
            required
            spellcheck="false"
          />
        </v-col>
      </v-row>
      <s-select
        v-else
        :model-value="props.modelValue.type"
        @update:model-value="updateProperty('type', $event)"
        :items="Object.values(FieldDataType)"
        :disabled="!props.canChangeStructure"
        :readonly="props.readonly"
        label="Data Type"
        hint="Data type of this field. Controls the allowed values and input form."
        required
      />

      <v-row v-if="![FieldDataType.BOOLEAN, FieldDataType.OBJECT].includes(props.modelValue.type as any)" class="mt-0">
        <v-col class="mt-2 pt-0">
          <s-checkbox
            :model-value="props.modelValue.required || false"
            @update:model-value="updateProperty('required', $event)"
            :readonly="props.readonly"
            label="Required"
            hint="Determines whether this field is required (must be filled) or optional (can be empty)"
          />
        </v-col>

        <!-- String options -->
        <template v-if="props.modelValue.type === FieldDataType.STRING">
          <v-col class="mt-2 pt-0">
            <s-checkbox
              :model-value="props.modelValue.spellcheck || false"
              @update:model-value="updateProperty('spellcheck', $event)"
              :readonly="props.readonly"
              label="Spellcheck Supported"
              hint="Support spellchecking for this fields text content."
            />
          </v-col>

          <v-col class="mt-2 pt-0">
            <s-combobox
              :model-value="props.modelValue.pattern"
              @update:model-value="updateProperty('pattern', $event)"
              :items="predefinedRegexPatterns.map(p => p.value)"
              :readonly="props.readonly"
              label="Pattern"
              hint="RegEx pattern to validate the input against."
              :clearable="!props.readonly"
              :rules="rules.pattern"
              spellcheck="false"
            >
              <template #item="{item, props: itemProps}">
                <v-list-item 
                  v-bind="itemProps" 
                  :title="predefinedRegexPatterns.find(p => p.value === item.value)?.title || 'Custom'" 
                  :subtitle="predefinedRegexPatterns.find(p => p.value === item.value)?.value || ''"
                />
              </template>
            </s-combobox>
          </v-col>
        </template>

        <!-- Number options -->
        <template v-if="props.modelValue.type === FieldDataType.NUMBER">
          <v-col class="mt-2 pt-0">
            <v-number-input
              :model-value="props.modelValue.minimum || null"
              @update:model-value="updateProperty('minimum', $event)"
              label="Minimum"
              :rules="rules.minimum"
              :persistent-hint="true"
              hide-details="auto"
              :max-errors="100"
              variant="outlined"
              control-variant="stacked"
              clearable
            />
          </v-col>
          <v-col class="mt-2 pt-0">
            <v-number-input
              :model-value="props.modelValue.maximum || null"
              @update:model-value="updateProperty('maximum', $event)"
              label="Maximum"
              :rules="rules.maximum"
              :persistent-hint="true"
              hide-details="auto"
              :max-errors="100"
              variant="outlined"
              control-variant="stacked"
              clearable
            />
          </v-col>
        </template>

        <!-- CVSS Options -->
        <template v-if="props.modelValue.type === FieldDataType.CVSS">
          <v-col class="mt-0 pt-0">
            <s-select
              :model-value="props.modelValue.cvss_version || null"
              @update:model-value="updateProperty('cvss_version', $event)"
              :items="[{ title: 'Any', value: null }, CvssVersion.CVSS40, CvssVersion.CVSS31]"
              :readonly="props.readonly"
              label="CVSS Version"
              hint="Require a specific CVSS version"
              class="mt-2"
            />
          </v-col>
          <v-col />
        </template>
      </v-row>

      <!-- Enum choices -->
      <v-list v-if="props.modelValue.type === FieldDataType.ENUM" class="bg-inherit">
        <draggable
          :model-value="props.modelValue.choices || []"
          @update:model-value="updateEnumChoice('sort', 0, $event)"
          :item-key="(item: EnumFieldChoiceDefinition) => (props.modelValue.choices || []).indexOf(item)"
          :disabled="props.readonly || !props.canChangeStructure"
          handle=".draggable-handle"
        >
          <template #item="{ element: choice, index: choiceIdx }">
            <v-lazy :min-height="50">
              <v-list-item>
                <template #prepend>
                  <v-icon
                    size="x-large"
                    class="draggable-handle"
                    :disabled="props.readonly || !props.canChangeStructure"
                    icon="mdi-drag-horizontal"
                  />
                </template>
                <template #default>
                  <v-row>
                    <v-col>
                      <s-text-field
                        :model-value="choice.value"
                        @update:model-value="updateEnumChoice('updateValue', choiceIdx, $event)"
                        :disabled="!props.canChangeStructure"
                        :readonly="props.readonly"
                        :rules="rules.choice"
                        label="Value"
                        required
                        spellcheck="false"
                        class="mt-2"
                      />
                    </v-col>
                    <v-col>
                      <s-text-field
                        :model-value="choice.label"
                        @update:model-value="updateEnumChoice('updateLabel', choiceIdx, $event)"
                        :readonly="props.readonly"
                        label="Label"
                        required
                        spellcheck="false"
                        class="mt-2"
                      />
                    </v-col>
                  </v-row>
                </template>
                <template #append>
                  <btn-delete
                    :delete="() => updateEnumChoice('delete', choiceIdx)"
                    :confirm="false"
                    :disabled="props.readonly || !props.canChangeStructure"
                    button-variant="icon"
                  />
                </template>
              </v-list-item>
            </v-lazy>
          </template>
        </draggable>
        <v-list-item>
          <s-btn-secondary
            @click="updateEnumChoice('add', 0)"
            :disabled="props.readonly || !props.canChangeStructure"
            prepend-icon="mdi-plus"
            text="Add Value"
          />
        </v-list-item>
      </v-list>

      <!-- Combobox suggestions -->
      <v-list v-if="props.modelValue.type === FieldDataType.COMBOBOX" class="bg-inherit">
        <draggable
          :model-value="props.modelValue.suggestions || []"
          @update:model-value="updateComboboxSuggestion('sort', 0, $event)"
          :item-key="(item: string) => props.modelValue.suggestions!.indexOf(item)"
          :disabled="props.readonly || !props.canChangeStructure"
          handle=".draggable-handle"
        >
          <template #item="{ element: suggestion, index: suggestionIdx }">
            <v-list-item>
              <template #prepend>
                <v-icon
                  size="x-large"
                  class="draggable-handle"
                  :disabled="props.readonly || !props.canChangeStructure"
                  icon="mdi-drag-horizontal"
                />
              </template>
              <template #default>
                <s-text-field
                  :model-value="suggestion"
                  @update:model-value="updateComboboxSuggestion('update', suggestionIdx, $event)"
                  :disabled="!props.canChangeStructure"
                  :readonly="props.readonly"
                  label="Value"
                  required
                  spellcheck="false"
                  class="mt-2"
                />
              </template>
              <template #append>
                <btn-delete
                  :delete="() => updateComboboxSuggestion('delete', suggestionIdx)"
                  :confirm="false"
                  :disabled="props.readonly || !props.canChangeStructure"
                  button-variant="icon"
                />
              </template>
            </v-list-item>
          </template>
        </draggable>

        <v-list-item>
          <s-btn-secondary
            @click="updateComboboxSuggestion('add', 0)"
            :disabled="props.readonly || !props.canChangeStructure"
            prepend-icon="mdi-plus"
            text="Add Value"
          />
        </v-list-item>
      </v-list>

      <dynamic-input-field
        v-if="![FieldDataType.OBJECT, FieldDataType.LIST, FieldDataType.USER].includes(props.modelValue.type as any)"
        :model-value="props.modelValue.default"
        @update:model-value="updateProperty('default', $event)"
        :definition="({...props.modelValue, label: 'Default Value', required: false, pattern: null} as FieldDefinition)"
        :lang="props.lang"
        v-model:spellcheck-enabled="localSettings.designSpellcheckEnabled"
        v-model:markdown-editor-mode="localSettings.designMarkdownEditorMode"
        :readonly="props.readonly"
        :disable-validation="true"
        data-testid='default-value'
      />

      <!-- List Item -->
      <design-input-field-definition
        v-else-if="props.modelValue.type === FieldDataType.LIST"
        :model-value="props.modelValue.items!"
        @update:model-value="updateProperty('items', $event)"
        :is-list-item="true"
        :nesting-level="props.nestingLevel + 1"
        :can-change-structure="props.canChangeStructure"
        :lang="props.lang"
        :readonly="props.readonly"
      />
      <!-- Object -->
      <v-list v-else-if="props.modelValue.type === FieldDataType.OBJECT" class="bg-inherit">
        <v-list-item v-for="f, fIdx in props.modelValue.properties || []" :key="fIdx">
          <template #default>
            <design-input-field-definition
              :model-value="f"
              @update:model-value="updateObject('update', fIdx, $event)"
              :nesting-level="props.nestingLevel + 1"
              :can-change-structure="props.canChangeStructure"
              :lang="props.lang"
              :readonly="props.readonly"
              :sibling-field-ids="props.modelValue.properties?.filter(p => p !== f).map(p => p.id)"
            />
          </template>
          <template #append>
            <div class="d-flex flex-column">
              <btn-delete
                :delete="() => updateObject('delete', fIdx)"
                :disabled="props.readonly || !props.canChangeStructure"
                button-variant="icon"
                density="comfortable"
              />
              <s-btn-icon 
                @click="updateObject('move', fIdx, fIdx - 1)"
                :disabled="props.readonly || fIdx === 0"
                density="comfortable"
              >
                <v-icon icon="mdi-arrow-up-drop-circle-outline" />
                <s-tooltip activator="parent" text="Move up in list" />
              </s-btn-icon>

              <s-btn-icon
                @click="updateObject('move', fIdx, fIdx + 1)"
                :disabled="props.readonly || fIdx === props.modelValue.properties!.length - 1"
                density="comfortable"
              >
                <v-icon icon="mdi-arrow-down-drop-circle-outline" />
                <s-tooltip activator="parent" text="Move down in list" />
              </s-btn-icon>
            </div>
          </template>
        </v-list-item>

        <v-list-item>
          <v-divider class="mb-2" />
          <s-btn-secondary
            @click="updateObject('add')"
            :disabled="props.readonly || !props.canChangeStructure"
            prepend-icon="mdi-plus"
            text="Add property"
          />
        </v-list-item>
      </v-list>
    </v-card-text>
  </s-card>
</template>

<script setup lang="ts">
import Draggable from "vuedraggable";
import { CvssVersion } from "@base/utils/cvss/base";
import { FieldDataType, FieldOrigin } from "#imports";

const props = withDefaults(defineProps<{
  modelValue: FieldDefinition;
  canChangeStructure?: boolean;
  isListItem?: boolean;
  readonly?: boolean;
  lang?: string|null;
  nestingLevel?: number;
  siblingFieldIds?: string[];
}>(), {
  lang: null,
  nestingLevel: 0,
  siblingFieldIds: () => [],
});
const emit = defineEmits<{
  'update:modelValue': [FieldDefinition];
}>();

const localSettings = useLocalSettings();

const rules = {
  id: [
    (id: string) => (
      /^[a-zA-Z_][a-zA-Z0-9_]*$/.test(id)
    ) || 'Invalid field ID',
    (id: string) => !props.siblingFieldIds.includes(id) || 'Field ID is not unique. This ID is already used by another field.',
  ],
  choice: [
    // v => (choices || []).filter(c => c.value === v).length === 1 || 'Enum value is not unique',
    (v: string) => /^[a-zA-Z0-9_-]+$/.test(v) || 'Invalid enum value',
  ],
  pattern: [
    (v: string) => {
      try {
        new RegExp(v);
        return true;
      } catch (e: any) {
        return e.message || 'Invalid regular expression';
      }
    },
  ],
  minimum: [
    (v: number) => v === null || v <= (props.modelValue.maximum ?? Number.MAX_SAFE_INTEGER) || 'Minimum must be smaller than maximum',
  ],
  maximum: [
    (v: number) => v === null || v >= (props.modelValue.minimum ?? Number.MIN_SAFE_INTEGER) || 'Maximum must be larger than minimum',
  ]
};

const predefinedRegexPatterns = [
  { title: 'E-Mail', value: "^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$" },
  { title: 'URL', value: "^(http(s)?:\\/\\/.)?[-a-zA-Z0-9@:%._\\+~#=]{1,256}\\.[a-zA-Z0-9()]{1,6}\\b([-a-zA-Z0-9()@:%_\\+.~#?&//=]*)$" },
  { title: 'UUID', value: "^[a-fA-F0-9]{8}-?[a-fA-F0-9]{4}-?[a-fA-F0-9]{4}-?[a-fA-F0-9]{4}-?[a-fA-F0-9]{12}$" },
  { title: 'Custom', value: null },
];

function updateProperty(property: string, val: any) {
  emit('update:modelValue', { ...props.modelValue, [property]: val });
}
function updateType(type: FieldDataType) {
  const newObj = { ...props.modelValue, type };

  // if type changes, ensure that default has the correct data type or set to null
  const def = props.modelValue.default;
  if (
    ([FieldDataType.STRING, FieldDataType.MARKDOWN, FieldDataType.CVSS, FieldDataType.COMBOBOX].includes(type) && !(def instanceof String)) ||
        (type === FieldDataType.NUMBER && !(def instanceof Number)) ||
        (type === FieldDataType.BOOLEAN && !(def instanceof Boolean)) ||
        (type === FieldDataType.ENUM && !(newObj.choices || []).find(c => c.value === def)) ||
        (type === FieldDataType.CWE && (!(def instanceof String) || !def.startsWith('CWE-'))) ||
        (type === FieldDataType.DATE) ||
        (type === FieldDataType.USER)
  ) {
    if (def !== null) {
      newObj.default = null;
    }
  }
  emit('update:modelValue', newObj);
}
function updateEnumChoice(action: string, choiceIdx: number, val?: any) {
  const newObj = { ...props.modelValue, choices: [...props.modelValue.choices!] };
  if (action === 'updateValue') {
    newObj.choices[choiceIdx]!.value = val;
  } else if (action === 'updateLabel') {
    newObj.choices[choiceIdx]!.label = val || '';
  } else if (action === 'delete') {
    newObj.choices = newObj.choices.filter((_, idx) => idx !== choiceIdx);
  } else if (action === 'add') {
    if (!val) {
      val = {
        value: uniqueName('new_value', newObj.choices.map(c => c.value || '')),
        label: 'New Enum Value',
      };
    }
    newObj.choices.push(val);
  } else if (action === 'sort') {
    newObj.choices = val;
  }

  emit('update:modelValue', newObj);
}
function updateComboboxSuggestion(action: string, suggestionIdx: number, val?: any) {
  const newObj = { ...props.modelValue, suggestions: [...props.modelValue.suggestions!] };
  if (action === 'update') {
    newObj.suggestions.splice(suggestionIdx, 1, val);
  } else if (action === 'delete') {
    newObj.suggestions.splice(suggestionIdx, 1);
  } else if (action === 'add') {
    newObj.suggestions.push(uniqueName('New Value', newObj.suggestions));
  } else if (action === 'sort') {
    newObj.suggestions = val;
  }
  emit('update:modelValue', newObj);
}
function updateObject(action: string, fieldIdx?: number, val?: FieldDefinition|any) {
  const newObj = { ...props.modelValue, properties: [...(props.modelValue.properties || [])] };
  if (action === "update") {
    newObj.properties = newObj.properties.map((f, idx) => idx !== fieldIdx ? f : val!);
  } else if (action === "delete") {
    newObj.properties = newObj.properties.filter((_, idx) => idx !== fieldIdx);
  } else if (action === 'add') {
    if (!val) {
      val = {
        id: '',
        type: FieldDataType.STRING,
        label: 'New Field',
        required: true,
        spellcheck: false,
        pattern: null,
        default: null,
        origin: FieldOrigin.CUSTOM,
      };
    }
    if (!val.id) {
      val.id = uniqueName('new_field', newObj.properties.map(f => f.id));
    }
    newObj.properties.push(val);
  } else if (action === 'sort') {
    newObj.properties = val;
  } else if (action === 'move') {
    const [moved] = newObj.properties.splice(fieldIdx!, 1);
    newObj.properties.splice(val!, 0, moved!);
  }
  emit('update:modelValue', newObj);
}

watch(() => props.modelValue.type, () => {
  if (props.modelValue.type === FieldDataType.ENUM && !props.modelValue.choices) {
    updateProperty('choices', [{ value: 'enum_val', label: 'Enum Value' }] as FieldDefinition['choices']);
  } else if (props.modelValue.type === FieldDataType.COMBOBOX && !props.modelValue.suggestions) {
    updateProperty('suggestions', ['Combobox Value'] as FieldDefinition['suggestions']);
  } else if (props.modelValue.type === FieldDataType.LIST && !props.modelValue.items) {
    updateProperty('items', { type: FieldDataType.STRING, default: null } as FieldDefinition['items']);
  } else if (props.modelValue.type === FieldDataType.OBJECT && !props.modelValue.properties) {
    updateProperty('properties', [{ id: 'nested_field', type: FieldDataType.STRING, label: 'Nested Field', default: null }] as FieldDefinition['properties']);
  }
});

</script>

<style lang="scss" scoped>
.draggable-handle {
  cursor: grab;
}
.v-list-item:deep(.v-list-item__prepend .v-list-item__spacer) {
  width: 0.5em;
}
</style>
