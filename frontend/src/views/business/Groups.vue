<script setup>
import { GroupService, UserService } from '@/client';
import { formatDateTime, getAvatarUrl } from '@/utils';
import { FilterMatchMode } from '@primevue/core/api';
import { useToast } from 'primevue/usetoast';
import { onMounted, ref } from 'vue';

const toast = useToast();
const dt = ref();
const groups = ref(null);
const users = ref([]);
const groupDialog = ref(false);
const deleteGroupDialog = ref(false);
const deleteGroupsDialog = ref(false);
const group = ref({});
const selectedGroups = ref();
const filters = ref({
    global: { value: null, matchMode: FilterMatchMode.CONTAINS }
});
const submitted = ref(false);
const loading = ref(true);

onMounted(() => {
    loadGroups();
    loadUsers();
});

const loadUsers = () => {
    UserService.readUsers().then((data) => {
        users.value = data.users.map((u) => ({ ...u, displayName: u.full_name || u.username }));
    });
};

const loadGroups = () => {
    loading.value = true;
    GroupService.readGroups().then((data) => {
        groups.value = data.groups;
        groups.value.forEach((group) => {
            group.created_at = new Date(group.created_at);
            if (group.members) {
                group.members.forEach((m) => {
                    m.displayName = m.full_name || m.username;
                });
            }
            group.user_names = group.members ? group.members.map((u) => u.displayName).join(', ') : '';
        });
        loading.value = false;
    });
};

const openNew = () => {
    group.value = {};
    submitted.value = false;
    groupDialog.value = true;
};

const hideDialog = () => {
    groupDialog.value = false;
    submitted.value = false;
};

const removeMember = (member) => {
    group.value.members = group.value.members.filter((m) => m.id !== member.id);
};

const saveGroup = async () => {
    submitted.value = true;

    if (group.value.name && group.value.name.trim()) {
        try {
            const payload = {
                ...group.value,
                member_ids: group.value.members ? group.value.members.map((u) => u.id) : []
            };

            if (group.value.id) {
                await GroupService.updateGroup({ groupId: group.value.id, requestBody: payload });
                toast.add({ severity: 'success', summary: 'Successful', detail: 'Group Updated', life: 3000 });
            } else {
                await GroupService.createGroup({ requestBody: payload });
                toast.add({ severity: 'success', summary: 'Successful', detail: 'Group Created', life: 3000 });
            }
            groupDialog.value = false;
            group.value = {};
            loadGroups();
        } catch (error) {
            toast.add({ severity: 'error', summary: 'Error', detail: error.message, life: 3000 });
        }
    }
};

const editGroup = (editGroup) => {
    group.value = { ...editGroup };
    groupDialog.value = true;
};

const confirmDeleteGroup = (deleteGroup) => {
    group.value = deleteGroup;
    deleteGroupDialog.value = true;
};

const deleteGroup = async () => {
    try {
        await GroupService.deleteGroup({ groupId: group.value.id });
        deleteGroupDialog.value = false;
        group.value = {};
        toast.add({ severity: 'success', summary: 'Successful', detail: 'Group Deleted', life: 3000 });
        loadGroups();
    } catch (error) {
        toast.add({ severity: 'error', summary: 'Error', detail: error.message, life: 3000 });
    }
};

const exportCSV = () => {
    dt.value.exportCSV();
};

const confirmDeleteSelected = () => {
    deleteGroupsDialog.value = true;
};

const deleteSelectedGroups = async () => {
    try {
        await Promise.all(selectedGroups.value.map((val) => GroupService.deleteGroup({ groupId: val.id })));
        deleteGroupsDialog.value = false;
        selectedGroups.value = null;
        toast.add({ severity: 'success', summary: 'Successful', detail: 'Groups Deleted', life: 3000 });
        loadGroups();
    } catch (error) {
        toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to delete some groups', life: 3000 });
    }
};
</script>

