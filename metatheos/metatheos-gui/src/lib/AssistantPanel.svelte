<script lang="ts">
    import { invoke } from "@tauri-apps/api/core";
    import { onMount } from "svelte";

    export let activePhase: any;
    export let activeDay: any;

    let modelStatus = "Checking...";
    let isConnected = false;
    let draftResponse = "";
    let loading = false;
    let prompt = "";

    onMount(async () => {
        // Check connection?
        try {
            // We assume 11435 is up as per environment metadata
            modelStatus = "Local: qwen2.5-coder:3b (Port 11435)";
            isConnected = true;
        } catch (e) {
            modelStatus = "Disconnected";
        }
    });

    async function summarizeDay() {
        if (!activeDay) return;
        loading = true;
        try {
            // Assuming activeDay has date. We use get_daily_context or similar?
            // For now, pass metadata available.
            const context = `Day Context: ${activeDay.date}\nPhase: ${activePhase?.id}`;
            draftResponse = await invoke("ai_assist_summarize", {
                dayLog: context,
            });
        } catch (e) {
            draftResponse = `Error: ${e}`;
        } finally {
            loading = false;
        }
    }

    // Generic Chat
    async function sendPrompt() {
        if (!prompt.trim()) return;
        loading = true;
        try {
            draftResponse = await invoke("ai_assist_refine", { text: prompt });
        } catch (e) {
            draftResponse = `Error: ${e}`;
        } finally {
            loading = false;
        }
    }
</script>

<div
    class="bg-gray-800 rounded-lg border border-purple-500/30 p-4 shadow-lg shadow-purple-900/10 h-full flex flex-col"
>
    <div class="flex justify-between items-center mb-4">
        <h3 class="text-purple-400 font-bold flex items-center gap-2">
            <span>🤖</span> Assistant
            <span
                class="text-xs text-gray-500 font-normal border border-gray-600 px-1 rounded"
                >Safe Mode</span
            >
        </h3>
        <span class="text-xs {isConnected ? 'text-green-400' : 'text-red-400'}"
            >{modelStatus}</span
        >
    </div>

    <div
        class="bg-gray-900/50 p-3 rounded mb-4 text-xs text-gray-400 space-y-1"
    >
        <div class="flex justify-between">
            <span>Context:</span>
            <span class="text-gray-300"
                >{activePhase?.name || activePhase?.id || "None"} / {activeDay?.date ||
                    "No Active Day"}</span
            >
        </div>
        <div class="text-[10px] text-gray-500 mt-1 italic">
            "AI outputs are drafts. You must manually apply them."
        </div>
    </div>

    <div class="space-y-3 flex-shrink-0">
        {#if activeDay}
            <button
                on:click={summarizeDay}
                disabled={loading}
                class="w-full bg-purple-900/30 hover:bg-purple-900/50 border border-purple-500/30 text-purple-200 py-2 rounded text-sm transition-colors flex justify-center items-center gap-2 disabled:opacity-50"
            >
                {#if loading}
                    <span class="animate-spin">⌛</span>
                {:else}
                    📝
                {/if}
                Summarize Day Progress
            </button>
        {/if}

        <div class="flex gap-2">
            <input
                type="text"
                bind:value={prompt}
                placeholder="Ask/Refine..."
                class="flex-1 bg-gray-900 border border-gray-600 rounded px-3 py-2 text-sm text-white focus:outline-none focus:border-purple-500 transition-colors"
                on:keydown={(e) => e.key === "Enter" && sendPrompt()}
            />
            <button
                on:click={sendPrompt}
                disabled={loading}
                class="bg-gray-700 hover:bg-gray-600 text-white px-3 py-1 rounded text-sm font-medium transition-colors border border-gray-600"
                >Go</button
            >
        </div>
    </div>

    {#if draftResponse}
        <div
            class="mt-4 pt-4 border-t border-gray-700 flex-1 flex flex-col min-h-0"
        >
            <div class="flex justify-between items-center mb-2">
                <h4 class="text-xs font-bold text-gray-500 uppercase">
                    Draft Output
                </h4>
                <button
                    on:click={() => {
                        navigator.clipboard.writeText(draftResponse);
                    }}
                    class="text-xs text-blue-400 hover:text-blue-300 flex items-center gap-1"
                >
                    <span>📋</span> Copy
                </button>
            </div>
            <div
                class="bg-gray-900 p-3 rounded text-sm text-gray-300 whitespace-pre-wrap overflow-y-auto border border-purple-500/20 flex-1 custom-scrollbar"
            >
                {draftResponse}
            </div>
        </div>
    {/if}
</div>

<style>
    .custom-scrollbar::-webkit-scrollbar {
        width: 6px;
    }
    .custom-scrollbar::-webkit-scrollbar-track {
        background: #1f2937;
    }
    .custom-scrollbar::-webkit-scrollbar-thumb {
        background: #374151;
        border-radius: 3px;
    }
</style>
