<template>
  <v-container>
    <v-form ref="form">
      <edit-toolbar :form="$refs.form" :save="changePassword">
        <template #title>Reset password of {{ user.username }}<template v-if="user.name"> ({{ user.name }})</template></template>
        <template #save-button-text>Reset Password</template>
      </edit-toolbar>

      <s-password-field 
        v-model="password" 
        label="New password"
        :error-messages="serverErrors?.password" 
        confirm show-strength
      />
    </v-form>
  </v-container>
</template>

<script>
export default {
  async asyncData({ params, $axios }) {
    return {
      user: await $axios.$get(`/pentestusers/${params.userId}/`),
    }
  },
  data() {
    return {
      password: null,
      serverErrors: null,
    }
  },
  methods: {
    async changePassword() {
      try {
        await this.$axios.$post(`/pentestusers/${this.$route.params.userId}/reset-password/`, {
          password: this.password,
        });
        this.serverErrors = null;
        this.$toast.success('Password changed');
        this.$router.push({ path: `/users/${this.user.id}/` });
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
