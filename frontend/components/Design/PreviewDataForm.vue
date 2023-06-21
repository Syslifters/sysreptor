<template>
  <split-menu v-model="menuSize">
    <template #menu>
      <v-list dense>
        <v-list-item-group v-model="currentItem" mandatory>
          <v-subheader>Sections</v-subheader>
          <v-list-item v-for="section in projectType.report_sections" :key="section.id" :value="section" link>
            <v-list-item-title>{{ section.label }}</v-list-item-title>
          </v-list-item>

          <v-subheader>Findings</v-subheader>
          <v-list-item 
            v-for="finding in projectType.report_preview_data.findings" :key="finding.id" 
            :value="finding" 
            :class="'finding-level-' + riskLevel(finding.cvss)"
            link
          >
            <v-list-item-title>{{ finding.title }}</v-list-item-title>
            <v-list-item-action>
              <btn-delete :delete="() => deleteFinding(finding)" :disabled="disabled" icon x-small />
            </v-list-item-action>
          </v-list-item>
        </v-list-item-group>
        <v-list-item>
          <v-list-item-action>
            <s-btn @click="createFinding" :disabled="disabled" color="secondary" x-small>
              <v-icon>mdi-plus</v-icon>
              Create
            </s-btn>
          </v-list-item-action>
        </v-list-item>
      </v-list>
    </template>

    <template #default>
      <template v-if="currentItemIsSection">
        <div v-for="fieldId in currentItem.fields" :key="fieldId">
          <dynamic-input-field 
            :value="value.report[fieldId]" @input="updateSectionField(fieldId, $event)" 
            :id="fieldId"
            :definition="projectType.report_fields[fieldId]" 
            :show-field-ids="true"
            :upload-file="uploadFile" 
            :rewrite-file-url="rewriteFileUrl"
            :selectable-users="[$auth.user]"
            :lang="projectType.language"
            :disabled="disabled"
          />
        </div>
      </template>
      <template v-else-if="currentItemIsFinding">
        <div v-for="fieldId in projectType.finding_field_order" :key="currentItem.id + fieldId">
          <dynamic-input-field 
            :value="currentItem[fieldId]" @input="updateFindingField(fieldId, $event)" 
            :id="fieldId"
            :definition="projectType.finding_fields[fieldId]" 
            :show-field-ids="true"
            :upload-file="uploadFile" 
            :rewrite-file-url="rewriteFileUrl"
            :selectable-users="[$auth.user]"
            :lang="projectType.language"
            :disabled="disabled"
          />
        </div>
      </template>
    </template>
  </split-menu>
</template>

<script>
import { v4 as uuidv4 } from 'uuid';
import * as cvss from "@/utils/cvss.js";
import { sortFindings } from '~/utils/other';

export default {
  props: {
    value: {
      type: Object,
      required: true,
    },
    projectType: {
      type: Object,
      required: true,
    },
    disabled: {
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
  },
  data() {
    return {
      currentItem: null,
      menuSize: 20,
    }
  },
  computed: {
    currentItemIsSection() {
      return this.currentItem && this.projectType.report_sections.some(s => s.id === this.currentItem.id);
    },
    currentItemIsFinding() {
      return this.currentItem && this.value.findings.some(f => f.id === this.currentItem.id);
    },
  },
  methods: {
    updateSectionField(fieldId, value) {
      const newVal = Object.assign({}, this.value);
      newVal.report = Object.assign({}, this.value.report, Object.fromEntries([[fieldId, value]]));
      this.$emit('input', newVal);
    },
    updateFindingField(fieldId, value) {
      const newVal = Object.assign({}, this.value);
      const newFinding = Object.assign({}, this.currentItem, Object.fromEntries([[fieldId, value]]));
      newVal.findings = sortFindings(
        this.value.findings
          .map(f => f.id === newFinding.id ? newFinding : f));
      this.$emit('input', newVal);
      this.currentItem = newFinding;
    },
    createField(definition) {
      if (definition.type === 'list') {
        return [];
      } else if (definition.type === 'object') {
        return this.createObject(definition.properties);
      }
      return definition.default;
    },
    createObject(properties) {
      return Object.fromEntries(
        Object.entries(properties)
          .map(([k, d]) => [k, this.createField(d)]));
    },
    createFinding() {
      const newFinding = this.createObject(this.projectType.finding_fields);
      newFinding.id = uuidv4();
      newFinding.title = newFinding.title || 'New Demo Finding';

      const newVal = Object.assign({}, this.value);
      newVal.findings = this.value.findings.concat([newFinding]);
      this.$emit('input', newVal);
      this.currentItem = newFinding;
    },
    deleteFinding(finding) {
      const newVal = Object.assign({}, this.value);
      newVal.findings = this.value.findings.filter(f => f.id !== finding.id);
      this.$emit('input', newVal);
    },
    riskLevel(cvssVector) {
      return cvss.levelNumberFromScore(cvss.scoreFromVector(cvssVector));
    },
  }
}
</script>

<style lang="scss" scoped>
@for $level from 1 through 5 {
  .finding-level-#{$level} {
    border-left: 0.4em solid map-get($risk-color-levels, $level);
  }
}

.v-list-item__action {
  margin: 0;
}
</style>
