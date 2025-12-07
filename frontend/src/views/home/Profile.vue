<script setup>
import { UserService } from '@/client';
import { Cropper } from 'vue-advanced-cropper';
import 'vue-advanced-cropper/dist/style.css';
import { useToast } from 'primevue/usetoast';
import { onMounted, ref, computed } from 'vue';

const toast = useToast();
const user = ref({});
const loading = ref(false);
const uploadingAvatar = ref(false);

// 头像裁剪相关
const cropperDialog = ref(false);
const cropperImage = ref(null);
const cropper = ref(null);

// 密码修改相关
const passwordDialog = ref(false);
const passwordForm = ref({
    current_password: '',
    new_password: '',
    confirmPassword: ''
});
const submittingPassword = ref(false);

// 个人信息编辑相关
const editMode = ref(false);
const editForm = ref({
    username: '',
    full_name: '',
    email: ''
});

// 计算头像初始字母
const avatarLabel = computed(() => {
    if (user.value.avatar) return '';
    return user.value.username?.charAt(0).toUpperCase() || user.value.email?.charAt(0).toUpperCase() || 'U';
});

onMounted(() => {
    loadUserProfile();
});

const loadUserProfile = async () => {
    loading.value = true;
    try {
        const data = await UserService.readUserMe();
        user.value = data;
        editForm.value = {
            username: data.username || '',
            full_name: data.full_name || '',
            email: data.email || ''
        };
    } catch (error) {
        toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to load user profile', life: 3000 });
    } finally {
        loading.value = false;
    }
};

const triggerFileInput = () => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'image/*';
    input.onchange = (e) => {
        const file = e.target.files[0];
        if (file) {
            if (file.size > 2000000) {
                toast.add({ severity: 'warn', summary: 'Warning', detail: 'File size should not exceed 2MB', life: 3000 });
                return;
            }
            const reader = new FileReader();
            reader.onload = (event) => {
                cropperImage.value = event.target.result;
                cropperDialog.value = true;
            };
            reader.readAsDataURL(file);
        }
    };
    input.click();
};

const cropImage = () => {
    if (cropper.value) {
        const { canvas } = cropper.value.getResult();
        if (canvas) {
            uploadingAvatar.value = true;
            canvas.toBlob(
                async (blob) => {
                    try {
                        const file = new File([blob], 'avatar.jpg', { type: 'image/jpeg' });
                        const formData = {
                            file: file
                        };
                        const data = await UserService.uploadAvatar({ formData });
                        user.value = data;
                        cropperDialog.value = false;
                        cropperImage.value = null;
                        toast.add({ severity: 'success', summary: 'Success', detail: 'Avatar uploaded successfully', life: 3000 });
                    } catch (error) {
                        toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to upload avatar', life: 3000 });
                    } finally {
                        uploadingAvatar.value = false;
                    }
                },
                'image/jpeg',
                0.9
            );
        }
    }
};

const cancelCrop = () => {
    cropperDialog.value = false;
    cropperImage.value = null;
};

const enableEditMode = () => {
    editMode.value = true;
};

const cancelEdit = () => {
    editMode.value = false;
    editForm.value = {
        username: user.value.username || '',
        full_name: user.value.full_name || '',
        email: user.value.email || ''
    };
};

const saveProfile = async () => {
    loading.value = true;
    try {
        const requestBody = {};
        if (editForm.value.username !== user.value.username) {
            requestBody.username = editForm.value.username;
        }
        if (editForm.value.full_name !== user.value.full_name) {
            requestBody.full_name = editForm.value.full_name;
        }
        if (editForm.value.email !== user.value.email) {
            requestBody.email = editForm.value.email;
        }

        if (Object.keys(requestBody).length === 0) {
            toast.add({ severity: 'info', summary: 'Info', detail: 'No changes to save', life: 3000 });
            editMode.value = false;
            return;
        }

        const data = await UserService.updateUserMe({ requestBody });
        user.value = data;
        editMode.value = false;
        toast.add({ severity: 'success', summary: 'Success', detail: 'Profile updated successfully', life: 3000 });
    } catch (error) {
        const detail = error.body?.detail || 'Failed to update profile';
        toast.add({ severity: 'error', summary: 'Error', detail, life: 3000 });
    } finally {
        loading.value = false;
    }
};

const openPasswordDialog = () => {
    passwordForm.value = {
        current_password: '',
        new_password: '',
        confirmPassword: ''
    };
    passwordDialog.value = true;
};

const closePasswordDialog = () => {
    passwordDialog.value = false;
    passwordForm.value = {
        current_password: '',
        new_password: '',
        confirmPassword: ''
    };
};

