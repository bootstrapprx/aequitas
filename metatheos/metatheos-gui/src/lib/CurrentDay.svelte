<script>
    import { invoke } from "@tauri-apps/api/core";
    import { onMount } from "svelte";
    import Toast from "./Toast.svelte";
    import OllamaChat from "./OllamaChat.svelte";
    import BeginDay from "./BeginDay.svelte";
    import Timeline from "./Timeline.svelte";
    import DayOutcomeBadge from "./DayOutcomeBadge.svelte";

    let loading = true;
    let error = null;
    let date = new Date().toISOString().split("T")[0]; // Today
    let content = "";
    let frontmatter = {};
    let rawContent = "";

    let hasActiveDay = false;

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
            const note = await invoke("get_daily_note", { date });

            if (note) {
                if (note.properties) {
                    frontmatter = { ...note.properties };
                } else if (note.raw_content) {
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
                    // Check if note object ITSELF has top-level fields (DB DTO)
                    // If note has 'mode', use it.
                    if (note.mode) frontmatter.mode = note.mode;
                    if (note.phase) frontmatter.phase = note.phase;
                }

                if (frontmatter.mode || note.mode) {
                    hasActiveDay = true;
                    content = note.content || "";
                } else {
                    hasActiveDay = false;
                }
            } else {
                hasActiveDay = false;
                content = "";
                frontmatter = {};
                rawContent = "";
            }
            error = null;
        } catch (err) {
            hasActiveDay = false;
            if (!err.toString().includes("not found")) {
                error = err.toString();
            }
        } finally {
            loading = false;
        }
    }

    function onDayStarted() {
        loadDaily();
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

<div class="flex h-full gap-4 relative">
    {#if !hasActiveDay && !loading}
        <div
            class="w-full h-full flex items-center justify-center bg-gray-50 dark:bg-gray-900"
        >
            <div
                class="max-w-4xl w-full bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 overflow-hidden"
            >
                <div
                    class="p-8 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50"
                >
                    <h1
                        class="text-3xl font-bold text-gray-800 dark:text-gray-100"
                    >
                        Begin Day
                    </h1>
                    <p class="text-gray-500">
                        Initialize your execution context
                    </p>
                </div>
                <BeginDay {date} on:dayStarted={onDayStarted} />
            </div>
        </div>
    {:else}
        <!-- Left: Daily Editor -->
        <div
            class="flex-1 flex flex-col bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden"
        >
            <!-- Header -->
            <div
                class="px-4 py-3 border-b border-gray-200 dark:border-gray-700 flex justify-between items-center bg-gray-50 dark:bg-gray-900/50"
            >
                <div class="flex items-center gap-3">
                    <h2 class="font-bold text-gray-900 dark:text-white">
                        Current Day: {date}
                    </h2>
                    <DayOutcomeBadge dayId={date} />
                </div>
                <div class="flex gap-2">
                    <button
                        class="text-xs btn btn-secondary"
                        on:click={loadDaily}>Reload</button
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

                    <!-- Timeline View -->
                    <div class="mt-4">
                        <Timeline scopeType="day" scopeId={date} heading="Day Timeline" collapsedInitially={true} />
                    </div>
                </div>
            {/if}
        </div>

        <!-- Right: Ollama Interaction -->
        <div class="w-[400px] flex flex-col">
            <OllamaChat context={rawContent} />
        </div>
    {/if}
</div>

<Toast bind:show={toastShow} message={toastMessage} type={toastType} />
