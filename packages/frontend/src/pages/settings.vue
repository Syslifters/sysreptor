<template>
  <full-height-page>
    <v-container class="pt-0">
      <v-form ref="form" class="h-100">
        <edit-toolbar v-bind="toolbarAttrs" />

        <s-card v-for="group in coreConfigGroups" :key="group.title" class="mt-4">
          <v-card-title>
            <component :is="group.professional_only ? ProInfo : 'span'">
              <v-icon start :icon="group.icon || 'mdi-cog'" />
              {{ group.title }}
            </component>
          </v-card-title>
          <v-card-text>
            <v-alert 
              v-if="group.danger"
              type="warning"
              title="Danger Zone"
              text="Changing these settings might prevent users from accessing the application."
              density="compact"
              class="mb-6"
            />

            <div v-for="field in group.fields" :key="field.id">
              <dynamic-input-field 
                v-model="configurationValues[field.id]"
                :definition="field"
                :disabled="field.set_in_env || (field.professional_only && !apiSettings.isProfessionalLicense)"
                :error-message="errorMessages?.[field.id]"
                v-bind="{...fieldAttrs, ...(field.set_in_env ? { rules: [] } : {}) }"
              >
                <template #label>
                  <v-tooltip :disabled="!field.set_in_env">
                    <template #activator="{props: tooltipProps}">
                      <span v-bind="tooltipProps" :class="{'info-env': field.set_in_env}">
                        <pro-info v-if="field.professional_only">{{ field.id }}</pro-info>
                        <span v-else>{{ field.id }}</span>
                        <span v-if="configurationFieldDefault(field)" class="text-body-small ml-2">{{ configurationFieldDefault(field) }}</span>
                        <v-icon v-if="field.set_in_env" end icon="mdi-cog-off" />
                      </span>
                    </template>
                    <template #default>
                      This setting is configured as environment variable.<br>
                      Update the value of the environment variable <v-code>{{ field.id }}</v-code> in <v-code>app.env</v-code><br>
                      or remove it from <v-code>app.env</v-code> to be able to change it here.
                    </template>
                  </v-tooltip>
                </template>
              </dynamic-input-field>
            </div>
          </v-card-text>  
        </s-card>

        <v-divider class="mt-8 mb-8" />

        <s-card v-for="plugin in configurationDefinition.plugins" :key="plugin.plugin_id" class="mt-4">
          <v-card-title>
            <component :is="plugin.professional_only ? ProInfo : 'span'">
              <v-icon start icon="mdi-puzzle" />
              Plugin {{ plugin.name }}
            </component>
          </v-card-title>
          <v-card-text v-if="plugin.description" class="pb-0">
            <markdown-preview :value="plugin.description" />
          </v-card-text>
          <v-card-text>
            <s-checkbox
              :model-value="isPluginEnabled(plugin)"
              @update:model-value="setPluginEnabled(plugin, $event)"
              :disabled="enabledPluginsSetInEnv || (plugin.professional_only && !apiSettings.isProfessionalLicense)"
              label="Is plugin enabled?"
            >
              <template #label>
                <v-tooltip>
                  <template #activator="{props: tooltipProps}">
                    <span :class="{'info-env': enabledPluginsSetInEnv}" v-bind="tooltipProps">
                      Is plugin enabled?
                      <v-icon v-if="enabledPluginsSetInEnv" end icon="mdi-cog-off" />
                    </span>
                  </template>
                  <template #default>
                    <template v-if="enabledPluginsSetInEnv">
                      Plugins can be enabled by configuring the environment variable <v-code>ENABLED_PLUGINS</v-code> in <v-code>app.env</v-code>.<br>
                      Add the plugin name to the environment variable: e.g. <v-code>ENABLED_PLUGINS="{{ plugin.name }},other-plugin,..."</v-code>
                    </template>
                    <template v-else>
                      Enable or disable this plugin for the application.
                    </template>
                  </template>
                </v-tooltip>
              </template>
            </s-checkbox>
            <div v-for="field in plugin.fields" :key="field.id">
              <dynamic-input-field 
                v-model="configurationValues[field.id]"
                :definition="field"
                :disabled="field.set_in_env || ((plugin.professional_only || field.professional_only) && !apiSettings.isProfessionalLicense)"
                :rules="field.set_in_env ? [] : undefined"
                :error-messages="errorMessages?.[field.id]"
                v-bind="{...fieldAttrs, ...(field.set_in_env ? { rules: [] } : {}) }"
              >
                <template #label>
                  <v-tooltip :disabled="!field.set_in_env">
                    <template #activator="{props: tooltipProps}">
                      <span v-bind="tooltipProps" :class="{'info-env': field.set_in_env}">
                        <pro-info v-if="plugin.professional_only || field.professional_only">{{ field.id }}</pro-info>
                        <span v-else>{{ field.id }}</span>
                        <span v-if="configurationFieldDefault(field)" class="text-body-small ml-2">{{ configurationFieldDefault(field) }}</span>
                        <v-icon v-if="field.set_in_env" end icon="mdi-cog-off" />
                      </span>
                    </template>
                    <template #default>
                      This setting is configured as environment variable.<br>
                      Update the value of the environment variable <v-code>{{ field.id }}</v-code> in <v-code>app.env</v-code><br>
                      or remove it from <v-code>app.env</v-code> to be able to change it here.
                    </template>
                  </v-tooltip>
                </template>
              </dynamic-input-field>
            </div>
          </v-card-text>
        </s-card>

      </v-form>
    </v-container>
  </full-height-page>
