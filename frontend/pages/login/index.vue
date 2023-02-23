<template>
  <v-container fluid fill-height>
    <v-layout align-center justify-center>
      <v-flex xs12 sm8 md4>
        <login-oidc-form>
          <template #append>
            <v-list-item>
              <s-btn to="/login/local" nuxt color="secondary" block>
                Login with local user
              </s-btn>
            </v-list-item>
          </template>
        </login-oidc-form>
      </v-flex>
    </v-layout>
  </v-container>
</template>

<script>
export default {
  auth: false,
  head: {
    title: 'Login',
  },
  mounted() {
    if (this.$store.getters['apisettings/settings'].auth_providers === 0) {
      this.$router.replace('/login/local/');
    }
  },
}
</script>
