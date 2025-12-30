<script>
  import { invoke } from '@tauri-apps/api/core'
  import { onMount } from 'svelte'
  import Toast from './Toast.svelte'

  let loading = true
  let error = null
  let devMode = false
  let prompts = []
  let filteredPrompts = []
  let agentFilter = 'all'
  let purposeFilter = 'all'
  let searchQuery = ''

  let toastShow = false
  let toastMessage = ''
  let toastType = 'success'

  // Modal state for viewing prompt details
  let showDetailModal = false
  let selectedPrompt = null

  // Cross-reference modal state
  let showReferencesModal = false
  let selectedPromptForRefs = null

  // Unique agents and purposes for filters
  let uniqueAgents = []
  let uniquePurposes = []

  const tauriAvailable = () => {
    if (typeof window === 'undefined') return false
    return Boolean(
      window.__TAURI__ ||
        window.__TAURI_IPC__ ||
        window.__TAURI_INTERNALS__
    )
  }

  onMount(async () => {
    if (!tauriAvailable()) {
      devMode = true
      loading = false
      return
    }
    await loadPrompts()
  })

  async function loadPrompts() {
    try {
      loading = true
      const result = await invoke('get_enriched_prompts')
      prompts = result

      // Extract unique agents and purposes for filters
      uniqueAgents = [...new Set(prompts.map(p => p.agent).filter(Boolean))].sort()
      uniquePurposes = [...new Set(prompts.map(p => p.purpose).filter(Boolean))].sort()

      applyFilters()
      error = null
    } catch (err) {
      error = err?.toString?.() ?? String(err)
    } finally {
      loading = false
    }
  }

  function applyFilters() {
    let filtered = prompts

    if (agentFilter !== 'all') {
      filtered = filtered.filter(prompt =>
        prompt.agent?.toLowerCase() === agentFilter.toLowerCase()
      )
    }

    if (purposeFilter !== 'all') {
      filtered = filtered.filter(prompt =>
        prompt.purpose?.toLowerCase() === purposeFilter.toLowerCase()
      )
    }

    if (searchQuery) {
      filtered = filtered.filter(prompt => {
        const q = searchQuery.toLowerCase()
        return (
          prompt.title.toLowerCase().includes(q) ||
          (prompt.prompt_id && prompt.prompt_id.toLowerCase().includes(q)) ||
          (prompt.agent && prompt.agent.toLowerCase().includes(q)) ||
          (prompt.purpose && prompt.purpose.toLowerCase().includes(q)) ||
          (prompt.prompt_text && prompt.prompt_text.toLowerCase().includes(q))
        )
      })
    }

    // Sort by timestamp (newest first)
    filtered.sort((a, b) => {
      if (!a.timestamp) return 1
      if (!b.timestamp) return -1
      return b.timestamp.localeCompare(a.timestamp)
    })

    filteredPrompts = filtered
  }

  function getAgentBadgeClass(agent) {
    if (!agent) return 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300'

    // Color-code by agent type
    const agentLower = agent.toLowerCase()
    if (agentLower.includes('architect')) {
      return 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300'
    } else if (agentLower.includes('guardian')) {
      return 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300'
    } else if (agentLower.includes('orchestrator')) {
      return 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300'
    } else if (agentLower.includes('librarian')) {
      return 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-300'
    } else {
      return 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300'
    }
  }

  function formatTimestamp(timestamp) {
    if (!timestamp) return 'n/a'
    try {
      return new Date(timestamp).toLocaleString()
    } catch {
      return timestamp
    }
  }

  function getStatusBadgeClass(status) {
    if (!status) return 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300'
    const s = status.toLowerCase()
    if (s === 'active') return 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300'
    if (s === 'draft') return 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-300'
    if (s === 'deprecated') return 'bg-gray-200 text-gray-700 dark:bg-gray-700 dark:text-gray-300'
    return 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300'
  }

  function openDetailModal(prompt) {
    selectedPrompt = prompt
    showDetailModal = true
  }

  function closeDetailModal() {
    showDetailModal = false
    selectedPrompt = null
  }

  function openReferencesModal(prompt) {
    selectedPromptForRefs = prompt
    showReferencesModal = true
  }

  function closeReferencesModal() {
    showReferencesModal = false
    selectedPromptForRefs = null
  }

  function showToast(message, type = 'success') {
    toastMessage = message
    toastType = type
    toastShow = true
  }

  $: {
    searchQuery
    agentFilter
    purposeFilter
    applyFilters()
  }
</script>

