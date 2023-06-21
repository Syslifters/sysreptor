<template>
  <s-dialog v-model="dialogVisible">
    <template #activator="{ on, attrs }">
      <s-btn color="primary" :loading="actionInProgress" class="ml-1 mr-1" v-bind="attrs" v-on="on">
        <v-icon>mdi-plus</v-icon>
        Create
      </s-btn>
    </template>
    <template #title>New Design</template>

    <template #default>
      <v-card-text>
        <project-type-selection v-model="currentDesign" return-object :required="false" autofocus />
      </v-card-text>
        
      <v-card-actions>
        <v-spacer />
        <s-btn @click="dialogVisible = false" color="secondary">
          Cancel
        </s-btn>
        <s-btn v-if="currentDesign" @click="copyDesign" :loading="actionInProgress" color="primary">
          Copy Existing Design
        </s-btn>
        <s-btn v-else @click="createEmptyDesign" :loading="actionInProgress" color="primary">
          Create Empty Design
        </s-btn>
      </v-card-actions>
    </template>
  </s-dialog>
</template>

<script>
export default {
  props: {
    projectTypeScope: {
      type: String,
      default: 'global',
    }
  },
  data() {
    return {
      dialogVisible: false,
      currentDesign: null,
      actionInProgress: false,
    }
  },
  watch: {
    dialogVisible() {
      this.currentDesign = null;
    },
  },
  methods: {
    async actionWrapper(action) {
      if (this.actionInProgress) {
        return;
      }

      this.actionInProgress = true;
      try {
        const obj = await action();
        this.$router.push(`/designs/${obj.id}`);
        this.$toast.success('Created new design');
      } catch (error) {
        this.$toast.global.requestError({ error });
      } finally {
        this.actionInProgress = false;
      }
    },
    async createEmptyDesign() {
      return await this.actionWrapper(async () => {
        return await this.$store.dispatch('projecttypes/create', {
          scope: this.projectTypeScope,
          name: 'New Design',
        });
      })
    },
    async copyDesign() {
      return await this.actionWrapper(async () => {
        return await this.$store.dispatch('projecttypes/copy', {
          id: this.currentDesign.id,
          scope: this.projectTypeScope,
        });
      })
    },
  }
}
</script>
