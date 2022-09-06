<template>
  <v-container fluid fill-height>
    <v-layout align-center justify-center>
      <v-flex xs12 sm8 md4>
        <s-card>
          <v-form ref="form" @submit.prevent="login">
            <v-toolbar dark class="login-header" flat tile>
              <v-toolbar-title>Login</v-toolbar-title>
            </v-toolbar>
            <v-card-text>
              <v-text-field
                v-model="form.username"
                type="text"
                name="username"
                label="Username"
                prepend-icon="mdi-account"
                spellcheck="false"
                autocomplete="off"
                required
              />
              <v-text-field
                v-model="form.password"
                type="password"
                name="password"
                label="Password"
                prepend-icon="mdi-lock"
                required
              />

              <p v-if="errorMessage" class="red--text">
                {{ errorMessage }}
              </p>
            </v-card-text>
            <v-card-actions>
              <v-spacer />
              <s-btn type="submit" color="primary">Login</s-btn>
            </v-card-actions>
          </v-form>
        </s-card>
      </v-flex>
    </v-layout>
  </v-container>
</template>

<script>
export default {
  data() {
    return {
      form: {
        username: '',
        password: '',
      },
      errorMessage: null,
    };
  },
  methods: {
    async login() {
      this.errorMessage = null;

      if (!this.form.username || !this.form.password) {
        this.errorMessage = 'Username and password are required';
        return;
      } 

      try {
        await this.$auth.loginWith('local', { data: this.form });
      } catch (error) {
        if (error?.response?.data?.detail) {
          this.errorMessage = error.response.data.detail;
        } else {
          this.$toast.global.requestError({ error, message: 'Login failed' });
        }
      }
    },
  },
};
</script>

<style lang="scss" scoped>
.login-header {
  background-color: $syslifters-darkblue !important;
}
</style>
