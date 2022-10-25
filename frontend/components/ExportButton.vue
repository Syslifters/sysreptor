<template>
  <s-btn @click="performExport" :loading="exportInProgress" color="secondary" class="ml-1 mr-1">
    <v-icon>mdi-download</v-icon>
    Export
  </s-btn>
</template>

<script>
import fileDownload from 'js-file-download';

export default {
  props: {
    exportUrl: {
      type: String,
      required: true,
    },
    name: {
      type: String,
      default: null,
    },
  },
  data() {
    return {
      exportInProgress: false,
    };
  },
  computed: {
    filename() {
      const name = (this.name || 'export').replaceAll(' ', '-');
      return name + '.tar.gz';
    },
  },
  methods: {
    async performExport() {
      if (this.exportInProgress) {
        return;
      }

      this.exportInProgress = true;
      try {
        const res = await this.$axios.$post(this.exportUrl, {}, {
          responseType: 'arraybuffer',
        });
        fileDownload(res, this.filename);
      } catch (error) {
        this.$toast.global.requestError({ error });
      } finally {
        this.exportInProgress = false;
      }
    }
  },
}
</script>
