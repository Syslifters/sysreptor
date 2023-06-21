<template>
  <v-form ref="form">
    <split-menu v-model="menuSize">
      <template #menu>
        <v-list>
          <v-list-item-title class="text-h6 pl-2">{{ projectType.name }}</v-list-item-title>

          <v-list-item-group v-model="currentItem" mandatory>
            <draggable 
              :value="reportSections" 
              @input="updateSectionOrder" 
              group="sections" 
              draggable=".draggable-section"
              :disabled="readonly"
            >
              <div v-for="s in reportSections" :key="s.id" class="draggable-section">
                <v-list-item :value="s" :ripple="false" link>
                  <v-list-item-title>{{ s.label }}</v-list-item-title>
                  <v-list-item-action>
                    <btn-delete v-if="s.fields.length === 0" :delete="() => deleteSection(s)" :disabled="readonly" icon small />
                  </v-list-item-action>
                </v-list-item>
                <v-list class="sublist" dense>
                  <draggable 
                    :value="s.fields" @input="updateFieldOrder(s, $event)" 
                    group="fields" 
                    draggable=".draggable-field"
                    :disabled="readonly"
                  >
                    <v-list-item v-for="f in s.fields" :key="f.id" :value="f" class="draggable-field" :ripple="false" link>
                      <v-list-item-title>{{ f.id }}</v-list-item-title>
                      <v-list-item-action>
                        <btn-delete v-if="f.origin !== 'core'" :delete="() => deleteField(s, f)" :disabled="readonly" icon x-small />
                      </v-list-item-action>
                    </v-list-item>
                  </draggable>

                  <v-list-item>
                    <s-btn @click.stop="addField(s)" color="secondary" :disabled="readonly" x-small>
                      <v-icon left>mdi-plus</v-icon>
                      Add Field
                    </s-btn>
                  </v-list-item>
                </v-list>

                <v-divider />
              </div>
            </draggable>
            <v-list-item>
              <s-btn @click.stop="addSection" :disabled="readonly" color="secondary" small>
                <v-icon left>mdi-plus</v-icon>
                Add Section
              </s-btn>
            </v-list-item>
          </v-list-item-group>
        </v-list>
      </template>

      <template #default>
        <edit-toolbar v-bind="toolbarAttrs" v-on="toolbarEvents" :form="$refs.form" />

        <template v-if="currentItemIsSection">
          <s-card>
            <v-card-title>Section: {{ currentItem.label }}</v-card-title>
            <v-card-text>
              <v-row>
                <v-col>
                  <s-text-field 
                    :value="currentItem.id" @input="updateCurrentSection('id', $event)"
                    label="Section ID"
                    :rules="rules.sectionId"
                    required
                    :disabled="readonly"
                  />
                </v-col>
                <v-col>
                  <s-text-field 
                    :value="currentItem.label" @input="updateCurrentSection('label', $event)"
                    label="Label"
                    required
                    :disabled="readonly"
                  />
                </v-col>
              </v-row>
            </v-card-text>
          </s-card>
          <s-card>
            <v-card-text>
              <design-input-field-definition
                v-for="f in currentItem.fields" :key="f.id"
                :value="f" @input="updateCurrentSectionField(f, $event)"
                :can-change-structure="!['core', 'predefined'].includes(f.origin)"
                :lang="projectType.language"
                :disabled="readonly"
              />
              <s-btn @click.stop="addField(currentItem)" :disabled="readonly" class="mt-4" color="secondary">
                <v-icon left>mdi-plus</v-icon>
                Add Field
              </s-btn>
            </v-card-text>
          </s-card>
        </template>
        <template v-else-if="currentItemIsField">
          <design-input-field-definition 
            :value="currentItem" @input="updateCurrentField"
            :can-change-structure="!['core', 'predefined'].includes(currentItem.origin)" 
            :lang="projectType.language"
            :disabled="readonly"
          />
        </template>
      </template>
    </split-menu>
  </v-form>
</template>

<script>
import Draggable from 'vuedraggable';
import { omit } from 'lodash';
import { set as vueSet } from 'vue';
import { uniqueName } from '~/utils/state';
import ProjectTypeLockEditMixin from '~/mixins/ProjectTypeLockEditMixin';

