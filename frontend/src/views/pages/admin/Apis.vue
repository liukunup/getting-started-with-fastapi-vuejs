<script setup>
import { ApiService, PolicyService, RoleService } from '@/client';
import { FilterMatchMode } from '@primevue/core/api';
import Button from 'primevue/button';
import Checkbox from 'primevue/checkbox';
import Column from 'primevue/column';
import TreeTable from 'primevue/treetable';
import Dialog from 'primevue/dialog';
import IconField from 'primevue/iconfield';
import InputIcon from 'primevue/inputicon';
import InputText from 'primevue/inputtext';
import Toolbar from 'primevue/toolbar';
import { useToast } from 'primevue/usetoast';
import { onMounted, ref } from 'vue';

const toast = useToast();
const apis = ref([]);
const apiDialog = ref(false);
const deleteApiDialog = ref(false);
const api = ref({});
const selectedApis = ref({});
const expandedKeys = ref({});
const filters = ref({
    global: { value: null, matchMode: FilterMatchMode.CONTAINS }
});
const submitted = ref(false);
const loading = ref(true);
const roles = ref([]);
const policies = ref([]);
const permissionsDialog = ref(false);
const selectedApi = ref({});
const rolePermissions = ref({});

onMounted(() => {
    loadApis();
    loadRolesAndPolicies();
});

function loadRolesAndPolicies() {
    RoleService.readRoles().then((data) => {
        roles.value = data.roles || data;
    });
    PolicyService.readPolicies().then((data) => {
        policies.value = data;
    });
}

function loadApis() {
    loading.value = true;
    ApiService.readApis()
        .then((data) => {
            console.log('APIs data received:', data);
            if (data) {
                if (Array.isArray(data.data)) {
                    apis.value = data.data;
                    expandedKeys.value = {};
                } else if (Array.isArray(data)) {
                    // Fallback for flat array
                    console.warn('Received flat array, converting to tree nodes');
                    apis.value = data.map((api) => ({
                        key: api.id,
                        data: api,
                        children: []
                    }));
                } else {
                    console.warn('Received unexpected data format:', data);
                    apis.value = [];
                }
            } else {
                apis.value = [];
            }
            console.log('apis.value set to:', apis.value);
            loading.value = false;
        })
        .catch((error) => {
            console.error('Failed to load APIs:', error);
            loading.value = false;
            toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to load APIs', life: 3000 });
        });
}

function openNew() {
    api.value = {};
    submitted.value = false;
    apiDialog.value = true;
}

function hideDialog() {
    apiDialog.value = false;
    submitted.value = false;
}

function saveApi() {
    submitted.value = true;

    if (api.value.name?.trim()) {
        if (api.value.id) {
            ApiService.updateApi({ apiId: api.value.id, requestBody: api.value }).then(() => {
                loadApis();
                toast.add({ severity: 'success', summary: 'Successful', detail: 'API Updated', life: 3000 });
            });
        } else {
            ApiService.createApi({ requestBody: api.value }).then(() => {
                loadApis();
                toast.add({ severity: 'success', summary: 'Successful', detail: 'API Created', life: 3000 });
            });
        }

        apiDialog.value = false;
        api.value = {};
    }
}

function editApi(item) {
    api.value = { ...item };
    apiDialog.value = true;
}

function confirmDeleteApi(item) {
    api.value = item;
    deleteApiDialog.value = true;
}

function deleteApi() {
    ApiService.deleteApi({ apiId: api.value.id }).then(() => {
        loadApis();
        deleteApiDialog.value = false;
        api.value = {};
        toast.add({ severity: 'success', summary: 'Successful', detail: 'API Deleted', life: 3000 });
    });
}

function openPermissions(item) {
    if (!item.path || !item.method) {
        return;
    }
    selectedApi.value = item;
    const perms = {};
    const roleList = Array.isArray(roles.value) ? roles.value : [];

    roleList.forEach((role) => {
        // Check if policy exists: sub=api:{role.name}, obj={item.path}, act={item.method}
        const hasPerm = policies.value.some((p) => p.sub === `api:${role.name}` && p.obj === item.path && p.act === item.method);
        perms[role.name] = hasPerm;
    });
    rolePermissions.value = perms;
    permissionsDialog.value = true;
}

