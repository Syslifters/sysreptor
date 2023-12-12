<template>
  <s-card class="mt-4">
    <v-card-title>Archiving Public Keys</v-card-title>
    <v-card-text>
      <v-list>
        <v-list-item v-for="publicKey in publicKeys" :key="publicKey.id">
          <v-list-item-title>
            {{ publicKey.name }}
            <template v-if="!publicKey.enabled">
              <v-chip size="small" class="ml-3" text="Disabled" />
            </template>
          </v-list-item-title>
          <template #append>
            <s-dialog v-model="editWizard.visible">
              <template #activator="{ props: dialogProps }">
                <v-btn
                  @click="openEditWizard(publicKey)"
                  icon="mdi-pencil"
                  variant="text"
                  v-bind="dialogProps"
                />
              </template>
              <template #title>Edit Public Key</template>
              <template #default>
                <v-card-text>
                  <s-text-field
                    v-model="editWizard.form.name"
                    label="Name"
                    spellcheck="false"
                  />
                  <s-checkbox
                    v-model="editWizard.form.enabled"
                    label="Enabled"
                    hint="If disabled, this key cannot be used to encrypt archives. But it can still be used to decrypt existing archives."
                  />

                  <h4 class="text-subtitle-1 mt-4">Public Key</h4>
                  <div v-if="encryptionKeyInfo" class="mb-1">
                    <v-chip size="small" v-if="['1', '2'].includes(encryptionKeyInfo.algo)">RSA {{ encryptionKeyInfo.length }} bit</v-chip>
                    <v-chip size="small" v-else-if="encryptionKeyInfo.algo === '16'">ElGamal {{ encryptionKeyInfo.length }} bit</v-chip>
                    <v-chip size="small" v-else-if="encryptionKeyInfo.algo === '18'">ECDH {{ encryptionKeyInfo.curve }}</v-chip>
                  </div>
                  <v-textarea
                    v-model="editWizard.publicKey!.public_key"
                    readonly
                    auto-grow
                    spellcheck="false"
                    class="textarea-codeblock pt-0"
                  />
                </v-card-text>
                <v-card-actions>
                  <v-spacer />
                  <s-btn-primary
                    @click="editWizardSave"
                    :loading="actionInProgress"
                    text="Save"
                  />
                </v-card-actions>
              </template>
            </s-dialog>

            <btn-delete button-variant="icon" :delete="() => deletePublicKey(publicKey)" />
          </template>
        </v-list-item>
        <v-list-item
          v-if="publicKeys.length === 0"
          title="No archiving public keys configured"
        />

        <v-list-item>
          <s-dialog v-model="setupWizard.visible">
            <template #activator="{ props: dialogProps }">
              <s-btn-secondary
                @click="openSetupWizard"
                v-bind="dialogProps"
                prepend-icon="mdi-plus"
                text="Add"
              />
            </template>
            <template #title>Setup Public Key</template>

            <template #default>
              <template v-if="setupWizard.step === SetupWizardStep.CREATE">
                <v-card-text>
                  <p>
                    To encrypt archives, you need to create a OpenPGP public key for encryption. You can use an existing key or create a new one.<br>
                    You can also generate the key on a YubiKey to use hardware encryption.
                  </p>

                  <v-tabs v-model="setupWizard.tab" grow height="2.5em" class="mt-4">
                    <v-tab value="software" text="Generate key" />
                    <v-tab value="yubikey" text="Generate hardware key (YubiKey 5)" />
                  </v-tabs>
                  <v-window v-model="setupWizard.tab">
                    <v-window-item value="software">
                      <p>
                        Use the following command to generate a new Elliptic Curve key pair. <br>
                        Pro-Tip: You can also use <s-code>gpg --full-generate-key</s-code> to customize ciphers and other configs.
                      </p>
                      <s-code class="code-snippet">
                        cat &lt;&lt; EOF &gt; config.txt<br>
                        Key-Type: ECDSA<br>
                        Key-Curve: nistp521<br>
                        Subkey-Type: ECDH<br>
                        Subkey-Curve: nistp521<br>
                        Subkey-Usage: encrypt<br>
                        Expire-Date: 0<br>
                        Name-Comment: SysReptor Archiving<br>
                        Name-Real: {{ auth.user.value!.name || auth.user.value!.username }}<br>
                        <template v-if="auth.user.value!.email">Name-Email: {{ auth.user.value!.email }}<br></template>
                        EOF<br>
                        gpg --batch --generate-key config.txt<br>
                        <br>
                        gpg --list-secret-keys --keyid-format=long<br>
                        gpg --armor --export &lt;key-id&gt;<br>
                      </s-code>
                    </v-window-item>
                    <v-window-item value="yubikey">
                      <p>
                        Use the following command to generate a new Elliptic Curve key pair on a YubiKey 5.<br>
                        The private key is generated on the YubiKey and never leaves the device.<br>
                        Beware that you cannot backup the key. We recommend that you add a second key as a fallback in case you lose your YubiKey.
                      </p>

                      <s-code class="code-snippet">
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
                        Cardholder's surname: {{ auth.user.value!.last_name }}<br>
                        Cardholder's given name: {{ auth.user.value!.first_name }}<br>
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
                        Real name: {{ auth.user.value!.name || auth.user.value!.username }}<br>
                        Email address: {{ auth.user.value!.email }}<br>
                        Comment: SysReptor Archiving Key<br>
                        You selected this USER-ID:<br>
                        "{{ auth.user.value!.name || auth.user.value!.username }} (SysReptor Archiving Key) <template v-if="auth.user.value!.email">&lt;{{ auth.user.value!.email }}&gt;</template>"<br>
                        <br>
                        Change (N)ame, (C)omment, (E)mail or (O)kay/(Q)uit? O<br>
                        public and secret key created and signed.<br>
                        <br>
                        gpg/card&gt; quit<br>
                        <br>
                        gpg --list-secret-keys --keyid-format=long<br>
                        gpg --armor --export &lt;key-id&gt;<br>
                      </s-code>
                    </v-window-item>
                  </v-window>

                  <v-textarea
                    v-model="setupWizard.form.public_key"
                    label="Public Key"
                    hint="OpenPGP public key for encryption. It does not has to be publicly trusted and can be a key only used for archiving."
                    persistent-hint
                    :error-messages="error || []"
                    spellcheck="false"
                    class="mt-4 textarea-codeblock"
                  />
                </v-card-text>
                <v-card-actions>
                  <v-spacer />
                  <s-btn-primary
                    @click="setupWizardRegisterBegin"
                    :disabled="!setupWizard.form.public_key"
                    :loading="actionInProgress"
                    text="Next"
                  />
                </v-card-actions>
              </template>

              <template v-else-if="setupWizard.step === SetupWizardStep.VERIFY">
                <v-card-text>
                  <p>
                    Please decrypt the following message with your private key to verify that you own it.<br>
                    Copy the decrypted verification code below.
                  </p>
                  <p class="mb-0"><s-code>gpg --decrypt message.txt</s-code></p>
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
                    :error-messages="error || []"
                    spellcheck="false"
                  />
                </v-card-text>
                <v-card-actions>
                  <v-spacer />
                  <s-btn-primary
                    @click="setupWizardRegisterComplete"
                    :disabled="!setupWizard.form.verification"
                    :loading="actionInProgress"
                    text="Activate"
                  />>
                </v-card-actions>
              </template>
              <template v-else-if="setupWizard.step === SetupWizardStep.SET_NAME">
                <v-card-text>
                  <p>
                    Set a name for the new public key to identify it later.
                  </p>

                  <s-text-field
                    v-model="setupWizard.form.name"
                    label="Name"
                    spellcheck="false"
                  />
                </v-card-text>
                <v-card-actions>
                  <v-spacer />
                  <s-btn-primary
                    @click="setupWizardSetName"
                    :loading="actionInProgress"
                    text="Save"
                  />
                </v-card-actions>
              </template>
            </template>
          </s-dialog>
        </v-list-item>
      </v-list>
    </v-card-text>
  </s-card>