export default {
  components: { Draggable },
  mixins: [ProjectTypeLockEditMixin],
  data() {
    return {
      currentItem: null,
      rules: {
        sectionId: [
          id => /^[a-zA-Z0-9_-]+$/.test(id) || 'Invalid ID',
        ]
      }
    }
  },
  computed: {
    menuSize: {
      get() {
        return this.$store.state.settings.reportFieldDefinitionMenuSize;
      }, 
      set(val) {
        this.$store.commit('settings/updateReportFieldDefinitionMenuSize', val);
      }
    },
    reportSections() {
      return this.projectType.report_sections.map(s => Object.assign({}, s, { fields: s.fields.map(f => ({ id: f, ...this.projectType.report_fields[f] })) }));
    },
    reportFields() {
      return this.reportSections.map(s => s.fields).flat();
    },
    currentItemIsSection() {
      return this.currentItem && !this.currentItemIsField && this.reportSections.some(s => s.id === this.currentItem.id);
    },
    currentItemIsField() {
      return this.reportFields.includes(this.currentItem);
    }
  },
  methods: {
    updateField(field, val) {
      // Update field order in section
      const section = this.projectType.report_sections.find(s => s.fields.includes(field.id));
      const oldIdx = section.fields.indexOf(field.id);
      if (oldIdx !== -1) {
        vueSet(section.fields, oldIdx, val.id);
      } else {
        section.fields.push(val.id);
      }

      // Update field definition
      delete this.projectType.report_fields[field.id];
      this.projectType.report_fields[val.id] = omit(val, ['id']);
    },
    updateCurrentSectionField(field, val) {
      const sectionId = this.currentItem.id;
      this.updateField(field, val);

      this.currentItem = this.reportSections.find(s => s.id === sectionId);
    },
    updateCurrentField(val) {
      this.updateField(this.currentItem, val);

      this.currentItem = this.reportFields.find(f => f.id === val.id);
    },
    updateFieldOrder(section, fields) {
      section = this.projectType.report_sections.find(s => s.id === section.id);
      section.fields = fields.map(f => f.id);
    },
    addField(section) {
      section = this.projectType.report_sections.find(s => s.id === section.id);
      const fieldId = uniqueName('new_field', Object.keys(this.projectType.report_fields));
      this.projectType.report_fields[fieldId] = {
        type: 'string',
        label: 'New Field',
        required: true,
        default: 'TODO: fill field in report'
      };
      section.fields.push(fieldId);

      if (this.currentItemIsSection && section.id === this.currentItem.id) {
        this.currentItem = this.reportSections.find(s => s.id === section.id);
      } else {
        this.currentItem = this.reportSections.find(s => s.id === section.id).fields.find(f => f.id === fieldId);
      }
    },
    deleteField(section, field) {
      section = this.projectType.report_sections.find(s => s.id === section.id);
      section.fields = section.fields.filter(f => f !== field.id);
      delete this.projectType.report_fields[field.id];
    },
    updateCurrentSection(sectionField, val) {
      const section = this.projectType.report_sections.find(s => s.id === this.currentItem.id);
      section[sectionField] = val;
      this.currentItem = this.reportSections.find(s => s.id === section.id);
    },
    updateSectionOrder(sections) {
      this.projectType.report_sections = sections.map(s => Object.assign({}, s, { fields: s.fields.map(f => f.id) }));
    },
    addSection() {
      const sectionId = uniqueName('section', this.projectType.report_sections.map(s => s.id));
      this.projectType.report_sections.push({ id: sectionId, label: 'New Section', fields: [] });
      this.currentItem = this.reportSections.find(s => s.id === sectionId);
    },
    deleteSection(section) {
      this.projectType.report_sections = this.projectType.report_sections.filter(s => s.id !== section.id);
    },
    async performSave(data) {
      await this.$store.dispatch('projecttypes/partialUpdate', { obj: data, fields: ['report_sections', 'report_fields'] });
    }
  }
}
</script>

<style lang="scss" scoped>
.sublist {
  margin-left: 1em;
  padding-top: 0;
  padding-bottom: 0;
}

.draggable-field, .draggable-section > .v-list-item {
  cursor: move;
  cursor: grab;
}
</style>
