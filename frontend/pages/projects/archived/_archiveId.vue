<template>
  <v-container>
    <edit-toolbar>
      <template #title>{{ archive.name }}</template>

      <s-dialog v-model="restoreWizard.visible">
        <template #activator="{attrs, on}">
          <s-btn 
            :disabled="!publicKeyEncryptedKeyPartData"
            color="primary"
            v-bind="attrs" v-on="on"
          >
            <v-icon>mdi-folder-lock-open-outline</v-icon>
            Restore
          </s-btn>
        </template>
        <template #title>Restore Project</template>
        
        <template #default>
          <splitpanes class="default-theme">
            <pane :size="20">
              <v-list dense>
                <v-subheader>Public Keys</v-subheader>
                <v-list-item-group v-model="restoreWizard.selectedPart" mandatory>
                  <v-list-item
                    v-for="encryptedPart in publicKeyEncryptedKeyPartData"
                    :key="encryptedPart.id"
                    :value="encryptedPart"
                  >
                    <v-list-item-title>{{ encryptedPart.public_key.name }}</v-list-item-title>
                  </v-list-item>
                </v-list-item-group>
              </v-list>
            </pane>
            <pane :size="80">
              <v-container v-if="restoreWizard.selectedPart">
                <p>
                  Decrypt the following message with your private key <strong>{{ restoreWizard.selectedPart.public_key.name }}</strong>
                  and copy the decrypted data into the text field below.
                </p>
                <p><code>gpg --decrypt message.txt</code></p>
                <v-textarea
                  v-model="restoreWizard.selectedPart.encrypted_data"
                  auto-grow
                  readonly
                  spellcheck="false"
                  class="textarea-codeblock pt-0"
                />

                <s-text-field
                  v-model="restoreWizard.form.data"
                  label="Decrypted data"
                  :error-messages="restoreWizard.error"
                />
                <btn-confirm
                  :action="decryptKeyPart"
                  :disabled="!restoreWizard.form.data"
                  :confirm="false"
                  button-text="Restore"
                  button-icon="mdi-folder-lock-open-outline"
                  button-color="primary"
                  class="mt-4"
                />
              </v-container>
            </pane>
          </splitpanes>
        </template>
      </s-dialog>
    </edit-toolbar>

    <div class="mb-4">
      <chip-created :value="archive.created" />
      <chip-auto-delete :value="archive.auto_delete_date" />
      <chip-tag v-for="tag in archive.tags" :key="tag" :value="tag" />
    </div>

    <p class="mt-4">
      <strong>{{ archive.threshold }} of {{ archive.key_parts.length }}</strong> users are required to restore the project.<br>
      <template v-if="archive.key_parts.filter(p => p.is_decrypted).length > 0">
        <strong>{{ archive.threshold - archive.key_parts.filter(p => p.is_decrypted).length }} more users</strong> required to restore the project.
      </template>
    </p>

    <h6 class="text-h6 mt-4">Users</h6>
    <v-simple-table>
      <tbody>
        <tr v-for="keypart in archive.key_parts" :key="keypart.id">
          <td>
            {{ keypart.user.username }}<template v-if="keypart.user.name"> ({{ keypart.user.name }})</template>
            <v-chip v-if="!keypart.user.is_active" small class="ml-4" color="warning">
              <v-icon small left>mdi-alert</v-icon>
              inactive
            </v-chip>
          </td>
          <td>
            <template v-if="keypart.is_decrypted">
              <v-icon color="success">mdi-lock-open-variant</v-icon>
              Restored at {{ keypart.decrypted_at }}
            </template>
            <template v-else>
              <v-icon color="error">mdi-lock</v-icon>
              Encrypted
            </template>
          </td>
        </tr>
      </tbody>
    </v-simple-table>
  </v-container>
</template>

<script>
import { Splitpanes, Pane } from 'splitpanes';

export default {
  components: { Splitpanes, Pane },
  async asyncData({ $axios, $auth, params }) {
    const archive = await $axios.$get(`/archivedprojects/${params.archiveId}/`);
    const userKeyPart = archive.key_parts.find(keypart => keypart.user.id === $auth.user.id);
    let publicKeyEncryptedKeyPartData = null;
    if (userKeyPart && !userKeyPart.is_decrypted) {
      publicKeyEncryptedKeyPartData = await $axios.$get(`/archivedprojects/${params.archiveId}/keyparts/${userKeyPart.id}/public-key-encrypted-data/`);
    }
    return { archive, userKeyPart, publicKeyEncryptedKeyPartData };
  },
  data() {
    return {
      restoreWizard: {
        visible: false,
        selectedPart: null,
        form: {
          data: '',
        },
        error: null,
      }
    };
  },
  head() {
    return {
      titleTemplate: title => this.$root.$options.head.titleTemplate((title ? `${title} | ` : '') + this.archive.name),
    }
  },
  methods: {
    async decryptKeyPart() {
      try {
        const res = await this.$axios.$post(`/archivedprojects/${this.archive.id}/keyparts/${this.userKeyPart.id}/decrypt/`, this.restoreWizard.form);
        this.restoreWizard.visible = false;
        if (res.status === 'project-restored') {
          this.$toast.success('Project restored successfully.');
          this.$router.push(`/projects/${res.project_id}/`);
        } else {
          this.$toast.success('Key part decrypted successfully. More users are required to restore the project.');
          this.$nuxt.refresh();
        }
      } catch (error) {
        if (error?.response?.status === 400 && error?.response?.data?.[0]) {
          this.restoreWizard.error = error.response.data;
        }
      }
    },
  },
}
</script>

<style lang="scss" scoped>
@import '@/assets/splitpanes.scss';

.textarea-codeblock {
  :deep(textarea) {
    font-family: monospace;
    line-height: 1.2em;
    font-size: medium;
    background-color: rgba(0, 0, 0, 0.05);
    padding: 1em;
  }
}
</style>
