<template>
  <s-card>
    <v-card-text>
      <template v-if="!isListItem">
        <v-row>
          <v-col>
            <s-text-field
              :value="value.id"
              @change="emitInputVal('id', $event)"
              :rules="rules.id" 
              :disabled="disabled || !canChangeStructure"
              label="ID" 
              hint="Used to access this field in report templates"
              required
            />
          </v-col>
          <v-col>
            <s-select
              :value="value.type"
              @change="updateType($event)"
              :items="DATA_TYPES"
              :disabled="disabled || !canChangeStructure"
              label="Data Type"
              hint="Data type of this field. Controls the allowed values and input form."
              required
            />
          </v-col>

          <v-col>
            <s-text-field
              :value="value.label"
              @input="emitInputVal('label', $event)"
              :disabled="disabled"
              label="Label"
              hint="Friendly name used in input forms for this field"
              required
            />
          </v-col>
        </v-row>
        <v-row class="mt-0">
          <v-col class="mt-0 pt-0">
            <s-checkbox
              :value="value.required"
              @input="emitInputVal('required', $event)"
              :disabled="disabled"
              label="Required"
              hint="Determines whether this field is required must be filled or optional"
              class="mt-0"
            />
          </v-col>
        </v-row>
      </template>
      <s-select
        v-else
        :value="value.type"
        @change="emitInputVal('type', $event)"
        :items="DATA_TYPES"
        :disabled="disabled || !canChangeStructure"
        label="Data Type"
        hint="Data type of this field. Controls the allowed values and input form."
        required
      />

      <!-- Enum choices -->
      <v-list v-if="value.type === 'enum'">
        <v-list-item v-for="choice, choiceIdx in value.choices || []" :key="choiceIdx">
          <v-list-item-content>
            <v-row>
              <v-col>
                <s-text-field 
                  :value="choice.value"
                  @input="emitInputChoice('updateValue', choice, $event)"
                  :disabled="disabled || !canChangeStructure"
                  :rules="rules.choice"
                  label="Value"
                  required
                />
              </v-col>
              <v-col>
                <s-text-field 
                  :value="choice.label"
                  @input="emitInputChoice('updateLabel', choice, $event)"
                  :disabled="disabled"
                  label="Label"
                  required
                />
              </v-col>
            </v-row>
          </v-list-item-content>
          <v-list-item-action>
            <delete-button @delete="emitInputChoice('delete', choice)" :disabled="disabled || !canChangeStructure" icon />
          </v-list-item-action>
        </v-list-item>
        <v-list-item>
          <v-list-item-action>
            <s-btn @click="emitInputChoice('add')" :disabled="disabled || !canChangeStructure" color="secondary">
              <v-icon>mdi-plus</v-icon>
              Add Value
            </s-btn>
          </v-list-item-action>
        </v-list-item>
      </v-list>
    
      <dynamic-input-field
        v-if="!['object', 'list', 'user'].includes(value.type)"
        :value="value.default"
        @input="emitInputVal('default', $event)"
        :definition="{label: 'Default Value', type: value.type, choices: value.choices}"
        :lang="lang"
        :disabled="disabled"
      />
      <!-- List Item -->
      <input-field-definition
        v-else-if="value.type === 'list'"
        :value="value.items"
        @input="emitInputVal('items', $event)"
        :is-list-item="true"
        :can-change-structure="canChangeStructure"
        :lang="lang"
        :disabled="disabled"
      />
      <!-- Object -->
      <v-list v-else-if="value.type === 'object'">
        <v-list-item v-for="f in objectFields" :key="f.id">
          <v-list-item-content>
            <input-field-definition
              :value="f" 
              @input="emitInputObject('update', f.id, $event)" 
              :is-object="false"
              :can-change-structure="canChangeStructure"
              :lang="lang"
              :disabled="disabled"
            />
          </v-list-item-content>
          <v-list-item-action>
            <delete-button :disabled="disabled || !canChangeStructure" @delete="emitInputObject('delete', f.id)" icon />
          </v-list-item-action>
        </v-list-item>

        <v-divider />
        <v-list-item>
          <s-btn @click="emitInputObject('add')" :disabled="disabled || !canChangeStructure" color="secondary">
            <v-icon>mdi-plus</v-icon>
            Add property
          </s-btn>
        </v-list-item>
      </v-list>
    </v-card-text>
  </s-card>
</template>

