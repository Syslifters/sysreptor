<template>
  <s-card class="mt-4">
    <v-card-title>Archiving Public Keys</v-card-title>
    <v-card-text>
      <v-list>
        <v-list-item v-for="publicKey in publicKeys" :key="publicKey.id">
          <v-list-item-title>
            {{ publicKey.name }}
            <template v-if="!publicKey.enabled">
              <v-chip small class="ml-3">Disabled</v-chip>
            </template>
          </v-list-item-title>
          <v-list-item-action>
            <s-dialog v-model="editWizard.visible">
              <template #activator="{ on, attrs }">
                <v-btn @click="openEditWizard(publicKey)" icon v-bind="attrs" v-on="on">
                  <v-icon>mdi-pencil</v-icon>
                </v-btn>
              </template>
              <template #title>Edit Public Key</template>
              <template #default>
                <v-card-text>
                  <s-text-field
                    v-model="editWizard.form.name"
                    label="Name"
                  />
                  <s-checkbox
                    v-model="editWizard.form.enabled"
                    label="Enabled"
                    hint="If disabled, this key cannot be used to encrypt archives. But it can still be used to decrypt existing archives."
                  />

                  <h4 class="text-subtitle-1 mt-4">Public Key</h4>
                  <div v-if="encryptionKeyInfo = Object.values(editWizard.publicKey.public_key_info.subkey_info).find(sk => sk.cap === 'e')">
                    <v-chip small v-if="['1', '2'].includes(encryptionKeyInfo.algo)">RSA {{ encryptionKeyInfo.length }} bit</v-chip>
                    <v-chip small v-else-if="encryptionKeyInfo.algo === '16'">ElGamal {{ encryptionKeyInfo.length }} bit</v-chip>
                    <v-chip small v-else-if="encryptionKeyInfo.algo === '18'">ECDH {{ encryptionKeyInfo.curve }}</v-chip>
                  </div>
                  <v-textarea
                    v-model="editWizard.publicKey.public_key"
                    readonly
                    auto-grow
                    spellcheck="false"
                    class="textarea-codeblock pt-0"
                  />
                </v-card-text>
                <v-card-actions>
                  <s-btn @click="editWizardSave" :loading="actionInProgress" color="primary">
                    Save
                  </s-btn>
                </v-card-actions>
              </template>
            </s-dialog>
          </v-list-item-action>
          <v-list-item-action>
            <btn-delete icon :delete="() => deletePublicKey(publicKey)" />
          </v-list-item-action>
        </v-list-item>
        <v-list-item v-if="publicKeys.length === 0">
          <v-list-item-title>No archiving public keys configured</v-list-item-title>
        </v-list-item>

        <v-list-item>
          <s-dialog v-model="setupWizard.visible">
            <template #activator="{ on, attrs }">
              <s-btn color="secondary" @click="openSetupWizard" v-bind="attrs" v-on="on">
                <v-icon>mdi-plus</v-icon>
                Add
              </s-btn>
            </template>
            <template #title>Setup Public Key</template>

            <template #default>
              <template v-if="setupWizard.step === 'create'">
                <v-card-text>
                  <p>
                    To encrypt archives, you need to create a OpenPGP public key for encryption. You can use an existing key or create a new one.<br>
                    You can also generate the key on a YubiKey to use hardware encryption.
                  </p>

                  <v-tabs grow height="2.5em" class="mb-4">
                    <v-tab>Generate key</v-tab>
                    <v-tab-item>
                      <p>
                        Use the following command to generate a new Elliptic Curve key pair. <br>
                        Pro-Tip: You can also use <code>gpg --full-generate-key</code> to customize ciphers and other configs.
                      </p>
                      <code class="code-snippet">
                        cat &lt;&lt; EOF &gt; config.txt<br>
                        Key-Type: ECDSA<br>
                        Key-Curve: nistp521<br>
                        Subkey-Type: ECDH<br>
                        Subkey-Curve: nistp521<br>
                        Expire-Date: 0<br>
                        Name-Comment: SysReptor Archiving<br>
                        Name-Real: {{ $auth.user.name || $auth.user.username }}<br>
                        <template v-if="$auth.user.email">Name-Email: {{ $auth.user.email }}<br></template>
                        EOF<br>
                        gpg --batch --generate-key config.txt<br>
                        <br>
                        gpg --list-secret-keys --keyid-format=long<br>
                        gpg --armor --export &lt;key-id&gt;<br>
                      </code>
                    </v-tab-item>

                    <v-tab>Generate hardware key (YubiKey 5)</v-tab>
                    <v-tab-item>
                      <p>
                        Use the following command to generate a new Elliptic Curve key pair on a YubiKey 5.<br>
                        The private key is generated on the YubiKey and never leaves the device.<br>
                        Beware that you cannot backup the key. We recommend that you add a second key as a fallback in case you lose your YubiKey.
                      </p>

                      <code class="code-snippet">
                        gpg --card-edit<br>
                        <br>
                        Reader ...........: Yubico YubiKey FIDO CCID 00 00<br>
                        Application ID ...: XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX<br>
                        Application type .: OpenPGP<br>
                        Version ..........: 3.4<br>
                        Manufacturer .....: Yubico<br>
                        Serial number ....: 19763721<br>
                        Name of cardholder: [not set]<br>
                        Language prefs ...: [not set]<br>
                        Salutation .......:<br>
                        URL of public key : [not set]<br>
                        Login data .......: [not set]<br>
                        Signature PIN ....: not forced<br>
                        Key attributes ...: rsa2048 rsa2048 rsa2048<br>
                        Max. PIN lengths .: 127 127 127<br>
                        PIN retry counter : 3 0 3<br>
                        Signature counter : 0<br>
                        KDF setting ......: off<br>
                        UIF setting ......: Sign=off Decrypt=off Auth=off<br>
                        Signature key ....: [none]<br>
                        Encryption key....: [none]<br>
                        Authentication key: [none]<br>
                        General key info..: [none]<br>
                        <br>
                        gpg/card&gt; admin<br>
                        Admin commands are allowed<br>
                        <br>
                        # Change Yubikey Pin (optional)<br>
                        # Hint: default pin is 123456, default admin pin is 12345678<br>
                        gpg/card&gt; passwd<br>
                        gpg: OpenPGP card no. XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX detected<br>
                        <br>
                        1 - change PIN<br>
                        2 - unblock PIN<br>
                        3 - change Admin PIN<br>
                        4 - set the Reset Code<br>
                        Q - quit<br>
                        <br>
                        Your selection? 3<br>
                        PIN changed.<br>
                        <br>
                        1 - change PIN<br>
                        2 - unblock PIN<br>
                        3 - change Admin PIN<br>
                        4 - set the Reset Code<br>
                        Q - quit<br>
                        <br>
                        Your selection? 1<br>
                        PIN changed.<br>
                        <br>
                        1 - change PIN<br>
                        2 - unblock PIN<br>
                        3 - change Admin PIN<br>
                        4 - set the Reset Code<br>
                        Q - quit<br>
                        <br>
                        Your selection? Q<br>
                        <br>
                        gpg/card&gt; name<br>
                        Cardholder's surname: {{ $auth.user.last_name }}<br>
                        Cardholder's given name: {{ $auth.user.first_name }}<br>
                        <br>
                        # Change key type to elliptic curve (optional)<br>
                        gpg/card&gt; key-attr<br>
                        Changing card key attribute for: Signature key<br>
                        Please select what kind of key you want:<br>
                        &nbsp;&nbsp;&nbsp;(1) RSA<br>
                        &nbsp;&nbsp;&nbsp;(2) ECC<br>
                        Your selection? 2<br>
                        Please select which elliptic curve you want:<br>
                        &nbsp;&nbsp;&nbsp;(1) Curve 25519 *default*<br>
                        &nbsp;&nbsp;&nbsp;(4) NIST P-384<br>
                        Your selection? 1<br>
                        The card will now be re-configured to generate a key of type: ed25519<br>
                        Note: There is no guarantee that the card supports the requested<br>
                        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;key type or size.  If the key generation does not succeed,<br>
                        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;please check the documentation of your card to see which<br>
                        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;key types and sizes are supported.<br>
                        Changing card key attribute for: Encryption key<br>
                        Please select what kind of key you want:<br>
                        &nbsp;&nbsp;&nbsp;(1) RSA<br>
                        &nbsp;&nbsp;&nbsp;(2) ECC<br>
                        Your selection? 2<br>
                        Please select which elliptic curve you want:<br>
                        &nbsp;&nbsp;&nbsp;(1) Curve 25519 *default*<br>
                        &nbsp;&nbsp;&nbsp;(4) NIST P-384<br>
                        Your selection? 1<br>
                        The card will now be re-configured to generate a key of type: cv25519<br>
                        Changing card key attribute for: Authentication key<br>
                        Please select what kind of key you want:<br>
                        &nbsp;&nbsp;&nbsp;(1) RSA<br>
                        &nbsp;&nbsp;&nbsp;(2) ECC<br>
                        Your selection? 2<br>
                        Please select which elliptic curve you want:<br>
                        &nbsp;&nbsp;&nbsp;(1) Curve 25519 *default*<br>
                        &nbsp;&nbsp;&nbsp;(4) NIST P-384<br>
                        Your selection? 1<br>
                        The card will now be re-configured to generate a key of type: ed25519<br>
                        <br>
                        # Generate key pair<br>
                        gpg/card&gt; generate<br>
                        Make off-card backup of encryption key? (Y/n) n<br>
                        Please specify how long the key should be valid.<br>
                        0 = key does not expire<br>
                        &nbsp;&nbsp;&nbsp;&nbsp;&lt;n&gt;  = key expires in n days<br>
                        &nbsp;&nbsp;&nbsp;&lt;n&gt;w = key expires in n weeks<br>
                        &nbsp;&nbsp;&nbsp;&lt;n&gt;m = key expires in n months<br>
                        &nbsp;&nbsp;&nbsp;&lt;n&gt;y = key expires in n years<br>
                        Key is valid for? (0) 0<br>
                        Key does not expire at all<br>
                        Is this correct? (y/N) y<br>
                        <br>
                        GnuPG needs to construct a user ID to identify your key.<br>
                        <br>
                        Real name: {{ $auth.user.name || $auth.user.username }}<br>
                        Email address: {{ $auth.user.email }}<br>
                        Comment: SysReptor Archiving Key<br>
                        You selected this USER-ID:<br>
                        "{{ $auth.user.name || $auth.user.username }} (SysReptor Archiving Key) <template v-if="$auth.user.email">&lt;{{ $auth.user.email }}&gt;</template>"<br>
                        <br>
                        Change (N)ame, (C)omment, (E)mail or (O)kay/(Q)uit? O<br>
                        public and secret key created and signed.<br>
                        <br>
                        gpg/card&gt; quit<br>
                        <br>
                        gpg --list-secret-keys --keyid-format=long<br>
                        gpg --armor --export &lt;key-id&gt;<br>
                      </code>
                    </v-tab-item>
                  </v-tabs>

                  <v-textarea
                    v-model="setupWizard.form.public_key"
                    label="Public Key"
                    hint="OpenPGP public key for encryption. It does not has to be publicly trusted and can be a key only used for archiving."
                    persistent-hint
                    :error-messages="error"
                    spellcheck="false"
                    class="textarea-codeblock"
                  />
                </v-card-text>
                <v-card-actions>
                  <v-spacer />
                  <s-btn 
                    @click="setupWizardRegisterBegin" 
                    :disabled="!setupWizard.form.public_key"
                    :loading="actionInProgress" 
                    color="primary"
                  >
                    Next
                  </s-btn>
                </v-card-actions>
              </template>

              <template v-else-if="setupWizard.step === 'verify'">
                <v-card-text>
                  <p>
                    Please decrypt the following message with your private key to verify that you own it.<br>
                    Copy the decrypted verification code below.
                  </p>
                  <p class="mb-0"><code>gpg --decrypt message.txt</code></p>
                  <v-textarea
                    v-model="setupWizard.data.verification"
                    readonly
                    auto-grow
                    spellcheck="false"
                    class="textarea-codeblock"
                  />

                  <s-text-field
                    v-model="setupWizard.form.verification"
                    label="Verification"
                    :error-messages="error"
                  />
                </v-card-text>
                <v-card-actions>
                  <v-spacer />
                  <s-btn 
                    @click="setupWizardRegisterComplete" 
                    :disabled="!setupWizard.form.verification"
                    :loading="actionInProgress" 
                    color="primary"
                  >
                    Activate
                  </s-btn>
                </v-card-actions>
              </template>
              <template v-else-if="setupWizard.step === 'set-name'">
                <v-card-text>
                  <p>
                    Set a name for the new public key to identify it later.
                  </p>

                  <s-text-field
                    v-model="setupWizard.form.name"
                    label="Name"
                  />
                </v-card-text>
                <v-card-actions>
                  <v-spacer />
                  <s-btn @click="setupWizardSetName" :loading="actionInProgress" color="primary">
                    Save
                  </s-btn>
                </v-card-actions>
              </template>
            </template>
          </s-dialog>
        </v-list-item>
      </v-list>
    </v-card-text>
  </s-card>
