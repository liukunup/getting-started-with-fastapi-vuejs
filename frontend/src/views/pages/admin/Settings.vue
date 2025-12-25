<script setup>
import { ref, onMounted, watch } from 'vue';
import { useToast } from 'primevue/usetoast';
import { SettingsService, UtilService } from '@/client';

const toast = useToast();
const settings = ref({});

watch(() => settings.value.SMTP_TLS, (newVal) => {
    if (newVal) {
        settings.value.SMTP_SSL = false;
    }
});

watch(() => settings.value.SMTP_SSL, (newVal) => {
    if (newVal) {
        settings.value.SMTP_TLS = false;
    }
});
const loading = ref(false);
const loadingGeneral = ref(false);
const loadingSentry = ref(false);
const loadingEmail = ref(false);
const loadingOIDC = ref(false);
const loadingLDAP = ref(false);

const showTestEmailDialog = ref(false);
const testEmailAddress = ref('');
const sendingTestEmail = ref(false);

const getSettings = async () => {
    loading.value = true;
    try {
        const response = await SettingsService.getSettings();
        settings.value = response;
    } catch (error) {
        toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to load settings', life: 3000 });
    } finally {
        loading.value = false;
    }
};

const saveGeneral = async () => {
    loadingGeneral.value = true;
    try {
        await SettingsService.updateSettings({
            requestBody: {
                PROJECT_NAME: settings.value.PROJECT_NAME
            }
        });
        toast.add({ severity: 'success', summary: 'Success', detail: 'General settings updated', life: 3000 });
    } catch (error) {
        toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to update general settings', life: 3000 });
    } finally {
        loadingGeneral.value = false;
    }
};

const saveSentry = async () => {
    loadingSentry.value = true;
    try {
        await SettingsService.updateSettings({
            requestBody: {
                SENTRY_DSN: settings.value.SENTRY_DSN
            }
        });
        toast.add({ severity: 'success', summary: 'Success', detail: 'Sentry settings updated', life: 3000 });
    } catch (error) {
        toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to update sentry settings', life: 3000 });
    } finally {
        loadingSentry.value = false;
    }
};

const saveEmail = async () => {
    loadingEmail.value = true;
    try {
        const payload = {
            SMTP_HOST: settings.value.SMTP_HOST,
            SMTP_PORT: settings.value.SMTP_PORT,
            SMTP_USER: settings.value.SMTP_USER,
            EMAILS_FROM_EMAIL: settings.value.EMAILS_FROM_EMAIL,
            EMAILS_FROM_NAME: settings.value.EMAILS_FROM_NAME,
            SMTP_TLS: settings.value.SMTP_TLS,
            SMTP_SSL: settings.value.SMTP_SSL
        };

        if (settings.value.SMTP_PASSWORD) {
            payload.SMTP_PASSWORD = settings.value.SMTP_PASSWORD;
        }

        await SettingsService.updateSettings({ requestBody: payload });
        toast.add({ severity: 'success', summary: 'Success', detail: 'Email settings updated', life: 3000 });
    } catch (error) {
        toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to update email settings', life: 3000 });
    } finally {
        loadingEmail.value = false;
    }
};

const saveOIDC = async () => {
    loadingOIDC.value = true;
    try {
        const payload = {
            OIDC_ENABLED: settings.value.OIDC_ENABLED,
            OIDC_NAME: settings.value.OIDC_NAME,
            OIDC_AUTH_URL: settings.value.OIDC_AUTH_URL,
            OIDC_TOKEN_URL: settings.value.OIDC_TOKEN_URL,
            OIDC_USERINFO_URL: settings.value.OIDC_USERINFO_URL,
            OIDC_CLIENT_ID: settings.value.OIDC_CLIENT_ID,
            OIDC_SCOPES: settings.value.OIDC_SCOPES,
            SIGNOUT_REDIRECT_URL: settings.value.SIGNOUT_REDIRECT_URL,
            AUTO_LOGIN: settings.value.AUTO_LOGIN
        };

        if (settings.value.OIDC_CLIENT_SECRET) {
            payload.OIDC_CLIENT_SECRET = settings.value.OIDC_CLIENT_SECRET;
        }

        await SettingsService.updateSettings({ requestBody: payload });
        toast.add({ severity: 'success', summary: 'Success', detail: 'OIDC settings updated', life: 3000 });
    } catch (error) {
        toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to update OIDC settings', life: 3000 });
    } finally {
        loadingOIDC.value = false;
    }
};

