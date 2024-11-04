<script setup lang="ts">
import { ref, watch } from 'vue';
import CheckTheHash from '~~/utils/CheckTheHash';
import prototypes from '../../data/converted-prototypes.json';

const hash = ref("");
const results = ref<string[]>([]);
const copiedIndex = ref<number | null>(null);
const noResults = ref(false); // Flag for showing no results message

function renderHash() {
  console.log("Running render Hash");
  const possibleHashes: string[] = CheckTheHash(hash.value, prototypes);
  console.log(possibleHashes);
  results.value = possibleHashes;
  noResults.value = possibleHashes.length === 0 && hash.value.trim() !== ""; // Show message if no results
}

function copyToClipboard(text: string, index: number) {
  navigator.clipboard.writeText(text).then(() => {
    console.log('Copied to clipboard:', text);
    copiedIndex.value = index;
    setTimeout(() => {
      copiedIndex.value = null;
    }, 2000);
  });
}

// Watch for changes in the hash and run renderHash when hash updates
watch(hash, () => {
  renderHash();
});
</script>

<template>
  <v-container class="d-flex flex-row align-center justify-center">
    <v-row>
      <v-col cols="12" class="d-flex flex-column align-center">
        <!-- Text input triggers renderHash on input automatically -->
        <v-text-field
          v-model="hash"
          label="Paste The Hash"
          variant="underlined"
          spellcheck="false"
          hide-details="auto"
          autofocus
          class="mt-0 mb-2"
          style="width: 50vw;"
        />
      </v-col>

      <v-col cols="12" class="d-flex flex-column align-center">
        <!-- Display "No results found" message when no matching hashes -->
        <v-subheader v-if="noResults" class="text-h5 text-error mb-4">No matching hash mode found.</v-subheader>

        <!-- Display possible hashes if there are any -->
        <v-subheader v-if="results.length" class="text-h5 mb-4">Possible Hash Modes:</v-subheader>
        
        <v-list v-if="results.length" style="max-height: 70vh; width: 100%;">
          <v-list-item
            v-for="(result, index) in results"
            :key="index"
            class="mb-2 list-item"
            @click="copyToClipboard(result, index)"
          >
            <v-list-item-content>
              <v-list-item-title>{{ result }} <v-icon>mdi-content-copy</v-icon></v-list-item-title>
            </v-list-item-content>
            <v-list-item-content v-if="copiedIndex === index" class="ml-2">
              <v-list-item-title class="text-success">Copied</v-list-item-title>
            </v-list-item-content>
          </v-list-item>
        </v-list>

      </v-col>
    </v-row>
  </v-container>
</template>

<style scoped>
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
