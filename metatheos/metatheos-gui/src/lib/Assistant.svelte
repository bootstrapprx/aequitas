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
  let activeMode = 'ollama' // 'ollama', 'claude', 'webview'
  let lastContextDescriptor = null
  let reasonerResult = null
  let draftEditor = ''
  let intentOverride = ''
  let commitMessage = ''

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

  async function sendReasoner() {
    if (!currentMessage.trim()) return
    sending = true
    toastShow = false
    try {
      const response = await invoke('ollama_reason', {
        query: currentMessage.trim(),
        intentOverride: intentOverride || null,
      })
      reasonerResult = response
      draftEditor = response.draft_markdown || ''
    } catch (err) {
      toastMessage = `Reasoner error: ${err}`
      toastType = 'error'
      toastShow = true
    } finally {
      sending = false
    }
  }

  async function sendMessage() {
    if (!currentMessage.trim()) return

    if (activeMode === 'ollama') {
      return sendReasoner()
    }

    const userMessage = currentMessage.trim()
    currentMessage = ''
    showExamples = false

    // Add user message to chat
    messages = [...messages, { role: 'user', text: userMessage }]

    sending = true

    try {
      const response = await invoke('ai_ask', { query: userMessage })
      lastContextDescriptor = response.context_descriptor

      // Add AI response
      messages = [
        ...messages,
        {
          role: 'assistant',
          text: response.text,
          model: response.model,
          hasContext: response.context_descriptor?.included_goals?.length > 0,
          descriptor: response.context_descriptor,
          rejected: response.rejected,
          unknown: response.unknown_references,
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
    lastContextDescriptor = null
  }

  async function safeWriteDraft() {
    if (!reasonerResult || !reasonerResult.draft_path) {
      toastMessage = 'No draft path available'
      toastType = 'error'
      toastShow = true
      return
    }
    try {
      await invoke('safe_write_file', {
        file_path: reasonerResult.draft_path,
        new_content: draftEditor,
      })
      toastMessage = `Draft saved to ${reasonerResult.draft_path}`
      toastType = 'success'
      toastShow = true
    } catch (err) {
      toastMessage = `Safe write failed: ${err}`
      toastType = 'error'
      toastShow = true
    }
  }

  async function commitDraft() {
    if (!commitMessage.trim()) {
      toastMessage = 'Commit message required'
      toastType = 'error'
      toastShow = true
      return
    }
    try {
      const result = await invoke('commit_governance_changes', {
        message: commitMessage,
        related_ids: reasonerResult?.draft_path || '',
      })
      toastMessage = result.message || 'Committed'
      toastType = 'success'
      toastShow = true
    } catch (err) {
      toastMessage = `Commit failed: ${err}`
      toastType = 'error'
      toastShow = true
    }
  }

  function discardDraft() {
    reasonerResult = null
    draftEditor = ''
    commitMessage = ''
  }
</script>

<div class="h-full flex flex-col">
  <div class="flex items-center justify-between mb-4">
    <div>
      <h2 class="text-3xl font-bold text-gray-900 dark:text-white">AI Assistant</h2>
      <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
        Local model reasoning with governance guardrails (reason-only)
      </p>
    </div>

    <div class="flex items-center gap-2">
      {#if !loading}
        <!-- Mode Switcher -->
        <div class="flex gap-1 p-1 bg-gray-100 dark:bg-gray-800 rounded-lg">
          <button
            class="px-3 py-1 text-sm rounded transition-colors {activeMode === 'ollama'
              ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow'
              : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'}"
            on:click={() => (activeMode = 'ollama')}
          >
            Ollama (reason-only)
          </button>
          <button
            class="px-3 py-1 text-sm rounded transition-colors {activeMode === 'claude'
              ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow'
              : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'}"
            on:click={() => (activeMode = 'claude')}
          >
            {hasApiKey ? 'Claude (vault snapshot)' : 'Claude (requires key)'}
          </button>
          <button
            class="px-3 py-1 text-sm rounded transition-colors {activeMode === 'webview'
              ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow'
              : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'}"
            on:click={() => (activeMode = 'webview')}
          >
            Claude Web — no vault context
          </button>
        </div>

        {#if messages.length > 0 && activeMode === 'claude'}
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
  {:else if activeMode === 'ollama'}
    <div class="flex-1 flex flex-col gap-3 overflow-y-auto">
      <div class="card bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm font-semibold text-gray-900 dark:text-white">Local model (Ollama) — Reason-only — No auto writes</p>
            <p class="text-xs text-gray-600 dark:text-gray-400">
              Base URL: {reasonerResult?.base_url || 'http://127.0.0.1:11435'} · Model: {reasonerResult?.model || 'qwen2.5:7b-instruct'}
            </p>
          </div>
          <span class="text-xs px-2 py-1 rounded bg-orange-100 text-orange-700">No vault writes by model</span>
        </div>
      </div>

      <div class="card">
        <div class="flex flex-col gap-2">
          <div class="flex gap-2 items-center">
            <select
              class="px-3 py-2 rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-sm"
              bind:value={intentOverride}
            >
              <option value="">Auto intent</option>
              <option value="draft_goal">Draft Goal</option>
              <option value="update_goal">Update Goal</option>
              <option value="draft_decision">Draft Decision</option>
              <option value="draft_audit">Draft Audit</option>
              <option value="summarize_state">Summarize State</option>
              <option value="analyze_blockers">Analyze Blockers</option>
              <option value="explain_phase">Explain Phase</option>
            </select>
            <textarea
              class="flex-1 px-4 py-3 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white resize-none focus:ring-2 focus:ring-primary-500"
              rows="3"
              placeholder="Describe what you need drafted..."
              bind:value={currentMessage}
              on:keydown={handleKeyDown}
            ></textarea>
            <button class="btn btn-primary self-start" on:click={sendReasoner} disabled={sending || !currentMessage.trim()}>
              {sending ? 'Thinking...' : 'Generate Draft'}
            </button>
          </div>
          <p class="text-xs text-gray-500 dark:text-gray-400">Ollama reasons; Metatheos validates and writes via Safe Write.</p>
        </div>
      </div>

      {#if reasonerResult}
        <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
          <div class="card">
            <div class="flex items-center justify-between mb-2">
              <h3 class="font-semibold text-gray-900 dark:text-white">Intent & Context</h3>
              <div class="flex gap-2">
                <span class="px-2 py-1 text-xs rounded bg-blue-100 text-blue-800">Draft</span>
                <span class="px-2 py-1 text-xs rounded bg-gray-100 text-gray-700">No write performed</span>
              </div>
            </div>
            <p class="text-sm text-gray-700 dark:text-gray-300 mb-2">
              Intent: {reasonerResult.intent} (confidence {Math.round(reasonerResult.confidence * 100)}%) · {reasonerResult.rationale}
            </p>
            {#if reasonerResult.required_inputs?.length}
              <p class="text-xs text-gray-500 dark:text-gray-400 mb-2">Required inputs: {reasonerResult.required_inputs.join(', ')}</p>
            {/if}
            <div class="mt-3">
              <p class="text-xs uppercase text-gray-500">Context Used</p>
              <div class="mt-2 space-y-1 text-sm">
                {#if reasonerResult.context_used.phase}
                  <div><strong>Phase:</strong> {reasonerResult.context_used.phase.id} ({reasonerResult.context_used.phase.status || 'n/a'})</div>
                {/if}
                {#if reasonerResult.context_used.goals.length}
                  <div><strong>Goals:</strong> {reasonerResult.context_used.goals.map((g) => g.id).join(', ')}</div>
                {/if}
                {#if reasonerResult.context_used.decisions.length}
                  <div><strong>Decisions:</strong> {reasonerResult.context_used.decisions.map((g) => g.id).join(', ')}</div>
                {/if}
                {#if reasonerResult.context_used.audits.length}
                  <div><strong>Audits:</strong> {reasonerResult.context_used.audits.map((g) => g.id).join(', ')}</div>
                {/if}
                {#if reasonerResult.context_used.daily_notes.length}
                  <div><strong>Daily:</strong> {reasonerResult.context_used.daily_notes.map((g) => g.id).join(', ')}</div>
                {/if}
              </div>
            </div>
          </div>

          <div class="card">
            <h3 class="font-semibold text-gray-900 dark:text-white mb-2">Validation</h3>
            {#if reasonerResult.validation.valid}
              <div class="text-green-700 dark:text-green-300 text-sm">✅ Draft passed validation</div>
            {:else}
              <div class="text-red-700 dark:text-red-300 text-sm">❌ Validation failed</div>
            {/if}
            {#if reasonerResult.validation.errors.length}
              <ul class="mt-2 text-sm text-red-700 dark:text-red-300 list-disc list-inside">
                {#each reasonerResult.validation.errors as err}
                  <li>{err}</li>
                {/each}
              </ul>
            {/if}
            {#if reasonerResult.validation.warnings.length}
              <ul class="mt-2 text-sm text-yellow-700 dark:text-yellow-300 list-disc list-inside">
                {#each reasonerResult.validation.warnings as warn}
                  <li>{warn}</li>
                {/each}
              </ul>
            {/if}
          </div>
        </div>

        <div class="card">
          <div class="flex items-center justify-between mb-2">
            <h3 class="font-semibold text-gray-900 dark:text-white">Draft Preview (editable)</h3>
            <span class="text-xs text-gray-500">Path: {reasonerResult.draft_path || 'n/a'}</span>
          </div>
          {#if reasonerResult.draft_markdown}
            <textarea
              class="w-full h-64 px-3 py-2 rounded border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white font-mono text-sm"
              bind:value={draftEditor}
            ></textarea>
            <div class="flex flex-wrap gap-2 mt-3 items-center">
              <button class="btn btn-secondary" on:click={() => (draftEditor = reasonerResult.draft_markdown || '')} disabled={!reasonerResult.draft_markdown}>
                Reset Draft
              </button>
              <button class="btn btn-primary" on:click={safeWriteDraft} disabled={!reasonerResult.validation.valid || sending || !reasonerResult.draft_path}>
                Apply via Safe Edit
              </button>
              <input
                type="text"
                class="px-3 py-2 rounded border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm flex-1"
                placeholder="Commit message"
                bind:value={commitMessage}
              />
              <button class="btn btn-secondary" on:click={commitDraft} disabled={!commitMessage.trim()}>
                Commit
              </button>
              <button class="btn btn-secondary" on:click={discardDraft}>
                Discard
              </button>
              <span class="text-xs text-gray-500">No write performed until you apply.</span>
            </div>
          {:else}
            <p class="text-sm text-gray-600 dark:text-gray-300">No draft produced (analysis-only intent). Nothing to apply.</p>
          {/if}
        </div>

        <div class="card">
          <h3 class="font-semibold text-gray-900 dark:text-white mb-2">Raw Model Output</h3>
          <pre class="bg-gray-100 dark:bg-gray-900 text-xs p-3 rounded overflow-auto">{reasonerResult.raw_model_output}</pre>
        </div>
      {/if}
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
          <strong>ℹ️ Web Chatbot Mode (NO VAULT CONTEXT):</strong> Using claude.ai web interface. For integrated AI assistance with your governance data, set
          the <code class="px-1 py-0.5 bg-blue-100 dark:bg-blue-900 rounded">ANTHROPIC_API_KEY</code> environment variable and restart the app.
        </p>
      </div>
    </div>
  {:else}
    <!-- AI Chat Interface -->
    <div class="flex-1 flex flex-col overflow-hidden">
      {#if lastContextDescriptor}
        <div class="card mb-3 bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700">
          <div class="flex items-center justify-between">
            <h3 class="font-semibold text-gray-900 dark:text-white">Context Used</h3>
            <span class="text-xs px-2 py-1 rounded bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-200">
              Mode: {lastContextDescriptor.mode || 'stateless'}
            </span>
          </div>
          <div class="mt-2 grid grid-cols-2 gap-3 text-sm">
            <div>
              <p class="text-gray-600 dark:text-gray-400">Phase</p>
              <p class="font-mono text-gray-900 dark:text-white">{lastContextDescriptor.phase || 'n/a'}</p>
            </div>
            <div>
              <p class="text-gray-600 dark:text-gray-400">Decisions</p>
              <p class="text-gray-900 dark:text-white">not loaded</p>
            </div>
            <div>
              <p class="text-gray-600 dark:text-gray-400">Goals included</p>
              <p class="text-gray-900 dark:text-white truncate">
                {lastContextDescriptor.included_goals && lastContextDescriptor.included_goals.length
                  ? lastContextDescriptor.included_goals.join(', ')
                  : 'none'}
              </p>
            </div>
            <div>
              <p class="text-gray-600 dark:text-gray-400">Audits</p>
              <p class="text-gray-900 dark:text-white">not loaded</p>
            </div>
            <div class="col-span-2">
              <p class="text-gray-600 dark:text-gray-400">Status counts</p>
              <p class="text-gray-900 dark:text-white">
                {#if lastContextDescriptor.status_counts}
                  {#each Object.entries(lastContextDescriptor.status_counts) as [status, count]}
                    <span class="mr-2">{status}: {count}</span>
                  {/each}
                {:else}
                  n/a
                {/if}
              </p>
            </div>
          </div>
        </div>
      {/if}
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
                      · goals snapshot context
                    {/if}
                  </div>
                {/if}
                {#if message.rejected}
                  <div class="text-sm whitespace-pre-wrap text-red-600 dark:text-red-300">
                    {message.text}
                  </div>
                  {#if message.unknown?.length}
                    <p class="text-xs text-red-500 dark:text-red-300 mt-2">Unknown references: {message.unknown.join(', ')}</p>
                  {/if}
                {:else}
                  <div class="text-sm whitespace-pre-wrap">{message.text}</div>
                {/if}
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
