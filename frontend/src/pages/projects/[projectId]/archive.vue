<template>
  <v-container class="pt-0">
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

    <v-table>
      <tbody>
        <tr v-for="user in allArchiverUsers" :key="user.id">
          <td>
            {{ user.username }}<template v-if="user.name"> ({{ user.name }})</template>
          </td>
          <td>
            <v-chip v-if="user.is_project_member" size="small">Project Member</v-chip>
            <v-chip v-else-if="user.is_global_archiver" size="small">Global Archiver</v-chip>
          </td>
          <td>
            <p v-if="user.can_restore" class="ma-0">
              <v-icon color="green" icon="mdi-checkbox-marked" />
              User will be added as archiver.
            </p>
            <p v-if="!user.has_public_keys" class="ma-0">
              <v-icon color="warning" icon="mdi-alert" />
              User does not have any public keys. Add public keys <strong>before</strong> archiving the project.
              <v-btn
                v-if="user.id === $auth.user.value!.id"
                to="/users/self/publickeys/"
                target="_blank"
                size="small"
                color="secondary"
                prepend-icon="mdi-folder-key"
                text="Add public key"
              />
            </p>
            <p v-if="!user.is_active" class="ma-0">
              <v-icon color="warning" icon="mdi-alert" />
              User is inactive.
            </p>
          </td>
        </tr>
      </tbody>
    </v-table>

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

<script setup lang="ts">
import sortBy from "lodash/sortBy";
import { ArchiveCheckResult } from "~/utils/types";

const route = useRoute();
const apiSettings = useApiSettings();
const projectStore = useProjectStore();

const project = await useAsyncDataE(async () => await projectStore.getById(route.params.projectId as string));
const archiveCheck = await useFetchE<ArchiveCheckResult>(`/api/v1/pentestprojects/${route.params.projectId}/archive-check/`, { method: 'GET' });

const allArchiverUsers = computed(() => sortBy(archiveCheck.value.users, [u => !u.can_restore, 'created']));
const archiverUsers = computed(() => allArchiverUsers.value.filter(u => u.can_restore));
const threshold = computed(() => apiSettings.settings!.archiving_threshold);
const canArchive = computed(() => apiSettings.settings!.features.archiving && threshold.value > 0 && threshold.value <= archiverUsers.value.length);
const warnings = computed(() => {
  const out = [];
  if (archiverUsers.value.length < threshold.value) {
    out.push({
      level: 'error',
      message: `Too few archivers. At least ${threshold.value} users are required to restore the archive.`,
    });
  } else if (threshold.value === archiverUsers.value.length) {
    out.push({
      level: 'warning',
      message: 'All archivers are required to restore the archive. If one user loses their key, the archive is lost forever. Consider adding more users before archiving.',
    });
  }
  // else if (threshold.value > 1 && threshold.value > archiverUsers.value.length * 0.55) {
  //   out.push({
  //     level: 'warning',
  //     message: 'Too many users are required to restore the archive. Consider adding more users before archiving.'
  //   });
  // }
  return out;
});

async function performArchiveProject() {
  const archivedProject = await $fetch<ArchivedProject>(`/api/v1/pentestprojects/${project.value.id}/archive/`, {
    method: 'POST',
    body: {}
  });
  successToast(`Project ${archivedProject.name} archived.`);
  await navigateTo(`/projects/archived/${archivedProject.id}/`);
}
</script>