<template>
    <div>
        <div class="card">
            <Toolbar class="mb-6">
                <template #start>
                    <Button label="New" icon="pi pi-plus" severity="secondary" class="mr-2" @click="openNew" />
                    <Button label="Delete" icon="pi pi-trash" severity="secondary" @click="confirmDeleteSelected" :disabled="!selectedGroups || !selectedGroups.length" />
                </template>

                <template #end>
                    <Button label="Export" icon="pi pi-upload" severity="secondary" @click="exportCSV($event)" />
                </template>
            </Toolbar>

            <DataTable
                ref="dt"
                v-model:selection="selectedGroups"
                :value="groups"
                dataKey="id"
                :paginator="true"
                :rows="10"
                :filters="filters"
                paginatorTemplate="FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink CurrentPageReport RowsPerPageDropdown"
                :rowsPerPageOptions="[5, 10, 25]"
                currentPageReportTemplate="Showing {first} to {last} of {totalRecords} groups"
                :loading="loading"
            >
                <template #empty> No groups found. </template>
                <template #header>
                    <div class="flex flex-wrap gap-2 items-center justify-between">
                        <h4 class="m-0">Manage Groups</h4>
                        <IconField>
                            <InputIcon>
                                <i class="pi pi-search" />
                            </InputIcon>
                            <InputText v-model="filters['global'].value" placeholder="Search..." />
                        </IconField>
                    </div>
                </template>

                <Column selectionMode="multiple" style="width: 3rem" :exportable="false"></Column>
                <Column field="name" header="Name" sortable style="min-width: 8rem"></Column>
                <Column field="description" header="Description" sortable style="min-width: 12rem"></Column>
                <Column field="owner.full_name" header="Owner" sortable style="min-width: 8rem">
                    <template #body="{ data }">
                        <Chip :label="data.owner?.full_name || data.owner?.username || 'Unknown'" :image="getAvatarUrl(data.owner?.avatar)" class="mr-2" />
                    </template>
                </Column>
                <Column field="user_names" header="Users" sortable style="min-width: 8rem">
                    <template #body="{ data }">
                        <AvatarGroup v-if="data.members && data.members.length > 0">
                            <Avatar v-for="member in data.members.slice(0, 4)" :key="member.id" :image="getAvatarUrl(member.avatar)" size="normal" shape="circle" />
                            <Avatar v-if="data.members.length > 4" :label="`+${data.members.length - 4}`" shape="circle" size="normal" :style="{ 'background-color': '#9c27b0', color: '#ffffff' }" />
                        </AvatarGroup>
                    </template>
                </Column>
                <Column field="created_at" header="Created At" sortable style="min-width: 8rem">
                    <template #body="{ data }">
                        {{ formatDateTime(new Date(data.created_at)) }}
                    </template>
                </Column>
                <Column :exportable="false" style="min-width: 8rem">
                    <template #body="slotProps">
                        <Button icon="pi pi-pencil" outlined rounded class="mr-2" @click="editGroup(slotProps.data)" />
                        <Button icon="pi pi-trash" outlined rounded severity="danger" @click="confirmDeleteGroup(slotProps.data)" />
                    </template>
                </Column>
            </DataTable>
        </div>

        <Dialog v-model:visible="groupDialog" :style="{ width: '450px' }" header="Group Details" :modal="true">
            <div class="flex flex-col gap-6">
                <div>
                    <label for="name" class="block font-bold mb-3">Name</label>
                    <InputText id="name" v-model.trim="group.name" required="true" autofocus :invalid="submitted && !group.name" fluid />
                    <small v-if="submitted && !group.name" class="text-red-500">Name is required.</small>
                </div>
                <div>
                    <label for="description" class="block font-bold mb-3">Description</label>
                    <Textarea id="description" v-model="group.description" required="true" rows="3" cols="20" fluid />
                </div>
                <div>
                    <label for="members" class="block font-bold mb-3">Members</label>
                    <MultiSelect id="members" v-model="group.members" :options="users" optionLabel="displayName" dataKey="id" placeholder="Select Members" filter fluid showClear>
                        <template #value="slotProps">
                            <div class="flex flex-wrap gap-2" v-if="slotProps.value && slotProps.value.length">
                                <Chip v-for="option in slotProps.value" :key="option.id" :label="option.displayName" :image="getAvatarUrl(option.avatar)" removable @remove="removeMember(option)" />
                            </div>
                            <template v-else>
                                {{ slotProps.placeholder }}
                            </template>
                        </template>
                        <template #option="slotProps">
                            <div class="flex items-center">
                                <Avatar :image="getAvatarUrl(slotProps.option.avatar)" shape="circle" size="small" class="mr-2" />
                                <span>{{ slotProps.option.displayName }}</span>
                            </div>
                        </template>
                    </MultiSelect>
                </div>
            </div>

            <template #footer>
                <Button label="Cancel" icon="pi pi-times" text @click="hideDialog" />
                <Button label="Save" icon="pi pi-check" @click="saveGroup" />
            </template>
        </Dialog>

        <Dialog v-model:visible="deleteGroupDialog" :style="{ width: '450px' }" header="Confirm" :modal="true">
            <div class="flex items-center gap-4">
                <i class="pi pi-exclamation-triangle !text-3xl" />
                <span v-if="group"
                    >Are you sure you want to delete <b>{{ group.name }}</b
                    >?</span
                >
            </div>
            <template #footer>
                <Button label="No" icon="pi pi-times" text @click="deleteGroupDialog = false" />
                <Button label="Yes" icon="pi pi-check" @click="deleteGroup" />
            </template>
        </Dialog>

        <Dialog v-model:visible="deleteGroupsDialog" :style="{ width: '450px' }" header="Confirm" :modal="true">
            <div class="flex items-center gap-4">
                <i class="pi pi-exclamation-triangle !text-3xl" />
                <span v-if="group">Are you sure you want to delete the selected groups?</span>
            </div>
            <template #footer>
                <Button label="No" icon="pi pi-times" text @click="deleteGroupsDialog = false" />
                <Button label="Yes" icon="pi pi-check" text @click="deleteSelectedGroups" />
            </template>
        </Dialog>
    </div>
</template>
