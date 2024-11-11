<script setup lang="ts">
import { ref, computed } from 'vue';
import CheckTheHash from '~~/utils/CheckTheHash';
import prototypes from '../../data/converted-prototypes.json';

const hash = ref("");
const results = computed(() => {
  const possibleHashes: string[] = CheckTheHash(hash.value, prototypes);
  noResults.value = possibleHashes.length === 0 && hash.value.trim() !== ""; // Show message if no results
  return possibleHashes;
});
const noResults = ref(false); // Flag for showing no results message

function copyToClipboard(text: string) {
  navigator.clipboard.writeText(text).then(() => {
    successToast('Copied');
  });
}
</script>

<template>
  <full-height-page class="scrollbar">
    <div class="content-wrapper">
      <v-container class="pt-5">
        <v-row>
          <v-col cols="12" class="d-flex flex-column align-center">
            <!-- Text input triggers renderHash on input automatically -->
            <v-text-field v-model="hash" label="Paste The Hash" variant="underlined" spellcheck="false"
              hide-details="auto" autofocus class="mt-0 mb-2" style="width: 50vw;" />
          </v-col>

          <v-col cols="12" class="d-flex flex-column align-center">
            <!-- Display "No results found" message when no matching hashes -->
            <v-subheader v-if="noResults" class="text-h5 text-error mb-4">No matching hash mode found.</v-subheader>

            <!-- Display possible hashes if there are any -->
            <v-subheader v-if="results.length" class="text-h5 mb-4">Possible Hash Modes:</v-subheader>

            <v-list v-if="results.length" class="pt-0 overflow-visible" style="width: 100%;">
              <v-list-item v-for="(result, index) in results" :key="index" class="mb-2 list-item"
                @click="copyToClipboard(result)">
                <v-list-item-content>
                  <v-list-item :title="result" prepend-icon="mdi-content-copy"></v-list-item>
                </v-list-item-content>
              </v-list-item>
            </v-list>
          </v-col>
        </v-row>
      </v-container>
      <div class="flex-grow-1"></div>
      <footer class="footer">
        <p>Identification based on: <a href="https://github.com/noraj/haiti" target="_blank">noraj/haiti</a></p>
      </footer>
    </div>
  </full-height-page>
</template>

<style scoped>
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

.flex-grow-1 {
  flex-grow: 1;
}

.footer {
  padding: 1rem;
  background-color: #353535;
  border-top: 1px solid #1d1d1d;
  text-align: center;
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
