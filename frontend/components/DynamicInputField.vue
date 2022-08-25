<template>
  <div :id="id" class="mt-4"> 
    <!-- String -->
    <s-text-field
      v-if="definition.type === 'string'"
      :value="formValue"
      @input="emitInput"
      :label="label"
      :disabled="disabled"
    />

    <!-- Markdown -->
    <div v-else-if="definition.type === 'markdown'">
      <label>{{ label }}</label>
      <markdown-field
        :value="formValue"
        @input="emitInput"
        :upload-image="uploadImage"
        :image-urls-relative-to="imageUrlsRelativeTo"
        :label="label"
        :disabled="disabled"
      />
    </div>

    <!-- Date -->
    <v-menu
      v-else-if="definition.type === 'date'"
      v-model="datePickerVisible"
      :disabled="disabled"
      :close-on-content-click="false"
      offset-y
    >
      <template #activator="{ on, attrs }">
        <s-text-field
          :value="formValue"
          v-bind="attrs" v-on="on"
          :label="label"
          :disabled="disabled"
          readonly
          clearable @click:clear="emitInput(null)"
        />
      </template>
      <template #default>
        <v-date-picker
          :value="formValue"
          @input="datePickerVisible = false; emitInput($event);"
        />
      </template>
    </v-menu>

    <!-- Enum -->
    <s-select
      v-else-if="definition.type === 'enum'"
      :value="formValue"
      @change="emitInput"
      :items="[{value: null, label: '---'}].concat(definition.choices)"
      item-text="label"
      item-value="value"
      :label="label"
      :disabled="disabled"
      hide-details
      clearable
    />

    <!-- Number -->
    <s-text-field
      v-else-if="definition.type === 'number'"
      :value="formValue"
      @input="emitInput"
      type="number"
      :disabled="disabled"
    />

    <!-- Boolean -->
    <v-checkbox
      v-else-if="definition.type === 'boolean'"
      :value="formValue"
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
    <v-card v-else-if="definition.type === 'object'" outlined>
      <div class="mt-4 mb-2 ml-4">{{ label }}</div>

      <dynamic-input-field
        v-for="(objectFieldDefinition, objectFieldId) in definition.properties"
        :key="objectFieldId"
        :value="formValue[objectFieldId]"
        @input="emitInputObject(objectFieldId, $event)"
        :definition="objectFieldDefinition"
        :id="id ? (id + '.' + objectFieldId) : null"
        :show-field-ids="showFieldIds"
        :selectable-users="selectableUsers"
        :disabled="disabled"
      />
    </v-card>

    <!-- List -->
    <v-card v-else-if="definition.type === 'list'" outlined>
      <div class="mt-4 mb-2 ml-4">{{ label }}</div>

      <v-list>
        <v-list-item v-for="(entryVal, entryIdx) in formValue" :key="entryIdx">
          <v-list-item-content>
            <dynamic-input-field
              :value="entryVal"
              @input="emitInputList('update', entryIdx, $event)"
              :definition="definition.items"
              :id="id ? (id + '[' + entryIdx + ']') : null"
              :show-field-ids="showFieldIds"
              :selectable-users="selectableUsers"
              :disabled="disabled"
            />
          </v-list-item-content>

          <v-list-item-action>
            <delete-button icon @delete="emitInputList('delete', entryIdx)" :disabled="disabled" :confirm="!isEmptyOrDefault(entryVal, definition.items)" />
          </v-list-item-action>
        </v-list-item>

        <v-list-item>
          <s-btn @click="emitInputList('add')" color="secondary" :disabled="disabled">
            <v-icon>mdi-plus</v-icon>
            Add
          </s-btn>
        </v-list-item>
      </v-list>
    </v-card>

    <div v-else>
      {{ definition }}
    </div>
  </div>
</template>

<script>
import CvssField from "./CvssField.vue";
import DeleteButton from './DeleteButton.vue';
import MarkdownField from './MarkdownField.vue';
import UserSelection from './UserSelection.vue';
export default {
  components: { CvssField, MarkdownField, DeleteButton, UserSelection },
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
    uploadImage: {
      type: Function,
      default: null,
    },
    imageUrlsRelativeTo: {
      type: String,
      default: null,
    },
    selectableUsers: {
      type: Array,
      default: null,
    },
    disabled: {
      type: Boolean,
      default: false,
    }
  },
  emits: ["updated"],
  data() {
    return {
      datePickerVisible: false,
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
        out += ' (' + this.id + ')';  
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
