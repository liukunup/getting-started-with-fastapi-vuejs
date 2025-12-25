<script setup>
import { TaskService } from '@/client';
import { FilterMatchMode } from '@primevue/core/api';
import * as cronstruePkg from 'cronstrue/i18n';
import { useToast } from 'primevue/usetoast';
import { onMounted, ref, computed } from 'vue';

const cronstrue = cronstruePkg.default || cronstruePkg;

const toast = useToast();
const dt = ref();
const tasks = ref(null);
const taskDialog = ref(false);
const deleteTaskDialog = ref(false);
const deleteTasksDialog = ref(false);
const executionsDialog = ref(false);
const task = ref({});
const selectedTasks = ref();
const filters = ref({
    global: { value: null, matchMode: FilterMatchMode.CONTAINS }
});
const submitted = ref(false);
const loading = ref(true);

// 执行记录相关
const executions = ref([]);
const executionsLoading = ref(false);
const selectedTaskForExecutions = ref(null);

// 任务类型选项
const taskTypes = [
    { label: '异步任务', value: 'async' },
    { label: '定时任务', value: 'scheduled' },
    { label: '周期任务', value: 'periodic' }
];

// 周期调度类型选项
const periodicScheduleTypes = [
    { label: 'Crontab', value: 'crontab' },
    { label: 'Interval', value: 'interval' }
];

// 预定义的Celery任务
const predefinedTasks = ref([]);
const loadingTasks = ref(false);

// 加载已注册的Celery任务
const loadRegisteredTasks = async () => {
    loadingTasks.value = true;
    try {
        const tasks = await TaskService.getRegisteredTasks();
        predefinedTasks.value = tasks.map((task) => ({ label: task, value: task }));
    } catch (error) {
        console.error('Failed to load registered tasks:', error);
        // 使用默认任务列表
        predefinedTasks.value = [
            { label: 'demo_task', value: 'demo_task' },
            { label: 'demo_dynamic_task', value: 'demo_dynamic_task' }
        ];
    } finally {
        loadingTasks.value = false;
    }
};

// 任务状态
const taskStatuses = [
    { label: '等待中', value: 'pending', severity: 'info' },
    { label: '已开始', value: 'started', severity: 'warning' },
    { label: '运行中', value: 'running', severity: 'warning' },
    { label: '成功', value: 'success', severity: 'success' },
    { label: '失败', value: 'failed', severity: 'danger' },
    { label: '已撤销', value: 'revoked', severity: 'secondary' },
    { label: '已禁用', value: 'disabled', severity: 'secondary' }
];

// 执行状态
const executionStatuses = [
    { label: '等待中', value: 'pending', severity: 'info' },
    { label: '已开始', value: 'started', severity: 'warning' },
    { label: '运行中', value: 'running', severity: 'warning' },
    { label: '成功', value: 'success', severity: 'success' },
    { label: '失败', value: 'failed', severity: 'danger' },
    { label: '已撤销', value: 'revoked', severity: 'secondary' },
    { label: '已禁用', value: 'disabled', severity: 'secondary' }
];

// 计算属性：是否显示定时配置
const showScheduledTime = computed(() => {
    return task.value.task_type === 'scheduled';
});

const showPeriodicConfig = computed(() => {
    return task.value.task_type === 'periodic';
});

const showCrontab = computed(() => {
    return task.value.task_type === 'periodic' && task.value.periodic_schedule_type === 'crontab';
});

const showInterval = computed(() => {
    return task.value.task_type === 'periodic' && task.value.periodic_schedule_type === 'interval';
});

const crontabDescription = computed(() => {
    if (!showCrontab.value) return '';

    const minute = task.value.crontab_minute || '*';
    const hour = task.value.crontab_hour || '*';
    const dayOfMonth = task.value.crontab_day_of_month || '*';
    const month = task.value.crontab_month_of_year || '*';
    const dayOfWeek = task.value.crontab_day_of_week || '*';

    const cronExpression = `${minute} ${hour} ${dayOfMonth} ${month} ${dayOfWeek}`;

    try {
        return cronstrue.toString(cronExpression, { locale: 'zh_CN' });
    } catch (e) {
        return '无效的 Crontab 表达式';
    }
});

onMounted(() => {
    loadRegisteredTasks();
    loadTasks();
});

