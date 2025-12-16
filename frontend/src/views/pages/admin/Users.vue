<script setup>
import { UserService } from '@/client';
import { AdminService } from '@/service/AdminService';
import { getAvatarUrl } from '@/utils';
import { FilterMatchMode, FilterOperator } from '@primevue/core/api';
import Select from 'primevue/select';
import { useToast } from 'primevue/usetoast';
import { onMounted, ref } from 'vue';

const toast = useToast();
const dt = ref();
const users = ref(null);
const roles = ref([]);
const currentUser = ref(null);
const userDialog = ref(false);
const deleteUserDialog = ref(false);
const deleteUsersDialog = ref(false);
const user = ref({});
const selectedUsers = ref();
const filters = ref({
    global: { value: null, matchMode: FilterMatchMode.CONTAINS }
});
const submitted = ref(false);
const loading = ref(true);

onMounted(() => {
    loadUsers();
    loadRoles();
    UserService.readUserMe().then((data) => {
        currentUser.value = data;
    });
});

const loadRoles = () => {
    AdminService.getRoles().then((data) => {
        // The API returns { roles: [...], total: ... }
        // We need to assign the array to roles.value
        if (data && Array.isArray(data.roles)) {
            roles.value = data.roles;
        } else if (Array.isArray(data)) {
            // Fallback if API changes to return array directly
            roles.value = data;
        } else {
            roles.value = [];
        }
    });
};

