<template>
  <v-dialog v-model="dialogVisible" max-width="50%">
    <template #activator="{ on, attrs }">
      <s-btn color="primary" :loading="actionInProgress" v-bind="attrs" v-on="on">
        <v-icon>mdi-plus</v-icon>
        Create Design
      </s-btn>
    </template>

    <template #default>
      <s-card>
        <v-card-title>
          <v-toolbar flat>
            <v-toolbar-title>Create Design</v-toolbar-title>
            <v-spacer />
            <s-tooltip>
              <template #activator="{attrs, on}">
                <s-btn v-bind="attrs" v-on="on" @click="closeDialog" icon x-large>
                  <v-icon>mdi-close-thick</v-icon>
                </s-btn>
              </template>
              <span>Cancel</span>
            </s-tooltip>
          </v-toolbar>
        </v-card-title>

        <v-card-text>
          <project-type-selection v-model="currentDesign" return-object :required="false" />
        </v-card-text>
        
        <v-card-actions>
          <v-spacer />
          <s-btn @click="closeDialog" color="secondary">
            Cancel
          </s-btn>
          <s-btn v-if="currentDesign" @click="copyDesign" :loading="actionInProgress" color="primary">
            Copy Existing Design
          </s-btn>
          <s-btn v-else @click="createEmptyDesign" :loading="actionInProgress" color="primary">
            Create Empty Design
          </s-btn>
        </v-card-actions>
      </s-card>
    </template>
  </v-dialog>
</template>

<script>
export default {
  data() {
    return {
      dialogVisible: false,
      currentDesign: null,
      actionInProgress: false,
    }
  },
  methods: {
    closeDialog() {
      this.dialogVisible = false;
      this.currentDesign = null;
    },
    async actionWrapper(action) {
      if (this.actionInProgress) {
        return;
      }

      this.actionInProgress = true;
      try {
        const obj = await action();
        this.$router.push(`/designer/${obj.id}`);
        this.$$toast.success('Created new design');
      } catch (error) {
        this.$toast.global.requestError({ error });
      } finally {
        this.actionInProgress = false;
      }
    },
    async createEmptyDesign() {
      return await this.actionWrapper(async () => {
        return await this.$store.dispatch('projecttypes/create', {
          name: 'New Design',
        });
      })
    },
    async copyDesign() {
      return await this.actionWrapper(async () => {
        return await this.$store.dispatch('projecttypes/copy', {
          id: this.currentDesign.id,
        });
      })
    },
  }
}
</script>