const saveLDAP = async () => {
    loadingLDAP.value = true;
    try {
        const payload = {
            LDAP_ENABLED: settings.value.LDAP_ENABLED,
            LDAP_HOST: settings.value.LDAP_HOST,
            LDAP_PORT: settings.value.LDAP_PORT,
            LDAP_BIND_DN: settings.value.LDAP_BIND_DN,
            LDAP_BASE_DN: settings.value.LDAP_BASE_DN,
            LDAP_USER_FILTER: settings.value.LDAP_USER_FILTER,
            LDAP_EMAIL_ATTRIBUTE: settings.value.LDAP_EMAIL_ATTRIBUTE,
            LDAP_NAME_ATTRIBUTE: settings.value.LDAP_NAME_ATTRIBUTE
        };

        if (settings.value.LDAP_BIND_PASSWORD) {
            payload.LDAP_BIND_PASSWORD = settings.value.LDAP_BIND_PASSWORD;
        }

        await SettingsService.updateSettings({ requestBody: payload });
        toast.add({ severity: 'success', summary: 'Success', detail: 'LDAP settings updated', life: 3000 });
    } catch (error) {
        toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to update LDAP settings', life: 3000 });
    } finally {
        loadingLDAP.value = false;
    }
};

const openTestEmailDialog = () => {
    testEmailAddress.value = settings.value.EMAILS_FROM_EMAIL || '';
    showTestEmailDialog.value = true;
};

const sendTestEmail = async () => {
    if (!testEmailAddress.value) {
        toast.add({ severity: 'warn', summary: 'Warning', detail: 'Please enter an email address', life: 3000 });
        return;
    }

    sendingTestEmail.value = true;
    try {
        await UtilService.testEmail({ emailTo: testEmailAddress.value });
        toast.add({ severity: 'success', summary: 'Success', detail: 'Test email sent successfully', life: 3000 });
        showTestEmailDialog.value = false;
    } catch (error) {
        toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to send test email', life: 3000 });
    } finally {
        sendingTestEmail.value = false;
    }
};

onMounted(() => {
    getSettings();
});
</script>

