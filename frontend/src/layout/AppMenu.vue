<script setup>
import { ref, onMounted } from 'vue';
import { MenuService } from '@/service/MenuService';
import AppMenuItem from './AppMenuItem.vue';

const model = ref([]);

const staticMenu = [
    {
        label: 'Home',
        items: [
            { label: 'Dashboard', icon: 'pi pi-fw pi-home', to: '/' }
        ]
    },
    {
        label: 'Get Started',
        items: [
            {
                label: 'Documentation',
                icon: 'pi pi-fw pi-book',
                to: '/documentation'
            },
            {
                label: 'View Source',
                icon: 'pi pi-fw pi-github',
                url: 'https://github.com/primefaces/sakai-vue',
                target: '_blank'
            }
        ]
    }
];

const mapMenu = (menu) => {
    return {
        label: menu.label,
        icon: menu.icon,
        to: menu.to,
        url: menu.url,
        target: menu.target,
        class: menu.clazz,
        visible: !menu.is_hidden,
        items: menu.items && menu.items.length > 0 ? menu.items.map(mapMenu) : undefined
    };
};

onMounted(async () => {
    try {
        const menus = await MenuService.getMenus();
        model.value = menus.map(mapMenu);
    } catch (e) {
        console.error("Failed to load menus", e);
        model.value = staticMenu;
    }
});
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
