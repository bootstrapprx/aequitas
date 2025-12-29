<script>
  import { invoke } from '@tauri-apps/api/core'
  import { onMount } from 'svelte'
  import Toast from './Toast.svelte'

  let hasApiKey = false
  let loading = true
  let messages = []
  let currentMessage = ''
  let sending = false
  let examples = []
  let showExamples = true
  let activeMode = 'chat' // 'chat' or 'webview'

  // Toast
  let toastShow = false
  let toastMessage = ''
  let toastType = 'success'

  onMount(async () => {
    try {
      hasApiKey = await invoke('ai_check_config')
      examples = await invoke('ai_get_examples')
      loading = false

      if (!hasApiKey) {
        // Show info message about API key
        toastMessage = 'No API key detected. You can use the webview chatbot or configure ANTHROPIC_API_KEY.'
        toastType = 'info'
        toastShow = true
        activeMode = 'webview'
      }
    } catch (err) {
      console.error('Failed to check AI config:', err)
      loading = false
    }
  })

  async function sendMessage() {
    if (!currentMessage.trim()) return

    const userMessage = currentMessage.trim()
    currentMessage = ''
    showExamples = false

    // Add user message to chat
    messages = [...messages, { role: 'user', text: userMessage }]

    sending = true

    try {
      const response = await invoke('ai_ask', { query: userMessage })

      // Add AI response
      messages = [
        ...messages,
        {
          role: 'assistant',
          text: response.text,
          model: response.model,
          hasContext: response.context.length > 0,
        },
      ]

      // Scroll to bottom
      setTimeout(() => {
        const chatContainer = document.querySelector('.chat-messages')
        if (chatContainer) {
          chatContainer.scrollTop = chatContainer.scrollHeight
        }
      }, 100)
    } catch (err) {
      toastMessage = `Error: ${err}`
      toastType = 'error'
      toastShow = true

      // Remove loading message
      messages = messages.slice(0, -1)
    } finally {
      sending = false
    }
  }

  function useExample(example) {
    currentMessage = example
    showExamples = false
  }

  function handleKeyDown(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      sendMessage()
    }
  }

  function clearChat() {
    messages = []
    showExamples = true
  }
</script>