</template>

<script setup lang="ts">
import { VForm } from 'vuetify/components';
import ProInfo from '@base/components/ProInfo.vue';
import { wait } from '@base/utils/helpers';

export type ConfigurationFieldDefinition = FieldDefinition & {
  group?: string;
  set_in_env?: boolean;
  professional_only?: boolean;
}

export type PluginConfigurationDefinition = {
  plugin_id: string;
  name: string;
  description?: string|null;
  professional_only: boolean;
  enabled: boolean;
  fields: ConfigurationFieldDefinition[];
}

export type ConfigurationDefinition = {
  core: ConfigurationFieldDefinition[];
  plugins: PluginConfigurationDefinition[];
}

definePageMeta({
  title: 'Settings',
  toplevel: true,
});
useHeadExtended({
  breadcrumbs: () => [{ title: 'Settings', to: '/settings/' }],
});

const apiSettings = useApiSettings();

const configurationDefinition = await useFetchE<ConfigurationDefinition>('/api/v1/utils/configuration/definition/', { method: 'GET' });
const configurationValues = await useFetchE<Record<string, any>>('/api/v1/utils/configuration/', { method: 'GET', deep: true });

const enabledPluginsSetInEnv = computed(() => configurationDefinition.value.core.find(f => f.id === 'ENABLED_PLUGINS')?.set_in_env === true);
const enabledPlugins = computed(() => {
  const v = configurationValues.value?.ENABLED_PLUGINS;
  return Array.isArray(v) ? v.filter(p => typeof p === 'string') : [];
});

function isPluginEnabled(plugin: PluginConfigurationDefinition): boolean {
  if (plugin.professional_only && !apiSettings.isProfessionalLicense) {
    return false;
  }
  return enabledPlugins.value.includes(plugin.name) || 
         enabledPlugins.value.includes(plugin.plugin_id) || 
         enabledPlugins.value.includes('*');
}

function setPluginEnabled(plugin: PluginConfigurationDefinition, enabled: boolean) {
  const allPluginNames = configurationDefinition.value.plugins.map(p => p.name);
  let current = [...enabledPlugins.value];
  if (current.includes('*')) {
    current = allPluginNames;
  }

  if (enabled) {
    if (!current.includes(plugin.name)) {
      current = [...current, plugin.name];
    }
  } else {
    current = current.filter(p => ![plugin.name, plugin.plugin_id].includes(p));
  }
  configurationValues.value['ENABLED_PLUGINS'] = current;
}
const coreConfigGroups = computed(() => {
  const coreGroups = [
    {
      group: 'other',
      title: 'Application Settings',
      professional_only: false,
    },
    {
      group: 'sharing',
      title: 'Sharing Settings',
      icon: 'mdi-share-variant',
      professional_only: false,
    },
    {
      group: 'language',
      title: 'Language and Spellcheck Settings',
      icon: 'mdi-translate',
      professional_only: false,
    },
    {
      group: 'archiving',
      title: 'Archiving Settings',
      icon: 'mdi-folder-lock',
      professional_only: true,
    },
    {
      group: 'auth',
      title: 'Authentication Settings',
      icon: 'mdi-account',
      professional_only: true,
      danger: true,
    },
    {
      group: 'permissions',
      title: 'Permission Settings',
      professional_only: true,
    },
    {
      group: 'ai_agent',
      title: 'AI Agent Settings',
      professional_only: true,
    },
  ]

  return coreGroups.map(group => ({
    ...group,
    fields: configurationDefinition.value.core.filter(d => d.group === group.group || (group.group === 'general' && !d.group)),
  })).filter(group => group.fields.length > 0);
});

const form = useTemplateRef<VForm>('form');
const { toolbarAttrs } = useLockEdit({
  form,
  data: configurationValues,
  performSave,
})

const markdownEditorMode = ref(MarkdownEditorMode.MARKDOWN);
const fieldAttrs = computed(() => ({
  lang: 'auto',
  spellcheckSupported: false,
  markdownEditorMode: markdownEditorMode.value,
  'onUpdate:markdownEditorMode': (v: MarkdownEditorMode) => { markdownEditorMode.value = v; },
}));

const errorMessages = ref<any|null>(null);
async function performSave(data: Record<string, any>) {
  try {
    configurationValues.value = await $fetch('/api/v1/utils/configuration/', {
      method: 'PATCH',
      body: data,
    });
    errorMessages.value = null;

    // Wait some time to ensure server worker processes began restarting
    await wait(2000);
    // Reload frontend to re-initialize settings, plugins, etc.
    window.location.reload();
  } catch (error: any) {
    errorMessages.value = error?.data
    throw error;
  }
}


function configurationFieldDefault(field: FieldDefinition) {
  if ([FieldDataType.BOOLEAN, FieldDataType.NUMBER].includes(field.type) || (field.type === FieldDataType.STRING && field.default === null)) {
    return `(default: ${field.default})`;
  } else if ([FieldDataType.STRING].includes(field.type)) {
    return `(default: "${field.default}")`;
  }
  return null;
}
</script>

<style lang="scss" scoped>
.info-env {
  pointer-events: all;
}
</style>