const loadTasks = () => {
    loading.value = true;
    TaskService.readTasks()
        .then((data) => {
            tasks.value = data.tasks;
            loading.value = false;
        })
        .catch((error) => {
            toast.add({ severity: 'error', summary: 'Error', detail: error.message, life: 3000 });
            loading.value = false;
        });
};

const formatDate = (value) => {
    if (!value) return '';
    const dateStr = value.endsWith('Z') || value.includes('+') ? value : value + 'Z';
    return new Date(dateStr).toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false
    });
};

const getStatusLabel = (status) => {
    const statusObj = taskStatuses.find((s) => s.value === status);
    return statusObj ? statusObj.label : status;
};

const getStatusSeverity = (status) => {
    const statusObj = taskStatuses.find((s) => s.value === status);
    return statusObj ? statusObj.severity : 'info';
};

const openNew = () => {
    task.value = {
        task_type: 'async',
        celery_task_name: '',
        celery_task_args: '[]',
        celery_task_kwargs: '{}',
        enabled: true,
        periodic_schedule_type: 'crontab',
        crontab_minute: '*',
        crontab_hour: '*',
        crontab_day_of_week: '*',
        crontab_day_of_month: '*',
        crontab_month_of_year: '*',
        interval_seconds: null,
        interval_minutes: null,
        interval_hours: null,
        interval_days: null
    };
    submitted.value = false;
    taskDialog.value = true;
};

const hideDialog = () => {
    taskDialog.value = false;
    submitted.value = false;
};

const validateTask = () => {
    if (!task.value.name || !task.value.name.trim()) {
        toast.add({ severity: 'error', summary: 'Error', detail: 'Task name is required', life: 3000 });
        return false;
    }
    if (!task.value.celery_task_name) {
        toast.add({ severity: 'error', summary: 'Error', detail: 'Celery task name is required', life: 3000 });
        return false;
    }
    if (task.value.task_type === 'scheduled' && !task.value.scheduled_time) {
        toast.add({ severity: 'error', summary: 'Error', detail: 'Scheduled time is required for scheduled tasks', life: 3000 });
        return false;
    }

    // 验证JSON格式
    try {
        if (task.value.celery_task_args) {
            JSON.parse(task.value.celery_task_args);
        }
        if (task.value.celery_task_kwargs) {
            JSON.parse(task.value.celery_task_kwargs);
        }
    } catch (e) {
        toast.add({ severity: 'error', summary: 'Error', detail: 'Invalid JSON format for args or kwargs', life: 3000 });
        return false;
    }

    return true;
};

const saveTask = async () => {
    submitted.value = true;

    if (!validateTask()) {
        return;
    }

    try {
        const payload = { ...task.value };

        // 转换日期格式
        if (payload.scheduled_time) {
            payload.scheduled_time = new Date(payload.scheduled_time).toISOString();
        }

        if (task.value.id) {
            await TaskService.updateTask({ taskId: task.value.id, requestBody: payload });
            toast.add({ severity: 'success', summary: 'Successful', detail: 'Task Updated', life: 3000 });
        } else {
            await TaskService.createTask({ requestBody: payload });
            toast.add({ severity: 'success', summary: 'Successful', detail: 'Task Created', life: 3000 });
        }
        taskDialog.value = false;
        task.value = {};
        loadTasks();
    } catch (error) {
        toast.add({ severity: 'error', summary: 'Error', detail: error.message, life: 3000 });
    }
};

const editTask = (editTask) => {
    task.value = { ...editTask };
    // 转换日期格式用于显示 - DatePicker需要Date对象
    if (task.value.scheduled_time) {
        task.value.scheduled_time = new Date(task.value.scheduled_time);
    }
    taskDialog.value = true;
};

const confirmDeleteTask = (deleteTask) => {
    task.value = deleteTask;
    deleteTaskDialog.value = true;
};

const deleteTask = async () => {
    try {
        await TaskService.deleteTask({ taskId: task.value.id });
        deleteTaskDialog.value = false;
        task.value = {};
        toast.add({ severity: 'success', summary: 'Successful', detail: 'Task Deleted', life: 3000 });
        loadTasks();
    } catch (error) {
        toast.add({ severity: 'error', summary: 'Error', detail: error.message, life: 3000 });
    }
};

const executeTask = async (taskItem) => {
    try {
        await TaskService.triggerTask({ taskId: taskItem.id });
        toast.add({ severity: 'success', summary: 'Successful', detail: 'Task execution triggered', life: 3000 });
        loadTasks();
    } catch (error) {
        toast.add({ severity: 'error', summary: 'Error', detail: error.message, life: 3000 });
    }
};

