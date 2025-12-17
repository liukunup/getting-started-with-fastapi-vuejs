<script setup>
import { formatDateTime } from '@/utils';
import { ref, onMounted, onUnmounted, watch } from 'vue';
import { useToast } from 'primevue/usetoast';
import Button from 'primevue/button';
import DataTable from 'primevue/datatable';
import Column from 'primevue/column';
import TabView from 'primevue/tabview';
import TabPanel from 'primevue/tabpanel';
import Tag from 'primevue/tag';
import Badge from 'primevue/badge';
import Dialog from 'primevue/dialog';
import SelectButton from 'primevue/selectbutton';
import { CeleryService } from '@/client';

const toast = useToast();

// 状态
const loading = ref(false);
const loadingWorkers = ref(false);
const loadingActiveTasks = ref(false);
const loadingScheduledTasks = ref(false);
const loadingReservedTasks = ref(false);
const loadingRegisteredTasks = ref(false);

const activeTab = ref(0);

// 数据
const stats = ref({
    workers: { total: 0, online: 0 },
    tasks: { active: 0, scheduled: 0, reserved: 0, total: 0 }
});

const workers = ref([]);
const activeTasks = ref([]);
const scheduledTasks = ref([]);
const reservedTasks = ref([]);
const registeredTasks = ref([]);

// Worker详情
const workerDetailsDialog = ref(false);
const selectedWorker = ref(null);

// 自动刷新
let refreshInterval = null;
const autoRefreshInterval = ref(0);
const refreshOptions = ref([
    { label: '手动', value: 0 },
    { label: '5s', value: 5000 },
    { label: '15s', value: 15000 },
    { label: '60s', value: 60000 }
]);

watch(autoRefreshInterval, (newValue) => {
    if (refreshInterval) {
        clearInterval(refreshInterval);
        refreshInterval = null;
    }
    if (newValue > 0) {
        refreshInterval = setInterval(refreshAll, newValue);
    }
});

// 获取统计信息
const getStats = async () => {
    try {
        const response = await CeleryService.getCeleryStats();
        stats.value = response;
    } catch (error) {
        console.error('Failed to get stats:', error);
        toast.add({ severity: 'error', summary: '错误', detail: '获取统计信息失败', life: 3000 });
    }
};

// 获取Workers
const getWorkers = async () => {
    loadingWorkers.value = true;
    try {
        const response = await CeleryService.getWorkers();
        workers.value = response.workers || [];
    } catch (error) {
        console.error('Failed to get workers:', error);
        toast.add({ severity: 'error', summary: '错误', detail: '获取Workers失败', life: 3000 });
    } finally {
        loadingWorkers.value = false;
    }
};

// 获取活跃任务
const getActiveTasks = async () => {
    loadingActiveTasks.value = true;
    try {
        const response = await CeleryService.getActiveTasks();
        activeTasks.value = response.tasks || [];
    } catch (error) {
        console.error('Failed to get active tasks:', error);
        toast.add({ severity: 'error', summary: '错误', detail: '获取活跃任务失败', life: 3000 });
    } finally {
        loadingActiveTasks.value = false;
    }
};

// 获取计划任务
const getScheduledTasks = async () => {
    loadingScheduledTasks.value = true;
    try {
        const response = await CeleryService.getScheduledTasks();
        scheduledTasks.value = response.tasks || [];
    } catch (error) {
        console.error('Failed to get scheduled tasks:', error);
        toast.add({ severity: 'error', summary: '错误', detail: '获取计划任务失败', life: 3000 });
    } finally {
        loadingScheduledTasks.value = false;
    }
};

// 获取保留任务
const getReservedTasks = async () => {
    loadingReservedTasks.value = true;
    try {
        const response = await CeleryService.getReservedTasks();
        reservedTasks.value = response.tasks || [];
    } catch (error) {
        console.error('Failed to get reserved tasks:', error);
        toast.add({ severity: 'error', summary: '错误', detail: '获取保留任务失败', life: 3000 });
    } finally {
        loadingReservedTasks.value = false;
    }
};

