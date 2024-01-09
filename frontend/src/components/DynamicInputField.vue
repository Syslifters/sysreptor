<template>
  <div :id="props.id" class="mt-4">
    <!-- String -->
    <markdown-text-field
      v-if="definition.type === 'string'"
      v-model="formValue"
      validate-on="input lazy"
      :spellcheck-supported="definition.spellcheck"
      :rules="[(v: string) => validateRegexPattern(v)]"
      v-bind="fieldAttrs"
    />

    <!-- Markdown -->
    <markdown-field
      v-else-if="definition.type === 'markdown'"
      v-model="formValue"
      v-bind="fieldAttrs"
    />

    <!-- Date -->
    <s-date-picker
      v-else-if="definition.type === 'date'"
      v-model="formValue"
      :locale="props.lang || undefined"
      v-bind="fieldAttrs"
    />

    <!-- Enum -->
    <s-autocomplete
      v-else-if="definition.type === 'enum'"
      v-model="formValue"
      :items="[{value: null as string|null, label: '---'}].concat(definition.choices!)"
      item-title="label"
      item-value="value"
      clearable
      v-bind="fieldAttrs"
    />

    <!-- Combobox -->
    <s-combobox
      v-else-if="definition.type === 'combobox'"
      v-model="formValue"
      :items="definition.suggestions"
      clearable
      spellcheck="false"
      v-bind="fieldAttrs"
    />

    <!-- Number -->
    <s-text-field
      v-else-if="definition.type === 'number'"
      :model-value="formValue"
      @update:model-value="emitUpdate(parseFloat($event))"
      type="number"
      v-bind="fieldAttrs"
    />

    <!-- Boolean -->
    <s-checkbox
      v-else-if="definition.type === 'boolean'"
      :model-value="formValue || false"
      @update:model-value="emitUpdate($event)"
      v-bind="fieldAttrs"
    />

    <!-- CVSS -->
    <s-cvss-field
      v-else-if="definition.type === 'cvss'"
      v-model="formValue"
      :cvss-version="definition.cvss_version"
      :disable-validation="props.disableValidation"
      v-bind="fieldAttrs"
    />

    <!-- User -->
    <s-user-selection
      v-else-if="definition.type === 'user'"
      :model-value="formValue"
      @update:model-value="emitUpdate(($event as UserShortInfo|null)?.id || null)"
      :selectable-users="selectableUsers"
      v-bind="fieldAttrs"
    />

    <!-- Object -->
    <s-card v-else-if="definition.type === 'object'">
      <v-card-title class="text-body-1">{{ label }}</v-card-title>

      <v-card-text>
        <dynamic-input-field
          v-for="(objectFieldDefinition, objectFieldId) in definition.properties"
          :key="objectFieldId"
          :model-value="formValue[objectFieldId]"
          @update:model-value="emitInputObject(objectFieldId as string, $event)"
          :definition="objectFieldDefinition"
          :id="props.id ? (props.id + '.' + objectFieldId) : undefined"
          :show-field-ids="showFieldIds"
          :selectable-users="selectableUsers"
          :disable-validation="props.disableValidation"
          v-bind="fieldAttrs"
        />
      </v-card-text>
    </s-card>

    <!-- List -->
    <s-card v-else-if="definition.type === 'list'">
      <v-card-title class="text-body-1">
        <div class="d-flex flex-row">
          <span>{{ label }}</span>

          <template v-if="definition.items!.type === 'string'">
            <v-spacer />
            <s-btn-icon
              @click="bulkEditList = !bulkEditList"
              density="comfortable"
            >
              <v-icon v-if="bulkEditList" icon="mdi-format-list-bulleted" />
              <v-icon v-else icon="mdi-playlist-edit" />
              <s-tooltip activator="parent">
                <span v-if="bulkEditList">Edit as list</span>
                <span v-else>Bulk edit list items</span>
              </s-tooltip>
            </s-btn-icon>
          </template>
        </div>
      </v-card-title>

      <v-card-text>
        <!-- Bulk edit list items of list[string] -->
        <v-textarea
          v-if="definition.items!.type === 'string' && bulkEditList"
          :model-value="(formValue || []).join('\n')"
          @update:model-value="emitInputStringList"
          auto-grow
          hide-details="auto"
          spellcheck="false"
          variant="outlined"
          v-bind="fieldAttrs"
          label="Enter one item per line"
          class="mt-4"
        />
        <v-list v-else class="pa-0">
          <draggable
            v-model="formValue"
            :item-key="(item: any) => formValue.indexOf(item)"
            :disabled="props.disabled"
            handle=".draggable-handle"
          >
            <template #item="{element: entryVal, index: entryIdx}">
              <v-list-item class="pa-0">
                <template #default>
                  <dynamic-input-field
                    :model-value="entryVal"
                    @update:model-value="emitInputList('update', entryIdx as number, $event)"
                    @keydown="onListKeyDown"
                    :definition="definition.items!"
                    :id="id ? (id + '[' + entryIdx + ']') : undefined"
                    :show-field-ids="showFieldIds"
                    :selectable-users="selectableUsers"
                    :disable-validation="props.disableValidation"
                    v-bind="fieldAttrs"
                  />
                </template>
                <template #append>
                  <div 
                    v-if="[FieldDataType.MARKDOWN, FieldDataType.OBJECT, FieldDataType.LIST].includes(props.definition.items!.type)"
                    class="d-flex flex-column"
                  >
                    <btn-delete
                      :delete="() => emitInputList('delete', entryIdx as number)"
                      :confirm="!isEmptyOrDefault(entryVal, definition.items!)"
                      :disabled="props.disabled"
                      density="compact"
                      button-variant="icon"
                      class="mb-4"
                    />

                    <s-btn-icon 
                      @click="emitInputList('move', entryIdx, entryIdx - 1)"
                      :disabled="props.disabled || entryIdx === 0"
                      density="compact"
                    >
                      <v-icon icon="mdi-arrow-up-drop-circle-outline" />
                      <s-tooltip activator="parent" text="Move up in list" />
                    </s-btn-icon>
                    <s-btn-icon
                      @click="emitInputList('move', entryIdx, entryIdx + 1)"
                      :disabled="props.disabled || entryIdx === formValue.length - 1"
                      density="compact"
                    >
                      <v-icon icon="mdi-arrow-down-drop-circle-outline" />
                      <s-tooltip activator="parent" text="Move down in list" />
                    </s-btn-icon>
                  </div>
                  <div v-else>
                    <v-icon
                      size="x-large"
                      class="draggable-handle" 
                      :disabled="props.disabled"
                      icon="mdi-drag-horizontal" 
                    />
                    <btn-delete
                      :delete="() => emitInputList('delete', entryIdx as number)"
                      :confirm="!isEmptyOrDefault(entryVal, definition.items!)"
                      :disabled="props.disabled"
                      button-variant="icon"
                    />
                  </div>
                </template>
              </v-list-item>
            </template>
          </draggable>

          <v-list-item class="pa-0">
            <s-btn-secondary
              @click="emitInputList('add')"
              :disabled="props.disabled"
              prepend-icon="mdi-plus"
              text="Add"
            />
          </v-list-item>
        </v-list>
      </v-card-text>
    </s-card>

    <div v-else>
      {{ definition }}
    </div>
  </div>
