<script setup>
import { TaskService } from '@/client';
import { FilterMatchMode, FilterOperator } from '@primevue/core/api';
import { useToast } from 'primevue/usetoast';
import { onMounted, ref } from 'vue';

const toast = useToast();
const dt = ref();
const executions = ref([]);
const filters = ref(null);
const loading = ref(true);
const globalFilterValue = ref('');
const deleteExecutionDialog = ref(false);
const executionToDelete = ref(null);
const executionDialog = ref(false);
const selectedExecution = ref(null);

// 执行状态选项
const executionStatuses = [
    { label: '等待中', value: 'pending' },
    { label: '已开始', value: 'started' },
    { label: '成功', value: 'success' },
    { label: '失败', value: 'failure' },
    { label: '重试', value: 'retry' },
    { label: '已撤销', value: 'revoked' }
];

onMounted(() => {
    initFilters();
    loadExecutions();
});

const initFilters = () => {
    filters.value = {
        global: { value: null, matchMode: FilterMatchMode.CONTAINS },
        task_name: { operator: FilterOperator.AND, constraints: [{ value: null, matchMode: FilterMatchMode.CONTAINS }] },
        celery_task_id: { operator: FilterOperator.AND, constraints: [{ value: null, matchMode: FilterMatchMode.CONTAINS }] },
        status: { value: null, matchMode: FilterMatchMode.EQUALS },
        worker: { operator: FilterOperator.AND, constraints: [{ value: null, matchMode: FilterMatchMode.CONTAINS }] },
        started_at: { operator: FilterOperator.AND, constraints: [{ value: null, matchMode: FilterMatchMode.DATE_IS }] },
        completed_at: { operator: FilterOperator.AND, constraints: [{ value: null, matchMode: FilterMatchMode.DATE_IS }] }
    };
};

const clearFilter = () => {
    initFilters();
    globalFilterValue.value = '';
};

const onGlobalFilterChange = (value) => {
    filters.value['global'].value = value;
};

const loadExecutions = async () => {
    loading.value = true;
    try {
        const data = await TaskService.getAllTaskExecutions({ skip: 0, limit: 100 });
        executions.value = data.executions || [];
        loading.value = false;
    } catch (error) {
        console.error('Load executions error:', error);
        toast.add({ severity: 'error', summary: 'Error', detail: error.message, life: 3000 });
        executions.value = [];
        loading.value = false;
    }
};

const formatDate = (value) => {
    if (!value) return '';
    return new Date(value).toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
};

const getStatusLabel = (status) => {
    const statusObj = executionStatuses.find((s) => s.value === status);
    return statusObj ? statusObj.label : status;
};

const getStatusSeverity = (status) => {
    switch (status) {
        case 'pending':
            return 'info';
        case 'started':
            return 'warn';
        case 'success':
            return 'success';
        case 'failure':
            return 'danger';
        case 'retry':
            return 'warn';
        case 'revoked':
            return 'secondary';
        default:
            return 'info';
    }
};

const formatRuntime = (runtime) => {
    if (!runtime) return '-';
    if (runtime < 1) return `${(runtime * 1000).toFixed(0)}ms`;
    return `${runtime.toFixed(2)}s`;
};

const exportCSV = () => {
    dt.value.exportCSV();
};

const confirmDeleteExecution = (execution) => {
    executionToDelete.value = execution;
    deleteExecutionDialog.value = true;
};

const openExecutionDialog = (execution) => {
    selectedExecution.value = execution;
    executionDialog.value = true;
};

const deleteExecutionConfirmed = async () => {
    try {
        await TaskService.deleteExecution({ executionId: executionToDelete.value.id });
        executions.value = executions.value.filter((e) => e.id !== executionToDelete.value.id);
        deleteExecutionDialog.value = false;
        executionToDelete.value = null;
        toast.add({ severity: 'success', summary: 'Success', detail: 'Execution deleted successfully', life: 3000 });
    } catch (error) {
        console.error('Delete execution error:', error);
        toast.add({ severity: 'error', summary: 'Error', detail: error.message, life: 3000 });
    }
};
</script>