</template>

<script>
import { pick } from 'lodash';

export default {
  async asyncData({ $axios }) {
    return { 
      publicKeys: await $axios.$get('/pentestusers/self/publickeys/')
    };
  },
  data() {
    return {
      setupWizard: {
        visible: false,
        form: null,
      },
      editWizard: {
        visible: false,
        form: null,
        publicKey: null,
      },
      error: null,
      actionInProgress: false,
    };
  },
  methods: {
    async requestWrapper(fn) {
      if (this.actionInProgress) {
        return false;
      }

      try {
        this.actionInProgress = true;
        await fn();
        this.error = null;
      } catch (error) {
        if (error?.response?.status === 400 && error?.response?.data) {
          this.error = error.response.data;
        }
        this.$toast.global.requestError({ error });
      } finally {
        this.actionInProgress = false;
      }
    },
    openSetupWizard() {
      this.error = null;
      this.setupWizard = {
        visible: true,
        step: 'create',
        form: {
          public_key: '',
          name: 'Archiving Public Key',
        },
        data: null,
      };
    },
    async setupWizardRegisterBegin() {
      await this.requestWrapper(async () => {
        this.setupWizard.data = await this.$axios.$post('/pentestusers/self/publickeys/register/begin/', this.setupWizard.form);
        this.setupWizard.form = {
          verification: '',
        };
        this.setupWizard.step = 'verify';
      });
    },
    async setupWizardRegisterComplete() {
      await this.requestWrapper(async () => {
        this.setupWizard.data = await this.$axios.$post('/pentestusers/self/publickeys/register/complete/', this.setupWizard.form);
        this.setupWizard.form = {
          name: this.setupWizard.data.public_key_info.uids?.[0] || '',
        };
        this.setupWizard.step = 'set-name';
      });
    },
    async setupWizardSetName() {
      await this.requestWrapper(async () => {
        const obj = await this.$axios.$patch(`/pentestusers/self/publickeys/${this.setupWizard.data.id}/`, this.setupWizard.form);
        this.publicKeys.push(obj);
        this.setupWizard.visible = false;
        this.$toast.success('Archiving Public Key setup completed');
      });
    },
    openEditWizard(publicKey) {
      this.error = null;
      this.editWizard = {
        visible: true,
        form: pick(publicKey, ['id', 'name', 'enabled']),
        publicKey,
      };
    },
    async editWizardSave() {
      await this.requestWrapper(async () => {
        const publicKey = await this.$axios.$patch(`/pentestusers/self/publickeys/${this.editWizard.form.id}/`, this.editWizard.form);
        this.publicKeys = this.publicKeys.map(pk => pk.id === publicKey.id ? publicKey : pk);
        this.editWizard.visible = false;
      });
    },
    async deletePublicKey(publicKey) {
      await this.requestWrapper(async () => {
        await this.$axios.$delete(`/pentestusers/self/publickeys/${publicKey.id}/`);
        this.publicKeys = this.publicKeys.filter(pk => pk.id !== publicKey.id);
      });
    },
  }
}
</script>

<style lang="scss" scoped>
.textarea-codeblock {
  :deep(textarea) {
    font-family: monospace;
    line-height: 1.2em;
    font-size: medium;
    background-color: rgba(0, 0, 0, 0.05);
    padding: 1em;
  }
}

.code-snippet {
  display: block;
}
</style>