</template>

<script setup lang="ts">
import Draggable from 'vuedraggable';
import pick from 'lodash/pick';
import { MarkdownEditorMode, type UserShortInfo } from '~/utils/types';
import type { MarkdownProps } from "~/composables/markdown";
import regexWorkerUrl from '~/workers/regexWorker?worker&url';

const props = defineProps<MarkdownProps & {
  modelValue?: any;
  definition: FieldDefinition;
  id?: string;
  showFieldIds?: boolean;
  selectableUsers?: UserShortInfo[];
  disabled?: boolean;
  autofocus?: boolean;
  disableValidation?: boolean;
}>();
const emit = defineEmits<{
  'update:modelValue': [value: any];
  'update:spellcheckEnabled': [value: boolean];
  'update:markdownEditorMode': [value: MarkdownEditorMode];
}>();

function getInitialValue(fieldDef: FieldDefinition, useDefault = true): any {
  if (fieldDef.default && useDefault) {
    return fieldDef.default;
  } else if (fieldDef.type === "list") {
    return [];
  } else if (fieldDef.type === 'object') {
    return Object.fromEntries(Object.entries(fieldDef.properties!).map(([f, d]) => [f, getInitialValue(d, useDefault)]));
  } else {
    return null;
  }
}
function emitUpdate(val: any) {
  emit('update:modelValue', val);
}
function emitInputObject(objectFieldId: string, val: any) {
  emitUpdate({ ...formValue.value, [objectFieldId]: val });
}
function emitInputList(action: string, entryIdx?: number, entryVal: any|number|null = null) {
  const newVal = [...formValue.value];
  if (action === "update") {
    newVal[entryIdx!] = entryVal;
  } else if (action === "delete") {
    newVal.splice(entryIdx!, 1);
  } else if (action === 'add') {
    if (entryVal === null) {
      entryVal = getInitialValue(props.definition.items!);
    }

    newVal.push(entryVal);
  } else if (action === 'move') {
    const [moved] = newVal.splice(entryIdx!, 1);
    newVal.splice(entryVal!, 0, moved);
  }
  emitUpdate(newVal);
}

