<template>
  <v-list dense>
    <v-list-item>
      <project-type-selection
        v-model="fieldFilterDesign"
        label="Show fields of"
        :query-filters="{scope: ['global']}"
        :outlined="false"
        :additional-items="[{id: 'all', name: 'All Designs'}]"
      />
    </v-list-item>

    <v-list-item v-for="d in fieldDefinition" :key="d.id">
      <v-list-item-title>{{ d.id }}</v-list-item-title>
      <v-list-item-action v-if="d.origin !== 'core'">
        <s-btn @click="toggleFieldVisible(d)" icon x-small>
          <v-icon v-if="d.visible">mdi-eye</v-icon>
          <v-icon v-else>mdi-eye-off</v-icon>
        </s-btn>
      </v-list-item-action>
    </v-list-item>
  </v-list>
</template>

<script>
export default {
  async fetch() {
    await this.$store.dispatch('templates/getFieldDefinition');
  },
  computed: {
    fieldDefinition() {
      return this.$store.getters['templates/fieldDefinitionList'];
    },
    fieldFilterDesign: {
      get() {
        return this.$store.state.settings.templateFieldFilterDesign;
      },
      set(val) {
        this.$store.commit('settings/updateTemplateFieldFilterDesign', val);
      }
    },
    fieldFilterHiddenFields: {
      get() {
        return this.$store.state.settings.templateFieldFilterHiddenFields;
      },
      set(val) {
        this.$store.commit('settings/updateTemplateFieldFilterHiddenFields', val);
      }
    },
  },
  watch: {
    async fieldFilterDesign(val) {
      if (val === 'all') {
        this.fieldFilterHiddenFields = [];
      } else {
        try {
          const projectType = await this.$store.dispatch('projecttypes/getById', val);
          this.fieldFilterHiddenFields = this.fieldDefinition.filter(d => !Object.keys(projectType.finding_fields).includes(d.id)).map(d => d.id);
        } catch (error) {
          this.fieldFilterDesign = 'all';
        }
      }
    },
  },
  methods: {
    toggleFieldVisible(d) {
      if (this.fieldFilterHiddenFields.includes(d.id)) {
        this.fieldFilterHiddenFields = this.fieldFilterHiddenFields.filter(f => f !== d.id);
      } else {
        this.fieldFilterHiddenFields = [...this.fieldFilterHiddenFields, d.id];
      }
    },
  }
}
</script>
