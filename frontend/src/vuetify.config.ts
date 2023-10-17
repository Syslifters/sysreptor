import { defineVuetifyConfiguration } from "vuetify-nuxt-module/custom-configuration";

export default defineVuetifyConfiguration({
  directives: true,
  labComponents: true,
  icons: {
    defaultSet: 'mdi',
  },

  theme: {
    defaultTheme: 'light',
    themes: {
      light: {
        dark: false,
        colors: {
          primary: '#1976D2',
          secondary: '#424242',
          accent: '#82B1FF',
          error: '#FF5252',
          info: '#2196F3',
          success: '#4CAF50',
          warning: '#FFC107',
          'on-warning': '#1E1E1E',
        },
        variables: {
          'high-emphasis-opacity': 0.9,
          'medium-emphasis-opacity': 0.70,
          'disabled-opacity': 0.70,
        },
      },
      // dark: {
      //   dark: true,
      //   colors: {
      //     primary: '#1976D2',
      //     secondary: '#424242',
      //     accent: '#82B1FF',
      //     error: '#FF5252',
      //     info: '#2196F3',
      //     success: '#4CAF50',
      //     warning: '#FFC107',
      //   },
      // },
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
      color: 'primary',
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
