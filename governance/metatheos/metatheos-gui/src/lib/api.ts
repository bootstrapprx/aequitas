import { invoke } from '@tauri-apps/api/core';

const isTauri = () => {
    return '__TAURI_INTERNALS__' in window;
};

export async function apiInvoke<T>(command: string, args: Record<string, any> = {}): Promise<T> {
    if (isTauri()) {
        console.debug(`[Tauri] Invoking ${command}`, args);
        return await invoke<T>(command, args);
    } else {
        console.debug(`[Web] Fetching /api/invoke/${command}`, args);
        const response = await fetch(`/api/invoke/${command}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(args),
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`API Error: ${response.statusText} - ${errorText}`);
        }

        const json = await response.json();
        // Server returns { status: "ok", data: ... } or { status: "error", ... }
        if (json.status === 'error') {
            throw new Error(json.message || 'Unknown server error');
        }

        return json.data as T;
    }
}