const updatePassword = async () => {
    if (!passwordForm.value.current_password || !passwordForm.value.new_password) {
        toast.add({ severity: 'warn', summary: 'Warning', detail: 'Please fill all password fields', life: 3000 });
        return;
    }

    if (passwordForm.value.new_password !== passwordForm.value.confirmPassword) {
        toast.add({ severity: 'warn', summary: 'Warning', detail: 'New passwords do not match', life: 3000 });
        return;
    }

    if (passwordForm.value.new_password.length < 8) {
        toast.add({ severity: 'warn', summary: 'Warning', detail: 'Password must be at least 8 characters', life: 3000 });
        return;
    }

    submittingPassword.value = true;
    try {
        const requestBody = {
            current_password: passwordForm.value.current_password,
            new_password: passwordForm.value.new_password
        };
        await UserService.updatePasswordMe({ requestBody });
        closePasswordDialog();
        toast.add({ severity: 'success', summary: 'Success', detail: 'Password updated successfully', life: 3000 });
    } catch (error) {
        const detail = error.body?.detail || 'Failed to update password';
        toast.add({ severity: 'error', summary: 'Error', detail, life: 3000 });
    } finally {
        submittingPassword.value = false;
    }
};

const formatDate = (value) => {
    if (!value) return '';
    return new Date(value).toLocaleDateString('en-US', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
    });
};
</script>

