<script>
  import { invoke } from '@tauri-apps/api/core'
  import { onMount } from 'svelte'
  import Toast from './Toast.svelte'

  let loading = true
  let error = null
  let devMode = false
  let data = {
    current_phase: null,
    active_goals: [],
    blocked_goals: [],
    total_goals: 0,
    today_exists: false,
    today_path: '',
    today_mode: null,
    today_goals: [],
    today_blockers: [],
    today_decisions: [],
    recent_decisions: [],
    canon_docs: [],
    warnings: [],
  }

  let creatingNote = false
  let noteDate = new Date().toISOString().split('T')[0]
  let selectedMode = ''
  let goalsInput = ''
  let blockersInput = ''
  let decisionsInput = ''
  const modeOptions = [
    { value: '', label: 'Unspecified' },
    { value: 'light', label: 'Light Day' },
    { value: 'heavy', label: 'Heavy Day' },
    { value: 'review', label: 'Review Day' },
  ]

  let toastShow = false
  let toastMessage = ''
  let toastType = 'success'

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
    await loadDashboard()
  })

  async function loadDashboard() {
    try {
      loading = true
      data = await invoke('get_dashboard_data')
      selectedMode = data.today_mode || ''
      goalsInput = (data.today_goals || []).join('\n')
      blockersInput = (data.today_blockers || []).join('\n')
      decisionsInput = (data.today_decisions || []).join('\n')
      error = null
    } catch (err) {
      error = err?.toString?.() ?? String(err)
    } finally {
      loading = false
    }
  }

  function getStatusBadge(status) {
    const classes = {
      planned: 'badge-planned',
      active: 'badge-active',
      blocked: 'badge-blocked',
      partial: 'badge-partial',
      done: 'badge-completed',
      archived: 'badge-archived',
    }
    return classes[status] || 'badge'
  }

  function formatDate(value) {
    if (!value) return 'n/a'
    return new Date(value).toLocaleDateString()
  }

  async function createDailyNote() {
    if (devMode) {
      toastMessage = 'Tauri is not available. Run `cargo tauri dev` to create notes.'
      toastType = 'error'
      toastShow = true
      return
    }

    try {
      creatingNote = true
      const path = await invoke('create_daily_note', { date: noteDate })
      if (selectedMode) {
        await setDailyMode(false)
      }
      toastMessage = `Daily note ready at ${path}`
      toastType = 'success'
      toastShow = true
      await loadDashboard()
    } catch (err) {
      toastMessage = err?.toString?.() ?? String(err)
      toastType = 'error'
      toastShow = true
    } finally {
      creatingNote = false
    }
  }

  async function setDailyMode(showToast = true) {
    if (devMode) {
      toastMessage = 'Tauri is not available. Run `cargo tauri dev` to edit notes.'
      toastType = 'error'
      toastShow = true
      return
    }
    try {
      await invoke('set_daily_mode', { date: noteDate, mode: selectedMode || null })
      if (showToast) {
        toastMessage = selectedMode
          ? `Mode set to ${selectedMode} for ${noteDate}`
          : `Mode cleared for ${noteDate}`
        toastType = 'success'
        toastShow = true
      }
      await loadDashboard()
    } catch (err) {
      if (showToast) {
        toastMessage = err?.toString?.() ?? String(err)
        toastType = 'error'
        toastShow = true
      }
    }
  }

  function toList(text) {
    return text
      .split('\n')
      .map(s => s.trim())
      .filter(Boolean)
  }

  async function saveDaily() {
    if (devMode) {
      toastMessage = 'Tauri is not available. Run `cargo tauri dev` to edit notes.'
      toastType = 'error'
      toastShow = true
      return
    }
    try {
      await invoke('update_daily_note', {
        payload: {
          date: noteDate,
          mode: selectedMode || null,
          protocol: null,
          goals: toList(goalsInput),
          blockers: toList(blockersInput),
          decisions: toList(decisionsInput),
        },
      })
      toastMessage = 'Daily note saved'
      toastType = 'success'
      toastShow = true
      await loadDashboard()
    } catch (err) {
      toastMessage = err?.toString?.() ?? String(err)
      toastType = 'error'
      toastShow = true
    }
  }
</script>

