<script>
  import { invoke } from '@tauri-apps/api/core'
  import { onMount } from 'svelte'

  let loading = true
  let error = null
  let devMode = false
  let audits = []

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
      audits = await invoke('list_audits')
      error = null
    } catch (err) {
      error = err?.toString?.() ?? String(err)
    } finally {
      loading = false
    }
  }

  function formatDate(value) {
    if (!value) return 'n/a'
    return new Date(value).toLocaleDateString()
  }
</script>

<div>
  <div class="flex items-center justify-between mb-6">
    <div>
      <h2 class="text-3xl font-bold text-gray-900 dark:text-white">Audits</h2>
      <p class="text-sm text-gray-500 dark:text-gray-400">
        Read-only view of 05_AUDITS (scope, date, findings summary)
      </p>
    </div>
    <button class="btn btn-primary" on:click={loadAudits} disabled={loading}>
      {loading ? 'Refreshing…' : 'Refresh'}
    </button>
  </div>

  {#if devMode}
    <div class="card mb-6 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800">
      <h3 class="text-lg font-semibold text-yellow-800 dark:text-yellow-200 mb-2">Tauri not detected</h3>
      <p class="text-yellow-700 dark:text-yellow-200 text-sm">
        Run <code>cargo tauri dev</code> to load audits from the Governance Vault.
      </p>
    </div>
  {/if}

  {#if loading && audits.length === 0}
    <div class="card">
      <p class="text-gray-500 dark:text-gray-400">Loading audits...</p>
    </div>
  {:else if error}
    <div class="card bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800">
      <p class="text-red-800 dark:text-red-200">Error: {error}</p>
    </div>
  {:else}
    <div class="card">
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-xl font-semibold text-gray-900 dark:text-white">Audit Records</h3>
        <span class="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">Read-only</span>
      </div>

      {#if audits.length === 0}
        <p class="text-sm text-gray-500 dark:text-gray-400">No audits found.</p>
      {:else}
        <div class="space-y-3">
          {#each audits as audit}
            <div class="p-4 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
              <div class="flex items-start justify-between gap-3">
                <div>
                  <div class="text-lg font-semibold text-gray-900 dark:text-white">
                    {audit.title}
                  </div>
                  <div class="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    Date: {formatDate(audit.date)} · Scope: {audit.scope || 'n/a'} · Risk: {audit.risk || 'n/a'}
                  </div>
                  <div class="text-sm text-gray-700 dark:text-gray-200 mt-2">
                    {audit.summary || 'No findings summary provided.'}
                  </div>
                </div>
                <span class="text-xs font-mono text-gray-500 dark:text-gray-400">
                  {audit.file_path}
                </span>
              </div>
            </div>
          {/each}
        </div>
      {/if}
    </div>
  {/if}
</div>
