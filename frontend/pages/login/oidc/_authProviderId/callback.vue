<template>
  <v-container fluid fill-height>
    <v-layout align-center justify-center>
      <v-flex xs12 sm8 md4>
        <s-card>
          <v-toolbar dark class="login-header" flat tile>
            <v-toolbar-title>Login</v-toolbar-title>
          </v-toolbar>

          <v-card-text>
            <v-alert color="error">
              {{ errorMessage }}
            </v-alert>
          </v-card-text>

          <v-card-actions>
            <v-spacer />
            <s-btn to="/login/?logout=true" nuxt color="primary">
              Back
            </s-btn>
          </v-card-actions>
        </s-card>
      </v-flex>
    </v-layout>
  </v-container>
</template>

<script>
export default {
  auth: false,
  async asyncData({ $axios, $auth, route }) {
    let errorMessage = null;

    try {
      await $axios.$get(`/auth/login/oidc/${route.params.authProviderId}/complete/`, {
        params: route.query
      });
      await $auth.fetchUser();
      $auth.redirect('home');
    } catch (error) {
      if (error?.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      } else {
        errorMessage = 'Login failed';
      }
    }

    return { errorMessage };
  },
  head: {
    title: 'Login',
  },
}
</script>
