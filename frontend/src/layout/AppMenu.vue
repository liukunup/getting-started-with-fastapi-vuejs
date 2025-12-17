<script setup>
import { computed } from 'vue';
import { useAuthStore } from '@/store/auth';
import AppMenuItem from './AppMenuItem.vue';

const authStore = useAuthStore();

const model = computed(() => authStore.menus);
</script>

<template>
    <ul class="layout-menu">
        <template v-for="(item, i) in model" :key="item">
            <app-menu-item v-if="!item.separator" :item="item" :index="i"></app-menu-item>
            <li v-if="item.separator" class="menu-separator"></li>
        </template>
    </ul>
</template>

<style lang="scss" scoped></style>
