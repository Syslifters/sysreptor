<template>
  <div :id="id" class="mt-4"> 
    <!-- String -->
    <markdown-text-field
      v-if="definition.type === 'string'"
      :value="formValue"
      @input="emitInput"
      :label="label"
      :disabled="disabled"
      :lang="lang"
      :spellcheck-supported="definition.spellcheck"
    />

    <!-- Markdown -->
    <markdown-field
      v-else-if="definition.type === 'markdown'"
      :value="formValue"
      @input="emitInput"
      :label="label"
      :upload-file="uploadFile"
      :rewrite-file-url="rewriteFileUrl"
      :rewrite-reference-link="rewriteReferenceLink"
      :disabled="disabled"
      :lang="lang"
    />

    <!-- Date -->
    <v-menu
      v-else-if="definition.type === 'date'"
      v-model="datePickerVisible"
      :disabled="disabled"
      :close-on-content-click="false"
      min-width="auto"
      offset-y
    >
      <template #activator="{ on, attrs }">
        <s-text-field
          :value="formValue"
          v-bind="attrs" v-on="on"
          :label="label"
          :disabled="disabled"
          prepend-inner-icon="mdi-calendar"
          readonly
          clearable 
          @click:clear="emitInput(null)"
        />
      </template>
      <template #default>
        <v-date-picker
          :value="formValue"
          @input="datePickerVisible = false; emitInput($event);"
          :locale="lang"
          :first-day-of-week="1"
        />
      </template>
    </v-menu>

    <!-- Enum -->
    <s-autocomplete
      v-else-if="definition.type === 'enum'"
      :value="formValue"
      @change="emitInput"
      :items="[{value: null, label: '---'}].concat(definition.choices)"
      item-text="label"
      item-value="value"
      :label="label"
      :disabled="disabled"
      clearable
    />
    <s-combobox
      v-else-if="definition.type === 'combobox'"
      :value="formValue"
      @input="emitInput($event)"
      :items="definition.suggestions"
      :label="label"
      :disabled="disabled"
      clearable
    />

    <!-- Number -->
    <s-text-field
      v-else-if="definition.type === 'number'"
      :value="formValue"
      @input="emitInput(parseFloat($event))"
      type="number"
      :label="label"
      :disabled="disabled"
    />

    <!-- Boolean -->
    <s-checkbox
      v-else-if="definition.type === 'boolean'"
      :value="formValue || false"
      @change="emitInput"
      :label="label"
      :disabled="disabled"
    />

    <!-- CVSS -->
    <cvss-field
      v-else-if="definition.type === 'cvss'"
      :value="formValue"
      @input="emitInput"
      :label="label"
      :disabled="disabled"
    />

    <!-- User -->
    <user-selection
      v-else-if="definition.type === 'user'"
      :value="formValue"
      @input="emitInput($event.id)"
      :label="label"
      :selectable-users="selectableUsers"
      :disabled="disabled"
    />

    <!-- Object -->
    <s-card v-else-if="definition.type === 'object'">
      <v-card-title class="text-body-1 pb-2">{{ label }}</v-card-title>

      <dynamic-input-field
        v-for="(objectFieldDefinition, objectFieldId) in definition.properties"
        :key="objectFieldId"
        :value="formValue[objectFieldId]"
        @input="emitInputObject(objectFieldId, $event)"
        :definition="objectFieldDefinition"
        :id="id ? (id + '.' + objectFieldId) : null"
        :show-field-ids="showFieldIds"
        :selectable-users="selectableUsers"
        :upload-file="uploadFile"
        :rewrite-file-url="rewriteFileUrl"
        :rewrite-reference-link="rewriteReferenceLink"
        :disabled="disabled"
        :lang="lang"
      />
    </s-card>

    <!-- List -->
    <s-card v-else-if="definition.type === 'list'">
      <v-card-title class="text-body-1 pb-2">
        <span>{{ label }}</span>

        <template v-if="definition.items.type === 'string'">
          <v-spacer />
          <s-tooltip>
            <template #activator="{on, attrs}">
              <s-btn v-bind="attrs" v-on="on" @click="bulkEditList = !bulkEditList" icon>
                <v-icon v-if="bulkEditList">mdi-format-list-bulleted</v-icon>
                <v-icon v-else>mdi-playlist-edit</v-icon>
              </s-btn>
            </template>

            <template #default>
              <span v-if="bulkEditList">Edit as list</span>
              <span v-else>Bulk edit list items</span>
            </template>
          </s-tooltip>
        </template>
      </v-card-title>

      <template v-if="definition.items.type === 'string' && bulkEditList">
        <!-- Bulk edit list items of list[string] -->
        <v-textarea
          :value="(formValue || []).join('\n')" @input="emitInputStringList"
          label="Enter one item per line"
          :disabled="disabled"
          :lang="lang"
          auto-grow
          hide-details="auto"
          spellcheck="false"
          outlined 
        />
      </template>
      <v-list v-else>
        <v-list-item v-for="(entryVal, entryIdx) in formValue" :key="entryIdx">
          <v-list-item-content>
            <dynamic-input-field
              :value="entryVal"
              @input="emitInputList('update', entryIdx, $event)"
              :definition="definition.items"
              :id="id ? (id + '[' + entryIdx + ']') : null"
              :show-field-ids="showFieldIds"
              :selectable-users="selectableUsers"
              :upload-file="uploadFile"
              :rewrite-file-url="rewriteFileUrl"
              :rewrite-reference-link="rewriteReferenceLink"
              :disabled="disabled"
              :lang="lang"
            />
          </v-list-item-content>

          <v-list-item-action>
            <btn-delete icon :delete="() => emitInputList('delete', entryIdx)" :disabled="disabled" :confirm="!isEmptyOrDefault(entryVal, definition.items)" />
          </v-list-item-action>
        </v-list-item>

        <v-list-item>
          <s-btn @click="emitInputList('add')" color="secondary" :disabled="disabled">
            <v-icon>mdi-plus</v-icon>
            Add
          </s-btn>
        </v-list-item>
      </v-list>
    </s-card>

    <div v-else>
      {{ definition }}
    </div>
  </div>
