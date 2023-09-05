import urlJoin from "url-join"
import LockEditMixin from "~/mixins/LockEditMixin";
import { uploadFileHelper } from '~/utils/upload';

export default {
  mixins: [LockEditMixin],
  data() {
    return {
      project: null,
    };
  },
  computed: {
    projectUrl() {
      return `/pentestprojects/${this.$route.params.projectId}/`;
    },
    projectTypeUrl() {
      if (!this.project) {
        return null;
      }
      return `/projecttypes/${this.project.project_type}/`;
    },
  },
  methods: {
    getHasEditPermissions() {
      if (this.project) {
        return !this.project.readonly;
      }
      return true;
    },
    getErrorMessage() {
      if (this.project?.readonly) {
        return 'This project is finished and cannot be changed anymore. In order to edit this project, re-activate it in the project settings.'
      }
      return LockEditMixin.methods.getErrorMessage();
    },
    async uploadFile(file) {
      const img = await uploadFileHelper(this.$axios, urlJoin(this.projectUrl, '/images/'), file);
      return `![](/images/name/${img.name})`;
    },
    rewriteFileUrl(imgSrc) {
      if (imgSrc.startsWith('/assets/')) {
        return urlJoin(this.projectTypeUrl, imgSrc);
      }
      return urlJoin(this.projectUrl, imgSrc);
    },
    rewriteReferenceLink(refId) {
      const finding = this.$store.getters['projects/findings'](this.project.id).find(f => f.id === refId);
      if (finding) {
        return {
          href: `/projects/${this.project.id}/reporting/findings/${finding.id}/`,
          title: `[Finding ${finding.data.title}]`,
        };
      }
      return null;
    },
  }
}
