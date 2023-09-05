import { formatISO9075 } from 'date-fns'
import ProjectLockEditMixin from '~/mixins/ProjectLockEditMixin'

export default {
  mixins: [ProjectLockEditMixin],
  computed: {
    projectUrl() {
      return `/pentestprojects/${this.$route.params.projectId}/history/${this.$route.params.historyDate}/`;
    },
    projectTypeUrl() {
      return `/projecttypes/${this.project.project_type}/history/${this.$route.params.historyDate}/`;
    },
  },
  methods: {
    getHasEditPermissions() {
      return false;
    },
    getErrorMessage() {
      return `This is a historical version from ${formatISO9075(new Date(this.$route.params.historyDate))}.`;
    },
  }
}