<script>
import { omit } from 'lodash';
import { uniqueName } from '~/utils/state';

const DATA_TYPES = {
  markdown: 'markdown',
  string: 'string',
  enum: 'enum',
  date: 'date',
  user: 'user',
  list: 'list',
  object: 'object',
  number: 'number',
  boolean: 'boolean',
  cvss: 'cvss',
};

export default {
  props: {
    value: {
      type: Object,
      required: true
    },
    canChangeStructure: {
      type: Boolean,
      default: false,
    },
    isListItem: {
      type: Boolean,
      default: false,
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
  emits: ['input', 'updateId', 'updateOrder'],
  data() {
    return {
      rules: {
        id: [
          id => (
            // this.parentObject.filter(f => id === f.id).length === 1 && 
            // TODO: validate ID unique
            // TODO: validate custom ID not in list of core and predefined field IDs
            /^[a-zA-Z_][a-zA-Z0-9_]+$/.test(id)
          ) || 'Invalid field ID',
        ],
        choice: [
          // v => (choices || []).filter(c => c.value === v).length === 1 || 'Enum value is not unique',
          v => /^[a-zA-Z0-9_-]+$/.test(v) || 'Invalid enum value',
        ]
      },
    };
  },
  computed: {
    DATA_TYPES: () => Object.keys(DATA_TYPES),
    objectFields() {
      if (this.value.type === 'object') {
        return Object.keys(this.value.properties || {}).sort().map(f => ({ id: f, ...this.value.properties[f] }));
      } else {
        return [];
      }
    },
  },
  watch: {
    'value.type' (newType, oldType) {
      if (this.value.type === 'enum' && !this.value.choices) {
        this.emitInputVal('choices', [{ value: 'enum_val', label: 'Enum Value' }]);
      } else if (this.value.type === 'list' && !this.value.items) {
        this.emitInputVal('items', { type: 'string', default: null });
      } else if (this.value.type === 'object' && !this.value.properties) {
        this.emitInputVal('properties', { nested_field: { type: 'string', label: 'Nested Field', default: null } });
      }
    }
  },
  methods: {
    updateType(val) {
      const newObj = Object.assign({}, this.value, Object.fromEntries([['type', val]]));

      // if type changes, ensure that default has the correct data type or set to null
      if (
        (['string', 'markdown', 'cvss'].includes(val) && !(val instanceof String)) || 
        (val === 'number' && !(val instanceof Number)) || 
        (val === 'boolean' && !(val instanceof Boolean)) || 
        (val === 'enum' && !(this.value.choices || []).find(c => c.id === this.value.default)) ||
        (val === 'date') ||
        (val === 'user')
      ) {
        if (this.default !== null) {
          newObj.default = null;
        }
      }
      this.$emit('input', newObj);
    },
    emitInputVal(property, val) {
      const newObj = Object.assign({}, this.value, Object.fromEntries([[property, val]]));
      this.$emit('input', newObj);
    },
    emitInputChoice(action, choice, val = null) {
      const newObj = Object.assign({}, this.value, { choices: [...this.value.choices] });
      if (action === 'updateValue') {
        newObj.choices.filter(c => c.value === choice.value)[0].value = val;
      } else if (action === 'updateLabel') {
        newObj.choices.filter(c => c.value === choice.value)[0].label = val;
      } else if (action === 'delete') {
        newObj.choices = newObj.choices.filter(c => c.value !== choice.value);
      } else if (action === 'add') {
        if (val === null) {
          val = {
            value: uniqueName('new_value', newObj.choices.map(c => c.id)),
            label: 'New Enum Value',
          }
        }
        newObj.choices.push(val);
      }

      this.$emit('input', newObj);
    },
    emitInputObject(action, fieldId = null, val = null) {
      const newObj = Object.assign({}, this.value);
      if (action === "update") {
        delete newObj.properties[fieldId];
        newObj.properties[val.id] = omit(val, ['id']);
      } else if (action === "delete") {
        newObj.properties = omit(newObj.properties, [fieldId]);
      } else if (action === 'add') {
        if (val === null) {
          val = {
            type: 'string',
            label: 'New Field',
            required: true,
            default: null,
          };
        }
        if (fieldId === null) {
          fieldId = uniqueName('new_field', Object.keys(newObj.properties));
        }

        newObj.properties[fieldId] = val;
      }

      this.$emit('input', newObj);
    },
  }
}
</script>
