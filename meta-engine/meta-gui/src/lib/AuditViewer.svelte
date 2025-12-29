<script>
  import { invoke } from '@tauri-apps/api/core'
  import { onMount } from 'svelte'

  let loading = true
  let error = null
  let audit = {
    results: [],
    total_files: 0,
  }

  let errors = []
  let warnings = []
  let infos = []

  onMount(async () => {
    await runAudit()
  })

  async function runAudit() {
    try {
      loading = true
      audit = await invoke('run_audit')

      errors = audit.results.filter(r => r.severity === 'Error')
      warnings = audit.results.filter(r => r.severity === 'Warning')
      infos = audit.results.filter(r => r.severity === 'Info')

      loading = false
    } catch (err) {
      error = err
      loading = false
    }
  }

  function getSeverityIcon(severity) {
    const icons = {
      Error: '❌',
      Warning: '⚠',
      Info: 'ℹ',
    }
    return icons[severity] || '•'
  }

  function getSeverityClass(severity) {
    const classes = {
      Error: 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800',
      Warning: 'bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-800',
      Info: 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800',
    }
    return classes[severity] || ''
  }

  function getSeverityTextClass(severity) {
    const classes = {
      Error: 'text-red-800 dark:text-red-200',
      Warning: 'text-yellow-800 dark:text-yellow-200',
      Info: 'text-blue-800 dark:text-blue-200',
    }
    return classes[severity] || ''
  }
</script>

<div>
  <div class="flex items-center justify-between mb-6">
    <h2 class="text-3xl font-bold text-gray-900 dark:text-white">Governance Audit</h2>
    <button class="btn btn-primary" on:click={runAudit} disabled={loading}>
      {loading ? 'Running...' : 'Run Audit'}
    </button>
  </div>

  {#if loading && audit.results.length === 0}
    <div class="card">
      <p class="text-gray-500 dark:text-gray-400">Running governance audit...</p>
    </div>
  {:else if error}
    <div class="card bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800">
      <p class="text-red-800 dark:text-red-200">Error: {error}</p>
    </div>
  {:else}
    <!-- Summary Cards -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
      <div class="card">
        <div class="text-sm font-medium text-gray-500 dark:text-gray-400">Total Files</div>
        <div class="text-3xl font-bold text-gray-900 dark:text-white mt-2">
          {audit.total_files}
        </div>
      </div>

      <div class="card">
        <div class="text-sm font-medium text-gray-500 dark:text-gray-400">Errors</div>
        <div class="text-3xl font-bold text-red-600 dark:text-red-400 mt-2">
          {errors.length}
        </div>
      </div>

      <div class="card">
        <div class="text-sm font-medium text-gray-500 dark:text-gray-400">Warnings</div>
        <div class="text-3xl font-bold text-yellow-600 dark:text-yellow-400 mt-2">
          {warnings.length}
        </div>
      </div>

      <div class="card">
        <div class="text-sm font-medium text-gray-500 dark:text-gray-400">Info</div>
        <div class="text-3xl font-bold text-blue-600 dark:text-blue-400 mt-2">
          {infos.length}
        </div>
      </div>
    </div>

    <!-- Status -->
    {#if errors.length === 0 && warnings.length === 0}
      <div class="card bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 mb-6">
        <div class="flex items-center gap-3">
          <span class="text-4xl">✓</span>
          <div>
            <h3 class="text-lg font-semibold text-green-800 dark:text-green-200">
              Governance is Valid
            </h3>
            <p class="text-green-700 dark:text-green-300 text-sm">
              No errors or warnings found
            </p>
          </div>
        </div>
      </div>
    {/if}

    <!-- Errors -->
    {#if errors.length > 0}
      <div class="card mb-6">
        <h3 class="text-xl font-semibold text-red-600 dark:text-red-400 mb-4 flex items-center gap-2">
          <span>{getSeverityIcon('Error')}</span>
          Errors ({errors.length})
        </h3>
        <div class="space-y-3">
          {#each errors as result}
            <div class="p-4 rounded-lg border {getSeverityClass('Error')}">
              <div class="flex items-start gap-3">
                <span class="text-xl">{getSeverityIcon('Error')}</span>
                <div class="flex-1">
                  <div class="font-mono text-sm {getSeverityTextClass('Error')} mb-1">
                    {result.file.replace(/^governance\//, '')}
                    {#if result.line}
                      :{result.line}
                    {/if}
                  </div>
                  <p class="{getSeverityTextClass('Error')}">
                    {result.message}
                  </p>
                </div>
              </div>
            </div>
          {/each}
        </div>
      </div>
    {/if}

    <!-- Warnings -->
    {#if warnings.length > 0}
      <div class="card mb-6">
        <h3 class="text-xl font-semibold text-yellow-600 dark:text-yellow-400 mb-4 flex items-center gap-2">
          <span>{getSeverityIcon('Warning')}</span>
          Warnings ({warnings.length})
        </h3>
        <div class="space-y-3">
          {#each warnings as result}
            <div class="p-4 rounded-lg border {getSeverityClass('Warning')}">
              <div class="flex items-start gap-3">
                <span class="text-xl">{getSeverityIcon('Warning')}</span>
                <div class="flex-1">
                  <div class="font-mono text-sm {getSeverityTextClass('Warning')} mb-1">
                    {result.file.replace(/^governance\//, '')}
                    {#if result.line}
                      :{result.line}
                    {/if}
                  </div>
                  <p class="{getSeverityTextClass('Warning')}">
                    {result.message}
                  </p>
                </div>
              </div>
            </div>
          {/each}
        </div>
      </div>
    {/if}

    <!-- Info -->
    {#if infos.length > 0}
      <div class="card">
        <h3 class="text-xl font-semibold text-blue-600 dark:text-blue-400 mb-4 flex items-center gap-2">
          <span>{getSeverityIcon('Info')}</span>
          Info ({infos.length})
        </h3>
        <div class="space-y-3">
          {#each infos as result}
            <div class="p-4 rounded-lg border {getSeverityClass('Info')}">
              <div class="flex items-start gap-3">
                <span class="text-xl">{getSeverityIcon('Info')}</span>
                <div class="flex-1">
                  <div class="font-mono text-sm {getSeverityTextClass('Info')} mb-1">
                    {result.file.replace(/^governance\//, '')}
                  </div>
                  <p class="{getSeverityTextClass('Info')}">
                    {result.message}
                  </p>
                </div>
              </div>
            </div>
          {/each}
        </div>
      </div>
    {/if}
  {/if}
</div>
