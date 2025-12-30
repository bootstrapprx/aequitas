<script>
  import { invoke } from '@tauri-apps/api/core'
  import { onMount } from 'svelte'
  import Toast from './Toast.svelte'

  let loading = true
  let error = null
  let devMode = false
  let audits = []
  let filteredAudits = []
  let riskFilter = 'all'
  let searchQuery = ''

  let toastShow = false
  let toastMessage = ''
  let toastType = 'success'

  // Modal state for viewing audit details
  let showDetailModal = false
  let selectedAudit = null

  // Cross-reference modal state
  let showReferencesModal = false
  let selectedAuditForRefs = null

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
    await loadAudits()
  })

  async function loadAudits() {
    try {
      loading = true
      const result = await invoke('get_enriched_audits')
      audits = result
      applyFilters()
      error = null
    } catch (err) {
      error = err?.toString?.() ?? String(err)
    } finally {
      loading = false
    }
  }

  function applyFilters() {
    let filtered = audits

    if (riskFilter !== 'all') {
      filtered = filtered.filter(audit =>
        audit.risk?.toLowerCase() === riskFilter.toLowerCase()
      )
    }

    if (searchQuery) {
      filtered = filtered.filter(audit => {
        const q = searchQuery.toLowerCase()
        return (
          audit.title.toLowerCase().includes(q) ||
          (audit.scope && audit.scope.toLowerCase().includes(q)) ||
          (audit.auditor && audit.auditor.toLowerCase().includes(q)) ||
          (audit.summary && audit.summary.toLowerCase().includes(q))
        )
      })
    }

    // Sort by date (newest first)
    filtered.sort((a, b) => {
      if (!a.date) return 1
      if (!b.date) return -1
      return b.date.localeCompare(a.date)
    })

    filteredAudits = filtered
  }

  function getRiskBadgeClass(risk) {
    if (!risk) return 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300'
    switch (risk.toLowerCase()) {
      case 'critical':
        return 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300'
      case 'high':
        return 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-300'
      case 'medium':
        return 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-300'
      case 'low':
        return 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300'
      default:
        return 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300'
    }
  }

  function openDetailModal(audit) {
    selectedAudit = audit
    showDetailModal = true
  }

  function closeDetailModal() {
    showDetailModal = false
    selectedAudit = null
  }

  function openReferencesModal(audit) {
    selectedAuditForRefs = audit
    showReferencesModal = true
  }

  function closeReferencesModal() {
    showReferencesModal = false
    selectedAuditForRefs = null
  }

  function showToast(message, type = 'success') {
    toastMessage = message
    toastType = type
    toastShow = true
  }

  $: {
    searchQuery
    riskFilter
    applyFilters()
  }
</script>