</template>

<script setup lang="ts">
import pick from 'lodash/pick';

const auth = useAuth();

const publicKeys = await useFetchE<UserPublicKey[]>('/api/v1/pentestusers/self/publickeys/', { method: 'GET' });

enum SetupWizardStep {
  CREATE = 'create',
  VERIFY = 'verify',
  SET_NAME = 'set-name',
}

const actionInProgress = ref(false);
const error = ref<any|null>(null);
const setupWizard = ref({
  visible: false,
  step: SetupWizardStep.CREATE,
  tab: 'software',
  form: {} as any,
  data: null as any|null,
});
const editWizard = ref({
  visible: false,
  form: {} as any,
  publicKey: null as UserPublicKey|null,
});
const encryptionKeyInfo = computed<any|null>(() => {
  if (!editWizard.value.publicKey) {
    return null;
  }
  return Object.values(editWizard.value.publicKey.public_key_info.subkey_info).find((sk: any) => sk.cap === 'e');
});

async function requestWrapper(fn: () => Promise<void>) {
  if (actionInProgress.value) {
    return false;
  }

  try {
    actionInProgress.value = true;
    await fn();
    error.value = null;
  } catch (ex: any) {
    if (ex?.status === 400 && ex?.data) {
      error.value = ex.data;
    }
    requestErrorToast({ error: ex });
  } finally {
    actionInProgress.value = false;
  }
}