<div>
  <div class="flex items-center justify-between mb-6">
    <div>
      <h2 class="text-3xl font-bold text-gray-900 dark:text-white">Dashboard</h2>
      <p class="text-sm text-gray-500 dark:text-gray-400">
        Live view of the Governance Vault
      </p>
    </div>
    <button class="btn btn-secondary" on:click={loadDashboard} disabled={loading}>
      {loading ? 'Refreshing…' : 'Refresh'}
    </button>
  </div>

  {#if devMode}
    <div class="card mb-6 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800">
      <h3 class="text-lg font-semibold text-yellow-800 dark:text-yellow-200 mb-2">Tauri not detected</h3>
      <p class="text-yellow-700 dark:text-yellow-200 text-sm">
        Launch with <code>cargo tauri dev</code> to hydrate the dashboard from the Governance Vault.
      </p>
      <p class="text-yellow-700 dark:text-yellow-200 text-sm mt-2">
        The UI remains available for layout verification; data loading is disabled in this mode.
      </p>
    </div>
  {/if}

  {#if loading}
    <div class="card">
      <p class="text-gray-500 dark:text-gray-400">Loading governance data...</p>
    </div>
  {:else if error}
    <div class="card bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800">
      <p class="text-red-800 dark:text-red-200">Error: {error}</p>
    </div>
  {:else}
    <!-- Context and Stats -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
      <div class="card">
        <div class="text-sm font-medium text-gray-500 dark:text-gray-400">Current Phase</div>
        <div class="text-2xl font-bold text-gray-900 dark:text-white mt-2">
          {#if data.current_phase}
            {data.current_phase.phase_id} — {data.current_phase.title}
          {:else}
            Not detected
          {/if}
        </div>
        {#if data.current_phase?.status}
          <div class="text-sm text-gray-500 dark:text-gray-400 mt-1">
            Status: {data.current_phase.status}
          </div>
        {/if}
      </div>

      <div class="card">
        <div class="text-sm font-medium text-gray-500 dark:text-gray-400">Active Goals</div>
        <div class="text-3xl font-bold text-green-600 dark:text-green-400 mt-2">
          {data.active_goals.length}
        </div>
      </div>

      <div class="card">
        <div class="text-sm font-medium text-gray-500 dark:text-gray-400">Blocked Goals</div>
        <div class="text-3xl font-bold text-red-600 dark:text-red-400 mt-2">
          {data.blocked_goals.length}
        </div>
      </div>

      <div class="card">
        <div class="text-sm font-medium text-gray-500 dark:text-gray-400">Total Goals</div>
        <div class="text-3xl font-bold text-gray-900 dark:text-white mt-2">
          {data.total_goals}
        </div>
      </div>
    </div>

    <!-- Today -->
    <div class="card mb-6">
      <div class="flex items-center justify-between gap-4">
        <div>
          <h3 class="text-xl font-semibold text-gray-900 dark:text-white">Today</h3>
          <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
            {#if data.today_exists}
              Daily note exists at <span class="font-mono text-xs">{data.today_path}</span>
            {:else}
              Missing daily note for today.
            {/if}
          </p>
          <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">
            Target date: {noteDate}
          </p>
          {#if data.today_mode}
            <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">
              Current mode: {data.today_mode}
            </p>
          {/if}
        </div>
        <div class="flex items-center gap-3">
          <input
            type="date"
            bind:value={noteDate}
            class="px-3 py-2 rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
          />
          <select
            class="px-3 py-2 rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm"
            bind:value={selectedMode}
            on:change={() => setDailyMode()}
            disabled={devMode}
          >
            {#each modeOptions as option}
              <option value={option.value}>{option.label}</option>
            {/each}
          </select>
          <button class="btn btn-primary" on:click={createDailyNote} disabled={creatingNote || devMode}>
            {creatingNote ? 'Creating...' : data.today_exists ? 'Re-create' : 'Create note'}
          </button>
        </div>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
        <div class="flex flex-col gap-2">
          <label class="text-sm text-gray-500 dark:text-gray-400">Goals</label>
          <textarea
            rows="5"
            bind:value={goalsInput}
            class="w-full px-3 py-2 rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm"
            placeholder="One goal per line"
          />
        </div>
        <div class="flex flex-col gap-2">
          <label class="text-sm text-gray-500 dark:text-gray-400">Blockers</label>
          <textarea
            rows="5"
            bind:value={blockersInput}
            class="w-full px-3 py-2 rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm"
            placeholder="One blocker per line"
          />
        </div>
        <div class="flex flex-col gap-2">
          <label class="text-sm text-gray-500 dark:text-gray-400">Decisions</label>
          <textarea
            rows="5"
            bind:value={decisionsInput}
            class="w-full px-3 py-2 rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm"
            placeholder="One decision per line"
          />
        </div>
      </div>

      <div class="flex justify-end mt-4">
        <button class="btn btn-primary" on:click={saveDaily} disabled={devMode}>
          Save daily note
        </button>
      </div>
    </div>

    <!-- Governance Warnings -->
    <div class="card mb-6">
      <h3 class="text-xl font-semibold text-gray-900 dark:text-white mb-3">Governance Warnings</h3>
      {#if data.warnings.length === 0}
        <p class="text-sm text-gray-500 dark:text-gray-400">No gaps detected.</p>
      {:else}
        <div class="space-y-2">
          {#each data.warnings as warning}
            <div class="p-3 rounded-md border border-yellow-200 dark:border-yellow-800 bg-yellow-50 dark:bg-yellow-900/20">
              <div class="text-xs uppercase tracking-wide text-yellow-700 dark:text-yellow-200 font-semibold">
                {warning.kind}
              </div>
              <div class="text-sm text-gray-800 dark:text-gray-100">{warning.message}</div>
            </div>
          {/each}
        </div>
      {/if}
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
      <!-- Active Goals -->
      <div class="card">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-xl font-semibold text-gray-900 dark:text-white">Active Goals</h3>
          <div class="text-sm text-gray-500 dark:text-gray-400">Showing {data.active_goals.length}</div>
        </div>
        {#if data.active_goals.length === 0}
          <p class="text-sm text-gray-500 dark:text-gray-400">No active goals found.</p>
        {:else}
          <div class="space-y-3">
            {#each data.active_goals as goal}
              <div class="p-4 rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800">
                <div class="flex items-center gap-2">
                  <span class="font-mono text-sm font-semibold text-primary-600 dark:text-primary-300">{goal.goal_id}</span>
                  <span class="badge {getStatusBadge(goal.status)}">{goal.status}</span>
                  {#if goal.phase}
                    <span class="text-xs text-gray-500 dark:text-gray-400">Phase {goal.phase}</span>
                  {/if}
                  {#if goal.updated}
                    <span class="text-xs text-gray-500 dark:text-gray-400">Updated {formatDate(goal.updated)}</span>
                  {/if}
                </div>
                <p class="text-gray-900 dark:text-white font-semibold mt-1">{goal.title}</p>
                <div class="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  {#if goal.dependencies.length > 0}
                    Dependencies: {goal.dependencies.join(', ')}
                  {:else}
                    No dependencies
                  {/if}
                </div>
              </div>
            {/each}
          </div>
        {/if}
      </div>

      <!-- Blockers -->
      <div class="card">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-xl font-semibold text-gray-900 dark:text-white">Blockers</h3>
          <div class="text-sm text-gray-500 dark:text-gray-400">Explicitly visible</div>
        </div>
        {#if data.blocked_goals.length === 0}
          <p class="text-sm text-gray-500 dark:text-gray-400">No blocked goals.</p>
        {:else}
          <div class="space-y-3">
            {#each data.blocked_goals as goal}
              <div class="p-4 rounded-lg border border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/20">
                <div class="flex items-center gap-2">
                  <span class="font-mono text-sm font-semibold text-red-700 dark:text-red-300">{goal.goal_id}</span>
                  <span class="badge {getStatusBadge(goal.status)}">{goal.status}</span>
                  {#if goal.phase}
                    <span class="text-xs text-red-700 dark:text-red-200">Phase {goal.phase}</span>
                  {/if}
                </div>
                <p class="text-gray-900 dark:text-white font-semibold mt-1">{goal.title}</p>
              </div>
            {/each}
          </div>
        {/if}
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Recent Decisions -->
      <div class="card">
        <h3 class="text-xl font-semibold text-gray-900 dark:text-white mb-3">Recent Decisions</h3>
        {#if data.recent_decisions.length === 0}
          <p class="text-sm text-gray-500 dark:text-gray-400">No decisions found.</p>
        {:else}
          <div class="space-y-2">
            {#each data.recent_decisions as decision}
              <div class="p-3 rounded-md border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
                <div class="flex items-center justify-between">
                  <div>
                    <div class="font-semibold text-gray-900 dark:text-white">{decision.title}</div>
                    <div class="text-xs text-gray-500 dark:text-gray-400">
                      {decision.decision_id}
                      {#if decision.status}
                        · {decision.status}
                      {/if}
                    </div>
                  </div>
                  <div class="text-xs text-gray-500 dark:text-gray-400">
                    {formatDate(decision.updated || decision.date)}
                  </div>
                </div>
              </div>
            {/each}
          </div>
        {/if}
      </div>

      <!-- Canon Snapshot -->
      <div class="card">
        <div class="flex items-center justify-between mb-3">
          <h3 class="text-xl font-semibold text-gray-900 dark:text-white">Canon Snapshot</h3>
          <span class="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">Immutable</span>
        </div>
        {#if data.canon_docs.length === 0}
          <p class="text-sm text-gray-500 dark:text-gray-400">No canon documents found under CONSTITUTION/.</p>
        {:else}
          <ul class="space-y-2">
            {#each data.canon_docs as doc}
              <li class="flex items-center justify-between p-3 rounded-md border border-gray-200 dark:border-gray-700">
                <div>
                  <div class="font-semibold text-gray-900 dark:text-white">{doc.title}</div>
                  <div class="text-xs font-mono text-gray-500 dark:text-gray-400">{doc.file_path}</div>
                </div>
                <span class="text-xs text-gray-500 dark:text-gray-400">read-only</span>
              </li>
            {/each}
          </ul>
        {/if}
      </div>
    </div>
  {/if}
</div>

<Toast bind:show={toastShow} message={toastMessage} type={toastType} />
