<template>
  <v-container>
    <h1>Archive Project</h1>
    <p class="text-h6">
      <strong>Name:</strong> {{ project.name }}
    </p>

    <p>
      Archiving exports the project with all its data (finding, sections, notes, images, etc.) into an archive and encrypts it.<br>
      The archive is encrypted with AES, the AES key is split using Shamir Secret Sharing into multiple parts. 
      Each part is assigned to a user and encrypted with the user's public keys.<br>
      The archive can only be restored if at least <strong>{{ threshold }}</strong> users decrypt their key part with their private keys and combine them.
    </p>

    <h6 class="text-h6 mt-4">Users</h6>
    <p>
      <strong>{{ threshold }} of {{ archiverUsers.length }}</strong> users are required to restore the archive.<br>
      <template v-if="threshold > 1">
        At least {{ threshold }} users need to work together to restore the archive.
      </template>
    </p>

    <v-simple-table>
      <tbody>
        <tr v-for="user in allArchiverUsers" :key="user.id">
          <td>
            {{ user.username }}<template v-if="user.name"> ({{ user.name }})</template>
          </td>
          <td>
            <v-chip v-if="user.is_project_member" small>Project Member</v-chip>
            <v-chip v-else-if="user.is_archiver" small>Global Archiver</v-chip>
          </td>
          <td>
            <p v-if="user.can_restore" class="ma-0">
              <v-icon color="green">mdi-checkbox-marked</v-icon>
              User will be added as archiver.
            </p>
            <p v-if="!user.has_public_keys" class="ma-0">
              <v-icon color="warning">mdi-alert</v-icon> 
              User does not have any public keys. Add public keys <strong>before</strong> archiving the project.
              <v-btn v-if="user.id === $auth.user.id" to="/users/self/publickeys/" nuxt target="_blank" small color="secondary">
                <v-icon>mdi-folder-key</v-icon>
                Add public key
              </v-btn>
            </p>
            <p v-if="!user.is_active" class="ma-0">
              <v-icon color="warning">mdi-alert</v-icon> 
              User is inactive.
            </p>
          </td>
        </tr>
      </tbody>
    </v-simple-table>

    <error-list :value="warnings" />
    <btn-confirm
      :disabled="!canArchive"
      :action="performArchiveProject"
      button-text="Archive Project"
      button-icon="mdi-folder-lock-outline"
      button-color="primary"
      tooltip-text="Archive Project"
      :dialog-text="`Archive and encrypt this project. You need at least ${threshold} of ${archiverUsers.length} users to restore this project.`"
      :confirm-input="project.name"
    />
  </v-container>
</template>

<script>
import { sortBy } from 'lodash';

export default {
  async asyncData({ $axios, params }) {
    const [project, archiveCheck] = await Promise.all([
      $axios.$get(`/pentestprojects/${params.projectId}/`),
      $axios.$get(`/pentestprojects/${params.projectId}/archive-check/`)
    ]);
    return { project, archiveCheck };
  },
  computed: {
    threshold() {
      return this.$store.getters['apisettings/settings'].archiving_threshold;
    },
    allArchiverUsers() {
      return sortBy(this.archiveCheck.users, [u => !u.can_restore, 'created']);
    },
    archiverUsers() {
      return this.allArchiverUsers.filter(u => u.can_restore);
    },
    canArchive() {
      return this.$store.getters['apisettings/settings'].features.archiving && 
        this.threshold > 0 && this.threshold <= this.archiverUsers.length;
    },
    warnings() {
      const out = [];
      if (this.archiverUsers.length < this.threshold) {
        out.push({
          level: 'error',
          message: `Too few archivers. At least ${this.threshold} users are required to restore the archive.`,
        });
      } else if (this.threshold === this.archiverUsers.length) {
        out.push({
          level: 'warning',
          message: 'All archivers are required to restore the archive. If one user loses their key, the archive is lost forever. Consider adding more users before archiving.',
        });
      } else if (this.threshold > 1 && this.threshold > this.archiverUsers.length * 0.55 && this.archiverU) {
        out.push({
          level: 'warning',
          message: 'Too many users are required to restore the archive. Consider adding more users before archiving.'
        });
      }
      return out;
    },
  },
  methods: {
    async performArchiveProject() {
      const archivedProject = await this.$axios.$post(`/pentestprojects/${this.project.id}/archive/`, {});
      this.$toast.success(`Project ${archivedProject.name} archived.`);
      this.$router.push(`/projects/archived/${archivedProject.id}/`);
    },
  }
}
</script>
