<script setup>
import { ApplicationService } from '@/service/ApplicationService';
import { FilterMatchMode } from '@primevue/core/api';
import { useToast } from 'primevue/usetoast';
import { onMounted, ref } from 'vue';

const toast = useToast();
const dt = ref();
const applications = ref(null);
const applicationDialog = ref(false);
const appKeyDialog = ref(false);
const newAppKey = ref('');
const deleteApplicationDialog = ref(false);
const deleteApplicationsDialog = ref(false);
const application = ref({});
const selectedApplications = ref();
const filters = ref({
    global: { value: null, matchMode: FilterMatchMode.CONTAINS }
});
const submitted = ref(false);
const loading = ref(true);

onMounted(() => {
    loadApplications();
});

const loadApplications = () => {
    loading.value = true;
    ApplicationService.getApplications().then((data) => {
        applications.value = data.applications;
        // applications.value.forEach((app) => {
        //     app.created_at = new Date(app.created_at);
        // });
        loading.value = false;
    });
};

const formatDate = (value) => {
    if (!value) return '';
    return new Date(value).toLocaleDateString('en-US', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
    });
};

const openNew = () => {
    application.value = {};
    submitted.value = false;
    applicationDialog.value = true;
};

const hideDialog = () => {
    applicationDialog.value = false;
    submitted.value = false;
};

const saveApplication = async () => {
    submitted.value = true;

    if (application.value.name && application.value.name.trim()) {
        try {
            if (application.value.id) {
                await ApplicationService.updateApplication(application.value.id, application.value);
                toast.add({ severity: 'success', summary: 'Successful', detail: 'Application Updated', life: 3000 });
            } else {
                const response = await ApplicationService.createApplication(application.value);
                if (response.app_key) {
                    newAppKey.value = response.app_key;
                    appKeyDialog.value = true;
                }
                toast.add({ severity: 'success', summary: 'Successful', detail: 'Application Created', life: 3000 });
            }
            applicationDialog.value = false;
            application.value = {};
            loadApplications();
        } catch (error) {
            toast.add({ severity: 'error', summary: 'Error', detail: error.message, life: 3000 });
        }
    }
};

const editApplication = (editApp) => {
    application.value = { ...editApp };
    applicationDialog.value = true;
};

const confirmDeleteApplication = (deleteApp) => {
    application.value = deleteApp;
    deleteApplicationDialog.value = true;
};

const deleteApplication = async () => {
    try {
        await ApplicationService.deleteApplication(application.value.id);
        deleteApplicationDialog.value = false;
        application.value = {};
        toast.add({ severity: 'success', summary: 'Successful', detail: 'Application Deleted', life: 3000 });
        loadApplications();
    } catch (error) {
        toast.add({ severity: 'error', summary: 'Error', detail: error.message, life: 3000 });
    }
};

const exportCSV = () => {
    dt.value.exportCSV();
};

const confirmDeleteSelected = () => {
    deleteApplicationsDialog.value = true;
};

const deleteSelectedApplications = async () => {
    try {
        await Promise.all(selectedApplications.value.map((val) => ApplicationService.deleteApplication(val.id)));
        deleteApplicationsDialog.value = false;
        selectedApplications.value = null;
        toast.add({ severity: 'success', summary: 'Successful', detail: 'Applications Deleted', life: 3000 });
        loadApplications();
    } catch (error) {
        toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to delete some applications', life: 3000 });
    }
};
</script>

