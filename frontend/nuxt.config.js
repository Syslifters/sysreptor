import { resolve } from 'path';
import colors from 'vuetify/es5/util/colors'
import MonacoWebpackPlugin from 'monaco-editor-webpack-plugin'
import { LicenseWebpackPlugin } from 'license-webpack-plugin';
import licenseTextOverrides from './licenseTextOverrides.js';

const babelPresets = [
  ["@babel/preset-env", { targets: ">0.25%, not dead" }]
];

export default {
  // Build as SPA application
  ssr: false,
  target: 'server',

  // Global page headers: https://go.nuxtjs.dev/config-head
  head: {
    title: null,
    titleTemplate: title => (title ? `${title} | ` : '') + 'SysReptor',
    htmlAttrs: {
      lang: 'en'
    },
    meta: [
      { charset: 'utf-8' },
      { name: 'viewport', content: 'width=device-width, initial-scale=1' },
      { name: 'format-detection', content: 'telephone=no' }
    ],
    link: [
      { rel: 'icon', type: 'image/x-icon', href: '/static/favicon.ico' }
    ]
  },

  // Global CSS: https://go.nuxtjs.dev/config-css
  css: [
    '~/assets/global.scss',
  ],

  // Plugins to run before rendering page: https://go.nuxtjs.dev/config-plugins
  plugins: [
    '~/plugins/apisettings.js',
  ],

  // Auto import components: https://go.nuxtjs.dev/config-components
  components: true,

  // Modules for dev and build (recommended): https://go.nuxtjs.dev/config-modules
  buildModules: [
    // https://go.nuxtjs.dev/eslint
    '@nuxtjs/eslint-module',
    // https://go.nuxtjs.dev/vuetify
    '@nuxtjs/vuetify',
  ],

  // Modules: https://go.nuxtjs.dev/config-modules
  modules: [
    // https://go.nuxtjs.dev/axios
    '@nuxtjs/axios',
    '@nuxtjs/auth-next',
    '@nuxtjs/toast',
    ['nuxt-vuex-localstorage', {
      mode: 'debug',
      localStorage: ['settings'],
    }],
    ...(process.env.NODE_ENV === 'development' ? ['@nuxtjs/proxy'] : []),
  ],

  // Loading bar
  loading: {
    color: 'white',
    height: '2px'
  },

  // Axios module configuration: https://go.nuxtjs.dev/config-axios
  axios: {
    // Workaround to avoid enforcing hard-coded localhost:3000: https://github.com/nuxt-community/axios-module/issues/308
    baseURL: '/api/v1/',
    progress: false,
  },

  auth: {
    cookie: false,
    scopeKey: 'scope',
    strategies: {
      local: false,
      cookie: {
        scheme: '@/utils/auth',
        token: {
          required: false,
          type: false
        },
        user: {
          property: false,
          autoFetch: true,
        },
        endpoints: {
          user: { url: '/pentestusers/self/', method: 'get' },
          logout: { url: '/auth/logout/', method: 'post', data: {} },
          login: false,
          refresh: false,
        },
      },
    },
    watchLoggedIn: true,
    rewriteRedirects: true,
    redirect: {
      login: '/login/',
      reauth: '/login/reauth/',
      logout: '/login/?logout=true',
      home: '/'
    },
  },

  router: {
    middleware: ['auth'],
  },

  // Vuetify module configuration: https://go.nuxtjs.dev/config-vuetify
  vuetify: {
    customVariables: ['~/assets/variables.scss'],
    treeShake: true,
    defaultAssets: false,
    icons: {
      iconfont: 'mdi',
    },
    theme: {
      dark: false,
      themes: {
        dark: {
          primary: colors.blue.darken2,
          accent: colors.grey.darken3,
          secondary: colors.amber.darken3,
          info: colors.teal.lighten1,
          warning: colors.amber.base,
          error: colors.deepOrange.accent4,
          success: colors.green.accent3,
        }
      }
    }
  },

  toast: {
    position: 'bottom-right',
    duration: 5 * 1000,
    keepOnHover: true,
    iconPack: 'mdi',
    closeOnSwipe: true,
    register: [
      {
        name: 'requestError',
        message: ({ error, message = null }) => {
          // eslint-disable-next-line no-console
          console.log('Request error', error, message, error?.response?.data);

          if (!message) {
            if (error?.config?.method === 'get') {
              message = 'Failed to load data';
            } else if (['post', 'put', 'patch'].includes(error?.config?.method)) {
              message = 'Failed to save data';
            } else if (error?.config?.method === 'delete') {
              message = 'Failed to delete data';
            } else {
              message = 'Request error';
            }
          }
          if (error?.response?.data?.detail) {
            message += ': ' + error?.response?.data?.detail;
          } else if (Array.isArray(error?.response?.data) && error?.response?.data?.length === 1) {
            message += ': ' + error?.response?.data[0];
          } else if (error?.response?.status === 429) {
            message += ': Exceeded rate limit. Try again later.';
          }
          return message;
        },
        options: {
          type: 'error',
          icon: 'mdi-alert-outline'
        }
      }
    ]
  },

  // Build Configuration: https://go.nuxtjs.dev/config-build
  build: {
    publicPath: '/static/_nuxt/',
    plugins: [
      new MonacoWebpackPlugin({
        languages: ['html', 'css'],
        features: [
          'bracketMatching', 'comment', 'cursorUndo', 'find', 'folding', 'indentation', 'inlineCompletions', 
          'inspectTokens', 'linesOperations', 'parameterHints', 'rename', 'smartSelect', 'suggest', 'wordHighlighter',
        ],
      }),
      new LicenseWebpackPlugin({
        perChunkOutput: false,
        outputFilename: 'NOTICE',
        excludedPackageTest: packageName => ['reportcreator-rendering', 'reportcreator-markdown'].includes(packageName),
        licenseTypeOverrides: {
          stackframe: 'Unlicense',
        },
        licenseTextOverrides,
        unacceptableLicenseTest: licenseType => ![
          'Apache-2.0', 'MIT', 'BSD-2-Clause', 'BSD-3-Clause', 'ISC', 'Unlicense',
          '(MPL-2.0 OR Apache-2.0)', '(MIT AND BSD-3-Clause)'
        ].includes(licenseType),
      }),
    ],
    babel: {
      babelrc: false,
      presets: babelPresets,
    },
    terser: {
      sourceMap: true,
    },
    extend (config, { dev, isClient }) {
      if (isClient && !dev) {
        // Enable source maps in production
        if (process.env.NODE_ENV !== 'development') {
          config.devtool = 'source-map';
        }
        
        // Resolve dependencies of local packages
        config.resolve.modules.push(resolve(__dirname, '..', 'packages', 'markdown', 'node_modules'));

        // Transpile monaco workers to be able to use them
        config.module.rules.push({
          include: [
            resolve(__dirname, 'node_modules', 'monaco-editor'),
          ],
          test: /\.js$/,
          loader: "babel-loader",
          options: {
            presets: babelPresets,
            cacheDirectory: false,
            compact: false,
          }
        });
      } 
    }
  },

  // Dev API proxy
  proxy: {
    '/api': {
      target: 'http://api:8000',
      changeOrigin: false,
    },
    '/admin': 'http://api:8000',
    '/static': 'http://api:8000',
  },
}
