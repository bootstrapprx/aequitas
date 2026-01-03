<script>
    import { invoke } from "@tauri-apps/api/core";
    import { onMount } from "svelte";
    import Toast from "./Toast.svelte";
    import OllamaChat from "./OllamaChat.svelte";

    let loading = true;
    let error = null;
    let date = new Date().toISOString().split("T")[0]; // Today
    let content = "";
    let frontmatter = {};
    let rawContent = ""; // For context passing

    // Toast
    let toastShow = false;
    let toastMessage = "";
    let toastType = "success";

    // State
    let saving = false;
    let showFields = true;

    onMount(async () => {
        await loadDaily();
    });

    async function loadDaily() {
        try {
            loading = true;
            // Try to get existing note
            // detailed response needed: content + parsed frontmatter
            const note = await invoke("get_daily_note", { date });

            if (note) {
                // DB-backed note has properties map
                if (note.properties) {
                    frontmatter = { ...note.properties };
                } else if (note.raw_content) {
                    // Fallback to manual parse if raw_content exists (legacy FS)
                    const match = note.raw_content.match(
                        /^---\n([\s\S]*?)\n---/,
                    );
                    if (match) {
                        const fmString = match[1];
                        frontmatter = {};
                        fmString.split("\n").forEach((line) => {
                            const parts = line.split(":");
                            if (parts.length >= 2) {
                                const key = parts[0].trim();
                                const val = parts.slice(1).join(":").trim();
                                if (key) frontmatter[key] = val;
                            }
                        });
                    }
                } else {
                    frontmatter = {};
                }

                content = note.content || "";

                // For Ollama context, we reconstruct the full note since we might not have raw_content
                let contextStr = "---\n";
                for (const [key, val] of Object.entries(frontmatter)) {
                    if (val) contextStr += `${key}: ${val}\n`;
                }
                contextStr += "---\n\n" + content;
                rawContent = contextStr;
            } else {
                content = "";
                frontmatter = {};
                rawContent = "";
            }
            error = null;
        } catch (err) {
            if (err.toString().includes("not found")) {
                // Create empty state, or auto-create?
                // Let's offer to create
                content = "";
                frontmatter = {};
                error = "No daily note for today.";
            } else {
                error = err.toString();
            }
        } finally {
            loading = false;
        }
    }

    async function createDaily() {
        try {
            loading = true;
            await invoke("create_daily_note", { date });
            await loadDaily();
            toastMessage = "Daily note created";
            toastShow = true;
        } catch (err) {
            toastMessage = err.toString();
            toastType = "error";
            toastShow = true;
            loading = false;
        }
    }

    async function save() {
        saving = true;
        try {
            // We need a way to save body + fields.
            // Current commands might be limited.
            // write_daily_note takes a string content.
            // We'll construct the file content manually for now if needed,
            // or assume write_daily_note handles raw text.

            // Reconstruct file:
            let fileContent = "---\n";
            for (const [key, val] of Object.entries(frontmatter)) {
                if (val) fileContent += `${key}: ${val}\n`;
            }
            fileContent += "---\n\n" + content;

            await invoke("write_daily_note", { date, content: fileContent });

            rawContent = fileContent; // Update context
            toastMessage = "Saved";
            toastShow = true;
        } catch (err) {
            toastMessage = err.toString();
            toastType = "error";
            toastShow = true;
        } finally {
            saving = false;
        }
    }

    function addField() {
        const key = prompt("Field name:");
        if (key) {
            frontmatter[key] = "";
            frontmatter = frontmatter; // trigger update
        }
    }
</script>

<div class="flex h-full gap-4">
    <!-- Left: Daily Editor -->
    <div
        class="flex-1 flex flex-col bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden"
    >
        <!-- Header -->
        <div
            class="px-4 py-3 border-b border-gray-200 dark:border-gray-700 flex justify-between items-center bg-gray-50 dark:bg-gray-900/50"
        >
            <h2 class="font-bold text-gray-900 dark:text-white">
                Current Day: {date}
            </h2>
            <div class="flex gap-2">
                <button class="text-xs btn btn-secondary" on:click={loadDaily}
                    >Reload</button
                >
                <button
                    class="text-xs btn btn-primary"
                    on:click={save}
                    disabled={saving || error}
                >
                    {saving ? "Saving..." : "Save"}
                </button>
            </div>
        </div>

        {#if loading}
            <div class="p-8 text-center text-gray-500">Loading...</div>
        {:else if error}
            <div
                class="flex-1 flex flex-col items-center justify-center p-8 text-center"
            >
                <p class="text-gray-600 mb-4">{error}</p>
                {#if error.includes("No daily note")}
                    <button class="btn btn-primary" on:click={createDaily}
                        >Initialize Today</button
                    >
                {/if}
            </div>
        {:else}
            <div class="flex-1 overflow-y-auto p-4">
                <!-- Dynamic Management (Frontmatter) -->
                <div
                    class="mb-4 p-3 bg-gray-50 dark:bg-gray-900 rounded border border-gray-200 dark:border-gray-700"
                >
                    <div class="flex justify-between items-center mb-2">
                        <h3
                            class="text-sm font-semibold text-gray-700 dark:text-gray-300"
                        >
                            Properties (Dynamic Management)
                        </h3>
                        <button
                            class="text-xs text-blue-500 hover:text-blue-600"
                            on:click={addField}>+ Field</button
                        >
                    </div>
                    <div class="grid grid-cols-2 gap-2">
                        {#each Object.entries(frontmatter) as [key, value]}
                            <div class="contents">
                                <label
                                    class="text-xs text-gray-500 flex items-center justify-between gap-2 w-full"
                                >
                                    {key}
                                    <input
                                        type="text"
                                        bind:value={frontmatter[key]}
                                        class="px-2 py-1 text-sm border rounded bg-white dark:bg-gray-800 border-gray-300 dark:border-gray-600 focus:ring-1 focus:ring-blue-500 focus:outline-none flex-1 ml-2"
                                    />
                                </label>
                            </div>
                        {/each}
                    </div>
                </div>

                <!-- Content -->
                <textarea
                    class="w-full h-[500px] p-4 font-mono text-sm bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded focus:ring-2 focus:ring-blue-500 focus:outline-none resize-none"
                    bind:value={content}
                    placeholder="Daily notes..."
                ></textarea>
            </div>
        {/if}
    </div>

    <!-- Right: Ollama Interaction -->
    <div class="w-[400px] flex flex-col">
        <OllamaChat context={rawContent} />
    </div>
</div>

<Toast bind:show={toastShow} message={toastMessage} type={toastType} />