const toggleTaskStatus = async (taskItem) => {
    try {
        if (taskItem.enabled) {
            await TaskService.disableTask({ taskId: taskItem.id });
            toast.add({ severity: 'success', summary: 'Successful', detail: 'Task disabled', life: 3000 });
        } else {
            await TaskService.enableTask({ taskId: taskItem.id });
            toast.add({ severity: 'success', summary: 'Successful', detail: 'Task enabled', life: 3000 });
        }
        loadTasks();
    } catch (error) {
        toast.add({ severity: 'error', summary: 'Error', detail: error.message, life: 3000 });
    }
};

const exportCSV = () => {
    dt.value.exportCSV();
};

const confirmDeleteSelected = () => {
    deleteTasksDialog.value = true;
};

const deleteSelectedTasks = async () => {
    try {
        await Promise.all(selectedTasks.value.map((val) => TaskService.deleteTask({ taskId: val.id })));
        deleteTasksDialog.value = false;
        selectedTasks.value = null;
        toast.add({ severity: 'success', summary: 'Successful', detail: 'Tasks Deleted', life: 3000 });
        loadTasks();
    } catch (error) {
        toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to delete some tasks', life: 3000 });
    }
};

const getCrontabDisplay = (taskItem) => {
    if (taskItem.task_type !== 'periodic') return '-';

    if (taskItem.periodic_schedule_type === 'interval') {
        const parts = [];
        if (taskItem.interval_days) parts.push(`${taskItem.interval_days}天`);
        if (taskItem.interval_hours) parts.push(`${taskItem.interval_hours}小时`);
        if (taskItem.interval_minutes) parts.push(`${taskItem.interval_minutes}分钟`);
        if (taskItem.interval_seconds) parts.push(`${taskItem.interval_seconds}秒`);
        return parts.length > 0 ? `每 ${parts.join(' ')}` : '-';
    }

    return `${taskItem.crontab_minute || '*'} ${taskItem.crontab_hour || '*'} ${taskItem.crontab_day_of_month || '*'} ${taskItem.crontab_month_of_year || '*'} ${taskItem.crontab_day_of_week || '*'}`;
};

const viewExecutions = async (taskItem) => {
    selectedTaskForExecutions.value = taskItem;
    executionsLoading.value = true;
    executionsDialog.value = true;

    try {
        const response = await TaskService.getTaskExecutions({ taskId: taskItem.id });
        executions.value = response.executions || [];
    } catch (error) {
        toast.add({ severity: 'error', summary: 'Error', detail: error.message, life: 3000 });
    } finally {
        executionsLoading.value = false;
    }
};

const getExecutionStatusLabel = (status) => {
    const statusObj = executionStatuses.find((s) => s.value === status);
    return statusObj ? statusObj.label : status;
};

const getExecutionStatusSeverity = (status) => {
    const statusObj = executionStatuses.find((s) => s.value === status);
    return statusObj ? statusObj.severity : 'info';
};

const formatRuntime = (runtime) => {
    if (!runtime) return '-';
    if (runtime < 1) return `${(runtime * 1000).toFixed(0)}ms`;
    return `${runtime.toFixed(2)}s`;
};

const setNow = () => {
    task.value.scheduled_time = new Date();
};
</script>

