<template>
  <v-app>
    <v-layout full-height class="align-center justify-center">
      <v-empty-state
        :title="errorHeading"
        color="primary"
        action-text="Go back home"
        @click:action="handleError"
      >
        <template #media>
          <img v-if="props.error.statusCode === 404" src="~/assets/dino/notfound.svg" alt="" class="img-raptor" />
          <icon v-else class="emoji-heading" icon="fluent-emoji:face-with-peeking-eye" />
        </template>
        <template #text>
          <div v-if="props.error.statusCode === 404">
            This site has gone.<br />
            {{ errorMessage }}
          </div>
          <div v-else>
            {{ errorMessage }}<br />
            <div v-if="![401, 403].includes(props.error.statusCode)">
              This should not have happened.<br />
              If you think this is a vulnerability, please <a href="https://docs.syslifters.com/vulnerability-disclosure/" target="_blank">disclose responsibly</a>.<br />
            </div>
          </div>
        </template>
      </v-empty-state>
    </v-layout>
  </v-app>
</template>

<script setup lang="ts">
import { Icon, addIcon } from '@iconify/vue/dist/offline';
import faceWithPeekingEyeIcon from '@iconify/icons-fluent-emoji/face-with-peeking-eye';
import type { NuxtError } from 'nuxt/app';

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
});
const errorMessage = computed(() => {
  let message = props.error.message || 'Error';

  if ((props.error?.data as any)?.detail) {
    message += ': ' + (props.error?.data as any)?.detail;
  } else if (Array.isArray(props.error?.data) && props.error?.data?.length === 1) {
    message += ': ' + props.error?.data[0];
  }
  return message;
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
.img-raptor {
  display: block;
  width: 25rem;
}
</style>