<template>
    <div v-if="loading && !settings.PROJECT_NAME" class="card p-4">Loading...</div>
    <div v-else class="flex flex-col gap-4">
        <!-- General Settings -->
        <div class="card">
            <div class="flex justify-between items-center mb-4">
                <div class="font-semibold text-xl">General</div>
                <Button label="Save" icon="pi pi-save" @click="saveGeneral" :loading="loadingGeneral" size="small" />
            </div>
            <div class="field">
                <label for="project_name" class="block font-medium mb-2">Project Name</label>
                <InputText id="project_name" v-model="settings.PROJECT_NAME" class="w-full" />
            </div>
        </div>

        <!-- Sentry Settings -->
        <div class="card">
            <div class="flex justify-between items-center mb-4">
                <div class="font-semibold text-xl">Sentry</div>
                <Button label="Save" icon="pi pi-save" @click="saveSentry" :loading="loadingSentry" size="small" />
            </div>
            <div class="field">
                <label for="sentry_dsn" class="block font-medium mb-2">Sentry DSN</label>
                <InputText id="sentry_dsn" v-model="settings.SENTRY_DSN" class="w-full" />
            </div>
        </div>

        <!-- Email Settings -->
        <div class="card">
            <div class="flex justify-between items-center mb-4">
                <div class="font-semibold text-xl">Email</div>
                <div class="flex gap-2">
                    <Button label="Test Email" icon="pi pi-envelope" @click="openTestEmailDialog" severity="secondary" size="small" />
                    <Button label="Save" icon="pi pi-save" @click="saveEmail" :loading="loadingEmail" size="small" />
                </div>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div class="field">
                    <label for="smtp_host" class="block font-medium mb-2">Host</label>
                    <InputText id="smtp_host" v-model="settings.SMTP_HOST" class="w-full" />
                </div>
                <div class="field">
                    <label for="smtp_user" class="block font-medium mb-2">User</label>
                    <InputText id="smtp_user" v-model="settings.SMTP_USER" class="w-full" />
                </div>
                <div class="field">
                    <label for="smtp_port" class="block font-medium mb-2">Port</label>
                    <InputNumber id="smtp_port" v-model="settings.SMTP_PORT" class="w-full" :useGrouping="false" />
                </div>
                <div class="field">
                    <label for="smtp_password" class="block font-medium mb-2">Password</label>
                    <InputText id="smtp_password" v-model="settings.SMTP_PASSWORD" type="password" class="w-full" placeholder="Leave empty to keep unchanged" />
                </div>
                <div class="field">
                    <label for="emails_from_email" class="block font-medium mb-2">From Email</label>
                    <InputText id="emails_from_email" v-model="settings.EMAILS_FROM_EMAIL" class="w-full" />
                </div>
                <div class="field">
                    <label for="emails_from_name" class="block font-medium mb-2">From Name</label>
                    <InputText id="emails_from_name" v-model="settings.EMAILS_FROM_NAME" class="w-full" />
                </div>
            </div>

            <div class="flex gap-4 mt-4">
                <div class="field-checkbox flex align-items-center">
                    <Checkbox inputId="smtp_tls" v-model="settings.SMTP_TLS" :binary="true" />
                    <label for="smtp_tls" class="ml-2">TLS</label>
                </div>
                <div class="field-checkbox flex align-items-center">
                    <Checkbox inputId="smtp_ssl" v-model="settings.SMTP_SSL" :binary="true" />
                    <label for="smtp_ssl" class="ml-2">SSL</label>
                </div>
            </div>
        </div>

        <!-- OIDC Settings -->
        <div class="card">
            <div class="flex justify-between items-center mb-4">
                <div class="font-semibold text-xl">OIDC</div>
                <div class="flex gap-2 items-center">
                    <div class="flex align-items-center">
                        <ToggleSwitch inputId="oidc_auto_login" v-model="settings.AUTO_LOGIN" />
                        <label for="oidc_auto_login" class="ml-2">Auto Login</label>
                    </div>
                    <div class="flex align-items-center ml-4">
                        <ToggleSwitch inputId="oidc_enabled" v-model="settings.OIDC_ENABLED" />
                        <label for="oidc_enabled" class="ml-2">Enable OIDC</label>
                    </div>
                    <Button label="Save" icon="pi pi-save" @click="saveOIDC" :loading="loadingOIDC" size="small" class="ml-4" />
                </div>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div class="field">
                    <label for="oidc_name" class="block font-medium mb-2">Provider Name</label>
                    <InputText id="oidc_name" v-model="settings.OIDC_NAME" class="w-full" placeholder="e.g. Google, Auth0" />
                </div>
                <div class="field">
                    <label for="oidc_client_id" class="block font-medium mb-2">Client ID</label>
                    <InputText id="oidc_client_id" v-model="settings.OIDC_CLIENT_ID" class="w-full" />
                </div>
                <div class="field">
                    <label for="oidc_scopes" class="block font-medium mb-2">Scopes</label>
                    <InputText id="oidc_scopes" v-model="settings.OIDC_SCOPES" class="w-full" placeholder="openid profile email" />
                </div>
                <div class="field">
                    <label for="oidc_client_secret" class="block font-medium mb-2">Client Secret</label>
                    <InputText id="oidc_client_secret" v-model="settings.OIDC_CLIENT_SECRET" type="password" class="w-full" placeholder="Leave empty to keep unchanged" />
                </div>
                <div class="field col-span-2">
                    <label for="oidc_auth_url" class="block font-medium mb-2">Authorization URL</label>
                    <InputText id="oidc_auth_url" v-model="settings.OIDC_AUTH_URL" class="w-full" />
                </div>
                <div class="field col-span-2">
                    <label for="oidc_token_url" class="block font-medium mb-2">Token URL</label>
                    <InputText id="oidc_token_url" v-model="settings.OIDC_TOKEN_URL" class="w-full" />
                </div>
                <div class="field col-span-2">
                    <label for="oidc_userinfo_url" class="block font-medium mb-2">UserInfo URL</label>
                    <InputText id="oidc_userinfo_url" v-model="settings.OIDC_USERINFO_URL" class="w-full" />
                </div>
                <div class="field col-span-2">
                    <label for="oidc_signout_redirect_url" class="block font-medium mb-2">Signout Redirect URL</label>
                    <InputText id="oidc_signout_redirect_url" v-model="settings.SIGNOUT_REDIRECT_URL" class="w-full" />
                </div>
            </div>
        </div>

        <!-- LDAP Settings -->
        <div class="card">
            <div class="flex justify-between items-center mb-4">
                <div class="font-semibold text-xl">LDAP</div>
                <div class="flex gap-2 items-center">
                    <div class="flex align-items-center">
                        <ToggleSwitch inputId="ldap_enabled" v-model="settings.LDAP_ENABLED" />
                        <label for="ldap_enabled" class="ml-2">Enable LDAP</label>
                    </div>
                    <Button label="Save" icon="pi pi-save" @click="saveLDAP" :loading="loadingLDAP" size="small" class="ml-4" />
                </div>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div class="field">
                    <label for="ldap_server" class="block font-medium mb-2">Server</label>
                    <InputText id="ldap_server" v-model="settings.LDAP_HOST" class="w-full" />
                </div>
                <div class="field">
                    <label for="ldap_bind_dn" class="block font-medium mb-2">Bind DN</label>
                    <InputText id="ldap_bind_dn" v-model="settings.LDAP_BIND_DN" class="w-full" />
                </div>
                <div class="field">
                    <label for="ldap_port" class="block font-medium mb-2">Port</label>
                    <InputNumber id="ldap_port" v-model="settings.LDAP_PORT" class="w-full" :useGrouping="false" />
                </div>
                <div class="field">
                    <label for="ldap_bind_password" class="block font-medium mb-2">Bind Password</label>
                    <InputText id="ldap_bind_password" v-model="settings.LDAP_BIND_PASSWORD" type="password" class="w-full" placeholder="Leave empty to keep unchanged" />
                </div>
                <div class="field">
                    <label for="ldap_base_dn" class="block font-medium mb-2">Base DN</label>
                    <InputText id="ldap_base_dn" v-model="settings.LDAP_BASE_DN" class="w-full" />
                </div>
                <div class="field">
                    <label for="ldap_user_filter" class="block font-medium mb-2">User Filter</label>
                    <InputText id="ldap_user_filter" v-model="settings.LDAP_USER_FILTER" class="w-full" />
                </div>
                <div class="field">
                    <label for="ldap_email_attr" class="block font-medium mb-2">Email Attribute</label>
                    <InputText id="ldap_email_attr" v-model="settings.LDAP_EMAIL_ATTRIBUTE" class="w-full" />
                </div>
                <div class="field">
                    <label for="ldap_username_attr" class="block font-medium mb-2">Username Attribute</label>
                    <InputText id="ldap_username_attr" v-model="settings.LDAP_USERNAME_ATTRIBUTE" class="w-full" />
                </div>
                <div class="field">
                    <label for="ldap_fullname_attr" class="block font-medium mb-2">Fullname Attribute</label>
                    <InputText id="ldap_fullname_attr" v-model="settings.LDAP_FULLNAME_ATTRIBUTE" class="w-full" />
                </div>
            </div>
        </div>
    </div>

    <Dialog v-model:visible="showTestEmailDialog" header="Send Test Email" :modal="true" class="p-fluid" :style="{ width: '450px' }">
        <div class="field">
            <label for="test_email">Recipient Email</label>
            <InputText id="test_email" v-model="testEmailAddress" required="true" autofocus />
            <small class="p-error" v-if="!testEmailAddress">Email is required.</small>
        </div>
        <template #footer>
            <Button label="Cancel" icon="pi pi-times" text @click="showTestEmailDialog = false" />
            <Button label="Send" icon="pi pi-check" text @click="sendTestEmail" :loading="sendingTestEmail" />
        </template>
    </Dialog>
</template>
