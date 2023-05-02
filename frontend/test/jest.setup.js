import path from 'path'
import Vue from 'vue'
import Vuex from 'vuex';
import Vuetify from 'vuetify';

jest.useFakeTimers();

const loadComponents = [
  'Btn/Delete.vue',
  'Btn/Confirm.vue',
  'S/Tooltip.vue',
  'S/Btn.vue',
  'S/Dialog.vue',
  'SavingLoaderSpinner.vue',
];

const componentBasePath = path.join(__dirname, '../components/');
loadComponents.forEach((componentPath) => {
  const file = path.join(componentBasePath, componentPath);
  const name = path.relative(componentBasePath, file).replaceAll('/', '').slice(0, -4);
  Vue.component(name, require(file).default);
})

Vue.use(Vuetify);
Vue.use(Vuex);
Vue.use({
  install(Vue, options) {
    Vue.prototype.$axios = {
      post: jest.fn(() => Promise.resolve({ status: 201, data: {} })),
      $post: jest.fn(() => Promise.resolve({})),
    };
  }
});
Vue.use({
  install(Vue, options) {
    Vue.prototype.$auth = {
      isLoggedIn: true,
      user: {
        id: 'user',
        username: 'user',
        name: 'user',
      }
    }
  }
});
Vue.use({
  install(Vue, options) {
    Vue.prototype.$toast = {
      global: {
        requestError: jest.fn(),
      }
    }
  }
})
global.Vue = Vue;