function openSetupWizard() {
  error.value = null;
  setupWizard.value = {
    visible: true,
    step: SetupWizardStep.CREATE,
    tab: 'software',
    form: {
      public_key: null,
      name: 'Archiving Public Key',
    },
    data: null,
  };
}

async function setupWizardRegisterBegin() {
  await requestWrapper(async () => {
    setupWizard.value.data = await $fetch('/api/v1/pentestusers/self/publickeys/register/begin/', {
      method: 'POST',
      body: setupWizard.value.form,
    });
    setupWizard.value.form = {
      verification: '',
    };
    setupWizard.value.step = SetupWizardStep.VERIFY;
  });
}

async function setupWizardRegisterComplete() {
  await requestWrapper(async () => {
    setupWizard.value.data = await $fetch('/api/v1/pentestusers/self/publickeys/register/complete/', {
      method: 'POST',
      body: setupWizard.value.form,
    });
    setupWizard.value.form = {
      name: setupWizard.value.data!.public_key_info.uids?.[0] || '',
    };
    setupWizard.value.step = SetupWizardStep.SET_NAME;
  });
}

async function setupWizardSetName() {
  await requestWrapper(async () => {
    const obj = await $fetch<UserPublicKey>(`/api/v1/pentestusers/self/publickeys/${setupWizard.value.data.id}/`, {
      method: 'PATCH',
      body: setupWizard.value.form
    });
    publicKeys.value.push(obj);
    setupWizard.value.visible = false;
    successToast('Archiving Public Key setup completed');
  });
}

function openEditWizard(publicKey: UserPublicKey) {
  error.value = null;
  editWizard.value = {
    visible: true,
    form: pick(publicKey, ['id', 'name', 'enabled']),
    publicKey,
  };
}

async function editWizardSave() {
  await requestWrapper(async () => {
    const publicKey = await $fetch<UserPublicKey>(`/api/v1/pentestusers/self/publickeys/${editWizard.value.form.id}/`, {
      method: 'PATCH',
      body: editWizard.value.form,
    });
    publicKeys.value = publicKeys.value.map(pk => pk.id === publicKey.id ? publicKey : pk);
    editWizard.value.visible = false;
  });
}

async function deletePublicKey(publicKey: UserPublicKey) {
  await requestWrapper(async () => {
    await $fetch(`/api/v1/pentestusers/self/publickeys/${publicKey.id}/`, {
      method: 'DELETE'
    });
    publicKeys.value = publicKeys.value.filter(pk => pk.id !== publicKey.id);
  });
}
</script>

<style lang="scss" scoped>
@use "@/assets/vuetify" as vuetify;

.textarea-codeblock {
  :deep(textarea) {
    font-family: monospace;
    line-height: 1.2em;
    font-size: medium;
    background-color: vuetify.$code-background-color;
    color: vuetify.$code-color;
  }
}

.code-snippet {
  display: block;
  padding: 0.5em;
}
</style>
