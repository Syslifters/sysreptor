<template>
  <s-card class="mt-4">
    <v-card-text>
      <template v-if="!isListItem">
        <v-row>
          <v-col>
            <s-text-field
              :model-value="props.modelValue.id"
              @update:model-value="updateProperty('id', $event)"
              :rules="rules.id"
              :disabled="props.disabled || !props.canChangeStructure"
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
              :items="Object.values(FieldDataType)"
              :disabled="props.disabled || !props.canChangeStructure"
              label="Data Type"
              hint="Data type of this field. Controls the allowed values and input form."
              required
            />
          </v-col>

          <v-col>
            <s-text-field
              :model-value="props.modelValue.label"
              @update:model-value="updateProperty('label', $event)"
              :disabled="props.disabled"
              label="Label"
              hint="Friendly name used in input forms for this field"
              required
              spellcheck="false"
            />
          </v-col>
        </v-row>
        <v-row v-if="![FieldDataType.BOOLEAN, FieldDataType.OBJECT].includes(props.modelValue.type as any)" class="mt-0">
          <v-col class="mt-0 pt-0">
            <s-checkbox
              :model-value="props.modelValue.required || false"
              @update:model-value="updateProperty('required', $event)"
              :disabled="props.disabled"
              label="Required"
              hint="Determines whether this field is required must be filled or optional"
              class="mt-0"
            />
          </v-col>
          <v-col class="mt-0 pt-0" v-if="props.modelValue.type === FieldDataType.STRING">
            <s-checkbox
              :model-value="props.modelValue.spellcheck || false"
              @update:model-value="updateProperty('spellcheck', $event)"
              :disabled="props.disabled"
              label="Spellcheck Supported"
              hint="Support spellchecking for this fields text content."
              class="mt-0"
            />
          </v-col>
        </v-row>
      </template>
      <s-select
        v-else
        :model-value="props.modelValue.type"
        @update:model-value="updateProperty('type', $event)"
        :items="Object.values(FieldDataType)"
        :disabled="props.disabled || !props.canChangeStructure"
        label="Data Type"
        hint="Data type of this field. Controls the allowed values and input form."
        required
      />

      <!-- Enum choices -->
      <v-list v-if="props.modelValue.type === FieldDataType.ENUM">
        <draggable
          :model-value="props.modelValue.choices || []"
          @update:model-value="updateEnumChoice('sort', 0, $event)"
          :item-key="item => (props.modelValue.choices || []).indexOf(item)"
          :disabled="props.disabled || !props.canChangeStructure"
          handle=".draggable-handle"
        >
          <template #item="{ element: choice, index: choiceIdx }">
            <v-list-item>
              <template #prepend>
                <v-icon
                  size="x-large"
                  class="draggable-handle"
                  :disabled="props.disabled || !props.canChangeStructure"
                  icon="mdi-drag"
                />
              </template>
              <template #default>
                <v-row>
                  <v-col>
                    <s-text-field
                      :model-value="choice.value"
                      @update:model-value="updateEnumChoice('updateValue', choiceIdx, $event)"
                      :disabled="props.disabled || !props.canChangeStructure"
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
                      :disabled="props.disabled"
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
                  :disabled="props.disabled || !props.canChangeStructure"
                  button-variant="icon"
                />
              </template>
            </v-list-item>
          </template>
        </draggable>
        <v-list-item>
          <s-btn
            @click="updateEnumChoice('add', 0)"
            :disabled="props.disabled || !props.canChangeStructure"
            color="secondary"
            prepend-icon="mdi-plus"
            text="Add Value"
          />
        </v-list-item>
      </v-list>

      <!-- Combobox suggestions -->
      <v-list v-if="props.modelValue.type === FieldDataType.COMBOBOX">
        <v-list-item v-for="(suggestion, suggestionIdx) in props.modelValue.suggestions || []" :key="suggestionIdx">
          <template #default>
            <s-text-field
              :model-value="suggestion"
              @update:model-value="updateComboboxSuggestion('update', suggestionIdx, $event)"
              :disabled="props.disabled || !props.canChangeStructure"
              label="Value"
              required
              spellcheck="false"
            />
          </template>
          <template #append>
            <btn-delete
              :delete="() => updateComboboxSuggestion('delete', suggestionIdx)"
              :confirm="false"
              :disabled="props.disabled || !props.canChangeStructure"
              button-variant="icon"
            />
          </template>
        </v-list-item>
        <v-list-item>
          <s-btn
            @click="updateComboboxSuggestion('add', 0)"
            :disabled="props.disabled || !props.canChangeStructure"
            color="secondary"
            prepend-icon="mdi-plus"
            text="Add Value"
          />
        </v-list-item>
      </v-list>

      <dynamic-input-field
        v-if="![FieldDataType.OBJECT, FieldDataType.LIST, FieldDataType.USER].includes(props.modelValue.type as any)"
        :model-value="props.modelValue.default"
        @update:model-value="updateProperty('default', $event)"
        :definition="{...props.modelValue, label: 'Default Value', required: false} as FieldDefinition"
        :lang="props.lang"
        :disabled="props.disabled"
      />

      <!-- List Item -->
      <design-input-field-definition
        v-else-if="props.modelValue.type === FieldDataType.LIST"
        :model-value="props.modelValue.items! as FieldDefinitionWithId"
        @update:model-value="updateProperty('items', $event)"
        :is-list-item="true"
        :can-change-structure="props.canChangeStructure"
        :lang="props.lang"
        :disabled="props.disabled"
      />
      <!-- Object -->
      <v-list v-else-if="props.modelValue.type === FieldDataType.OBJECT">
        <v-list-item v-for="f in objectFields" :key="f.id">
          <template #default>
            <design-input-field-definition
              :model-value="f"
              @update:model-value="updateObject('update', f.id, $event)"
              :is-object="false"
              :can-change-structure="props.canChangeStructure"
              :lang="props.lang"
              :disabled="props.disabled"
            />
          </template>
          <template #append>
            <btn-delete
              :delete="() => updateObject('delete', f.id)"
              :disabled="props.disabled || !props.canChangeStructure"
              button-variant="icon"
            />
          </template>
        </v-list-item>

        <v-divider />
        <v-list-item>
          <s-btn
            @click="updateObject('add')"
            :disabled="props.disabled || !props.canChangeStructure"
            color="secondary"
            prepend-icon="mdi-plus"
            text="Add property"
          />
        </v-list-item>
      </v-list>
    </v-card-text>
  </s-card>
