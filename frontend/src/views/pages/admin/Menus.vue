<script setup>
import { MenuService, PolicyService, RoleService } from '@/client';
import { FilterMatchMode } from '@primevue/core/api';
import Button from 'primevue/button';
import Checkbox from 'primevue/checkbox';
import Column from 'primevue/column';
import Dialog from 'primevue/dialog';
import InputText from 'primevue/inputtext';
import Toolbar from 'primevue/toolbar';
import TreeTable from 'primevue/treetable';
import { useToast } from 'primevue/usetoast';
import { onMounted, ref } from 'vue';

const toast = useToast();
const dt = ref();
const menus = ref([]);
const menuDialog = ref(false);
const deleteMenuDialog = ref(false);
const menu = ref({});
const selectedMenus = ref();
const filters = ref({
    global: { value: null, matchMode: FilterMatchMode.CONTAINS }
});
const submitted = ref(false);
const roles = ref([]);
const policies = ref([]);
const permissionsDialog = ref(false);
const selectedMenu = ref({});
const rolePermissions = ref({});

onMounted(() => {
    loadMenus();
    loadRolesAndPolicies();
});

function loadRolesAndPolicies() {
    RoleService.readRoles().then((data) => {
        roles.value = data.roles || data; // Handle if response is wrapped
    });
    PolicyService.readPolicies().then((data) => {
        policies.value = data;
    });
}

function loadMenus() {
    // Get tree structure (flatten=false)
    MenuService.readMenus()
        .then((data) => {
            console.log('Menus data:', data);
            // TreeTable expects a specific node structure with 'data' and 'children'
            // But if our API returns objects with 'children', we can map it or configure TreeTable
            // PrimeVue TreeTable can work with arbitrary data if we don't use the TreeNode interface strictly for everything,
            // but usually it expects { key: '...', data: { ... }, children: [ ... ] }
            // Let's transform the data to match TreeTable requirements better if needed,
            // or just pass it if TreeTable supports direct binding (it usually needs TreeNode structure).

            // Transform API response to TreeNode structure
            if (Array.isArray(data)) {
                menus.value = transformToTreeNode(data);
            } else {
                console.error('Menus data is not an array:', data);
                menus.value = [];
            }
        })
        .catch((err) => {
            console.error('Failed to load menus:', err);
            toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to load menus', life: 3000 });
        });
}

function transformToTreeNode(items) {
    return items.map((item) => ({
        key: item.id,
        data: item,
        children: item.items ? transformToTreeNode(item.items) : []
    }));
}

function openNew(parent = null) {
    menu.value = { is_hidden: false, parent_id: parent ? parent.id : null };
    submitted.value = false;
    menuDialog.value = true;
}

function hideDialog() {
    menuDialog.value = false;
    submitted.value = false;
}

function saveMenu() {
    submitted.value = true;

    if (menu.value.label?.trim()) {
        if (menu.value.id) {
            MenuService.updateMenu({ menuId: menu.value.id, requestBody: menu.value }).then(() => {
                loadMenus();
                toast.add({ severity: 'success', summary: 'Successful', detail: 'Menu Updated', life: 3000 });
            });
        } else {
            MenuService.createMenu({ requestBody: menu.value }).then(() => {
                loadMenus();
                toast.add({ severity: 'success', summary: 'Successful', detail: 'Menu Created', life: 3000 });
            });
        }

        menuDialog.value = false;
        menu.value = {};
    }
}

function editMenu(item) {
    menu.value = { ...item };
    menuDialog.value = true;
}

function confirmDeleteMenu(item) {
    menu.value = item;
    deleteMenuDialog.value = true;
}

function deleteMenu() {
    MenuService.deleteMenu({ menuId: menu.value.id }).then(() => {
        loadMenus();
        deleteMenuDialog.value = false;
        menu.value = {};
        toast.add({ severity: 'success', summary: 'Successful', detail: 'Menu Deleted', life: 3000 });
    });
}

function openPermissions(item) {
    selectedMenu.value = item;
    // Calculate permissions
    const perms = {};
    // Ensure roles is an array
    const roleList = Array.isArray(roles.value) ? roles.value : [];

    roleList.forEach((role) => {
        // Check if policy exists: sub=menu:{role.name}, obj={item.label}, act=visible
        const hasPerm = policies.value.some((p) => p.sub === `menu:${role.name}` && p.obj === item.label && p.act === 'visible');
        perms[role.name] = hasPerm;
    });
    rolePermissions.value = perms;
    permissionsDialog.value = true;
}

