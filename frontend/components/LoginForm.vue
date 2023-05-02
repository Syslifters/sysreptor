<template>
  <s-card>
    <v-toolbar dark class="login-header" flat tile>
      <v-toolbar-title><slot name="title">Login</slot></v-toolbar-title>
    </v-toolbar>

    <template v-if="step === 'username'">
      <v-form ref="form" @submit.prevent="loginUsername">
        <v-card-text>
          <v-text-field
            v-model="formUsername.username"
            type="text"
            name="username"
            label="Username"
            prepend-icon="mdi-account"
            spellcheck="false"
            autocomplete="off"
            :autofocus="!username"
            :disabled="Boolean(username)"
            required
          />
          <v-text-field
            v-model="formUsername.password"
            type="password"
            name="password"
            label="Password"
            prepend-icon="mdi-lock"
            :autofocus="Boolean(username)"
            required
          />

          <slot name="message" />
          <p v-if="errorMessage" class="red--text">
            {{ errorMessage }}
          </p>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <slot name="actions"></slot>
          <s-btn type="submit" color="primary">
            Login
          </s-btn>
        </v-card-actions>
      </v-form>
    </template>

    <template v-else-if="step === 'mfa'">
      <v-form ref="form" @submit.prevent="loginCode">
        <v-card-text :set="methodTypeInfo = mfaMethodChoices.find(c => c.value === currentMfaMethod.method_type)">
          <v-card-title>
            <v-icon class="mr-3">{{ methodTypeInfo.icon }}</v-icon>
            {{ currentMfaMethod.name }}
          </v-card-title>

          <template v-if="currentMfaMethod.method_type === 'fido2'">
            <p>Use your security key to log in.</p>
          </template>
          <template v-else-if="currentMfaMethod.method_type === 'totp'">
            <v-otp-input
              v-model="formCode.code"
              type="number"
              length="6"
              @finish="loginCode"
              spellcheck="false"
              autocomplete="off"
              autofocus
              required
            />
          </template>
          <template v-else-if="currentMfaMethod.method_type === 'backup'">
            <v-otp-input
              v-model="formCode.code"
              type="text"
              length="12"
              @finish="loginCode"
              spellcheck="false"
              autocomplete="off"
              autofocus
              required
            />
          </template>

          <slot name="message" />
          <p v-if="errorMessage" class="red--text">
            {{ errorMessage }}
          </p>
        </v-card-text>

        <v-card-actions>
          <v-spacer />
          <s-btn v-if="mfaMethods.length > 1" @click="step = 'mfa-select'" color="secondary">
            Try another MFA method
          </s-btn>
          <s-btn v-if="['totp', 'backup'].includes(currentMfaMethod.method_type)" type="submit" color="primary">Login</s-btn>
          <s-btn v-else-if="currentMfaMethod.method_type === 'fido2'" @click="beginMfaLogin(currentMfaMethod)" color="primary">Try again</s-btn>
        </v-card-actions>
      </v-form>
    </template>

    <template v-else-if="step === 'mfa-select'">
      <v-card-text>
        <h2>Choose MFA method</h2>

        <v-list>
          <v-list-item v-for="mfaMethod in mfaMethods" :key="mfaMethod.id" link @click="beginMfaLogin(mfaMethod)">
            <v-list-item-title>
              <v-icon class="mr-3">{{ mfaMethodChoices.find(c => c.value === mfaMethod.method_type).icon }}</v-icon>
              {{ mfaMethod.name }}
            </v-list-item-title>
          </v-list-item>
        </v-list>
      </v-card-text>
    </template>
  </s-card>
</template>

<script>
import { get as navigatorCredentialsGet, parseRequestOptionsFromJSON } from "@github/webauthn-json/browser-ponyfill";
import { mfaMethodChoices } from '~/utils/other';

export default {
  props: {
    username: {
      type: String,
      default: null
    },
  },
  data() {
    return {
      step: 'username',
      actionInProgress: false,
      errorMessage: null,
      formUsername: {
        username: this.username || '',
        password: '',
      },
      mfaMethods: [],
      currentMfaMethod: null,
      formCode: {
        code: '',
      },
    };
  },
  computed: {
    mfaMethodChoices() {
      return mfaMethodChoices;
    },
  },
  methods: {
    async loginStep(fn) {
      if (this.actionInProgress) {
        return;
      }

      try {
        this.actionInProgress = true;
        this.errorMessage = null;
        
        const res = await fn();
        if (!res) {
          return;
        }

        if (res.status === 'success') {
          // trigger login in nuxt-auth
          await this.$auth.fetchUser();
          this.$emit('login', res);
        } else if (res.status === 'mfa-required') {
          this.mfaMethods = res.mfa;
          this.beginMfaLogin(res.mfa.find(m => m.is_primary) || res.mfa[0])
        }
      } catch (error) {
        if (error?.response?.data?.detail) {
          this.errorMessage = error.response.data.detail;
        } else if (error?.response?.data?.non_field_errors) {
          this.errorMessage = error.response.data.non_field_errors[0];
        } else if (error instanceof DOMException) {
          this.errorMessage = error.message;
        } else {
          this.$toast.global.requestError({ error, message: 'Login failed' });
        }
      } finally {
        this.actionInProgress = false;
      }
    },
    async loginUsername() {
      await this.loginStep(async () => {
        if (!this.formUsername.username || !this.formUsername.password) {
          this.errorMessage = 'Username and password are required';
          return null;
        }
        return await this.$axios.$post('/auth/login/', this.formUsername);
      })
    },
    beginMfaLogin(mfaMethod) {
      this.currentMfaMethod = mfaMethod;
      this.step = 'mfa';
      this.errorMessage = null;
      this.formCode = { code: '' };

      if (this.currentMfaMethod.method_type === 'fido2') {
        this.$nextTick(async () => {
          await this.loginStep(async () => {
            const options = await this.$axios.$post('/auth/login/fido2/begin/', {});
            const fido2Response = await navigatorCredentialsGet(parseRequestOptionsFromJSON(options));
            return await this.$axios.$post('/auth/login/fido2/complete/', fido2Response);
          });
        });
      }
    },
    async loginCode() {
      await this.loginStep(async () => {
        return await this.$axios.$post('/auth/login/code/', {
          id: this.currentMfaMethod.id,
          code: this.formCode.code,
        });
      });
    },
  },
};
</script>