<template>
    <div>
        <div class="card">
            <Toolbar class="mb-6">
                <template #start>
                    <Button label="New" icon="pi pi-plus" severity="secondary" class="mr-2" @click="openNew" />
                    <Button label="Delete" icon="pi pi-trash" severity="secondary" @click="confirmDeleteSelected" :disabled="!selectedTasks || !selectedTasks.length" />
                </template>

                <template #end>
                    <Button label="Export" icon="pi pi-upload" severity="secondary" @click="exportCSV($event)" />
                </template>
            </Toolbar>

            <DataTable
                ref="dt"
                v-model:selection="selectedTasks"
                :value="tasks"
                dataKey="id"
                :paginator="true"
                :rows="10"
                :filters="filters"
                paginatorTemplate="FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink CurrentPageReport RowsPerPageDropdown"
                :rowsPerPageOptions="[5, 10, 25]"
                currentPageReportTemplate="Showing {first} to {last} of {totalRecords} tasks"
                :loading="loading"
            >
                <template #empty> No tasks found. </template>
                <template #header>
                    <div class="flex flex-wrap gap-2 items-center justify-between">
                        <h4 class="m-0">Manage Tasks</h4>
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
                <Column field="celery_task_name" header="Celery Task" sortable style="min-width: 16rem">
                    <template #body="{ data }">
                        <span>{{ data.celery_task_name }}</span>
                    </template>
                </Column>
                <Column header="Schedule" style="min-width: 12rem">
                    <template #body="{ data }">
                        <span v-if="data.task_type === 'scheduled'">
                            {{ formatDate(data.scheduled_time) }}
                        </span>
                        <span v-else-if="data.task_type === 'periodic'">
                            {{ getCrontabDisplay(data) }}
                        </span>
                        <span v-else>立即执行</span>
                    </template>
                </Column>
                <Column field="task_type" header="Type" sortable style="min-width: 8rem">
                    <template #body="{ data }">
                        <Tag :value="data.task_type === 'async' ? '异步' : data.task_type === 'scheduled' ? '定时' : '周期'" :severity="data.task_type === 'async' ? 'info' : data.task_type === 'scheduled' ? 'warning' : 'success'" />
                    </template>
                </Column>
                <Column field="status" header="Status" sortable style="min-width: 8rem">
                    <template #body="{ data }">
                        <Tag :value="getStatusLabel(data.status)" :severity="getStatusSeverity(data.status)" />
                    </template>
                </Column>
                <Column field="enabled" header="Enabled" sortable style="min-width: 8rem">
                    <template #body="{ data }">
                        <Tag :value="data.enabled ? 'Yes' : 'No'" :severity="data.enabled ? 'success' : 'danger'" />
                    </template>
                </Column>
                <Column field="last_run_time" header="Last Run" sortable style="min-width: 12rem">
                    <template #body="{ data }">
                        <span class="text-sm">{{ data.last_run_time ? formatDate(data.last_run_time) : '-' }}</span>
                    </template>
                </Column>
                <Column :exportable="false" style="min-width: 18rem">
                    <template #body="slotProps">
                        <Button icon="pi pi-history" outlined rounded class="mr-2" @click="viewExecutions(slotProps.data)" v-tooltip="'View Executions'" severity="secondary" />
                        <Button icon="pi pi-play" outlined rounded class="mr-2" @click="executeTask(slotProps.data)" v-tooltip="'Execute'" :disabled="!slotProps.data.enabled" />
                        <Button
                            :icon="slotProps.data.enabled ? 'pi pi-pause' : 'pi pi-play-circle'"
                            outlined
                            rounded
                            class="mr-2"
                            @click="toggleTaskStatus(slotProps.data)"
                            :severity="slotProps.data.enabled ? 'warning' : 'success'"
                            v-tooltip="slotProps.data.enabled ? 'Disable' : 'Enable'"
                        />
                        <Button icon="pi pi-pencil" outlined rounded class="mr-2" @click="editTask(slotProps.data)" />
                        <Button icon="pi pi-trash" outlined rounded severity="danger" @click="confirmDeleteTask(slotProps.data)" />
                    </template>
                </Column>
            </DataTable>
        </div>

        <Dialog v-model:visible="taskDialog" :style="{ width: '600px' }" header="Task Details" :modal="true">
            <div class="flex flex-col gap-6">
                <div>
                    <label for="name" class="block font-bold mb-3">Name</label>
                    <InputText id="name" v-model.trim="task.name" required="true" autofocus :invalid="submitted && !task.name" fluid />
                    <small v-if="submitted && !task.name" class="text-red-500">Name is required.</small>
                </div>

                <div>
                    <label for="description" class="block font-bold mb-3">Description</label>
                    <Textarea id="description" v-model="task.description" rows="2" fluid />
                </div>

                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <label for="task_type" class="block font-bold mb-3">Task Type</label>
                        <Select id="task_type" v-model="task.task_type" :options="taskTypes" optionLabel="label" optionValue="value" placeholder="Select Type" fluid />
                    </div>

                    <div class="flex flex-col">
                        <label class="block font-bold mb-3">Enable Task</label>
                        <div class="flex items-center flex-1">
                            <Checkbox id="enabled" v-model="task.enabled" :binary="true" />
                            <label for="enabled" class="ml-2">{{ task.enabled ? 'Enabled' : 'Disabled' }}</label>
                        </div>
                    </div>
                </div>

                <div>
                    <label for="celery_task_name" class="block font-bold mb-3">Celery Task Name</label>
                    <Select id="celery_task_name" v-model="task.celery_task_name" :options="predefinedTasks" optionLabel="label" optionValue="value" placeholder="Select or enter task name" editable fluid />
                </div>

                <div v-if="showScheduledTime">
                    <label for="scheduled_time" class="block font-bold mb-3">Scheduled Time</label>
                    <div class="flex gap-2 items-start">
                        <div class="flex-1">
                            <DatePicker
                                id="scheduled_time"
                                v-model="task.scheduled_time"
                                :showIcon="true"
                                :showButtonBar="true"
                                :showTime="true"
                                :showSeconds="true"
                                hourFormat="24"
                                dateFormat="yy/mm/dd"
                                placeholder="选择日期时间或直接粘贴"
                                fluid
                                :manualInput="true"
                            />
                        </div>
                        <Button label="此刻" icon="pi pi-clock" @click="setNow" outlined severity="info" v-tooltip="'设置为当前时间'" />
                    </div>
                    <small class="text-gray-500 mt-1 block"> 支持选择年月日时分秒，可直接粘贴日期时间字符串（如：2024-12-02 14:30:00） </small>
                </div>

                <!-- 周期任务配置 -->
                <div v-if="showPeriodicConfig">
                    <label for="periodic_schedule_type" class="block font-bold mb-3">调度类型</label>
                    <Select id="periodic_schedule_type" v-model="task.periodic_schedule_type" :options="periodicScheduleTypes" optionLabel="label" optionValue="value" placeholder="选择调度类型" fluid />
                </div>

                <div v-if="showCrontab" class="border p-4 rounded">
                    <div class="grid grid-cols-5 gap-2 text-xs mb-2">
                        <span class="text-center font-semibold">Minute</span>
                        <span class="text-center font-semibold">Hour</span>
                        <span class="text-center font-semibold">Day of Month</span>
                        <span class="text-center font-semibold">Month of Year</span>
                        <span class="text-center font-semibold">Day of Week</span>
                    </div>
                    <div class="grid grid-cols-5 gap-2">
                        <InputText v-model="task.crontab_minute" placeholder="*" />
                        <InputText v-model="task.crontab_hour" placeholder="*" />
                        <InputText v-model="task.crontab_day_of_month" placeholder="*" />
                        <InputText v-model="task.crontab_month_of_year" placeholder="*" />
                        <InputText v-model="task.crontab_day_of_week" placeholder="*" />
                    </div>
                    <div class="mt-2 p-2 bg-gray-50 rounded text-sm text-gray-700"><span class="font-semibold">含义：</span> {{ crontabDescription }}</div>
                    <small class="text-gray-500 mt-2 block">Use * for any value, numbers for specific values, or cron expressions</small>
                </div>

                <div v-if="showInterval" class="border p-4 rounded">
                    <div class="grid grid-cols-4 gap-4">
                        <div>
                            <label for="interval_days" class="block text-sm font-semibold mb-2">天</label>
                            <InputNumber id="interval_days" v-model="task.interval_days" :min="0" :max="365" placeholder="0" fluid :useGrouping="false" />
                        </div>
                        <div>
                            <label for="interval_hours" class="block text-sm font-semibold mb-2">小时</label>
                            <InputNumber id="interval_hours" v-model="task.interval_hours" :min="0" :max="23" placeholder="0" fluid :useGrouping="false" />
                        </div>
                        <div>
                            <label for="interval_minutes" class="block text-sm font-semibold mb-2">分钟</label>
                            <InputNumber id="interval_minutes" v-model="task.interval_minutes" :min="0" :max="59" placeholder="0" fluid :useGrouping="false" />
                        </div>
                        <div>
                            <label for="interval_seconds" class="block text-sm font-semibold mb-2">秒</label>
                            <InputNumber id="interval_seconds" v-model="task.interval_seconds" :min="0" :max="59" placeholder="0" fluid :useGrouping="false" />
                        </div>
                    </div>
                    <small class="text-gray-500 mt-2 block">至少设置一个时间间隔值（例如：每5分钟、每1小时、每2天等）</small>
                </div>

                <div>
                    <label for="celery_task_args" class="block font-bold mb-3">Task Args (JSON Array)</label>
                    <Textarea id="celery_task_args" v-model="task.celery_task_args" placeholder='["arg1", "arg2"]' rows="3" fluid />
                </div>

                <div>
                    <label for="celery_task_kwargs" class="block font-bold mb-3">Task Kwargs (JSON Object)</label>
                    <Textarea id="celery_task_kwargs" v-model="task.celery_task_kwargs" placeholder='{"key": "value"}' rows="3" fluid />
                </div>
            </div>

            <template #footer>
                <Button label="Cancel" icon="pi pi-times" text @click="hideDialog" />
                <Button label="Save" icon="pi pi-check" @click="saveTask" />
            </template>
        </Dialog>

        <Dialog v-model:visible="deleteTaskDialog" :style="{ width: '450px' }" header="Confirm" :modal="true">
            <div class="flex items-center gap-4">
                <i class="pi pi-exclamation-triangle !text-3xl" />
                <span v-if="task"
                    >Are you sure you want to delete <b>{{ task.name }}</b
                    >?</span
                >
            </div>
            <template #footer>
                <Button label="No" icon="pi pi-times" text @click="deleteTaskDialog = false" />
                <Button label="Yes" icon="pi pi-check" @click="deleteTask" />
            </template>
        </Dialog>

        <Dialog v-model:visible="deleteTasksDialog" :style="{ width: '450px' }" header="Confirm" :modal="true">
            <div class="flex items-center gap-4">
                <i class="pi pi-exclamation-triangle !text-3xl" />
                <span v-if="task">Are you sure you want to delete the selected tasks?</span>
            </div>
            <template #footer>
                <Button label="No" icon="pi pi-times" text @click="deleteTasksDialog = false" />
                <Button label="Yes" icon="pi pi-check" text @click="deleteSelectedTasks" />
            </template>
        </Dialog>

        <!-- 执行记录对话框 -->
        <Dialog v-model:visible="executionsDialog" :style="{ width: '900px' }" header="Task Execution History" :modal="true">
            <div v-if="selectedTaskForExecutions">
                <div class="mb-4">
                    <h3 class="text-lg font-semibold">{{ selectedTaskForExecutions.name }}</h3>
                    <p class="text-sm text-gray-500">{{ selectedTaskForExecutions.description }}</p>
                </div>

                <DataTable :value="executions" :loading="executionsLoading" :paginator="true" :rows="10" showGridlines>
                    <template #empty> No execution records found. </template>

                    <Column field="celery_task_id" header="Celery Task ID" style="min-width: 200px">
                        <template #body="{ data }">
                            <span class="text-xs font-mono">{{ data.celery_task_id }}</span>
                        </template>
                    </Column>

                    <Column field="status" header="Status" style="min-width: 100px">
                        <template #body="{ data }">
                            <Tag :value="getExecutionStatusLabel(data.status)" :severity="getExecutionStatusSeverity(data.status)" />
                        </template>
                    </Column>

                    <Column field="started_at" header="Started At" sortable style="min-width: 150px">
                        <template #body="{ data }">
                            <span class="text-sm">{{ data.started_at ? formatDate(data.started_at) : '-' }}</span>
                        </template>
                    </Column>

                    <Column field="completed_at" header="Completed At" sortable style="min-width: 150px">
                        <template #body="{ data }">
                            <span class="text-sm">{{ data.completed_at ? formatDate(data.completed_at) : '-' }}</span>
                        </template>
                    </Column>

                    <Column field="runtime" header="Runtime" sortable style="min-width: 100px">
                        <template #body="{ data }">
                            <span class="text-sm">{{ formatRuntime(data.runtime) }}</span>
                        </template>
                    </Column>

                    <Column field="worker" header="Worker" style="min-width: 150px">
                        <template #body="{ data }">
                            <span class="text-xs">{{ data.worker || '-' }}</span>
                        </template>
                    </Column>

                    <Column header="Result" style="min-width: 200px">
                        <template #body="{ data }">
                            <div v-if="data.status === 'success' && data.result" class="max-w-xs">
                                <pre class="text-xs bg-gray-100 dark:bg-gray-800 p-2 rounded overflow-auto max-h-20">{{ data.result }}</pre>
                            </div>
                            <div v-else-if="data.status === 'failure' && data.traceback" class="max-w-xs">
                                <pre class="text-xs bg-red-50 dark:bg-red-900 p-2 rounded overflow-auto max-h-20 text-red-600 dark:text-red-300">{{ data.traceback }}</pre>
                            </div>
                            <span v-else class="text-sm text-gray-500">-</span>
                        </template>
                    </Column>
                </DataTable>
            </div>

            <template #footer>
                <Button label="Close" icon="pi pi-times" @click="executionsDialog = false" />
            </template>
        </Dialog>
    </div>
</template>
