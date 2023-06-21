<template>
  <div
    class="drag-drop-area"
    @drop.prevent="performFileUpload($event.dataTransfer.files)" 
    @dragover.prevent="showDropArea = true" 
    @dragenter.prevent="showDropArea = true" 
    @dragleave.prevent="showDropArea = false"
  >
    <!-- Upload files with drag-and-drop here -->
    <v-row class="ma-0">
      <v-col :cols="12" :md="3">
        <s-card>
          <v-card-actions>
            <s-btn :disabled="disabled || uploadInProgress" :loading="uploadInProgress" @click="$refs.fileInput.click()" color="primary" block>
              <v-icon>mdi-upload</v-icon>
              Upload
              <template #loader>
                <saving-loader-spinner />
                Uploading
              </template>
            </s-btn>
            <input ref="fileInput" type="file" multiple @change="performFileUpload($event.target.files)" :disabled="disabled || uploadInProgress" class="d-none" />
          </v-card-actions>
          <v-card-text class="text--small text-center pt-0">
            Attach files by drag and dropping
          </v-card-text>
        </s-card>
      </v-col>

      <v-col v-for="asset in assets.data" :key="asset.id" :cols="12" :md="3">
        <s-card>
          <v-img v-if="isImage(asset)" :src="imageUrl(asset)" aspect-ratio="2" />
          <v-card-title>{{ asset.name }}</v-card-title>
          <v-card-text class="text--small">
            {{ assetUrl(asset) }}
            <s-tooltip>
              <template #activator="{on, attrs}">
                <s-btn @click="copyAssetUrl(asset)" v-bind="attrs" v-on="on" icon small>
                  <v-icon small>mdi-clipboard-outline</v-icon>
                </s-btn>
              </template>
              <span>Copy path to clipboard</span>
            </s-tooltip>
          </v-card-text>
          <v-card-actions>
            <s-tooltip>
              <template #activator="{on, attrs}">
                <s-btn :to="imageUrl(asset)" download v-bind="attrs" v-on="on" icon>
                  <v-icon>mdi-download</v-icon>
                </s-btn>
              </template>
              <span>Download asset</span>
            </s-tooltip>
            <s-tooltip v-if="isImage(asset)">
              <template #activator="{on, attrs}">
                <s-btn :to="imageUrl(asset)" target="_blank" v-bind="attrs" v-on="on" icon>
                  <v-icon>mdi-open-in-new</v-icon>
                </s-btn>
              </template>
              <span>Show image in new tab</span>
            </s-tooltip>
            <v-spacer />
            <btn-delete icon :delete="() => performDelete(asset)" :disabled="disabled" />
          </v-card-actions>
        </s-card>
      </v-col>

      <v-col v-if="assets.hasNextPage" :cols="12" :md="3">
        <v-card>
          <v-card-text>
            <page-loader :items="assets" />
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <v-fade-transition v-if="!disabled">
      <v-overlay v-if="showDropArea" absolute>
        <div class="text-center mt-10">
          <h2>Drop files to upload</h2>
        </div>
      </v-overlay>
    </v-fade-transition>
  </div>
</template>

<script>
import { last } from 'lodash'
import FileDownload from 'js-file-download';
import urlJoin from 'url-join';
import PageLoader from '../PageLoader.vue';
import { uploadFileHelper } from '~/utils/upload';
import { absoluteApiUrl, CursorPaginationFetcher } from '~/utils/urls';

export default {
  components: { PageLoader },
  props: {
    projectType: {
      type: Object,
      required: true,
    },
    disabled: {
      type: Boolean,
      default: false,
    }
  },
  data() {
    return {
      assets: new CursorPaginationFetcher(`/projecttypes/${this.projectType.id}/assets/`, this.$axios, this.$toast),
      uploadInProgress: false,
      showDropArea: false,
    }
  },
  computed: {
    projectTypeBaseUrl() {
      return `/projecttypes/${this.projectType.id}/`;
    }
  },
  methods: {
    isImage(asset) {
      // Detect file type by extension
      // Used for displaying image previews
      return ['jpg', 'jpeg', 'png', 'gif', 'svg'].includes(last(asset.name.split('.')))
    },
    assetUrl(asset) {
      return `/assets/name/${asset.name}`;
    },
    imageUrl(asset) {
      return absoluteApiUrl(urlJoin(this.projectTypeBaseUrl, this.assetUrl(asset)), this.$axios);
    },
    async uploadSingleFile(file) {
      try {
        const asset = await uploadFileHelper(this.$axios, urlJoin(this.projectTypeBaseUrl, '/assets/'), file);
        this.assets.data.unshift(asset);
      } catch (error) {
        this.$toast.global.requestError({ error, message: 'Failed to upload ' + file.name });
      }
    },
    async performFileUpload(files) {
      if (this.uploadInProgress || this.disabled) {
        return;
      }

      try {
        this.uploadInProgress = true;
        this.showDropArea = false;

        // upload all files
        await Promise.all(Array.from(files).map(f => this.uploadSingleFile(f)));
      } finally {
        // clear file input
        this.$refs.fileInput.value = null;
        this.uploadInProgress = false;
      }
    },
    async performDelete(asset) {
      await this.$axios.$delete(urlJoin(this.projectTypeBaseUrl, `/assets/${asset.id}/`), { progess: false });
      this.assets.data = this.assets.data.filter(a => a.id !== asset.id);
    },
    copyAssetUrl(asset) {
      window.navigator.clipboard.writeText(this.assetUrl(asset));
    },
    async fetchNextPage(entries, observer, isIntersecting) {
      if (isIntersecting) {
        return await this.assets.fetchNextPage();
      }
    }
  }
}
</script>

<style lang="scss" scoped>
.drag-drop-area {
  min-height: 100%;
}

.text--small {
  font-size: smaller;
}
</style>
