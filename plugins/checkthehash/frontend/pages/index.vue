<script setup lang="ts">
import { ref, computed } from 'vue';
import CheckTheHash from '~~/utils/CheckTheHash';
import prototypes from '../data/converted-prototypes.json';
import type HashInfo from '~~/domain/hashinfo';

const hash = ref("");
const noResults = ref(false); // Flag for showing no results message

const results = computed(() => {
  const possibleHashes: HashInfo[] = CheckTheHash(hash.value, prototypes);
  noResults.value = possibleHashes.length === 0 && hash.value.trim() !== ""; // Show message if no results
  return possibleHashes;
});

function copyToClipboard(text: string) {
  navigator.clipboard.writeText(text).then(() => {
    successToast('Copied');
  });
}
</script>

<script lang="ts">
export default {
  data: () => ({
    // keeps track of whether a list item is open
    open: ['Open'],
  }),
}
</script>

<template>
  <full-height-page class="scrollbar">
    <div class="content-wrapper">
      <v-container class="pt-5">
        <!-- Text input triggers renderHash on input automatically -->
        <v-text-field v-model="hash" label="Paste The Hash" variant="underlined" spellcheck="false" hide-details="auto"
          autofocus class="mt-0 mb-2" style="width: 100%;" />

        <v-subheader v-if="noResults" class="text-h5 text-error mb-4">No matching hash mode found.</v-subheader>
        <v-subheader v-if="results.length" class="text-h5 mb-4">Possible Hash Modes:</v-subheader>
        <v-list v-if="results.length" v-model:opened="open">
          <template v-for="({ name, hashcat, john }, index) in results" :key="index">
            <v-list-group v-if="hashcat != null || john != null">
              <template v-slot:activator="{ props }">
                <v-list-item v-bind="props" :title="name"></v-list-item>
              </template>
              <v-list-item v-if="hashcat != null">
                <v-code class="code-container">
                  <v-icon size="small" class="copy-icon"
                    @click="copyToClipboard(`hashcat --hash-type=${hashcat} ${hash}`)">mdi-content-copy</v-icon>
                  <span class="command"> hashcat --hash-type={{ hashcat }} {{ hash }}</span>
                </v-code>
              </v-list-item>
              <v-list-item v-if="john != null">
                <v-code class="code-container">
                  <v-icon size="small" class="copy-icon"
                    @click="copyToClipboard(`john --format=${john} <(echo '${hash}')`)">mdi-content-copy</v-icon>
                  <span class="command"> john --format={{ john }} <(echo '{{ hash }}')</span>
                </v-code>
              </v-list-item>
            </v-list-group>
            <v-list-item v-else :title="name"></v-list-item>
          </template>
        </v-list>
      </v-container>
      <footer class="footer">
        <p>Identification based on: <a href="https://github.com/noraj/haiti" target="_blank">noraj/haiti</a></p>
      </footer>
    </div>
  </full-height-page>
</template>

<style scoped>
.copy-icon {
  margin-right: 5px;
}

.scrollbar {
  display: flex;
  flex-direction: column;
  max-height: 100vh;
  overflow-y: auto;
}

.full-height-page {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.content-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  height: 100%;
}

.footer {
  padding: 1rem;
  border-top: 1px solid darkgray;
  text-align: right;
  position: relative;
  bottom: 0;
}

.footer a {
  color: #007bff;
  text-decoration: none;
}

.footer a:hover {
  text-decoration: underline;
}

.footer p {
  font-size: small;
}

.list-item {
  animation: slide-in 0.5s ease-out;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.list-item:hover {
  background-color: #363636;
}

@keyframes slide-in {
  from {
    transform: translateY(20px);
    opacity: 0;
  }

  to {
    transform: translateY(0);
    opacity: 1;
  }
}
</style>
