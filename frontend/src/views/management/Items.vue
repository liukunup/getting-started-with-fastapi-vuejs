<script setup>
import { ItemService } from '@/client';
import { FilterMatchMode } from '@primevue/core/api';
import { useToast } from 'primevue/usetoast';
import { onMounted, ref } from 'vue';

const toast = useToast();
const dt = ref();
const items = ref(null);
const itemDialog = ref(false);
const deleteItemDialog = ref(false);
const deleteItemsDialog = ref(false);
const item = ref({});
const selectedItems = ref();
const filters = ref({
    global: { value: null, matchMode: FilterMatchMode.CONTAINS }
});
const submitted = ref(false);
const loading = ref(true);

// 默认头像URL
const defaultAvatar = 'https://primefaces.org/cdn/primevue/images/avatar/amyelsner.png';

// 获取头像URL，如果没有则返回默认头像
const getAvatarUrl = (avatarUrl) => {
    return avatarUrl || defaultAvatar;
};

onMounted(() => {
    loadItems();
});

const loadItems = () => {
    loading.value = true;
    ItemService.readItems().then((data) => {
        items.value = data.items;
        loading.value = false;
    });
};

const formatCurrency = (value) => {
    if (value) return value.toLocaleString('en-US', { style: 'currency', currency: 'USD' });
    return;
};

const formatDate = (value) => {
    if (!value) return '';
    return value.toLocaleDateString('en-US', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
    });
};

const openNew = () => {
    item.value = {};
    submitted.value = false;
    itemDialog.value = true;
};

const hideDialog = () => {
    itemDialog.value = false;
    submitted.value = false;
};

const saveItem = async () => {
    submitted.value = true;

    if (item.value.name && item.value.name.trim()) {
        try {
            const payload = { ...item.value };
            if (item.value.id) {
                await ItemService.updateItem({ itemId: item.value.id, requestBody: payload });
                toast.add({ severity: 'success', summary: 'Successful', detail: 'Item Updated', life: 3000 });
            } else {
                await ItemService.createItem({ requestBody: payload });
                toast.add({ severity: 'success', summary: 'Successful', detail: 'Item Created', life: 3000 });
            }
            itemDialog.value = false;
            item.value = {};
            loadItems();
        } catch (error) {
            toast.add({ severity: 'error', summary: 'Error', detail: error.message, life: 3000 });
        }
    }
};

const editItem = (editItem) => {
    item.value = { ...editItem };
    itemDialog.value = true;
};

const confirmDeleteItem = (deleteItem) => {
    item.value = deleteItem;
    deleteItemDialog.value = true;
};

const deleteItem = async () => {
    try {
        await ItemService.deleteItem({ itemId: item.value.id });
        deleteItemDialog.value = false;
        item.value = {};
        toast.add({ severity: 'success', summary: 'Successful', detail: 'Item Deleted', life: 3000 });
        loadItems();
    } catch (error) {
        toast.add({ severity: 'error', summary: 'Error', detail: error.message, life: 3000 });
    }
};

const exportCSV = () => {
    dt.value.exportCSV();
};

const confirmDeleteSelected = () => {
    deleteItemsDialog.value = true;
};

const deleteSelectedItems = async () => {
    try {
        // Assuming we process deletions sequentially or in parallel
        await Promise.all(selectedItems.value.map((val) => ItemService.deleteItem({ itemId: val.id })));
        deleteItemsDialog.value = false;
        selectedItems.value = null;
        toast.add({ severity: 'success', summary: 'Successful', detail: 'Items Deleted', life: 3000 });
        loadItems();
    } catch (error) {
        toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to delete some items', life: 3000 });
    }
};
</script>