// 获取已注册任务
const getRegisteredTasks = async () => {
    loadingRegisteredTasks.value = true;
    try {
        const response = await CeleryService.getRegisteredTasks();
        const tasks = response.tasks || [];
        registeredTasks.value = tasks.map((name) => ({ name }));
    } catch (error) {
        console.error('Failed to get registered tasks:', error);
        toast.add({ severity: 'error', summary: '错误', detail: '获取已注册任务失败', life: 3000 });
    } finally {
        loadingRegisteredTasks.value = false;
    }
};

// 刷新所有数据
const refreshAll = async () => {
    loading.value = true;
    try {
        await Promise.all([getStats(), getWorkers(), getActiveTasks(), getScheduledTasks(), getReservedTasks(), getRegisteredTasks()]);
    } finally {
        loading.value = false;
    }
};

// 撤销任务
const revokeTask = async (taskId) => {
    try {
        await CeleryService.revokeTask(taskId);
        toast.add({ severity: 'success', summary: '成功', detail: '任务已撤销', life: 3000 });
        await refreshAll();
    } catch (error) {
        console.error('Failed to revoke task:', error);
        toast.add({ severity: 'error', summary: '错误', detail: '撤销任务失败', life: 3000 });
    }
};

// 显示Worker详情
const showWorkerDetails = (worker) => {
    selectedWorker.value = worker;
    workerDetailsDialog.value = true;
};

// 辅助函数
const getWorkerShortName = (workerName) => {
    if (!workerName) return '';
    const parts = workerName.split('@');
    return parts.length > 1 ? parts[1] : workerName;
};

const formatTimestamp = (timestamp) => {
    if (!timestamp) return '';
    return new Date(timestamp * 1000).toLocaleString('zh-CN');
};

// 生命周期
onMounted(() => {
    refreshAll();
    if (autoRefreshInterval.value > 0) {
        refreshInterval = setInterval(refreshAll, autoRefreshInterval.value);
    }
});

onUnmounted(() => {
    if (refreshInterval) {
        clearInterval(refreshInterval);
    }
});
</script>

