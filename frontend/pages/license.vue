<template>
  <v-container>
    <h1>License Info</h1>

    <p v-if="license.error" class="red--text mt-2">
      <v-icon left color="red">mdi-alert-decagram</v-icon>
      License Error: {{ license.error }}<br>
      Falling back to a free community license. Some features are disabled.<br>
      See <a href="https://docs.sysreptor.com/features-and-pricing/" target="_blank">https://docs.sysreptor.com/features-and-pricing/</a>
    </p>

    <v-simple-table class="table-key-value">
      <tbody>
        <tr>
          <td>License Type:</td>
          <td>{{ license.type }}</td>
        </tr>
        <template v-if="license.type === 'professional'">
          <tr>
            <td>Licensed to:</td>
            <td>{{ license.name }}</td>
          </tr>
          <tr>
            <td>Valid from:</td>
            <td>{{ license.valid_from }}</td>
          </tr>
          <tr>
            <td>Valid until:</td>
            <td>
              {{ license.valid_until }}
              <v-chip v-if="new Date(license.valid_until) < new Date()" color="error" text-color="white" class="ml-2" small>
                Expired
              </v-chip>
              <v-chip v-else-if="new Date(license.valid_until) < new Date().setDate(new Date().getDate() + 2 * 30)" color="warning" class="ml-2" small>
                Expires soon
              </v-chip>
            </td>
          </tr>
        </template>
        <tr>
          <td>Max. Users:</td>
          <td>{{ license.users }}</td>
        </tr>
        <tr>
          <td>Active Users:</td>
          <td>
            {{ license.active_users }}
            <v-chip v-if="license.active_users > license.users" color="error" text-color="white" class="ml-2" small>
              Limit exceeded
            </v-chip>
          </td>
        </tr>
        <tr>
          <td>Software Version:</td>
          <td>{{ license.software_version }}</td>
        </tr>
      </tbody>
    </v-simple-table>
  </v-container>
</template>

<script>
export default {
  async asyncData({ $axios }) {
    return {
      license: await $axios.$get('/utils/license'),
    };
  },
  head: {
    title: 'License',
  },
}
</script>

<style lang="scss" scoped>
.table-key-value {
  td:first-child {
    font-weight: bold;
    width: 15em;
  }
  td:last-child {
    width: auto;
  }
}
</style>
