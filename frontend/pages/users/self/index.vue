<template>
  <v-form ref="form">
    <edit-toolbar :data="user" :form="$refs.form" :save="performSave" />

    <user-info-form v-model="user" :errors="serverErrors" />
  </v-form>
</template>

<script>
export default {
  async asyncData({ $axios }) {
    return {
      user: await $axios.$get('/pentestusers/self/'),
    };
  },
  data() {
    return {
      serverErrors: null,
    }
  },
  methods: {
    async performSave(data) {
      try {
        const user = await this.$axios.$patch('/pentestusers/self/', data);
        this.serverErrors = null;
        this.$auth.setUser(user);
      } catch (error) {
        if (error?.response?.status === 400 && error?.response?.data) {
          this.serverErrors = error.response.data;
        }
        throw error;
      }
    }
  }
}
</script>
