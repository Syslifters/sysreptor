<template>
  <v-form ref="form">
    <split-menu v-model="menuSize">
      <template #menu>
        <v-list dense>
          <v-list-item-title class="text-h6 pl-2">{{ projectType.name }}</v-list-item-title>

          <v-list-item-group v-model="currentField" mandatory>
            <v-list-item :value="null" :ripple="false" link>
              <v-list-item-title>All Fields</v-list-item-title>
            </v-list-item>

            <draggable 
              v-model="findingFields" 
              :group="{name: 'findingFields', put: ['predefinedFindingFields']}" 
              draggable=".draggable-item" 
              @add="addPredefinedField"
              :disabled="readonly"
            >
              <v-list-item v-for="f in findingFields" :key="f.id" :value="f" class="draggable-item" link :ripple="false">
                <v-list-item-title>{{ f.id }}</v-list-item-title>
                <v-list-item-action>
                  <btn-delete v-if="f.origin !== 'core'" :delete="() => deleteField(f.id)" icon x-small :disabled="readonly" />
                </v-list-item-action>
              </v-list-item>
            </draggable>
          </v-list-item-group>

          <v-divider />
          <v-list-group :value="true">
            <template #activator>
              <v-list-item-title>Predefined Fields</v-list-item-title>
            </template>
            <draggable 
              draggable=".draggable-item" 
              :sort="false" 
              :group="{name: 'predefinedFindingFields'}"
            >
              <v-list-item v-for="f in availablePredefinedFields" :key="f.id" class="draggable-item" :ripple="false">
                <v-list-item-title>{{ f.id }}</v-list-item-title>
              </v-list-item>
            </draggable>
          </v-list-group>

          <v-divider />
          <v-list-item>
            <s-btn @click.stop="addField" color="secondary" x-small :disabled="readonly">
              <v-icon left>mdi-plus</v-icon>
              Add Custom Field
            </s-btn>
          </v-list-item>
        </v-list>
      </template>

      <template #default>
        <edit-toolbar v-bind="toolbarAttrs" v-on="toolbarEvents" :form="$refs.form" />

        <template v-if="currentField === null">
          <design-input-field-definition
            v-for="f in findingFields" :key="f.id"
            :value="f" @input="updateField(f, $event)"
            :can-change-structure="!['core', 'predefined'].includes(f.origin)"
            :lang="projectType.language"
            :disabled="readonly"
          />
        </template>
        <design-input-field-definition 
          v-else-if="currentField.type"
          :value="currentField" @input="updateCurrentField"
          :can-change-structure="!['core', 'predefined'].includes(currentField.origin)" 
          :lang="projectType.language"
          :disabled="readonly"
        />
      </template>
    </split-menu>
  </v-form>
</template>

<script>
import { set as vueSet } from 'vue';
import { omit, cloneDeep, sortBy } from 'lodash';
import Draggable from 'vuedraggable';
import { uniqueName } from '~/utils/state';
import ProjectTypeLockEditMixin from '~/mixins/ProjectTypeLockEditMixin';

export default {
  components: { Draggable },
  mixins: [ProjectTypeLockEditMixin],
  async asyncData(options) {
    return {
      ...await ProjectTypeLockEditMixin.asyncData(options),
      predefinedFindingFields: await options.store.dispatch('projecttypes/getPredefinedFindingFields'),
    }
  },
  data() {
    return {
      currentField: null,
    }
  },
  computed: {
    findingFields: {
      get() {
        return this.projectType.finding_field_order.map(f => ({ id: f, ...this.projectType.finding_fields[f] }));
      },
      set(val) {
        // Field order
        this.projectType.finding_field_order = val.map(f => f.id);
      }
    },
    availablePredefinedFields() {
      const out = Object.entries(this.predefinedFindingFields)
        .map(([id, f]) => ({ id, ...f }))
        .filter(f => !this.findingFields.some(v => f.id === v.id));
      return sortBy(out, ['id']);
    },
    menuSize: {
      get() {
        return this.$store.state.settings.findingFieldDefinitionMenuSize;
      },
      set(val) {
        this.$store.commit('settings/updateFindingFieldDefinitionMenuSize', val);
      }
    },
  },
  methods: {
    updateField(field, val) {
      // Update field order
      const oldFieldIdx = this.projectType.finding_field_order.indexOf(field.id);
      if (oldFieldIdx !== -1) {
        vueSet(this.projectType.finding_field_order, oldFieldIdx, val.id);
      } else {
        this.projectType.finding_field_order = this.projectType.finding_field_order.filter(f => f !== field.id).concat([val.id]);
      }
      
      // Update field definition
      delete this.projectType.finding_fields[field.id];
      this.projectType.finding_fields[val.id] = omit(val, ['id']);
    },
    updateCurrentField(val) {
      this.updateField(this.currentField, val);

      // Update current field in selection
      this.currentField = this.findingFields.find(f => f.id === val.id);
    },
    addField() {
      const fieldId = uniqueName('new_field', this.projectType.finding_field_order);
      this.projectType.finding_fields[fieldId] = { type: 'string', origin: 'custom', label: 'New Field', required: true, default: 'TODO: fill field in report' };
      this.projectType.finding_field_order.push(fieldId);
      
      this.currentField = this.findingFields.find(f => f.id === fieldId);
    },
    addPredefinedField(event) {
      const predefinedField = this.availablePredefinedFields[event.oldIndex];
      this.projectType.finding_fields[predefinedField.id] = cloneDeep(omit(predefinedField, ['id']));
      this.projectType.finding_field_order.splice(event.newIndex, 0, predefinedField.id);

      this.currentField = this.findingFields.find(f => f.id === predefinedField.id);
    },
    deleteField(fieldId) {
      delete this.projectType.finding_fields[fieldId];
      this.projectType.finding_field_order = this.projectType.finding_field_order.filter(f => f !== fieldId);
    },
    async performSave(data) {
      await this.$store.dispatch('projecttypes/partialUpdate', { obj: data, fields: ['finding_fields', 'finding_field_order'] });
    }
  }
}
</script>

<style lang="scss" scoped>
  .draggable-item {
    cursor: move;
    cursor: grab;
  }
</style>
