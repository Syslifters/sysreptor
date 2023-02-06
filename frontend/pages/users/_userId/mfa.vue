<template>
    <s-card>
      <v-card-title>Multi Factor Authentication</v-card-title>
      <v-card-text>
        <p>
          If this user lost all its MFA methods and cannot log in anymore, you can remove all MFA devices to disable MFA.
        </p>

        <v-list>
          <v-list-item v-for="mfaMethod in mfaMethods" :key="mfaMethod.id">
            <v-list-item-title>
              <v-icon class="mr-3">{{ mfaMethodChoices.find(c => c.value === mfaMethod.method_type).icon }}</v-icon>
              {{ mfaMethod.name }}
              <template v-if="mfaMethod.is_primary">
                <v-chip small class="ml-3">Primary</v-chip>
              </template>
            </v-list-item-title>
            <v-list-item-action>
              <btn-delete icon :delete="() => deleteMfaMethod(mfaMethod)" :disabled="!canEdit" />
            </v-list-item-action>
          </v-list-item>
          <v-list-item v-if="mfaMethods.length === 0">
            <v-list-item-title>Multi Factor Authentication is disabled</v-list-item-title>
          </v-list-item>
        </v-list>
      </v-card-text>
    </s-card>
</template>

<script>
import { mfaMethodChoices } from '~/utils/other';

export default {
  async asyncData({ $axios, params }) {
    const [mfaMethods, user] = await Promise.all([
      $axios.$get(`/pentestusers/${params.userId}/mfa/`),
      $axios.$get(`/pentestusers/${params.userId}/`),
    ])
    return { mfaMethods, user };
  },
  computed: {
    mfaMethodChoices() {
      return mfaMethodChoices;
    },
    canEdit() {
      return this.$auth.hasScope('user_manager') && !this.user.is_system_user;
    }
  },
  methods: {
    async deleteMfaMethod(mfaMethod) {
      return await this.$axios.$delete(`/pentestusers/${this.params.userId}/mfa/${mfaMethod.id}/`);
    }
  }
}
</script>
