<template>
  <v-container>
    <v-form ref="form">
      <edit-toolbar :form="$refs.form" :save="changePassword">
        <template #save-button-text>Change Password</template>
      </edit-toolbar>

      <s-password-field 
        v-model="formData.old_password" 
        label="Old password"
        :error-messages="serverErrors?.old_password" 
      />
      <s-password-field 
        v-model="formData.new_password" 
        label="New password"
        :error-messages="serverErrors?.new_password" 
        confirm show-strength
      />
    </v-form>
  </v-container>
</template>

<script>
export default {
  data() {
    return {
      formData: {
        old_password: null,
        new_password: null,
      },
      serverErrors: null,
    }
  },
  methods: {
    async changePassword() {
      try {
        await this.$axios.$post('/pentestusers/self/change-password/', this.formData);
        this.serverErrors = null;
      } catch (error) {
        if (error?.response?.status === 400 && error?.response?.data) {
          this.serverErrors = error.response.data;
        }
        throw error;
      }
    },
  }
}
</script>
