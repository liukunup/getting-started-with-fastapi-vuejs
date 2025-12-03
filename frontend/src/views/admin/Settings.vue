<script setup>
import { ref, onMounted } from 'vue';
import { useToast } from 'primevue/usetoast';
import { SettingsService, UtilService } from '@/client';

const toast = useToast();
const settings = ref({});
const loading = ref(false);
const loadingGeneral = ref(false);
const loadingSentry = ref(false);
const loadingEmail = ref(false);

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
                <div class="font-semibold text-xl">General Settings</div>
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
                <div class="font-semibold text-xl">Sentry Configuration</div>
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
                <div class="font-semibold text-xl">Email Settings</div>
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
                    <label for="smtp_port" class="block font-medium mb-2">Port</label>
                    <InputNumber id="smtp_port" v-model="settings.SMTP_PORT" class="w-full" :useGrouping="false" />
                </div>
                <div class="field">
                    <label for="smtp_user" class="block font-medium mb-2">User</label>
                    <InputText id="smtp_user" v-model="settings.SMTP_USER" class="w-full" />
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
