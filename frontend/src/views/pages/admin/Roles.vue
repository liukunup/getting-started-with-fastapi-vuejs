<script setup>
import { RoleService } from '@/client';
import { FilterMatchMode } from '@primevue/core/api';
import { useToast } from 'primevue/usetoast';
import { onMounted, ref } from 'vue';

const toast = useToast();
const dt = ref();
const roles = ref([]);
const roleDialog = ref(false);
const deleteRoleDialog = ref(false);
const deleteRolesDialog = ref(false);
const role = ref({});
const selectedRoles = ref();
const filters = ref({
    global: { value: null, matchMode: FilterMatchMode.CONTAINS }
});
const submitted = ref(false);
const loading = ref(true);

const formatDate = (value) => {
    if (!value) return '';
    return new Date(value).toLocaleDateString('en-US', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
    });
};

onMounted(() => {
    loadRoles();
});

const loadRoles = () => {
    loading.value = true;
    RoleService.readRoles()
        .then((data) => {
            roles.value = data.roles || data;
            loading.value = false;
        })
        .catch((error) => {
            loading.value = false;
            toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to load roles', life: 3000 });
        });
};

const openNew = () => {
    role.value = {};
    submitted.value = false;
    roleDialog.value = true;
};

const hideDialog = () => {
    roleDialog.value = false;
    submitted.value = false;
};

const saveRole = async () => {
    submitted.value = true;

    if (role.value.name?.trim()) {
        try {
            if (role.value.id) {
                await RoleService.updateRole({ roleId: role.value.id, requestBody: role.value });
                toast.add({ severity: 'success', summary: 'Successful', detail: 'Role Updated', life: 3000 });
            } else {
                await RoleService.createRole({ requestBody: role.value });
                toast.add({ severity: 'success', summary: 'Successful', detail: 'Role Created', life: 3000 });
            }
            roleDialog.value = false;
            role.value = {};
            loadRoles();
        } catch (error) {
            toast.add({ severity: 'error', summary: 'Error', detail: error.message, life: 3000 });
        }
    }
};

const editRole = (item) => {
    role.value = { ...item };
    roleDialog.value = true;
};

const confirmDeleteRole = (item) => {
    role.value = item;
    deleteRoleDialog.value = true;
};

const deleteRole = async () => {
    try {
        await RoleService.deleteRole({ roleId: role.value.id });
        deleteRoleDialog.value = false;
        role.value = {};
        toast.add({ severity: 'success', summary: 'Successful', detail: 'Role Deleted', life: 3000 });
        loadRoles();
    } catch (error) {
        toast.add({ severity: 'error', summary: 'Error', detail: error.message, life: 3000 });
    }
};

const exportCSV = () => {
    dt.value.exportCSV();
};

const confirmDeleteSelected = () => {
    deleteRolesDialog.value = true;
};

const deleteSelectedRoles = async () => {
    try {
        await Promise.all(selectedRoles.value.map((val) => RoleService.deleteRole({ roleId: val.id })));
        deleteRolesDialog.value = false;
        selectedRoles.value = null;
        toast.add({ severity: 'success', summary: 'Successful', detail: 'Roles Deleted', life: 3000 });
        loadRoles();
    } catch (error) {
        toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to delete some roles', life: 3000 });
    }
};
</script>

<template>
    <div>
        <div class="card">
            <Toolbar class="mb-6">
                <template #start>
                    <Button label="New" icon="pi pi-plus" severity="secondary" class="mr-2" @click="openNew" />
                    <Button label="Delete" icon="pi pi-trash" severity="secondary" @click="confirmDeleteSelected" :disabled="!selectedRoles || !selectedRoles.length" />
                </template>

                <template #end>
                    <Button label="Export" icon="pi pi-upload" severity="secondary" @click="exportCSV($event)" />
                </template>
            </Toolbar>

            <DataTable
                ref="dt"
                v-model:selection="selectedRoles"
                :value="roles"
                dataKey="id"
                :paginator="true"
                :rows="10"
                :filters="filters"
                paginatorTemplate="FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink CurrentPageReport RowsPerPageDropdown"
                :rowsPerPageOptions="[5, 10, 25]"
                currentPageReportTemplate="Showing {first} to {last} of {totalRecords} roles"
                :loading="loading"
            >
                <template #empty> No roles found. </template>
                <template #header>
                    <div class="flex flex-wrap gap-2 items-center justify-between">
                        <h4 class="m-0">Manage Roles</h4>
                        <IconField>
                            <InputIcon>
                                <i class="pi pi-search" />
                            </InputIcon>
                            <InputText v-model="filters['global'].value" placeholder="Search..." />
                        </IconField>
                    </div>
                </template>

                <Column selectionMode="multiple" style="width: 3rem" :exportable="false"></Column>
                <Column field="name" header="Name" sortable style="width: 8rem">
                    <template #body="slotProps">
                        <span class="capitalize">{{ slotProps.data.name }}</span>
                    </template>
                </Column>
                <Column field="description" header="Description" sortable style="min-width: 12rem"></Column>
                <Column :exportable="false" style="min-width: 6rem">
                    <template #body="slotProps">
                        <Button icon="pi pi-pencil" outlined rounded class="mr-2" @click="editRole(slotProps.data)" />
                        <Button icon="pi pi-trash" outlined rounded severity="danger" @click="confirmDeleteRole(slotProps.data)" />
                    </template>
                </Column>
            </DataTable>
        </div>

        <Dialog v-model:visible="roleDialog" :style="{ width: '450px' }" header="Role Details" :modal="true">
            <div class="flex flex-col gap-6">
                <div>
                    <label for="name" class="block font-bold mb-3">Name</label>
                    <InputText id="name" v-model.trim="role.name" required="true" autofocus :invalid="submitted && !role.name" fluid />
                    <small v-if="submitted && !role.name" class="text-red-500">Name is required.</small>
                </div>
                <div>
                    <label for="description" class="block font-bold mb-3">Description</label>
                    <Textarea id="description" v-model="role.description" rows="3" cols="20" fluid />
                </div>
            </div>

            <template #footer>
                <Button label="Cancel" icon="pi pi-times" text @click="hideDialog" />
                <Button label="Save" icon="pi pi-check" @click="saveRole" />
            </template>
        </Dialog>

        <Dialog v-model:visible="deleteRoleDialog" :style="{ width: '450px' }" header="Confirm" :modal="true">
            <div class="flex items-center gap-4">
                <i class="pi pi-exclamation-triangle !text-3xl" />
                <span v-if="role"
                    >Are you sure you want to delete <b class="capitalize">{{ role.name }}</b
                    >?</span
                >
            </div>
            <template #footer>
                <Button label="No" icon="pi pi-times" text @click="deleteRoleDialog = false" />
                <Button label="Yes" icon="pi pi-check" @click="deleteRole" />
            </template>
        </Dialog>

        <Dialog v-model:visible="deleteRolesDialog" :style="{ width: '450px' }" header="Confirm" :modal="true">
            <div class="flex items-center gap-4">
                <i class="pi pi-exclamation-triangle !text-3xl" />
                <span v-if="role">Are you sure you want to delete the selected roles?</span>
            </div>
            <template #footer>
                <Button label="No" icon="pi pi-times" text @click="deleteRolesDialog = false" />
                <Button label="Yes" icon="pi pi-check" text @click="deleteSelectedRoles" />
            </template>
        </Dialog>
    </div>
</template>
