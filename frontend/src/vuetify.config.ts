import { defineVuetifyConfiguration } from "vuetify-nuxt-module/custom-configuration";
import { merge } from "lodash-es";

const sysreptorGreen = '#aabb11'
const sysreptorGreenDark = '#818b06'
const themeLightTextColor = '#1E1E1E';
const themeDarkTextColor = '#f0f0f0';

const themeCommon = {
  colors: {
    primary: sysreptorGreen,
    'on-primary': '#ffffff',
    'primary-bg': sysreptorGreenDark,
    'on-primary-bg': '#ffffff',
    secondary: '#4f4f4f',
    'on-secondary': '#ffffff',

    logo: sysreptorGreen,

    error: '#FF5252',
    info: '#2196F3',
    success: sysreptorGreen,
    warning: '#FFC107',
    'on-warning': themeLightTextColor,
  },
  variables: {
    'high-emphasis-opacity': 0.9,
    'medium-emphasis-opacity': 0.70,
    'disabled-opacity': 0.70,
  },
};
const themeLight = merge({}, themeCommon, {
  dark: false,
  colors: {
    primary: sysreptorGreenDark,
    logo: sysreptorGreenDark,

    background: '#ffffff',
    'on-background': themeLightTextColor,
    surface: '#ffffff',
    'on-surface': themeLightTextColor,

    header: '#ededed',
    'on-header': themeLightTextColor,
    drawer: '#ededed',
    'on-drawer': themeLightTextColor,

    'codemirror-selection': '#ADD6FF',
  },
  variables: {
    'border-color': themeLightTextColor,
    'theme-on-code': themeLightTextColor,
  },
});
const themeDark = merge({}, themeCommon, {
  dark: true,
  colors: {
    primary: sysreptorGreen,
    logo: sysreptorGreen,

    background: '#2a2a2a',
    'on-background': themeDarkTextColor,
    surface: '#2a2a2a',
    'on-surface': themeDarkTextColor,

    header: '#3c3c3c',
    'on-header': themeDarkTextColor,
    drawer: '#3c3c3c',
    'on-drawer': themeDarkTextColor,

    'codemirror-selection': '#264F78',
  },
  variables: {
    'border-color': themeDarkTextColor,
    'theme-on-code': themeDarkTextColor,
  }
});
const adminThemeMixin = {
  colors: {
    primary: '#ff7300',
    'primary-bg': '#ff7300',
    header: '#a04800',
    'on-header': '#ffffff',
    logo: '#ffffff',
  }
};

export default defineVuetifyConfiguration({
  directives: true,
  labComponents: true,
  icons: {
    defaultSet: 'mdi',
  },

  theme: {
    defaultTheme: 'light',
    themes: {
      light: themeLight,
      lightAdmin: merge({}, themeLight, adminThemeMixin),
      dark: themeDark,
      darkAdmin: merge({}, themeDark, adminThemeMixin),
    },
  },
  defaults: {
    SCode: {
      tag: 'code',
    },
    STooltip: {
      transition: 'fade-transition',
      openDelay: 200,
    },
    SCard: {
      variant: 'outlined',
    },
    SBtn: {
      variant: 'flat',
    },
    SBtnPrimary: {
      variant: 'flat',
      color: 'primary-bg',
    },
    SBtnSecondary: {
      variant: 'flat',
      color: 'secondary',
    },
    SBtnOther: {
      variant: 'text',
    },
    SBtnIcon: {
      icon: true,
      variant: 'text',
    },
    STextField: {
      persistentHint: true,
      hideDetails: 'auto',
      maxErrors: 100,
      variant: 'outlined',
      spellcheck: "false",
    },
    SCheckbox: {
      persistentHint: true,
      hideDetails: 'auto',
      maxErrors: 100,
    },
    SSelect: {
      persistentHint: true,
      hideDetails: 'auto',
      maxErrors: 100,
      variant: 'outlined',
    },
    SAutocomplete: {
      persistentHint: true,
      hideDetails: 'auto',
      maxErrors: 100,
      variant: 'outlined',
      spellcheck: "false",
    },
    SCombobox: {
      persistentHint: true,
      hideDetails: 'auto',
      maxErrors: 100,
      variant: 'outlined',
      spellcheck: "false",
    },
    SInput: {
      persistentHint: true,
      hideDetails: 'auto',
      maxErrors: 100,
    },
    SField: {
      variant: 'outlined',
      spellcheck: "false",
    },
  },
  aliases: {
    STooltip: 'VTooltip',
    SCard: 'VCard',
    SBtn: 'VBtn',
    SBtnPrimary: 'VBtn',
    SBtnSecondary: 'VBtn',
    SBtnOther: 'VBtn',
    SBtnIcon: 'VBtn',
    STextField: 'VTextField',
    SCheckbox: 'VCheckbox',
    SSelect: 'VSelect',
    SAutocomplete: 'VAutocomplete',
    SCombobox: 'VCombobox',
    SInput: 'VInput',
    SField: 'VField',
    SCode: 'VCode',
  },
})