<template>
    <div>
        <div class="card">
            <Toolbar class="mb-6">
                <template #start>
                    <Button label="New" icon="pi pi-plus" severity="secondary" class="mr-2" @click="openNew" />
                    <Button label="Delete" icon="pi pi-trash" severity="secondary" @click="confirmDeleteSelected" :disabled="!selectedApplications || !selectedApplications.length" />
                </template>

                <template #end>
                    <Button label="Export" icon="pi pi-upload" severity="secondary" @click="exportCSV($event)" />
                </template>
            </Toolbar>

            <DataTable
                ref="dt"
                v-model:selection="selectedApplications"
                :value="applications"
                dataKey="id"
                :paginator="true"
                :rows="10"
                :filters="filters"
                paginatorTemplate="FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink CurrentPageReport RowsPerPageDropdown"
                :rowsPerPageOptions="[5, 10, 25]"
                currentPageReportTemplate="Showing {first} to {last} of {totalRecords} applications"
                :loading="loading"
            >
                <template #empty> No applications found. </template>
                <template #header>
                    <div class="flex flex-wrap gap-2 items-center justify-between">
                        <h4 class="m-0">Manage Applications</h4>
                        <IconField>
                            <InputIcon>
                                <i class="pi pi-search" />
                            </InputIcon>
                            <InputText v-model="filters['global'].value" placeholder="Search..." />
                        </IconField>
                    </div>
                </template>

                <Column selectionMode="multiple" style="width: 3rem" :exportable="false"></Column>
                <Column field="name" header="Name" sortable style="min-width: 12rem"></Column>
                <Column field="description" header="Description" sortable style="min-width: 16rem"></Column>
                <Column field="app_id" header="App ID" sortable style="min-width: 12rem"></Column>
                <Column field="owner.full_name" header="Owner" sortable style="min-width: 10rem">
                    <template #body="{ data }">
                        <Chip :label="data.owner?.full_name || data.owner?.username || 'Unknown'" :image="data.owner?.avatar || 'https://primefaces.org/cdn/primevue/images/avatar/amyelsner.png'" class="mr-2" />
                    </template>
                </Column>
                <Column field="created_at" header="Created At" sortable style="min-width: 10rem">
                    <template #body="{ data }">
                        {{ formatDate(data.created_at) }}
                    </template>
                </Column>
                <Column :exportable="false" style="min-width: 12rem">
                    <template #body="slotProps">
                        <Button icon="pi pi-pencil" outlined rounded class="mr-2" @click="editApplication(slotProps.data)" />
                        <Button icon="pi pi-trash" outlined rounded severity="danger" @click="confirmDeleteApplication(slotProps.data)" />
                    </template>
                </Column>
            </DataTable>
        </div>

        <Dialog v-model:visible="applicationDialog" :style="{ width: '450px' }" header="Application Details" :modal="true">
            <div class="flex flex-col gap-6">
                <div>
                    <label for="name" class="block font-bold mb-3">Name</label>
                    <InputText id="name" v-model.trim="application.name" required="true" autofocus :invalid="submitted && !application.name" fluid />
                    <small v-if="submitted && !application.name" class="text-red-500">Name is required.</small>
                </div>
                <div>
                    <label for="description" class="block font-bold mb-3">Description</label>
                    <Textarea id="description" v-model="application.description" required="true" rows="3" cols="20" fluid />
                </div>
            </div>

            <template #footer>
                <Button label="Cancel" icon="pi pi-times" text @click="hideDialog" />
                <Button label="Save" icon="pi pi-check" @click="saveApplication" />
            </template>
        </Dialog>

        <Dialog v-model:visible="appKeyDialog" :style="{ width: '450px' }" header="Application Created" :modal="true">
            <div class="flex flex-col gap-4">
                <div class="text-surface-900 dark:text-surface-0 font-medium mb-2">
                    Please save your App Key securely. You won't be able to see it again!
                </div>
                <div class="flex items-center gap-2">
                    <InputText :value="newAppKey" readonly class="w-full" />
                    <Button icon="pi pi-copy" text @click="() => { navigator.clipboard.writeText(newAppKey); toast.add({ severity: 'info', summary: 'Copied', detail: 'App Key copied to clipboard', life: 3000 }); }" />
                </div>
            </div>
            <template #footer>
                <Button label="Close" icon="pi pi-check" @click="appKeyDialog = false" />
            </template>
        </Dialog>

        <Dialog v-model:visible="deleteApplicationDialog" :style="{ width: '450px' }" header="Confirm" :modal="true">
            <div class="flex items-center gap-4">
                <i class="pi pi-exclamation-triangle !text-3xl" />
                <span v-if="application"
                    >Are you sure you want to delete <b>{{ application.name }}</b
                    >?</span
                >
            </div>
            <template #footer>
                <Button label="No" icon="pi pi-times" text @click="deleteApplicationDialog = false" />
                <Button label="Yes" icon="pi pi-check" @click="deleteApplication" />
            </template>
        </Dialog>

        <Dialog v-model:visible="deleteApplicationsDialog" :style="{ width: '450px' }" header="Confirm" :modal="true">
            <div class="flex items-center gap-4">
                <i class="pi pi-exclamation-triangle !text-3xl" />
                <span v-if="application">Are you sure you want to delete the selected applications?</span>
            </div>
            <template #footer>
                <Button label="No" icon="pi pi-times" text @click="deleteApplicationsDialog = false" />
                <Button label="Yes" icon="pi pi-check" text @click="deleteSelectedApplications" />
            </template>
        </Dialog>
    </div>
</template>
