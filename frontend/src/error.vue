<template>
  <v-app>
    <v-container fluid class="fill-height">
      <v-layout class="align-center justify-center">
        <div>
          <h1 class="text-center">
            {{ errorHeading }}
          </h1>
          <div v-if="props.error.statusCode === 404">
            <icon class="emoji-heading" icon="game-icons:dinosaur-bones" />
            <p class="text-center">
              This site has gone.<br>
            </p>
          </div>
          <div v-else>
            <icon class="emoji-heading" icon="fluent-emoji:face-with-peeking-eye" />
            <div class="mx-12">
              <p class="text-center">
                {{ props.error.message }}<br />
                This should not have happened.<br />
                If you think this is a vulnerability, please <a href="https://docs.syslifters.com/vulnerability-disclosure/" target="_blank">disclose responsibly</a>.<br />
              </p>
            </div>
          </div>
          <v-btn @click="handleError" variant="text" text="Go back home" />
        </div>
      </v-layout>
    </v-container>
  </v-app>
</template>

<script setup lang="ts">
import { NuxtError } from "#app";
import { Icon, addIcon } from '@iconify/vue/dist/offline';
import dinosaurBonesIcon from '@iconify/icons-game-icons/dinosaur-bones';
import faceWithPeekingEyeIcon from '@iconify/icons-fluent-emoji/face-with-peeking-eye';

addIcon('game-icons:dinosaur-bones', dinosaurBonesIcon);
addIcon('fluent-emoji:face-with-peeking-eye', faceWithPeekingEyeIcon);

const props = defineProps<{
  error: NuxtError
}>();

const errorHeading = computed(() => {
  if (props.error.statusCode && props.error.statusMessage) {
    return props.error.statusCode + ' ' + props.error.statusMessage;
  } else {
    return 'Ooops!'
  }
})

function handleError() {
  clearError({ redirect: '/' });
}
</script>

<style lang="scss" scoped>
h1 {
  font-size: 20px;
}

.emoji-heading {
  font-size:7rem;
  display: block;
  margin: 15px auto 30px;
}
</style>
