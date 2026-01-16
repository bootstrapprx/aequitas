<script>
    import { invoke } from "@tauri-apps/api/core";
    import { onMount, afterUpdate } from "svelte";
    import Toast from "./Toast.svelte";

    export let context = ""; // Context string to send to the model

    let loading = false;
    let messages = [];
    let currentMessage = "";
    let chatContainer;

    // Toast
    let toastShow = false;
    let toastMessage = "";
    let toastType = "success";

    // Auto-scroll to bottom of chat
    afterUpdate(() => {
        if (chatContainer) {
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
    });

    async function sendMessage() {
        if (!currentMessage.trim()) return;

        const userMessage = currentMessage.trim();
        currentMessage = "";
        loading = true;

        // Add user message to UI
        messages = [...messages, { role: "user", text: userMessage }];

        try {
            // Construct query with context if available
            let query = userMessage;
            if (context) {
                query = `CONTEXT:\n${context}\n\nUSER REQUEST:\n${userMessage}`;
            }

            const response = await invoke("ollama_reason", {
                query: query,
                intentOverride: null, // Let the model decide or standard chat
            });

            // Valid response
            messages = [
                ...messages,
                {
                    role: "assistant",
                    text:
                        response.rationale ||
                        response.raw_model_output ||
                        "No response text",
                    model: response.model,
                    intent: response.intent,
                },
            ];
        } catch (err) {
            toastMessage = `Error: ${err}`;
            toastType = "error";
            toastShow = true;
            // Remove user message on failure? Or just show error. Keeping it is better DBG.
        } finally {
            loading = false;
        }
    }

    function handleKeyDown(event) {
        if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
            sendMessage();
        }
    }

    function clearChat() {
        messages = [];
    }
</script>

<div
    class="flex flex-col h-full bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden"
>
    <!-- Header -->
    <div
        class="px-4 py-3 border-b border-gray-200 dark:border-gray-700 flex justify-between items-center bg-gray-50 dark:bg-gray-900/50"
    >
        <div class="flex items-center gap-2">
            <span class="text-lg">🤖</span>
            <h3 class="font-semibold text-gray-900 dark:text-white">
                Ollama Chat
            </h3>
        </div>
        <button
            class="text-xs text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
            on:click={clearChat}
        >
            Clear
        </button>
    </div>

    <!-- Messages Area -->
    <div class="flex-1 overflow-y-auto p-4 space-y-4" bind:this={chatContainer}>
        {#if messages.length === 0}
            <div
                class="flex flex-col items-center justify-center h-full text-gray-400 text-sm text-center px-6"
            >
                <p class="mb-2">Send a message to start chatting.</p>
                {#if context}
                    <p
                        class="text-xs bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-300 px-2 py-1 rounded"
                    >
                        Context loaded from current page
                    </p>
                {/if}
            </div>
        {/if}

        {#each messages as msg}
            <div
                class="flex flex-col gap-1 {msg.role === 'user'
                    ? 'items-end'
                    : 'items-start'}"
            >
                <div
                    class="max-w-[85%] px-3 py-2 rounded-lg text-sm whitespace-pre-wrap {msg.role ===
                    'user'
                        ? 'bg-blue-600 text-white rounded-br-none'
                        : 'bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white rounded-bl-none'}"
                >
                    {msg.text}
                </div>
                {#if msg.role === "assistant" && msg.intent}
                    <span class="text-[10px] text-gray-400 px-1"
                        >intent: {msg.intent}</span
                    >
                {/if}
            </div>
        {/each}

        {#if loading}
            <div class="flex items-start">
                <div
                    class="bg-gray-100 dark:bg-gray-700 p-3 rounded-lg rounded-bl-none"
                >
                    <div class="flex gap-1">
                        <div
                            class="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce"
                            style="animation-delay: 0ms"
                        ></div>
                        <div
                            class="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce"
                            style="animation-delay: 150ms"
                        ></div>
                        <div
                            class="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce"
                            style="animation-delay: 300ms"
                        ></div>
                    </div>
                </div>
            </div>
        {/if}
    </div>

    <!-- Input Area -->
    <div
        class="p-3 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900/50"
    >
        <div class="flex gap-2">
            <textarea
                bind:value={currentMessage}
                on:keydown={handleKeyDown}
                placeholder="Type a message..."
                rows="1"
                class="flex-1 px-3 py-2 text-sm rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                style="min-height: 40px; max-height: 120px;"
            ></textarea>
            <button
                on:click={sendMessage}
                disabled={loading || !currentMessage.trim()}
                class="px-3 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white rounded-md transition-colors flex items-center justify-center min-w-[40px]"
            >
                <span class="text-lg">↑</span>
            </button>
        </div>
        <div class="text-[10px] text-gray-400 mt-1 text-center">
            Uses local Ollama model (reason-only)
        </div>
    </div>
</div>

<Toast bind:show={toastShow} message={toastMessage} type={toastType} />