</template>

<script>
export default {
  props: {
    value: {
      type: undefined,
      required: true,
    },
    definition: {
      type: Object,
      required: true,
    },
    id: {
      type: String,
      default: null,
    },
    showFieldIds: {
      type: Boolean,
      default: false,
    },
    uploadFile: {
      type: Function,
      default: null,
    },
    rewriteFileUrl: {
      type: Function,
      default: null,
    },
    rewriteReferenceLink: {
      type: Function,
      default: null,
    },
    selectableUsers: {
      type: Array,
      default: null,
    },
    disabled: {
      type: Boolean,
      default: false,
    },
    lang: {
      type: String,
      default: null,
    },
  },
  emits: ["updated"],
  data() {
    return {
      datePickerVisible: false,
      bulkEditList: false,
    };
  },
  computed: {
    formValue() {
      return this.value;
      // if (this.value !== null) {
      //   return this.value;
      // }
      // return this.definition.default;
    },
    label() {
      let out = this.definition.label || '';
      if (this.showFieldIds && this.id) {
        if (out) {
          out += ' (' + this.id + ')';  
        } else {
          out = this.id;
        }
      }
      return out;
    }
  },
  methods: {
    getInitialValue(fieldDef) {
      if (fieldDef.default) {
        return fieldDef.default;
      } else if (fieldDef.type === "list") {
        return [];
      } else if (fieldDef.type === 'object') {
        return Object.fromEntries(Object.entries(fieldDef.properties).map(([f, d]) => [f, this.getInitialValue(d)]));
      } else {
        return null;
      }
    },
    emitInput(val) {
      this.$emit("input", val);
    },
    emitInputObject(objectFieldId, val) {
      const newVal = Object.assign({}, this.value);
      newVal[objectFieldId] = val;
      this.$emit("input", newVal);
    },
    emitInputList(action, entryIdx, entryVal = null) {
      const newVal = [...this.formValue];
      if (action === "update") {
        newVal[entryIdx] = entryVal;
      } else if (action === "delete") {
        newVal.splice(entryIdx, 1);
      } else if (action === 'add') {
        if (entryVal === null) {
          entryVal = this.getInitialValue(this.definition.items);
        }

        newVal.push(entryVal);
      }

      this.$emit("input", newVal);
    },
    emitInputStringList(valuesListString) {
      const values = (valuesListString || '').split('\n').filter(v => !!v);
      this.$emit('input', values);
    },
    isEmptyOrDefault(value, definition) {
      if (definition.type === 'list') {
        return value.length === 0 || value.every(v => this.isEmptyOrDefault(v, definition.items));
      } else if (definition.type === 'object') {
        return !value || Object.entries(definition.properties).every(([k, d]) => this.isEmptyOrDefault(value[k], d));
      } else {
        return !value || value === definition.default;
      }
    },
  },
};
</script>