const loadUsers = () => {
    loading.value = true;
    UserService.readUsers()
        .then((data) => {
            // 将当前用户排在最前面
            if (currentUser.value && data.users) {
                const sortedUsers = [...data.users];
                const currentUserIndex = sortedUsers.findIndex((u) => u.id === currentUser.value.id);
                if (currentUserIndex > 0) {
                    const [current] = sortedUsers.splice(currentUserIndex, 1);
                    sortedUsers.unshift(current);
                }
                users.value = sortedUsers;
            } else {
                users.value = data.users;
            }
            loading.value = false;
        })
        .catch((error) => {
            loading.value = false;
            toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to load users', life: 3000 });
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
    user.value = { is_active: true };
    submitted.value = false;
    userDialog.value = true;
};

const hideDialog = () => {
    userDialog.value = false;
    submitted.value = false;
};

const saveUser = async () => {
    submitted.value = true;

    if (user.value.email && user.value.email.trim()) {
        try {
            if (user.value.id) {
                await UserService.updateUser({ userId: user.value.id, requestBody: user.value });
                toast.add({ severity: 'success', summary: 'Successful', detail: 'User Updated', life: 3000 });
            } else {
                await UserService.createUser({ requestBody: user.value });
                toast.add({ severity: 'success', summary: 'Successful', detail: 'User Created', life: 3000 });
            }
            userDialog.value = false;
            user.value = {};
            loadUsers();
        } catch (error) {
            toast.add({ severity: 'error', summary: 'Error', detail: error.message, life: 3000 });
        }
    }
};

const editUser = (editUser) => {
    user.value = { ...editUser };
    if (user.value.role) {
        user.value.role_id = user.value.role.id;
    }
    userDialog.value = true;
};

const confirmDeleteUser = (deleteUser) => {
    user.value = deleteUser;
    deleteUserDialog.value = true;
};

const deleteUser = async () => {
    try {
        await UserService.deleteUser({ userId: user.value.id });
        deleteUserDialog.value = false;
        user.value = {};
        toast.add({ severity: 'success', summary: 'Successful', detail: 'User Deleted', life: 3000 });
        loadUsers();
    } catch (error) {
        toast.add({ severity: 'error', summary: 'Error', detail: error.message, life: 3000 });
    }
};

const exportCSV = () => {
    dt.value.exportCSV();
};

const confirmDeleteSelected = () => {
    deleteUsersDialog.value = true;
};

const deleteSelectedUsers = async () => {
    try {
        await Promise.all(selectedUsers.value.map((val) => UserService.deleteUser({ userId: val.id })));
        deleteUsersDialog.value = false;
        selectedUsers.value = null;
        toast.add({ severity: 'success', summary: 'Successful', detail: 'Users Deleted', life: 3000 });
        loadUsers();
    } catch (error) {
        toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to delete some users', life: 3000 });
    }
};
</script>

<template>
    <div>
        <div class="card">
            <Toolbar class="mb-6">
                <template #start>
                    <Button label="New" icon="pi pi-plus" severity="secondary" class="mr-2" @click="openNew" />
                    <Button label="Delete" icon="pi pi-trash" severity="secondary" @click="confirmDeleteSelected" :disabled="!selectedUsers || !selectedUsers.length" />
                </template>

                <template #end>
                    <Button label="Export" icon="pi pi-upload" severity="secondary" @click="exportCSV($event)" />
                </template>
            </Toolbar>

            <DataTable
                ref="dt"
                v-model:selection="selectedUsers"
                :value="users"
                dataKey="id"
                :paginator="true"
                :rows="10"
                :filters="filters"
                paginatorTemplate="FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink CurrentPageReport RowsPerPageDropdown"
                :rowsPerPageOptions="[5, 10, 25]"
                currentPageReportTemplate="Showing {first} to {last} of {totalRecords} users"
                :loading="loading"
            >
                <template #empty> No users found. </template>
                <template #header>
                    <div class="flex flex-wrap gap-2 items-center justify-between">
                        <h4 class="m-0">Manage Users</h4>
                        <IconField>
                            <InputIcon>
                                <i class="pi pi-search" />
                            </InputIcon>
                            <InputText v-model="filters['global'].value" placeholder="Search..." />
                        </IconField>
                    </div>
                </template>

                <Column selectionMode="multiple" style="width: 3rem" :exportable="false"></Column>
                <Column header="Avatar" style="width: 5rem">
                    <template #body="{ data }">
                        <Avatar :image="getAvatarUrl(data.avatar)" shape="circle" size="normal" />
                    </template>
                </Column>
                <Column field="full_name" header="Full Name" sortable style="min-width: 12rem">
                    <template #body="{ data }">
                        <span :class="{ 'text-gray-500': !data.full_name }">{{ data.full_name || 'N/A' }}</span>
                        <Badge v-if="currentUser && currentUser.id === data.id" value="You" severity="info" class="ml-2" />
                    </template>
                </Column>
                <Column field="email" header="Email" sortable style="min-width: 16rem"></Column>
                <Column field="role.name" header="Role" sortable style="min-width: 10rem">
                    <template #body="{ data }">
                        {{ data.role ? data.role.name : 'N/A' }}
                    </template>
                </Column>
                <Column field="is_active" header="Active" dataType="boolean" style="min-width: 6rem">
                    <template #body="{ data }">
                        <i class="pi" :class="{ 'pi-check-circle text-green-500': data.is_active, 'pi-times-circle text-red-400': !data.is_active }"></i>
                    </template>
                </Column>
                <Column field="is_superuser" header="Superuser" dataType="boolean" style="min-width: 6rem">
                    <template #body="{ data }">
                        <i class="pi" :class="{ 'pi-check-circle text-green-500': data.is_superuser, 'pi-times-circle text-red-400': !data.is_superuser }"></i>
                    </template>
                </Column>
                <Column field="created_at" header="Created At" sortable style="min-width: 10rem">
                    <template #body="{ data }">
                        {{ formatDate(data.created_at) }}
                    </template>
                </Column>
                <Column :exportable="false" style="min-width: 12rem">
                    <template #body="slotProps">
                        <Button icon="pi pi-pencil" outlined rounded class="mr-2" @click="editUser(slotProps.data)" />
                        <Button icon="pi pi-trash" outlined rounded severity="danger" @click="confirmDeleteUser(slotProps.data)" />
                    </template>
                </Column>
            </DataTable>
        </div>

        <Dialog v-model:visible="userDialog" :style="{ width: '450px' }" header="User Details" :modal="true">
            <div class="flex flex-col gap-6">
                <div>
                    <label for="email" class="block font-bold mb-3">Email</label>
                    <InputText id="email" v-model.trim="user.email" required="true" :invalid="submitted && !user.email" fluid />
                    <small v-if="submitted && !user.email" class="text-red-500">Email is required.</small>
                </div>
                <div v-if="!user.id">
                    <label for="password" class="block font-bold mb-3">Password</label>
                    <InputText id="password" v-model.trim="user.password" required="true" :invalid="submitted && !user.password" fluid />
                    <small v-if="submitted && !user.password" class="text-red-500">Password is required.</small>
                </div>
                <div>
                    <label for="role" class="block font-bold mb-3">Role</label>
                    <Select id="role" v-model="user.role_id" :options="roles" optionLabel="name" optionValue="id" placeholder="Select a Role" fluid showClear class="w-full" />
                </div>
                <div class="flex items-center gap-4">
                    <div class="flex items-center gap-2">
                        <Checkbox v-model="user.is_active" :binary="true" inputId="is_active" />
                        <label for="is_active">Active</label>
                    </div>
                    <div class="flex items-center gap-2">
                        <Checkbox v-model="user.is_superuser" :binary="true" inputId="is_superuser" />
                        <label for="is_superuser">Superuser</label>
                    </div>
                </div>
            </div>

            <template #footer>
                <Button label="Cancel" icon="pi pi-times" text @click="hideDialog" />
                <Button label="Save" icon="pi pi-check" @click="saveUser" />
            </template>
        </Dialog>

        <Dialog v-model:visible="deleteUserDialog" :style="{ width: '450px' }" header="Confirm" :modal="true">
            <div class="flex items-center gap-4">
                <i class="pi pi-exclamation-triangle !text-3xl" />
                <span v-if="user"
                    >Are you sure you want to delete <b>{{ user.username }}</b
                    >?</span
                >
            </div>
            <template #footer>
                <Button label="No" icon="pi pi-times" text @click="deleteUserDialog = false" />
                <Button label="Yes" icon="pi pi-check" @click="deleteUser" />
            </template>
        </Dialog>

        <Dialog v-model:visible="deleteUsersDialog" :style="{ width: '450px' }" header="Confirm" :modal="true">
            <div class="flex items-center gap-4">
                <i class="pi pi-exclamation-triangle !text-3xl" />
                <span v-if="user">Are you sure you want to delete the selected users?</span>
            </div>
            <template #footer>
                <Button label="No" icon="pi pi-times" text @click="deleteUsersDialog = false" />
                <Button label="Yes" icon="pi pi-check" text @click="deleteSelectedUsers" />
            </template>
        </Dialog>
    </div>
</template>