function togglePermission(role, checked) {
    const policy = {
        sub: `menu:${role.name}`,
        obj: selectedMenu.value.label,
        act: 'visible'
    };

    if (checked) {
        PolicyService.addPolicy({ requestBody: policy }).then(() => {
            rolePermissions.value[role.name] = true;
            // Update local policies cache
            policies.value.push(policy);
            toast.add({ severity: 'success', summary: 'Permission Added', detail: `Added access for ${role.name}`, life: 3000 });
        });
    } else {
        PolicyService.removePolicy({ requestBody: policy }).then(() => {
            rolePermissions.value[role.name] = false;
            // Update local policies cache
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

        <div v-if="!menus || menus.length === 0" class="p-4 text-center">No menus found.</div>

        <TreeTable v-else :value="menus" tableStyle="min-width: 50rem">
            <template #header>
                <div class="flex flex-wrap gap-2 items-center justify-between">
                    <h4 class="m-0">Manage Menus</h4>
                    <IconField>
                        <InputIcon>
                            <i class="pi pi-search" />
                        </InputIcon>
                        <InputText v-model="filters['global'].value" placeholder="Search..." />
                    </IconField>
                </div>
            </template>

            <Column field="label" header="Label" :expander="true" style="min-width: 15rem"></Column>
            <Column field="icon" header="Icon" style="min-width: 16rem">
                <template #body="slotProps">
                    <div class="flex items-center gap-2">
                        <i v-if="slotProps.node.data.icon" :class="slotProps.node.data.icon" class="text-lg"></i>
                        <span v-if="slotProps.node.data.icon" class="text-sm text-gray-500">{{ slotProps.node.data.icon }}</span>
                    </div>
                </template>
            </Column>
            <Column field="to" header="To" style="min-width: 12rem"></Column>
            <Column field="component" header="Component" style="min-width: 15rem"></Column>
            <Column field="url" header="URL" style="min-width: 12rem"></Column>
            <Column field="target" header="Target" style="min-width: 8rem"></Column>
            <Column field="is_hidden" header="Hidden" style="min-width: 6rem">
                <template #body="slotProps">
                    <i class="pi" :class="{ 'pi-check text-green-500': slotProps.node.data.is_hidden, 'pi-times text-red-500': !slotProps.node.data.is_hidden }"></i>
                </template>
            </Column>
            <Column style="min-width: 12rem">
                <template #body="slotProps">
                    <Button icon="pi pi-plus" outlined rounded class="mr-2" @click="openNew(slotProps.node.data)" v-tooltip.top="'Add Child'" />
                    <Button icon="pi pi-pencil" outlined rounded class="mr-2" @click="editMenu(slotProps.node.data)" v-tooltip.top="'Edit'" />
                    <Button icon="pi pi-lock" outlined rounded class="mr-2" @click="openPermissions(slotProps.node.data)" v-tooltip.top="'Permissions'" />
                    <Button icon="pi pi-trash" outlined rounded severity="danger" @click="confirmDeleteMenu(slotProps.node.data)" v-tooltip.top="'Delete'" />
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

        <Dialog v-model:visible="menuDialog" :style="{ width: '450px' }" header="Menu Details" :modal="true">
            <div class="flex flex-col gap-6">
                <div>
                    <label for="label" class="block font-bold mb-3">Label</label>
                    <InputText id="label" v-model.trim="menu.label" required="true" autofocus :invalid="submitted && !menu.label" fluid />
                    <small class="text-red-500" v-if="submitted && !menu.label">Label is required.</small>
                </div>
                <div>
                    <label for="to" class="block font-bold mb-3">To (Internal Path)</label>
                    <InputText id="to" v-model.trim="menu.to" fluid />
                </div>
                <div>
                    <label for="component" class="block font-bold mb-3">Component</label>
                    <InputText id="component" v-model.trim="menu.component" fluid />
                </div>
                <div>
                    <label for="icon" class="block font-bold mb-3">Icon</label>
                    <InputText id="icon" v-model.trim="menu.icon" fluid />
                </div>
                <div>
                    <label for="url" class="block font-bold mb-3">URL (External Link)</label>
                    <InputText id="url" v-model.trim="menu.url" fluid />
                </div>
                <div>
                    <label for="target" class="block font-bold mb-3">Target</label>
                    <InputText id="target" v-model.trim="menu.target" fluid />
                </div>
                <div>
                    <label for="clazz" class="block font-bold mb-3">Class</label>
                    <InputText id="clazz" v-model.trim="menu.clazz" fluid />
                </div>
                <div class="flex items-center gap-2">
                    <Checkbox id="is_hidden" v-model="menu.is_hidden" :binary="true" />
                    <label for="is_hidden">Hidden</label>
                </div>
            </div>

            <template #footer>
                <Button label="Cancel" icon="pi pi-times" text @click="hideDialog" />
                <Button label="Save" icon="pi pi-check" @click="saveMenu" />
            </template>
        </Dialog>

        <Dialog v-model:visible="deleteMenuDialog" :style="{ width: '450px' }" header="Confirm" :modal="true">
            <div class="flex items-center gap-4">
                <i class="pi pi-exclamation-triangle !text-3xl" />
                <span v-if="menu"
                    >Are you sure you want to delete <b>{{ menu.label }}</b
                    >?</span
                >
            </div>
            <template #footer>
                <Button label="No" icon="pi pi-times" text @click="deleteMenuDialog = false" />
                <Button label="Yes" icon="pi pi-check" text @click="deleteMenu" />
            </template>
        </Dialog>
    </div>
</template>