function togglePermission(role, checked) {
    const policy = {
        sub: `api:${role.name}`,
        obj: selectedApi.value.path,
        act: selectedApi.value.method
    };

    if (checked) {
        PolicyService.addPolicy({ requestBody: policy }).then(() => {
            rolePermissions.value[role.name] = true;
            policies.value.push(policy);
            toast.add({ severity: 'success', summary: 'Permission Added', detail: `Added access for ${role.name}`, life: 3000 });
        });
    } else {
        PolicyService.removePolicy({ requestBody: policy }).then(() => {
            rolePermissions.value[role.name] = false;
            policies.value = policies.value.filter((p) => !(p.sub === policy.sub && p.obj === policy.obj && p.act === policy.act));
            toast.add({ severity: 'success', summary: 'Permission Removed', detail: `Removed access for ${role.name}`, life: 3000 });
        });
    }
}
</script>

<template>
    <div class="card">
        <Toolbar class="mb-4">
            <template #start>
                <Button label="New" icon="pi pi-plus" severity="secondary" class="mr-2" @click="openNew" />
            </template>
        </Toolbar>

        <TreeTable :value="apis" v-model:expandedKeys="expandedKeys" :loading="loading">
            <template #header>
                <div class="flex flex-wrap gap-2 items-center justify-between">
                    <h4 class="m-0">Manage APIs</h4>
                    <IconField>
                        <InputIcon>
                            <i class="pi pi-search" />
                        </InputIcon>
                        <InputText v-model="filters['global'].value" placeholder="Search..." />
                    </IconField>
                </div>
            </template>

            <Column field="name" header="Name" :expander="true" style="min-width: 15rem"></Column>
            <Column field="path" header="Path" style="min-width: 15rem"></Column>
            <Column field="method" header="Method" style="min-width: 8rem"></Column>
            <Column style="min-width: 12rem">
                <template #body="slotProps">
                    <div v-if="slotProps.node.data.path">
                        <Button icon="pi pi-pencil" outlined rounded class="mr-2" @click="editApi(slotProps.node.data)" />
                        <Button icon="pi pi-lock" outlined rounded class="mr-2" @click="openPermissions(slotProps.node.data)" v-tooltip.top="'Permissions'" />
                        <Button icon="pi pi-trash" outlined rounded severity="danger" @click="confirmDeleteApi(slotProps.node.data)" />
                    </div>
                </template>
            </Column>
        </TreeTable>

        <Dialog v-model:visible="permissionsDialog" :style="{ width: '450px' }" header="Manage Permissions" :modal="true">
            <div class="flex flex-col gap-4">
                <div v-for="role in roles" :key="role.id" class="flex items-center justify-between">
                    <span>{{ role.name }}</span>
                    <Checkbox :modelValue="rolePermissions[role.name]" @update:modelValue="(val) => togglePermission(role, val)" :binary="true" />
                </div>
            </div>
        </Dialog>

        <Dialog v-model:visible="apiDialog" :style="{ width: '450px' }" header="API Details" :modal="true">
            <div class="flex flex-col gap-6">
                <div>
                    <label for="group" class="block font-bold mb-3">Group</label>
                    <InputText id="group" v-model.trim="api.group" required="true" autofocus :invalid="submitted && !api.group" fluid />
                    <small class="text-red-500" v-if="submitted && !api.group">Group is required.</small>
                </div>
                <div>
                    <label for="name" class="block font-bold mb-3">Name</label>
                    <InputText id="name" v-model.trim="api.name" required="true" :invalid="submitted && !api.name" fluid />
                    <small class="text-red-500" v-if="submitted && !api.name">Name is required.</small>
                </div>
                <div>
                    <label for="path" class="block font-bold mb-3">Path</label>
                    <InputText id="path" v-model.trim="api.path" required="true" :invalid="submitted && !api.path" fluid />
                    <small class="text-red-500" v-if="submitted && !api.path">Path is required.</small>
                </div>
                <div>
                    <label for="method" class="block font-bold mb-3">Method</label>
                    <InputText id="method" v-model.trim="api.method" required="true" :invalid="submitted && !api.method" fluid />
                    <small class="text-red-500" v-if="submitted && !api.method">Method is required.</small>
                </div>
            </div>

            <template #footer>
                <Button label="Cancel" icon="pi pi-times" text @click="hideDialog" />
                <Button label="Save" icon="pi pi-check" @click="saveApi" />
            </template>
        </Dialog>

        <Dialog v-model:visible="deleteApiDialog" :style="{ width: '450px' }" header="Confirm" :modal="true">
            <div class="flex items-center gap-4">
                <i class="pi pi-exclamation-triangle !text-3xl" />
                <span v-if="api">Are you sure you want to delete this API?</span>
            </div>
            <template #footer>
                <Button label="No" icon="pi pi-times" text @click="deleteApiDialog = false" />
                <Button label="Yes" icon="pi pi-check" text @click="deleteApi" />
            </template>
        </Dialog>
    </div>
</template>
