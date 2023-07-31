<template>
  <split-menu v-model="menuSize">
    <template #menu>
      <template-field-selector />
    </template>

    <template #default>
      <template-editor v-model="template" :toolbar-attrs="toolbarAttrs" />
    </template>
  </split-menu>
</template>

<script>
import { v4 as uuidv4 } from 'uuid';

export default {
  data() {
    return {
      template: {
        id: uuidv4(),
        tags: [],
        translations: [{
          id: uuidv4(),
          is_main: true,
          language: this.$store.getters['apisettings/settings'].languages[0].code || 'en-US',
          status: 'in-progress',
          data: {
            title: 'TODO: New Template Title',
          },
        }],
      }
    }
  },
  head: {
    title: 'Templates',
  },
  computed: {
    menuSize: {
      get() {
        return this.$store.state.settings.templateInputMenuSize;
      },
      set(val) {
        this.$store.commit('settings/updateTemplateInputMenuSize', val);
      }
    },
    toolbarAttrs() {
      return {
        save: this.performCreate,
        saveButtonText: 'Create',
      };
    },
  },
  methods: {
    async performCreate() {
      const obj = await this.$store.dispatch('templates/create', this.template);
      this.$router.push(`/templates/${obj.id}/`);
    }
  }
}
</script>