<div class="p-6">
  <Toast bind:show={toastShow} message={toastMessage} type={toastType} />

  <div class="mb-6">
    <h1 class="text-3xl font-bold text-gray-900 dark:text-white mb-2">Audit Records</h1>
    <p class="text-gray-600 dark:text-gray-400">
      Review governance audit findings and cross-references
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
      <p class="text-red-800 dark:text-red-200 font-medium">Error loading audits:</p>
      <p class="text-red-700 dark:text-red-300 mt-1">{error}</p>
    </div>
  {/if}

  <!-- Filters -->
  <div class="flex flex-wrap gap-4 mb-6">
    <div class="flex-1 min-w-[300px]">
      <input
        type="text"
        placeholder="Search audits (title, scope, auditor, summary)..."
        bind:value={searchQuery}
        class="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent"
      />
    </div>
    <select
      bind:value={riskFilter}
      class="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500"
    >
      <option value="all">All Risk Levels</option>
      <option value="critical">Critical</option>
      <option value="high">High</option>
      <option value="medium">Medium</option>
      <option value="low">Low</option>
    </select>
  </div>

  {#if loading}
    <div class="flex items-center justify-center py-12">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
    </div>
  {:else if filteredAudits.length === 0}
    <div class="text-center py-12">
      <p class="text-gray-500 dark:text-gray-400 text-lg">
        {searchQuery || riskFilter !== 'all' ? 'No audits match your filters' : 'No audit records found'}
      </p>
    </div>
  {:else}
    <!-- Audit Cards -->
    <div class="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      {#each filteredAudits as audit (audit.file_path)}
        <div
          class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4 hover:shadow-lg transition-shadow cursor-pointer"
          on:click={() => openDetailModal(audit)}
        >
          <!-- Header -->
          <div class="flex items-start justify-between mb-3">
            <h3 class="font-semibold text-gray-900 dark:text-white text-lg flex-1">
              {audit.title}
            </h3>
            {#if audit.risk}
              <span class="ml-2 px-2 py-1 text-xs font-medium rounded {getRiskBadgeClass(audit.risk)}">
                {audit.risk}
              </span>
            {/if}
          </div>

          <!-- Metadata -->
          <div class="space-y-1 text-sm text-gray-600 dark:text-gray-400 mb-3">
            {#if audit.date}
              <div class="flex items-center gap-2">
                <span class="font-medium">Date:</span>
                <span>{audit.date}</span>
              </div>
            {/if}
            {#if audit.scope}
              <div class="flex items-center gap-2">
                <span class="font-medium">Scope:</span>
                <span class="truncate">{audit.scope}</span>
              </div>
            {/if}
            {#if audit.auditor}
              <div class="flex items-center gap-2">
                <span class="font-medium">Auditor:</span>
                <span>{audit.auditor}</span>
              </div>
            {/if}
          </div>

          <!-- Summary -->
          {#if audit.summary}
            <p class="text-sm text-gray-700 dark:text-gray-300 mb-3 line-clamp-2">
              {audit.summary}
            </p>
          {/if}

          <!-- Cross-References -->
          <div class="flex flex-wrap gap-2 text-xs">
            {#if audit.referenced_goals.length > 0}
              <button
                class="flex items-center gap-1 px-2 py-1 bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300 rounded hover:bg-blue-100 dark:hover:bg-blue-900/30 transition-colors"
                on:click|stopPropagation={() => openReferencesModal(audit)}
              >
                🎯 {audit.referenced_goals.length} goal{audit.referenced_goals.length !== 1 ? 's' : ''}
              </button>
            {/if}
            {#if audit.daily_references.length > 0}
              <button
                class="flex items-center gap-1 px-2 py-1 bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-300 rounded hover:bg-green-100 dark:hover:bg-green-900/30 transition-colors"
                on:click|stopPropagation={() => openReferencesModal(audit)}
              >
                📅 {audit.daily_references.length} daily note{audit.daily_references.length !== 1 ? 's' : ''}
              </button>
            {/if}
            {#if audit.related_prompts.length > 0}
              <button
                class="flex items-center gap-1 px-2 py-1 bg-purple-50 dark:bg-purple-900/20 text-purple-700 dark:text-purple-300 rounded hover:bg-purple-100 dark:hover:bg-purple-900/30 transition-colors"
                on:click|stopPropagation={() => openReferencesModal(audit)}
              >
                💡 {audit.related_prompts.length} prompt{audit.related_prompts.length !== 1 ? 's' : ''}
              </button>
            {/if}
          </div>
        </div>
      {/each}
    </div>
  {/if}
</div>

<!-- Detail Modal -->
{#if showDetailModal && selectedAudit}
  <div
    class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
    on:click={closeDetailModal}
  >
    <div
      class="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-3xl w-full max-h-[80vh] overflow-y-auto"
      on:click|stopPropagation
    >
      <div class="sticky top-0 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6 py-4 flex items-center justify-between">
        <h2 class="text-2xl font-bold text-gray-900 dark:text-white">
          {selectedAudit.title}
        </h2>
        <button
          on:click={closeDetailModal}
          class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 text-2xl"
        >
          ✕
        </button>
      </div>

      <div class="px-6 py-4 space-y-4">
        <!-- Metadata Grid -->
        <div class="grid grid-cols-2 gap-4 text-sm">
          {#if selectedAudit.date}
            <div>
              <span class="font-medium text-gray-600 dark:text-gray-400">Date:</span>
              <p class="text-gray-900 dark:text-white mt-1">{selectedAudit.date}</p>
            </div>
          {/if}
          {#if selectedAudit.risk}
            <div>
              <span class="font-medium text-gray-600 dark:text-gray-400">Risk Level:</span>
              <p class="mt-1">
                <span class="inline-block px-2 py-1 text-xs font-medium rounded {getRiskBadgeClass(selectedAudit.risk)}">
                  {selectedAudit.risk}
                </span>
              </p>
            </div>
          {/if}
          {#if selectedAudit.scope}
            <div>
              <span class="font-medium text-gray-600 dark:text-gray-400">Scope:</span>
              <p class="text-gray-900 dark:text-white mt-1">{selectedAudit.scope}</p>
            </div>
          {/if}
          {#if selectedAudit.auditor}
            <div>
              <span class="font-medium text-gray-600 dark:text-gray-400">Auditor:</span>
              <p class="text-gray-900 dark:text-white mt-1">{selectedAudit.auditor}</p>
            </div>
          {/if}
        </div>

        <!-- Summary -->
        {#if selectedAudit.summary}
          <div>
            <h3 class="font-medium text-gray-600 dark:text-gray-400 mb-2">Summary</h3>
            <p class="text-gray-900 dark:text-white">{selectedAudit.summary}</p>
          </div>
        {/if}

        <!-- Cross-References -->
        <div class="pt-4 border-t border-gray-200 dark:border-gray-700">
          <h3 class="font-medium text-gray-900 dark:text-white mb-3">Cross-References</h3>
          <div class="space-y-3">
            {#if selectedAudit.referenced_goals.length > 0}
              <div>
                <p class="text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">
                  Referenced Goals ({selectedAudit.referenced_goals.length})
                </p>
                <div class="flex flex-wrap gap-2">
                  {#each selectedAudit.referenced_goals as goalId}
                    <span class="px-2 py-1 bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300 rounded text-sm">
                      {goalId}
                    </span>
                  {/each}
                </div>
              </div>
            {/if}

            {#if selectedAudit.daily_references.length > 0}
              <div>
                <p class="text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">
                  Daily Note References ({selectedAudit.daily_references.length})
                </p>
                <div class="flex flex-wrap gap-2">
                  {#each selectedAudit.daily_references.slice(0, 10) as date}
                    <span class="px-2 py-1 bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-300 rounded text-sm font-mono">
                      {date}
                    </span>
                  {/each}
                  {#if selectedAudit.daily_references.length > 10}
                    <span class="px-2 py-1 text-gray-600 dark:text-gray-400 text-sm">
                      +{selectedAudit.daily_references.length - 10} more
                    </span>
                  {/if}
                </div>
              </div>
            {/if}

            {#if selectedAudit.related_prompts.length > 0}
              <div>
                <p class="text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">
                  Related Prompts ({selectedAudit.related_prompts.length})
                </p>
                <div class="flex flex-wrap gap-2">
                  {#each selectedAudit.related_prompts as promptId}
                    <span class="px-2 py-1 bg-purple-50 dark:bg-purple-900/20 text-purple-700 dark:text-purple-300 rounded text-sm">
                      {promptId}
                    </span>
                  {/each}
                </div>
              </div>
            {/if}

            {#if selectedAudit.referenced_goals.length === 0 && selectedAudit.daily_references.length === 0 && selectedAudit.related_prompts.length === 0}
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
{#if showReferencesModal && selectedAuditForRefs}
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
          Cross-References: {selectedAuditForRefs.title}
        </h3>
        <button
          on:click={closeReferencesModal}
          class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 text-2xl"
        >
          ✕
        </button>
      </div>

      <div class="px-6 py-4 space-y-4">
        {#if selectedAuditForRefs.referenced_goals.length > 0}
          <div>
            <h4 class="font-medium text-gray-900 dark:text-white mb-2">Referenced Goals</h4>
            <div class="space-y-1">
              {#each selectedAuditForRefs.referenced_goals as goalId}
                <div class="px-3 py-2 bg-blue-50 dark:bg-blue-900/20 rounded">
                  <span class="text-blue-700 dark:text-blue-300 font-mono text-sm">{goalId}</span>
                </div>
              {/each}
            </div>
          </div>
        {/if}

        {#if selectedAuditForRefs.daily_references.length > 0}
          <div>
            <h4 class="font-medium text-gray-900 dark:text-white mb-2">Daily Note References</h4>
            <div class="space-y-1">
              {#each selectedAuditForRefs.daily_references as date}
                <div class="px-3 py-2 bg-green-50 dark:bg-green-900/20 rounded">
                  <span class="text-green-700 dark:text-green-300 font-mono text-sm">{date}</span>
                </div>
              {/each}
            </div>
          </div>
        {/if}

        {#if selectedAuditForRefs.related_prompts.length > 0}
          <div>
            <h4 class="font-medium text-gray-900 dark:text-white mb-2">Related Prompts</h4>
            <div class="space-y-1">
              {#each selectedAuditForRefs.related_prompts as promptId}
                <div class="px-3 py-2 bg-purple-50 dark:bg-purple-900/20 rounded">
                  <span class="text-purple-700 dark:text-purple-300 font-mono text-sm">{promptId}</span>
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
  .line-clamp-2 {
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }
</style>
