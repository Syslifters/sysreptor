<template>
  <div>
    <split-menu v-model="menuSize">
      <template #menu>
        <v-list dense>
          <v-list-item-title class="text-h6 pl-2">{{ project.name }}</v-list-item-title>

          <v-subheader>Sections</v-subheader>
          <v-list-item
            v-for="section in sections"
            :key="section.id"
            nuxt
            :to="`/projects/${$route.params.projectId}/reporting/sections/${section.id}/`"
          >
            <lock-info :value="section.lock_info" />
            <v-list-item-content>
              <v-list-item-title>{{ section.label }}</v-list-item-title>
            </v-list-item-content>
          </v-list-item>

          <v-subheader>Findings</v-subheader>
          <v-list-item
            v-for="finding in findings"
            :key="finding.id"
            nuxt
            :to="`/projects/${$route.params.projectId}/reporting/findings/${finding.id}/`"
            :class="'finding-level-' + riskLevel(finding.data.cvss)"
          >
            <lock-info :value="finding.lock_info" />
            <v-list-item-content>
              <v-list-item-title>{{ finding.data.title }}</v-list-item-title>
            </v-list-item-content>
          </v-list-item>

          <v-list-item>
            <v-list-item-action>
              <create-finding-dialog :project="project" />
            </v-list-item-action>
          </v-list-item>
        </v-list>
      </template>

      <template #default>
        <NuxtChild />
      </template>
    </split-menu>
  </div>
</template>

<script>
import SplitMenu from '~/components/SplitMenu.vue';
import * as cvss from '@/utils/cvss.js';
import LockInfo from '~/components/LockInfo.vue';

export default {
  components: { SplitMenu, LockInfo },
  async asyncData({ params, store }) {
    const project = store.dispatch('projects/getById', params.projectId);
    const findings = store.dispatch('projects/getFindings', params.projectId);
    const sections = store.dispatch('projects/getSections', params.projectId);
    await Promise.all([project, findings, sections]);
    return { project: await project };
  },
  data() {
    return {
      refreshListingsInterval: null,
    }
  },
  computed: {
    findings() {
      return this.$store.getters['projects/findings'](this.project.id);
    },
    sections() {
      return this.$store.getters['projects/sections'](this.project.id);
    },
    menuSize: {
      get() {
        return this.$store.state.settings.reportInputMenuSize;
      },
      set(val) {
        this.$store.commit('settings/updateReportInputMenuSize', val);
      }
    },
  },
  mounted() {
    this.refreshListingsInterval = setInterval(this.refreshListings, 10_000);
  },
  destroyed() {
    if (this.refreshListingsInterval !== null) {
      clearInterval(this.refreshListingsInterval);
      this.refreshListingsInterval = null;
    }
  },
  methods: {
    refreshListings() {
      try {
        this.$store.dispatch('projects/fetchFindings', this.project.id);
        this.$store.dispatch('projects/fetchSections', this.project.id);
      } catch (error) {
        // hide error
      }
    },
    riskLevel(cvssVector) {
      return cvss.levelNumberFromScore(cvss.scoreFromVector(cvssVector));
    }
  }
};
</script>

<style lang="scss" scoped>
@for $level from 1 through 5 {
  .finding-level-#{$level} {
    border-left: 0.4em solid map-get($risk-color-levels, $level);
  }
}
</style>
