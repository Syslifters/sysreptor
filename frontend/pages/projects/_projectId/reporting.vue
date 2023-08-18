<template>
  <split-menu v-model="menuSize">
    <template #menu>
      <v-list dense class="pb-0 h-100 d-flex flex-column">
        <div>
          <v-list-item-title class="text-h6 pl-2">{{ project.name }}</v-list-item-title>
        </div>
          
        <div class="flex-grow-1 overflow-y-auto">
          <v-subheader>Sections</v-subheader>
          <v-list-item
            v-for="section in sections"
            :key="section.id"
            :to="`/projects/${$route.params.projectId}/reporting/sections/${section.id}/`"
            nuxt
          >
            <lock-info :value="section.lock_info" />
            <v-list-item-content>
              <v-list-item-title>{{ section.label }}</v-list-item-title>
              <v-list-item-subtitle>
                <span v-if="section.assignee" :class="{'assignee-self': section.assignee.id == $auth.user.id}">
                  @{{ section.assignee.username }}
                </span>
              </v-list-item-subtitle>
            </v-list-item-content>
            <status-info :value="section.status" />
          </v-list-item>

          <v-subheader>
            Findings
            <v-spacer />
            <s-tooltip>
              <template #activator="{on}">
                <s-btn 
                  @click="toggleOverrideFindingOrder" 
                  :disabled="project.readonly"
                  small
                  icon
                  v-on="on"
                >
                  <v-icon v-if="project.override_finding_order" small>mdi-sort-variant-off</v-icon>
                  <v-icon v-else small>mdi-sort-variant</v-icon>
                </s-btn>
              </template>

              <template #default>
                <span v-if="project.override_finding_order">Custom order</span>
                <span v-else>Default order</span>
              </template>
            </s-tooltip>
          </v-subheader>

          <draggable
            :value="findings"
            @input="sortFindings"
            draggable=".draggable-item" 
            handle=".draggable-handle"
            :disabled="project.readonly || !project.override_finding_order"
          >
            <v-list-item
              v-for="finding in findings"
              :key="finding.id"
              :to="`/projects/${$route.params.projectId}/reporting/findings/${finding.id}/`"
              nuxt
              :ripple="false"
              class="draggable-item"
              :class="'finding-level-' + riskLevel(finding)"
            >
              <v-list-item-icon v-if="project.override_finding_order" class="draggable-handle mr-2">
                <v-icon :disabled="disabled">mdi-drag-horizontal</v-icon>
              </v-list-item-icon>
              <lock-info :value="finding.lock_info" />
              <v-list-item-content>
                <v-list-item-title>{{ finding.data.title }}</v-list-item-title>
                <v-list-item-subtitle>
                  <span v-if="finding.assignee" :class="{'assignee-self': finding.assignee.id == $auth.user.id}">
                    @{{ finding.assignee.username }}
                  </span>
                </v-list-item-subtitle>
              </v-list-item-content>
              <status-info :value="finding.status" />
            </v-list-item>
          </draggable>
        </div>

        <div>
          <v-divider class="mb-1" />
          <v-list-item>
            <create-finding-dialog :project="project" />
          </v-list-item>
        </div>
      </v-list>
    </template>

    <template #default>
      <NuxtChild />
    </template>
  </split-menu>
</template>

<script>
import Draggable from 'vuedraggable';
import * as cvss from '@/utils/cvss.js';

export default {
  components: { Draggable },
  async asyncData({ params, store }) {
    const project = await store.dispatch('projects/fetchById', params.projectId);
    return { 
      project: await project,
      projectType: await store.dispatch('projecttypes/getById', project.project_type),
    };
  },
  data() {
    return {
      refreshListingsInterval: null,
      wasOverrideFindingOrder: false,
    }
  },
  head: {
    title: 'Reporting',
  },
  computed: {
    findings() {
      return this.$store.getters['projects/findings'](this.project.id, { projectType: this.projectType });
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
  watch: {
    'project.override_finding_order': {
      immediate: true,
      handler() {
        this.wasOverrideFindingOrder ||= this.project.override_finding_order;
      }
    }
  },
  mounted() {
    this.refreshListingsInterval = setInterval(this.refreshListings, 10_000);
  },
  beforeDestroy() {
    if (this.refreshListingsInterval !== null) {
      clearInterval(this.refreshListingsInterval);
      this.refreshListingsInterval = null;
    }
  },
  methods: {
    async refreshListings() {
      try {
        this.project = await this.$store.dispatch('projects/fetchById', this.project.id);
        this.project_type = await this.$store.dispatch('projecttypes/getById', this.project.project_type);
      } catch (error) {
        // hide error
      }
    },
    riskLevel(finding) {
      if ('severity' in this.projectType.finding_fields) {
        return cvss.levelNumberFromLevelName(finding.data.severity);
      } else if ('cvss' in this.projectType.finding_fields) {
        return cvss.levelNumberFromScore(cvss.scoreFromVector(finding.data.cvss));
      } else {
        return 'unknown';
      }
    },
    async toggleOverrideFindingOrder() {
      if (!this.wasOverrideFindingOrder) {
        // Use current sort order as starting point
        // But prevent destorying previous overwritten order on toggle
        await this.sortFindings(this.findings);
      }

      this.project = await this.$store.dispatch('projects/partialUpdate', { 
        obj: {
          id: this.project.id,
          override_finding_order: !this.project.override_finding_order,
        }
      });
    },
    async sortFindings(findings) {
      await this.$store.dispatch('projects/sortFindings', {
        projectId: this.project.id,
        findings,
      });
    },
  }
};
</script>

<style lang="scss" scoped>
@for $level from 1 through 5 {
  .finding-level-#{$level} {
    border-left: 0.4em solid map-get($risk-color-levels, $level);
  }
}

:deep(.v-list-item__subtitle) {
  font-size: x-small !important;
}

.draggable-handle {
  cursor: grab;
}
</style>