<template>
    <div class="card">
        <div class="flex justify-between items-center mb-4">
            <h2 class="text-3xl font-bold">Celery</h2>
            <div class="flex items-center gap-2">
                <SelectButton v-model="autoRefreshInterval" :options="refreshOptions" optionLabel="label" optionValue="value" :allowEmpty="false" />
                <Button icon="pi pi-refresh" label="刷新" @click="refreshAll" :loading="loading" />
            </div>
        </div>

        <!-- 统计卡片 -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
            <div class="card bg-blue-50 dark:bg-blue-900">
                <div class="flex justify-between items-start">
                    <div>
                        <div class="text-blue-500 text-xl font-semibold mb-2">Workers</div>
                        <div class="text-3xl font-bold text-blue-600 dark:text-blue-300">{{ stats.workers.total }}</div>
                        <div class="text-sm text-blue-400">在线: {{ stats.workers.online }}</div>
                    </div>
                    <i class="pi pi-users text-4xl text-blue-500"></i>
                </div>
            </div>

            <div class="card bg-green-50 dark:bg-green-900">
                <div class="flex justify-between items-start">
                    <div>
                        <div class="text-green-500 text-xl font-semibold mb-2">活跃任务</div>
                        <div class="text-3xl font-bold text-green-600 dark:text-green-300">{{ stats.tasks.active }}</div>
                        <div class="text-sm text-green-400">正在执行</div>
                    </div>
                    <i class="pi pi-cog text-4xl text-green-500"></i>
                </div>
            </div>

            <div class="card bg-yellow-50 dark:bg-yellow-900">
                <div class="flex justify-between items-start">
                    <div>
                        <div class="text-yellow-500 text-xl font-semibold mb-2">计划任务</div>
                        <div class="text-3xl font-bold text-yellow-600 dark:text-yellow-300">{{ stats.tasks.scheduled }}</div>
                        <div class="text-sm text-yellow-400">等待执行</div>
                    </div>
                    <i class="pi pi-clock text-4xl text-yellow-500"></i>
                </div>
            </div>

            <div class="card bg-purple-50 dark:bg-purple-900">
                <div class="flex justify-between items-start">
                    <div>
                        <div class="text-purple-500 text-xl font-semibold mb-2">保留任务</div>
                        <div class="text-3xl font-bold text-purple-600 dark:text-purple-300">{{ stats.tasks.reserved }}</div>
                        <div class="text-sm text-purple-400">已保留</div>
                    </div>
                    <i class="pi pi-inbox text-4xl text-purple-500"></i>
                </div>
            </div>
        </div>

        <!-- Tab 视图 -->
        <TabView v-model:activeIndex="activeTab">
            <!-- Workers 标签 -->
            <TabPanel header="Workers">
                <DataTable :value="workers" :loading="loadingWorkers" showGridlines>
                    <Column field="name" header="Worker名称" style="min-width: 250px">
                        <template #body="{ data }">
                            <div class="flex items-center gap-2">
                                <i class="pi pi-circle-fill text-green-500 text-xs"></i>
                                <span class="font-mono text-sm">{{ data.name }}</span>
                            </div>
                        </template>
                    </Column>
                    <Column field="status" header="状态">
                        <template #body="{ data }">
                            <Tag :value="data.status" :severity="data.status === 'online' ? 'success' : 'danger'" />
                        </template>
                    </Column>
                    <Column field="active_tasks" header="活跃任务数">
                        <template #body="{ data }">
                            <Badge :value="data.active_tasks.length" severity="info" />
                        </template>
                    </Column>
                    <Column field="registered_tasks" header="注册任务数">
                        <template #body="{ data }">
                            <Badge :value="data.registered_tasks.length" />
                        </template>
                    </Column>
                    <Column header="操作">
                        <template #body="{ data }">
                            <Button icon="pi pi-info-circle" text rounded @click="showWorkerDetails(data)" />
                        </template>
                    </Column>
                </DataTable>
            </TabPanel>

            <!-- 活跃任务标签 -->
            <TabPanel header="活跃任务">
                <DataTable :value="activeTasks" :loading="loadingActiveTasks" showGridlines>
                    <Column field="id" header="任务ID" style="min-width: 250px">
                        <template #body="{ data }">
                            <span class="font-mono text-xs">{{ data.id }}</span>
                        </template>
                    </Column>
                    <Column field="name" header="任务名称" style="min-width: 200px">
                        <template #body="{ data }">
                            <span class="font-semibold">{{ data.name }}</span>
                        </template>
                    </Column>
                    <Column field="worker" header="Worker" style="min-width: 150px">
                        <template #body="{ data }">
                            <span class="text-sm">{{ getWorkerShortName(data.worker) }}</span>
                        </template>
                    </Column>
                    <Column field="time_start" header="开始时间" style="min-width: 150px">
                        <template #body="{ data }">
                            <span class="text-sm">{{ formatTimestamp(data.time_start) }}</span>
                        </template>
                    </Column>
                    <Column header="操作">
                        <template #body="{ data }">
                            <Button icon="pi pi-times" severity="danger" text rounded @click="revokeTask(data.id)" v-tooltip="'撤销任务'" />
                        </template>
                    </Column>
                </DataTable>
            </TabPanel>

            <!-- 计划任务标签 -->
            <TabPanel header="计划任务">
                <DataTable :value="scheduledTasks" :loading="loadingScheduledTasks" showGridlines>
                    <Column field="id" header="任务ID" style="min-width: 250px">
                        <template #body="{ data }">
                            <span class="font-mono text-xs">{{ data.id }}</span>
                        </template>
                    </Column>
                    <Column field="name" header="任务名称" style="min-width: 200px">
                        <template #body="{ data }">
                            <span class="font-semibold">{{ data.name }}</span>
                        </template>
                    </Column>
                    <Column field="worker" header="Worker" style="min-width: 150px">
                        <template #body="{ data }">
                            <span class="text-sm">{{ getWorkerShortName(data.worker) }}</span>
                        </template>
                    </Column>
                    <Column field="eta" header="预计执行时间" style="min-width: 150px">
                        <template #body="{ data }">
                            <span class="text-sm">{{ formatDateTime(data.eta) }}</span>
                        </template>
                    </Column>
                    <Column header="操作">
                        <template #body="{ data }">
                            <Button icon="pi pi-times" severity="danger" text rounded @click="revokeTask(data.id)" v-tooltip="'撤销任务'" />
                        </template>
                    </Column>
                </DataTable>
            </TabPanel>

            <!-- 保留任务标签 -->
            <TabPanel header="保留任务">
                <DataTable :value="reservedTasks" :loading="loadingReservedTasks" showGridlines>
                    <Column field="id" header="任务ID" style="min-width: 250px">
                        <template #body="{ data }">
                            <span class="font-mono text-xs">{{ data.id }}</span>
                        </template>
                    </Column>
                    <Column field="name" header="任务名称" style="min-width: 200px">
                        <template #body="{ data }">
                            <span class="font-semibold">{{ data.name }}</span>
                        </template>
                    </Column>
                    <Column field="worker" header="Worker" style="min-width: 150px">
                        <template #body="{ data }">
                            <span class="text-sm">{{ getWorkerShortName(data.worker) }}</span>
                        </template>
                    </Column>
                    <Column header="操作">
                        <template #body="{ data }">
                            <Button icon="pi pi-times" severity="danger" text rounded @click="revokeTask(data.id)" v-tooltip="'撤销任务'" />
                        </template>
                    </Column>
                </DataTable>
            </TabPanel>

            <!-- 已注册任务标签 -->
            <TabPanel header="已注册任务">
                <DataTable :value="registeredTasks" :loading="loadingRegisteredTasks" showGridlines>
                    <Column field="name" header="任务名称" style="min-width: 300px">
                        <template #body="{ data }">
                            <span class="font-mono text-sm">{{ data.name }}</span>
                        </template>
                    </Column>
                </DataTable>
            </TabPanel>
        </TabView>

        <!-- Worker详情对话框 -->
        <Dialog v-model:visible="workerDetailsDialog" header="Worker 详情" :style="{ width: '50rem' }" :modal="true">
            <div v-if="selectedWorker">
                <h3 class="font-semibold text-lg mb-3">{{ selectedWorker.name }}</h3>

                <div class="mb-4">
                    <h4 class="font-semibold mb-2">统计信息</h4>
                    <div class="bg-gray-100 dark:bg-gray-800 p-3 rounded">
                        <pre class="text-xs overflow-auto">{{ JSON.stringify(selectedWorker.stats, null, 2) }}</pre>
                    </div>
                </div>

                <div class="mb-4">
                    <h4 class="font-semibold mb-2">活跃任务 ({{ selectedWorker.active_tasks.length }})</h4>
                    <div v-if="selectedWorker.active_tasks.length > 0" class="bg-gray-100 dark:bg-gray-800 p-3 rounded">
                        <ul class="list-disc list-inside">
                            <li v-for="task in selectedWorker.active_tasks" :key="task.id" class="text-sm mb-1">
                                {{ task.name }}
                            </li>
                        </ul>
                    </div>
                    <div v-else class="text-gray-500 text-sm">无活跃任务</div>
                </div>

                <div>
                    <h4 class="font-semibold mb-2">已注册任务 ({{ selectedWorker.registered_tasks.length }})</h4>
                    <div v-if="selectedWorker.registered_tasks.length > 0" class="bg-gray-100 dark:bg-gray-800 p-3 rounded max-h-60 overflow-auto">
                        <ul class="list-disc list-inside">
                            <li v-for="task in selectedWorker.registered_tasks" :key="task" class="text-xs mb-1 font-mono">
                                {{ task }}
                            </li>
                        </ul>
                    </div>
                    <div v-else class="text-gray-500 text-sm">无已注册任务</div>
                </div>
            </div>
        </Dialog>
    </div>
</template>

<style scoped>
.card {
    background: var(--surface-card);
    padding: 1.5rem;
    border-radius: 10px;
    margin-bottom: 1rem;
    box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
}
</style>