<div class="p-6">
  <Toast bind:show={toastShow} message={toastMessage} type={toastType} />

  <div class="mb-6">
    <h1 class="text-3xl font-bold text-gray-900 dark:text-white mb-2">Prompt Library</h1>
    <p class="text-gray-600 dark:text-gray-400">
      AI prompts, agent instructions, and cross-references
    </p>
    <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">
      Curated prompts from <code class="bg-gray-100 dark:bg-gray-800 px-1 rounded">06_PROMPTS/library</code>. AI transcripts (logs) are excluded.
    </p>
  </div>

  {#if devMode}
    <div class="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4 mb-4">
      <p class="text-yellow-800 dark:text-yellow-200">
        🔧 Development Mode — Tauri not available. Run with <code class="bg-yellow-100 dark:bg-yellow-800 px-1 rounded">cargo tauri dev</code>
      </p>
    </div>
  {/if}

  {#if error}
    <div class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 mb-4">
      <p class="text-red-800 dark:text-red-200 font-medium">Error loading prompts:</p>
      <p class="text-red-700 dark:text-red-300 mt-1">{error}</p>
    </div>
  {/if}

  <!-- Filters -->
  <div class="flex flex-wrap gap-4 mb-6">
    <div class="flex-1 min-w-[300px]">
      <input
        type="text"
        placeholder="Search prompts (title, ID, agent, purpose, text)..."
        bind:value={searchQuery}
        class="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent"
      />
    </div>
    <select
      bind:value={agentFilter}
      class="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500"
    >
      <option value="all">All Agents</option>
      {#each uniqueAgents as agent}
        <option value={agent}>{agent}</option>
      {/each}
    </select>
    <select
      bind:value={purposeFilter}
      class="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500"
    >
      <option value="all">All Purposes</option>
      {#each uniquePurposes as purpose}
        <option value={purpose}>{purpose}</option>
      {/each}
    </select>
  </div>

  {#if loading}
    <div class="flex items-center justify-center py-12">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
    </div>
  {:else if filteredPrompts.length === 0}
    <div class="text-center py-12">
      <p class="text-gray-500 dark:text-gray-400 text-lg">
        {searchQuery || agentFilter !== 'all' || purposeFilter !== 'all' ? 'No prompts match your filters' : 'No prompts found'}
      </p>
    </div>
  {:else}
    <!-- Prompt Cards -->
    <div class="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      {#each filteredPrompts as prompt (prompt.file_path)}
        <div
          class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4 hover:shadow-lg transition-shadow cursor-pointer"
          on:click={() => openDetailModal(prompt)}
        >
          <!-- Header -->
          <div class="flex items-start justify-between mb-3">
            <div class="flex-1 min-w-0">
              <h3 class="font-semibold text-gray-900 dark:text-white text-lg mb-1 truncate">
                {prompt.title}
              </h3>
              {#if prompt.prompt_id}
                <p class="text-xs font-mono text-gray-500 dark:text-gray-400 truncate">
                  ID: {prompt.prompt_id}
                </p>
              {/if}
            </div>
            <div class="flex items-center gap-2 flex-shrink-0">
              <span class="px-2 py-1 text-[10px] font-semibold rounded bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-200">
                Designed Prompt
              </span>
              {#if prompt.status}
                <span class="px-2 py-1 text-[10px] font-semibold rounded {getStatusBadgeClass(prompt.status)}">
                  {prompt.status}
                </span>
              {/if}
            </div>
          </div>

          <!-- Agent & Purpose -->
          <div class="space-y-2 mb-3">
            {#if prompt.agent}
              <div class="flex items-center gap-2">
                <span class="px-2 py-1 text-xs font-medium rounded {getAgentBadgeClass(prompt.agent)}">
                  {prompt.agent}
                </span>
              </div>
            {/if}
            {#if prompt.purpose}
              <p class="text-sm text-gray-600 dark:text-gray-400 truncate">
                Purpose: {prompt.purpose}
              </p>
            {/if}
            {#if prompt.origin}
              <p class="text-sm text-gray-600 dark:text-gray-400 truncate">
                Origin: {prompt.origin}
              </p>
            {/if}
            {#if prompt.timestamp}
              <p class="text-xs text-gray-500 dark:text-gray-500">
                {formatTimestamp(prompt.timestamp)}
              </p>
            {/if}
          </div>

          <!-- Prompt Preview -->
          {#if prompt.prompt_text}
            <p class="text-sm text-gray-700 dark:text-gray-300 mb-3 line-clamp-3">
              {prompt.prompt_text}
            </p>
          {/if}

          <!-- Cross-References -->
          <div class="flex flex-wrap gap-2 text-xs">
            {#if prompt.referenced_goals.length > 0}
              <button
                class="flex items-center gap-1 px-2 py-1 bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300 rounded hover:bg-blue-100 dark:hover:bg-blue-900/30 transition-colors"
                on:click|stopPropagation={() => openReferencesModal(prompt)}
              >
                🎯 {prompt.referenced_goals.length} goal{prompt.referenced_goals.length !== 1 ? 's' : ''}
              </button>
            {/if}
            {#if prompt.daily_references.length > 0}
              <button
                class="flex items-center gap-1 px-2 py-1 bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-300 rounded hover:bg-green-100 dark:hover:bg-green-900/30 transition-colors"
                on:click|stopPropagation={() => openReferencesModal(prompt)}
              >
                📅 {prompt.daily_references.length} daily note{prompt.daily_references.length !== 1 ? 's' : ''}
              </button>
            {/if}
            {#if prompt.related_audits.length > 0}
              <button
                class="flex items-center gap-1 px-2 py-1 bg-orange-50 dark:bg-orange-900/20 text-orange-700 dark:text-orange-300 rounded hover:bg-orange-100 dark:hover:bg-orange-900/30 transition-colors"
                on:click|stopPropagation={() => openReferencesModal(prompt)}
              >
                🔍 {prompt.related_audits.length} audit{prompt.related_audits.length !== 1 ? 's' : ''}
              </button>
            {/if}
          </div>
        </div>
      {/each}
    </div>
  {/if}
</div>

<!-- Detail Modal -->
{#if showDetailModal && selectedPrompt}
  <div
    class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
    on:click={closeDetailModal}
  >
    <div
      class="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-4xl w-full max-h-[85vh] overflow-y-auto"
      on:click|stopPropagation
    >
      <div class="sticky top-0 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6 py-4 flex items-center justify-between">
        <div class="flex-1 min-w-0">
          <h2 class="text-2xl font-bold text-gray-900 dark:text-white truncate">
            {selectedPrompt.title}
          </h2>
          {#if selectedPrompt.prompt_id}
            <p class="text-sm font-mono text-gray-500 dark:text-gray-400 mt-1">
              {selectedPrompt.prompt_id}
            </p>
          {/if}
        </div>
        <button
          on:click={closeDetailModal}
          class="ml-4 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 text-2xl flex-shrink-0"
        >
          ✕
        </button>
      </div>

      <div class="px-6 py-4 space-y-4">
        <!-- Metadata Grid -->
        <div class="grid grid-cols-2 gap-4 text-sm">
          {#if selectedPrompt.agent}
            <div>
              <span class="font-medium text-gray-600 dark:text-gray-400">Agent:</span>
              <p class="mt-1">
                <span class="inline-block px-2 py-1 text-xs font-medium rounded {getAgentBadgeClass(selectedPrompt.agent)}">
                  {selectedPrompt.agent}
                </span>
              </p>
            </div>
          {/if}
          {#if selectedPrompt.purpose}
            <div>
              <span class="font-medium text-gray-600 dark:text-gray-400">Purpose:</span>
              <p class="text-gray-900 dark:text-white mt-1">{selectedPrompt.purpose}</p>
            </div>
          {/if}
          {#if selectedPrompt.origin}
            <div>
              <span class="font-medium text-gray-600 dark:text-gray-400">Origin:</span>
              <p class="text-gray-900 dark:text-white mt-1">{selectedPrompt.origin}</p>
            </div>
          {/if}
          {#if selectedPrompt.status}
            <div>
              <span class="font-medium text-gray-600 dark:text-gray-400">Status:</span>
              <p class="mt-1">
                <span class="inline-block px-2 py-1 text-xs font-medium rounded {getStatusBadgeClass(selectedPrompt.status)}">
                  {selectedPrompt.status}
                </span>
              </p>
            </div>
          {/if}
          {#if selectedPrompt.timestamp}
            <div class="col-span-2">
              <span class="font-medium text-gray-600 dark:text-gray-400">Timestamp:</span>
              <p class="text-gray-900 dark:text-white mt-1">{formatTimestamp(selectedPrompt.timestamp)}</p>
            </div>
          {/if}
        </div>

        <!-- Prompt Text -->
        {#if selectedPrompt.prompt_text}
          <div>
            <h3 class="font-medium text-gray-600 dark:text-gray-400 mb-2">Prompt Text</h3>
            <div class="bg-gray-50 dark:bg-gray-900 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
              <pre class="text-sm text-gray-900 dark:text-white whitespace-pre-wrap font-mono">{selectedPrompt.prompt_text}</pre>
            </div>
          </div>
        {/if}

        <!-- Cross-References -->
        <div class="pt-4 border-t border-gray-200 dark:border-gray-700">
          <h3 class="font-medium text-gray-900 dark:text-white mb-3">Cross-References</h3>
          <div class="space-y-3">
            {#if selectedPrompt.referenced_goals.length > 0}
              <div>
                <p class="text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">
                  Referenced Goals ({selectedPrompt.referenced_goals.length})
                </p>
                <div class="flex flex-wrap gap-2">
                  {#each selectedPrompt.referenced_goals as goalId}
                    <span class="px-2 py-1 bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300 rounded text-sm">
                      {goalId}
                    </span>
                  {/each}
                </div>
              </div>
            {/if}

            {#if selectedPrompt.daily_references.length > 0}
              <div>
                <p class="text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">
                  Daily Note References ({selectedPrompt.daily_references.length})
                </p>
                <div class="flex flex-wrap gap-2">
                  {#each selectedPrompt.daily_references.slice(0, 10) as date}
                    <span class="px-2 py-1 bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-300 rounded text-sm font-mono">
                      {date}
                    </span>
                  {/each}
                  {#if selectedPrompt.daily_references.length > 10}
                    <span class="px-2 py-1 text-gray-600 dark:text-gray-400 text-sm">
                      +{selectedPrompt.daily_references.length - 10} more
                    </span>
                  {/if}
                </div>
              </div>
            {/if}

            {#if selectedPrompt.related_audits.length > 0}
              <div>
                <p class="text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">
                  Related Audits ({selectedPrompt.related_audits.length})
                </p>
                <div class="flex flex-wrap gap-2">
                  {#each selectedPrompt.related_audits as auditTitle}
                    <span class="px-2 py-1 bg-orange-50 dark:bg-orange-900/20 text-orange-700 dark:text-orange-300 rounded text-sm">
                      {auditTitle}
                    </span>
                  {/each}
                </div>
              </div>
            {/if}

            {#if selectedPrompt.referenced_goals.length === 0 && selectedPrompt.daily_references.length === 0 && selectedPrompt.related_audits.length === 0}
              <p class="text-sm text-gray-500 dark:text-gray-400 italic">
                No cross-references found
              </p>
            {/if}
          </div>
        </div>
      </div>

      <div class="sticky bottom-0 bg-gray-50 dark:bg-gray-900 px-6 py-4 border-t border-gray-200 dark:border-gray-700 flex justify-end gap-3">
        <button
          on:click={closeDetailModal}
          class="px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
        >
          Close
        </button>
      </div>
    </div>
  </div>
{/if}

<!-- References Modal -->
{#if showReferencesModal && selectedPromptForRefs}
  <div
    class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
    on:click={closeReferencesModal}
  >
    <div
      class="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-2xl w-full max-h-[60vh] overflow-y-auto"
      on:click|stopPropagation
    >
      <div class="sticky top-0 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6 py-4 flex items-center justify-between">
        <h3 class="text-xl font-semibold text-gray-900 dark:text-white">
          Cross-References: {selectedPromptForRefs.title}
        </h3>
        <button
          on:click={closeReferencesModal}
          class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 text-2xl"
        >
          ✕
        </button>
      </div>

      <div class="px-6 py-4 space-y-4">
        {#if selectedPromptForRefs.referenced_goals.length > 0}
          <div>
            <h4 class="font-medium text-gray-900 dark:text-white mb-2">Referenced Goals</h4>
            <div class="space-y-1">
              {#each selectedPromptForRefs.referenced_goals as goalId}
                <div class="px-3 py-2 bg-blue-50 dark:bg-blue-900/20 rounded">
                  <span class="text-blue-700 dark:text-blue-300 font-mono text-sm">{goalId}</span>
                </div>
              {/each}
            </div>
          </div>
        {/if}

        {#if selectedPromptForRefs.daily_references.length > 0}
          <div>
            <h4 class="font-medium text-gray-900 dark:text-white mb-2">Daily Note References</h4>
            <div class="space-y-1">
              {#each selectedPromptForRefs.daily_references as date}
                <div class="px-3 py-2 bg-green-50 dark:bg-green-900/20 rounded">
                  <span class="text-green-700 dark:text-green-300 font-mono text-sm">{date}</span>
                </div>
              {/each}
            </div>
          </div>
        {/if}

        {#if selectedPromptForRefs.related_audits.length > 0}
          <div>
            <h4 class="font-medium text-gray-900 dark:text-white mb-2">Related Audits</h4>
            <div class="space-y-1">
              {#each selectedPromptForRefs.related_audits as auditTitle}
                <div class="px-3 py-2 bg-orange-50 dark:bg-orange-900/20 rounded">
                  <span class="text-orange-700 dark:text-orange-300 text-sm">{auditTitle}</span>
                </div>
              {/each}
            </div>
          </div>
        {/if}
      </div>

      <div class="sticky bottom-0 bg-gray-50 dark:bg-gray-900 px-6 py-4 border-t border-gray-200 dark:border-gray-700 flex justify-end">
        <button
          on:click={closeReferencesModal}
          class="px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
        >
          Close
        </button>
      </div>
    </div>
  </div>
{/if}

<style>
  .line-clamp-3 {
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }
</style>