<template>
    <div>
        <div class="card">
            <Toolbar class="mb-6">
                <template #start>
                    <Button label="New" icon="pi pi-plus" severity="secondary" class="mr-2" @click="openNew" />
                    <Button label="Delete" icon="pi pi-trash" severity="secondary" @click="confirmDeleteSelected" :disabled="!selectedItems || !selectedItems.length" />
                </template>

                <template #end>
                    <Button label="Export" icon="pi pi-upload" severity="secondary" @click="exportCSV($event)" />
                </template>
            </Toolbar>

            <DataTable
                ref="dt"
                v-model:selection="selectedItems"
                :value="items"
                dataKey="id"
                :paginator="true"
                :rows="10"
                :filters="filters"
                paginatorTemplate="FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink CurrentPageReport RowsPerPageDropdown"
                :rowsPerPageOptions="[5, 10, 25]"
                currentPageReportTemplate="Showing {first} to {last} of {totalRecords} items"
                :loading="loading"
            >
                <template #empty> No items found. </template>
                <template #header>
                    <div class="flex flex-wrap gap-2 items-center justify-between">
                        <h4 class="m-0">Manage Items</h4>
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
                <Column field="owner.full_name" header="Owner" sortable style="min-width: 10rem">
                    <template #body="{ data }">
                        <Chip :label="data.owner?.full_name || data.owner?.username || 'Unknown'" :image="getAvatarUrl(data.owner?.avatar)" class="mr-2" />
                    </template>
                </Column>
                <Column field="created_at" header="Created At" sortable style="min-width: 12rem">
                    <template #body="{ data }">
                        {{ formatDate(new Date(data.created_at)) }}
                    </template>
                </Column>
                <Column :exportable="false" style="min-width: 12rem">
                    <template #body="slotProps">
                        <Button icon="pi pi-pencil" outlined rounded class="mr-2" @click="editItem(slotProps.data)" />
                        <Button icon="pi pi-trash" outlined rounded severity="danger" @click="confirmDeleteItem(slotProps.data)" />
                    </template>
                </Column>
            </DataTable>
        </div>

        <Dialog v-model:visible="itemDialog" :style="{ width: '450px' }" header="Item Details" :modal="true">
            <div class="flex flex-col gap-6">
                <div>
                    <label for="name" class="block font-bold mb-3">Name</label>
                    <InputText id="name" v-model.trim="item.name" required="true" autofocus :invalid="submitted && !item.name" fluid />
                    <small v-if="submitted && !item.name" class="text-red-500">Name is required.</small>
                </div>
                <div>
                    <label for="description" class="block font-bold mb-3">Description</label>
                    <Textarea id="description" v-model="item.description" required="true" rows="3" cols="20" fluid />
                </div>
            </div>

            <template #footer>
                <Button label="Cancel" icon="pi pi-times" text @click="hideDialog" />
                <Button label="Save" icon="pi pi-check" @click="saveItem" />
            </template>
        </Dialog>

        <Dialog v-model:visible="deleteItemDialog" :style="{ width: '450px' }" header="Confirm" :modal="true">
            <div class="flex items-center gap-4">
                <i class="pi pi-exclamation-triangle !text-3xl" />
                <span v-if="item"
                    >Are you sure you want to delete <b>{{ item.name }}</b
                    >?</span
                >
            </div>
            <template #footer>
                <Button label="No" icon="pi pi-times" text @click="deleteItemDialog = false" />
                <Button label="Yes" icon="pi pi-check" @click="deleteItem" />
            </template>
        </Dialog>

        <Dialog v-model:visible="deleteItemsDialog" :style="{ width: '450px' }" header="Confirm" :modal="true">
            <div class="flex items-center gap-4">
                <i class="pi pi-exclamation-triangle !text-3xl" />
                <span v-if="item">Are you sure you want to delete the selected items?</span>
            </div>
            <template #footer>
                <Button label="No" icon="pi pi-times" text @click="deleteItemsDialog = false" />
                <Button label="Yes" icon="pi pi-check" text @click="deleteSelectedItems" />
            </template>
        </Dialog>
    </div>
</template>