<template>
    <div class="card">
        <div class="font-semibold text-xl mb-4">Task Executions (Total: {{ executions.length }})</div>
        <DataTable
            ref="dt"
            :value="executions"
            dataKey="id"
            :paginator="true"
            :rows="10"
            v-model:filters="filters"
            filterDisplay="menu"
            :loading="loading"
            :globalFilterFields="['task_name', 'celery_task_id', 'status', 'worker']"
            :rowsPerPageOptions="[5, 10, 25, 50]"
            paginatorTemplate="FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink CurrentPageReport RowsPerPageDropdown"
            currentPageReportTemplate="Showing {first} to {last} of {totalRecords} executions"
            :rowHover="true"
            sortField="created_at"
            :sortOrder="-1"
        >
            <template #header>
                <div class="flex justify-between">
                    <Button type="button" icon="pi pi-filter-slash" label="Clear" outlined @click="clearFilter()" />
                    <div class="flex gap-2">
                        <IconField>
                            <InputIcon>
                                <i class="pi pi-search" />
                            </InputIcon>
                            <InputText v-model="globalFilterValue" @input="onGlobalFilterChange($event.target.value)" placeholder="Keyword Search" />
                        </IconField>
                        <Button label="Refresh" icon="pi pi-refresh" severity="secondary" @click="loadExecutions" />
                        <Button label="Export" icon="pi pi-upload" severity="secondary" @click="exportCSV($event)" />
                    </div>
                </div>
            </template>
            <template #empty> No execution records found. </template>
            <template #loading> Loading execution data. Please wait. </template>

            <Column field="task_name" header="Task Name" sortable style="min-width: 12rem">
                <template #body="{ data }">
                    <span>{{ data.task_name || '-' }}</span>
                </template>
                <template #filter="{ filterModel }">
                    <InputText v-model="filterModel.value" type="text" placeholder="Search by task name" />
                </template>
            </Column>

            <Column field="celery_task_id" header="Task ID" sortable style="min-width: 20rem" >
                <template #body="{ data }">
                    <span class="text-xs font-mono font-semibold text-primary cursor-pointer hover:underline" @click="openExecutionDialog(data)">{{ data.celery_task_id }}</span>
                </template>
                <template #filter="{ filterModel }">
                    <InputText v-model="filterModel.value" type="text" placeholder="Search by task ID" />
                </template>
            </Column>

            <Column field="status" header="Status" sortable :filterMenuStyle="{ width: '14rem' }" style="min-width: 8rem" >
                <template #body="{ data }">
                    <Tag :value="getStatusLabel(data.status)" :severity="getStatusSeverity(data.status)" />
                </template>
                <template #filter="{ filterModel }">
                    <Select v-model="filterModel.value" :options="executionStatuses" optionValue="value" optionLabel="label" placeholder="Select Status" showClear>
                        <template #option="slotProps">
                            <Tag :value="slotProps.option.label" :severity="getStatusSeverity(slotProps.option.value)" />
                        </template>
                    </Select>
                </template>
            </Column>

            <Column field="runtime" header="Runtime" sortable style="min-width: 8rem" >
                <template #body="{ data }">
                    <span class="text-sm font-semibold">{{ formatRuntime(data.runtime) }}</span>
                </template>
            </Column>
            
            <Column field="created_at" header="Created At" sortable style="min-width: 12rem" >
                <template #body="{ data }">
                    <span class="text-sm">{{ data.created_at ? formatDate(data.created_at) : '-' }}</span>
                </template>
            </Column>

            <Column field="started_at" header="Started At" sortable dataType="date" style="min-width: 12rem" >
                <template #body="{ data }">
                    <span class="text-sm">{{ data.started_at ? formatDate(data.started_at) : '-' }}</span>
                </template>
            </Column>

            <Column field="completed_at" header="Completed At" sortable dataType="date" style="min-width: 12rem" >
                <template #body="{ data }">
                    <span class="text-sm">{{ data.completed_at ? formatDate(data.completed_at) : '-' }}</span>
                </template>
            </Column>

            <Column :exportable="false" style="min-width: 3rem" >
                <template #body="{ data }">
                    <Button icon="pi pi-trash" outlined rounded severity="danger" @click="confirmDeleteExecution(data)" v-tooltip="'Delete execution'" />
                </template>
            </Column>
        </DataTable>

        <!-- Delete Confirmation Dialog -->
        <Dialog v-model:visible="deleteExecutionDialog" :style="{ width: '450px' }" header="Confirm" :modal="true">
            <div class="flex items-center gap-4">
                <i class="pi pi-exclamation-triangle !text-3xl" />
                <span v-if="executionToDelete">Are you sure you want to delete this execution record?</span>
            </div>
            <template #footer>
                <Button label="No" icon="pi pi-times" text @click="deleteExecutionDialog = false" />
                <Button label="Yes" icon="pi pi-check" severity="danger" @click="deleteExecutionConfirmed" />
            </template>
        </Dialog>

        <!-- Execution Details Dialog -->
        <Dialog v-model:visible="executionDialog" :style="{ width: '600px' }" header="Execution Details" :modal="true" class="p-fluid">
            <div v-if="selectedExecution" class="flex flex-col gap-4">
                <div class="grid grid-cols-12 gap-2">
                    <div class="col-span-4 font-semibold">Task Name:</div>
                    <div class="col-span-8">{{ selectedExecution.task_name || '-' }}</div>

                    <div class="col-span-4 font-semibold">Celery Task Name:</div>
                    <div class="col-span-8 font-mono text-sm">{{ selectedExecution.celery_task_name || '-' }}</div>
                    
                    <div class="col-span-4 font-semibold">Task ID:</div>
                    <div class="col-span-8 font-mono text-sm">{{ selectedExecution.celery_task_id }}</div>
                    
                    <div class="col-span-4 font-semibold">Status:</div>
                    <div class="col-span-8">
                        <Tag :value="getStatusLabel(selectedExecution.status)" :severity="getStatusSeverity(selectedExecution.status)" />
                    </div>
                    
                    <div class="col-span-4 font-semibold">Worker:</div>
                    <div class="col-span-8">{{ selectedExecution.worker || '-' }}</div>
                    
                    <div class="col-span-4 font-semibold">Started At:</div>
                    <div class="col-span-8">{{ formatDate(selectedExecution.started_at) }}</div>
                    
                    <div class="col-span-4 font-semibold">Completed At:</div>
                    <div class="col-span-8">{{ formatDate(selectedExecution.completed_at) }}</div>
                    
                    <div class="col-span-4 font-semibold">Runtime:</div>
                    <div class="col-span-8">{{ formatRuntime(selectedExecution.runtime) }}</div>
                </div>

                <div v-if="selectedExecution.celery_task_args">
                    <div class="font-semibold mb-2">Args:</div>
                    <div class="bg-gray-100 dark:bg-gray-800 p-2 rounded overflow-auto max-h-32 font-mono text-sm">
                        {{ selectedExecution.celery_task_args }}
                    </div>
                </div>

                <div v-if="selectedExecution.celery_task_kwargs">
                    <div class="font-semibold mb-2">Kwargs:</div>
                    <div class="bg-gray-100 dark:bg-gray-800 p-2 rounded overflow-auto max-h-32 font-mono text-sm">
                        {{ selectedExecution.celery_task_kwargs }}
                    </div>
                </div>

                <div v-if="selectedExecution.result">
                    <div class="font-semibold mb-2">Result:</div>
                    <div class="bg-gray-100 dark:bg-gray-800 p-2 rounded overflow-auto max-h-48 font-mono text-sm whitespace-pre-wrap">
                        {{ selectedExecution.result }}
                    </div>
                </div>

                <div v-if="selectedExecution.traceback">
                    <div class="font-semibold mb-2 text-red-500">Traceback:</div>
                    <div class="bg-red-50 dark:bg-red-900/20 p-2 rounded overflow-auto max-h-64 font-mono text-sm whitespace-pre-wrap text-red-700 dark:text-red-400">
                        {{ selectedExecution.traceback }}
                    </div>
                </div>
            </div>
            <template #footer>
                <Button label="Close" icon="pi pi-times" text @click="executionDialog = false" />
            </template>
        </Dialog>
    </div>
</template>
