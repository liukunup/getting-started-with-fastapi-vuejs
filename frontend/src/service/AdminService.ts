import { OpenAPI } from '@/client/core/OpenAPI';
import { request as __request } from '@/client/core/request';
import type { CancelablePromise } from '@/client/core/CancelablePromise';

// Define types manually since we can't regenerate sdk.gen.ts easily
export interface Role {
    id: string;
    name: string;
    description?: string;
    permissions?: Permission[];
}

export interface RoleCreate {
    name: string;
    description?: string;
}

export interface RoleUpdate {
    name?: string;
    description?: string;
}

export interface Permission {
    id: string;
    name: string;
    description?: string;
    roles?: Role[];
}

export interface PermissionCreate {
    name: string;
    description?: string;
}

export interface PermissionUpdate {
    name?: string;
    description?: string;
}

export interface Menu {
    id: string;
    label: string;
    icon?: string;
    to?: string;
    url?: string;
    target?: string;
    component?: string;
    clazz?: string;
    is_hidden?: boolean;
    parent_id?: string;
    children?: Menu[];
    items?: Menu[];
}

export interface MenuCreate {
    label: string;
    icon?: string;
    to?: string;
    url?: string;
    target?: string;
    component?: string;
    clazz?: string;
    is_hidden?: boolean;
    parent_id?: string;
}

export interface MenuUpdate {
    label?: string;
    icon?: string;
    to?: string;
    url?: string;
    target?: string;
    component?: string;
    clazz?: string;
    is_hidden?: boolean;
    parent_id?: string;
}

export interface Api {
    id: string;
    group: string;
    name: string;
    path: string;
    method: string;
}

export interface ApiCreate {
    group: string;
    name: string;
    path: string;
    method: string;
}

export interface ApiUpdate {
    group?: string;
    name?: string;
    path?: string;
    method?: string;
}

export interface Policy {
    sub: string;
    obj: string;
    act: string;
}

export class AdminService {
    // Roles
    public static getRoles(): CancelablePromise<Role[]> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/roles/',
        });
    }

    public static getRole(id: string): CancelablePromise<Role> {
        return __request(OpenAPI, {
            method: 'GET',
            url: `/api/v1/roles/${id}`,
        });
    }

    public static createRole(data: RoleCreate): CancelablePromise<Role> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/roles/',
            body: data,
        });
    }

    public static updateRole(id: string, data: RoleUpdate): CancelablePromise<Role> {
        return __request(OpenAPI, {
            method: 'PUT',
            url: `/api/v1/roles/${id}`,
            body: data,
        });
    }

    public static deleteRole(id: string): CancelablePromise<Role> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: `/api/v1/roles/${id}`,
        });
    }

    public static addPermissionToRole(roleId: string, permissionId: string): CancelablePromise<Role> {
        return __request(OpenAPI, {
            method: 'POST',
            url: `/api/v1/roles/${roleId}/permissions`,
            query: { permission_id: permissionId },
        });
    }

    public static removePermissionFromRole(roleId: string, permissionId: string): CancelablePromise<Role> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: `/api/v1/roles/${roleId}/permissions/${permissionId}`,
        });
    }

    // Permissions
    public static getPermissions(): CancelablePromise<Permission[]> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/permissions/',
        });
    }

    public static createPermission(data: PermissionCreate): CancelablePromise<Permission> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/permissions/',
            body: data,
        });
    }

    public static updatePermission(id: string, data: PermissionUpdate): CancelablePromise<Permission> {
        return __request(OpenAPI, {
            method: 'PUT',
            url: `/api/v1/permissions/${id}`,
            body: data,
        });
    }

    public static deletePermission(id: string): CancelablePromise<Permission> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: `/api/v1/permissions/${id}`,
        });
    }

    // Menus
    public static getMenus(flatten: boolean = false): CancelablePromise<Menu[]> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/menus/',
            query: {
                flatten: flatten,
            },
        });
    }

    public static createMenu(data: MenuCreate): CancelablePromise<Menu> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/menus/',
            body: data,
        });
    }

    public static updateMenu(id: string, data: MenuUpdate): CancelablePromise<Menu> {
        return __request(OpenAPI, {
            method: 'PUT',
            url: `/api/v1/menus/${id}`,
            body: data,
        });
    }

    public static deleteMenu(id: string): CancelablePromise<Menu> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: `/api/v1/menus/${id}`,
        });
    }

    // APIs
    public static getApis(): CancelablePromise<Api[]> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/apis/',
        });
    }

    public static createApi(data: ApiCreate): CancelablePromise<Api> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/apis/',
            body: data,
        });
    }

    public static updateApi(id: string, data: ApiUpdate): CancelablePromise<Api> {
        return __request(OpenAPI, {
            method: 'PUT',
            url: `/api/v1/apis/${id}`,
            body: data,
        });
    }

    public static deleteApi(id: string): CancelablePromise<Api> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: `/api/v1/apis/${id}`,
        });
    }

    // Policies (APIs)
    public static getPolicies(): CancelablePromise<Policy[]> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/policies/',
        });
    }

    public static addPolicy(data: Policy): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/policies/',
            body: data,
        });
    }

    public static removePolicy(data: Policy): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/api/v1/policies/',
            body: data,
        });
    }
}