const formValue = computed({
  get: () => {
    if (props.modelValue === null || props.modelValue === undefined) {
      return getInitialValue(props.definition, false);
    }
    return props.modelValue;
  },
  set: val => emitUpdate(val),
});
const label = computed(() => {
  let out = props.definition.label || '';
  if (props.showFieldIds && props.id) {
    if (out) {
      out += ' (' + props.id + ')';
    } else {
      out = props.id;
    }
  }
  return out;
})

function isEmptyOrDefault(value: any, definition: FieldDefinition): boolean {
  if (definition.type === 'list') {
    return value.length === 0 || value.every((v: any) => isEmptyOrDefault(v, definition.items!));
  } else if (definition.type === 'object') {
    return !value || Object.entries(definition.properties!).every(([k, d]) => isEmptyOrDefault(value[k], d));
  } else {
    return !value || value === definition.default;
  }
}

// Global worker instance reused for all components
const regexWorker = useState<Worker|null>('regexWorker', () => null);
async function validateRegexPattern(value: string) {
  if (props.definition.type !== FieldDataType.STRING || !props.definition.pattern || !value) {
    return true;
  }

  try {
    const pattern = new RegExp(props.definition.pattern);

    if (!regexWorker.value) {
      regexWorker.value = new Worker(regexWorkerUrl, { type: 'module' });
    }

    const threadedRegexMatch = new Promise((resolve) => {
      regexWorker.value!.addEventListener('message', (e: MessageEvent) => resolve(e.data), { once: true });
      regexWorker.value!.postMessage({ pattern, value }); // Send the string and regex to the worker
    });
    const timeoutReject = (timeoutMs: number) => new Promise((_resolve, reject) => setTimeout(() => reject(new Error("RegEx timeout")), timeoutMs));
    try {
      // Execute regex in a web worker with timeout to prevent RegEx DoS
      const res = await Promise.race([threadedRegexMatch, timeoutReject(500)]);
      if (!res) {
        return `Invalid format. Value does not match pattern ${pattern}`;
      }
    } catch (e: any) {
      const w = regexWorker.value;
      regexWorker.value = null;
      await w.terminate();
      return e.message;
    }
  } catch (e: any) {
    return e.message;
  }
  return true;
}
onUnmounted(async () => {
  if (regexWorker.value) {
    await regexWorker.value.terminate();
    regexWorker.value = null;
  }
})

const bulkEditList = ref(false);
function emitInputStringList(valuesListString?: string) {
  const values = (valuesListString || '').split('\n').filter(v => !!v);
  emitUpdate(values);
}
function onListKeyDown(event: KeyboardEvent) {
  // Disable vuetify list keyboard navigation
  if (['ArrowDown', 'ArrowUp', 'Home', 'End'].includes(event.key)) {
    event.stopPropagation();
  }
}

const attrs = useAttrs();
const fieldAttrs = computed(() => ({
  ...attrs,
  label: label.value,
  ...pick(props, ['disabled', 'autofocus', 'lang', 'spellcheckEnabled', 'markdownEditorMode', 'uploadFile', 'rewriteFileUrl', 'rewriteReferenceLink']),
  'onUpdate:spellcheckEnabled': (v: boolean) => emit('update:spellcheckEnabled', v),
  'onUpdate:markdownEditorMode': (v: MarkdownEditorMode) => emit('update:markdownEditorMode', v),
}))
</script>

<style lang="scss" scoped>
.draggable-handle {
  cursor: grab;
}
.v-list-item:deep(.v-list-item__append .v-list-item__spacer) {
  width: 0.5em;
}
</style>