<div class="h-full flex flex-col">
  <div class="flex items-center justify-between mb-4">
    <div>
      <h2 class="text-3xl font-bold text-gray-900 dark:text-white">AI Assistant</h2>
      <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
        Ask questions about your governance, get suggestions, and analyze goals
      </p>
    </div>

    <div class="flex items-center gap-2">
      {#if !loading}
        <!-- Mode Switcher -->
        <div class="flex gap-1 p-1 bg-gray-100 dark:bg-gray-800 rounded-lg">
          <button
            class="px-3 py-1 text-sm rounded transition-colors {activeMode === 'chat'
              ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow'
              : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'}"
            on:click={() => (activeMode = 'chat')}
          >
            {hasApiKey ? 'AI Chat' : 'Fallback Mode'}
          </button>
          <button
            class="px-3 py-1 text-sm rounded transition-colors {activeMode === 'webview'
              ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow'
              : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'}"
            on:click={() => (activeMode = 'webview')}
          >
            Web Chatbot
          </button>
        </div>

        {#if messages.length > 0 && activeMode === 'chat'}
          <button class="btn btn-secondary text-sm" on:click={clearChat}>Clear Chat</button>
        {/if}
      {/if}
    </div>
  </div>

  {#if loading}
    <div class="flex-1 flex items-center justify-center">
      <div class="text-center">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
        <p class="text-gray-600 dark:text-gray-400">Loading AI assistant...</p>
      </div>
    </div>
  {:else if activeMode === 'webview'}
    <!-- Webview Chatbot -->
    <div class="flex-1 card overflow-hidden">
      <div class="h-full">
        <iframe
          src="https://claude.ai"
          class="w-full h-full border-0"
          title="Claude Web Chatbot"
          sandbox="allow-scripts allow-same-origin allow-forms"
        ></iframe>
      </div>
      <div class="mt-2 p-3 bg-blue-50 dark:bg-blue-900/20 rounded border border-blue-200 dark:border-blue-800">
        <p class="text-sm text-blue-800 dark:text-blue-200">
          <strong>ℹ️ Web Chatbot Mode:</strong> Using claude.ai web interface. For integrated AI assistance with your governance data, set
          the <code class="px-1 py-0.5 bg-blue-100 dark:bg-blue-900 rounded">ANTHROPIC_API_KEY</code> environment variable and restart the app.
        </p>
      </div>
    </div>
  {:else}
    <!-- AI Chat Interface -->
    <div class="flex-1 flex flex-col overflow-hidden">
      <!-- Chat Messages -->
      <div class="flex-1 overflow-y-auto chat-messages space-y-4 p-4 bg-gray-50 dark:bg-gray-900 rounded-lg">
        {#if !hasApiKey}
          <div class="card bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800">
            <h3 class="font-semibold text-yellow-900 dark:text-yellow-100 mb-2">⚠️ No API Key Configured</h3>
            <p class="text-sm text-yellow-800 dark:text-yellow-200 mb-2">
              To use AI assistance, please set your <code class="px-1 py-0.5 bg-yellow-100 dark:bg-yellow-900 rounded">ANTHROPIC_API_KEY</code> environment variable.
            </p>
            <p class="text-sm text-yellow-700 dark:text-yellow-300">
              Alternatively, use the <strong>Web Chatbot</strong> tab above to access Claude directly through your browser.
            </p>
          </div>
        {/if}

        {#if showExamples && examples.length > 0}
          <div class="card">
            <h3 class="font-semibold text-gray-900 dark:text-white mb-3">💡 Try asking:</h3>
            <div class="space-y-2">
              {#each examples as example}
                <button
                  class="w-full text-left px-4 py-2 rounded-lg bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors text-sm"
                  on:click={() => useExample(example)}
                >
                  "{example}"
                </button>
              {/each}
            </div>
          </div>
        {/if}

        {#each messages as message}
          <div class="flex gap-3 {message.role === 'user' ? 'justify-end' : 'justify-start'}">
            <div class="max-w-[80%]">
              <div
                class="px-4 py-3 rounded-lg {message.role === 'user'
                  ? 'bg-primary-600 text-white'
                  : 'bg-white dark:bg-gray-800 text-gray-900 dark:text-white border border-gray-200 dark:border-gray-700'}"
              >
                {#if message.role === 'assistant' && message.model}
                  <div class="text-xs opacity-75 mb-2">
                    {message.model}
                    {#if message.hasContext}
                      · with governance context
                    {/if}
                  </div>
                {/if}
                <div class="text-sm whitespace-pre-wrap">{message.text}</div>
              </div>
            </div>
          </div>
        {/each}

        {#if sending}
          <div class="flex gap-3 justify-start">
            <div class="px-4 py-3 rounded-lg bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700">
              <div class="flex items-center gap-2">
                <div class="animate-spin rounded-full h-4 w-4 border-b-2 border-primary-600"></div>
                <span class="text-sm text-gray-600 dark:text-gray-400">Thinking...</span>
              </div>
            </div>
          </div>
        {/if}
      </div>

      <!-- Input Area -->
      <div class="mt-4">
        <div class="flex gap-2">
          <textarea
            bind:value={currentMessage}
            on:keydown={handleKeyDown}
            placeholder={hasApiKey ? "Ask a question about your governance..." : "API key required to ask questions"}
            disabled={!hasApiKey || sending}
            class="flex-1 px-4 py-3 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white resize-none focus:ring-2 focus:ring-primary-500 focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed"
            rows="3"
          ></textarea>
          <button
            on:click={sendMessage}
            disabled={!currentMessage.trim() || !hasApiKey || sending}
            class="btn btn-primary self-end"
          >
            {sending ? 'Sending...' : 'Send'}
          </button>
        </div>
        <p class="text-xs text-gray-500 dark:text-gray-400 mt-2">
          Press Enter to send, Shift+Enter for new line
        </p>
      </div>
    </div>
  {/if}
</div>

<Toast bind:show={toastShow} message={toastMessage} type={toastType} />

<style>
  .chat-messages {
    scroll-behavior: smooth;
  }

  .chat-messages::-webkit-scrollbar {
    width: 8px;
  }

  .chat-messages::-webkit-scrollbar-track {
    background: transparent;
  }

  .chat-messages::-webkit-scrollbar-thumb {
    background: #cbd5e0;
    border-radius: 4px;
  }

  .dark .chat-messages::-webkit-scrollbar-thumb {
    background: #4a5568;
  }
</style>