</template>

<script setup lang="ts">
import omit from "lodash/omit";
import Draggable from "vuedraggable";
import { FieldDataType, FieldDefinition, FieldDefinitionWithId, FieldOrigin } from "~/utils/types";

const props = defineProps<{
  modelValue: FieldDefinitionWithId;
  canChangeStructure?: boolean;
  isListItem?: boolean;
  disabled?: boolean;
  lang?: string|null;
}>();
const emit = defineEmits<{
  'update:modelValue': [FieldDefinitionWithId];
}>();

const rules = {
  id: [
    (id: string) => (
    // this.parentObject.filter(f => id === f.id).length === 1 &&
    // TODO: validate ID unique abd validate custom ID not in list of core and predefined field IDs
      /^[a-zA-Z_][a-zA-Z0-9_]*$/.test(id)
    ) || 'Invalid field ID',
  ],
  choice: [
    // v => (choices || []).filter(c => c.value === v).length === 1 || 'Enum value is not unique',
    (v: string) => /^[a-zA-Z0-9_-]+$/.test(v) || 'Invalid enum value',
  ]
};

const objectFields = computed(() => {
  if (props.modelValue.type === FieldDataType.OBJECT) {
    return Object.keys(props.modelValue.properties || {}).map(f => ({ id: f, ...props.modelValue.properties![f] }));
  } else {
    return [];
  }
});

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
    newObj.choices[choiceIdx].value = val;
  } else if (action === 'updateLabel') {
    newObj.choices[choiceIdx].label = val || '';
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
    newObj.suggestions.push('New Value');
  }
  // TODO: allow sorting of suggestions
  emit('update:modelValue', newObj);
}
function updateObject(action: string, fieldId?: string, val?: FieldDefinitionWithId) {
  const newObj = { ...props.modelValue, properties: { ...props.modelValue.properties } };
  if (action === "update") {
    delete newObj.properties![fieldId!];
    newObj.properties![val!.id] = omit(val!, ['id']);
  } else if (action === "delete") {
    newObj.properties = omit(newObj.properties, [fieldId!]);
  } else if (action === 'add') {
    if (!val) {
      val = {
        id: fieldId || '',
        type: FieldDataType.STRING,
        label: 'New Field',
        required: true,
        spellcheck: false,
        default: null,
        origin: FieldOrigin.CUSTOM,
      };
    }
    if (!val.id) {
      val.id = uniqueName('new_field', Object.keys(newObj.properties));
    }
    newObj.properties[val.id] = omit(val, ['id']);
  }

  emit('update:modelValue', newObj);
}

watch(() => props.modelValue.type, () => {
  if (props.modelValue.type === FieldDataType.ENUM && !props.modelValue.choices) {
    updateProperty('choices', [{ value: 'enum_val', label: 'Enum Value' }]);
  } else if (props.modelValue.type === FieldDataType.COMBOBOX && !props.modelValue.suggestions) {
    updateProperty('suggestions', ['Combobox Value']);
  } else if (props.modelValue.type === FieldDataType.LIST && !props.modelValue.items) {
    updateProperty('items', { type: FieldDataType.STRING, default: null });
  } else if (props.modelValue.type === FieldDataType.OBJECT && !props.modelValue.properties) {
    updateProperty('properties', { nested_field: { type: FieldDataType.STRING, label: 'Nested Field', default: null } });
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