<template>
    <div class="grid grid-cols-12 gap-8">
        <!-- 主要信息卡片 -->
        <div class="col-span-12 xl:col-span-8">
            <div class="card">
                <div class="flex items-center justify-between mb-6">
                    <h5 class="m-0">Profile Settings</h5>
                    <div class="flex gap-2">
                        <Button v-if="!editMode" label="Edit Profile" icon="pi pi-pencil" severity="secondary" @click="enableEditMode" />
                        <template v-else>
                            <Button label="Save" icon="pi pi-check" :loading="loading" @click="saveProfile" />
                            <Button label="Cancel" icon="pi pi-times" severity="secondary" text :disabled="loading" @click="cancelEdit" />
                        </template>
                    </div>
                </div>

                <div class="flex flex-col gap-6">
                    <!-- 头像部分 -->
                    <div class="border border-surface rounded-border p-4">
                        <label class="block font-bold mb-3">Avatar</label>
                        <div class="flex items-center gap-4">
                            <div class="relative cursor-pointer group" @click="triggerFileInput" title="Click to upload avatar">
                                <Avatar :image="avatarUrl" :label="avatarLabel" size="xlarge" shape="circle" />
                                <!-- Hover overlay -->
                                <div class="absolute inset-0 flex items-center justify-center bg-black bg-opacity-50 rounded-full opacity-0 group-hover:opacity-100 transition-opacity">
                                    <i class="pi pi-camera text-white text-2xl"></i>
                                </div>
                            </div>
                            <div class="flex-1">
                                <p class="text-surface-700 dark:text-surface-200 mb-2">
                                    <strong>{{ user.username }}</strong>
                                </p>
                                <small class="text-muted-color block">Click avatar to upload</small>
                                <small class="text-muted-color block">JPG, PNG. Max size 2MB</small>
                            </div>
                        </div>
                    </div>

                    <!-- 基本信息 -->
                    <div class="grid grid-cols-12 gap-4">
                        <div class="col-span-12 md:col-span-6">
                            <label for="username" class="block font-bold mb-3">Username</label>
                            <InputText id="username" v-model="editForm.username" :disabled="!editMode || loading" :placeholder="editMode ? 'Enter username' : ''" fluid />
                        </div>

                        <div class="col-span-12 md:col-span-6">
                            <label for="full_name" class="block font-bold mb-3">Full Name</label>
                            <InputText id="full_name" v-model="editForm.full_name" :disabled="!editMode || loading" :placeholder="editMode ? 'Enter full name' : ''" fluid />
                        </div>

                        <div class="col-span-12 md:col-span-6">
                            <label for="email" class="block font-bold mb-3">Email</label>
                            <InputText id="email" v-model="editForm.email" :disabled="!editMode || loading" :placeholder="editMode ? 'Enter email' : ''" type="email" fluid />
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- 侧边信息卡片 -->
        <div class="col-span-12 xl:col-span-4">
            <!-- 角色信息 -->
            <div v-if="user.role" class="card mb-6">
                <h5 class="mb-4">Role Information</h5>
                <div class="flex flex-col gap-4">
                    <div class="border border-surface rounded-border p-4 bg-primary-50 dark:bg-primary-900/10">
                        <div class="flex items-center gap-3 mb-2">
                            <i class="pi pi-shield text-primary text-2xl"></i>
                            <div class="flex-1">
                                <div class="font-bold text-lg text-primary">{{ user.role.name }}</div>
                                <small class="text-muted-color">User Role</small>
                            </div>
                        </div>
                        <div v-if="user.role.description" class="mt-3 pt-3 border-t border-surface">
                            <p class="text-sm text-surface-700 dark:text-surface-300">
                                {{ user.role.description }}
                            </p>
                        </div>
                    </div>
                </div>
            </div>

            <!-- 账号信息 -->
            <div class="card mb-6">
                <h5 class="mb-4">Account Information</h5>
                <div class="flex flex-col gap-4">
                    <div class="flex flex-col gap-2">
                        <label class="font-bold text-sm text-muted-color">Email Address</label>
                        <div class="flex items-center gap-2">
                            <i class="pi pi-envelope text-muted-color"></i>
                            <span>{{ user.email || 'N/A' }}</span>
                        </div>
                    </div>

                    <Divider />

                    <div class="flex flex-col gap-2">
                        <label class="font-bold text-sm text-muted-color">Account Status</label>
                        <div class="flex items-center gap-2">
                            <i :class="user.is_active ? 'pi pi-check-circle text-green-500' : 'pi pi-times-circle text-red-500'"></i>
                            <span>{{ user.is_active ? 'Active' : 'Inactive' }}</span>
                        </div>
                    </div>

                    <Divider />

                    <div class="flex flex-col gap-2">
                        <label class="font-bold text-sm text-muted-color">Created At</label>
                        <div class="flex items-center gap-2">
                            <i class="pi pi-calendar text-muted-color"></i>
                            <span>{{ formatDate(user.created_at) }}</span>
                        </div>
                    </div>

                    <div class="flex flex-col gap-2">
                        <label class="font-bold text-sm text-muted-color">Last Updated</label>
                        <div class="flex items-center gap-2">
                            <i class="pi pi-clock text-muted-color"></i>
                            <span>{{ formatDate(user.updated_at) }}</span>
                        </div>
                    </div>
                </div>
            </div>

            <!-- 安全设置 -->
            <div class="card">
                <h5 class="mb-4">Security</h5>
                <Button label="Change Password" icon="pi pi-key" severity="secondary" fluid @click="openPasswordDialog" />
            </div>
        </div>
    </div>

    <!-- 修改密码对话框 -->
    <Dialog v-model:visible="passwordDialog" :style="{ width: '450px' }" header="Change Password" :modal="true">
        <div class="flex flex-col gap-6">
            <div>
                <label for="current_password" class="block font-bold mb-3">Current Password</label>
                <Password id="current_password" v-model="passwordForm.current_password" :feedback="false" toggleMask placeholder="Enter current password" fluid />
            </div>
            <div>
                <label for="new_password" class="block font-bold mb-3">New Password</label>
                <Password id="new_password" v-model="passwordForm.new_password" toggleMask placeholder="Enter new password (min 8 characters)" fluid />
            </div>
            <div>
                <label for="confirm_password" class="block font-bold mb-3">Confirm New Password</label>
                <Password id="confirm_password" v-model="passwordForm.confirmPassword" :feedback="false" toggleMask placeholder="Re-enter new password" fluid />
            </div>
        </div>
        <template #footer>
            <Button label="Cancel" icon="pi pi-times" text @click="closePasswordDialog" :disabled="submittingPassword" />
            <Button label="Save" icon="pi pi-check" @click="updatePassword" :loading="submittingPassword" />
        </template>
    </Dialog>

    <!-- 图片裁剪对话框 -->
    <Dialog v-model:visible="cropperDialog" :style="{ width: '600px' }" header="Crop Avatar" :modal="true">
        <div class="flex flex-col gap-4">
            <div style="max-height: 400px; overflow: hidden">
                <Cropper
                    ref="cropper"
                    :src="cropperImage"
                    :stencil-props="{
                        aspectRatio: 1,
                        movable: true,
                        resizable: true
                    }"
                    :resize-image="{
                        adjustStencil: false
                    }"
                    image-restriction="stencil"
                />
            </div>
            <small class="text-muted-color">Drag to reposition and resize the crop area</small>
        </div>
        <template #footer>
            <Button label="Cancel" icon="pi pi-times" text @click="cancelCrop" :disabled="uploadingAvatar" />
            <Button label="Upload" icon="pi pi-check" @click="cropImage" :loading="uploadingAvatar" />
        </template>
    </Dialog>
</template>
