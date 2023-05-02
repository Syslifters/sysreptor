import LockEditMixin from '~/mixins/LockEditMixin';

function getProjectTypeUrl(params) {
  return `/projecttypes/${params.projectTypeId}/`;
}

export default {
  mixins: [LockEditMixin],
  async asyncData({ $axios, params }) {
    return {
      projectType: await $axios.$get(getProjectTypeUrl(params))
    }
  },
  head() {
    return {
      title: this.projectType.name,
    };
  },
  computed: {
    data() {
      return this.projectType;
    },
  },
  methods: {
    getBaseUrl(data) {
      return getProjectTypeUrl({ projectTypeId: data.id });
    },
    getHasEditPermissions() {
      return (this.projectType?.scope === 'global' && this.$auth.hasScope('designer')) ||
             (this.projectType?.scope === 'private' && this.$store.getters['apisettings/settings'].features.private_designs) ||
             (this.projectType?.scope === 'project' && this.projectType?.source === 'customized');
    },
    getErrorMessage() {
      if (this.projectType?.scope === 'project') {
        if (this.projectType?.source === 'snapshot') {
          return `This design cannot be edited because it is a snapshot from ${this.projectType.created.split('T')[0]}.`
        } else if (this.projectType?.source === 'imported_dependency') {
          return 'This design cannot be edited because it is an imported snapshot.';
        } else if (this.projectType?.source !== 'customized') {
          return 'This design is readonly and cannot be edited.';
        }
      }
      return LockEditMixin.methods.getErrorMessage();
    },
  }
}
