<script>
  import { invoke } from '@tauri-apps/api/core'
  import { onMount } from 'svelte'
  import Toast from './Toast.svelte'
  import PhaseEditor from './PhaseEditor.svelte'

  let loading = true
  let error = null
  let devMode = false

  // Editor state
  let showPhaseEditor = false
  let editingPhase = null
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
    protocols: [],
    latest_daily: null,
    active_by_phase: [],
    orphaned_goals: [],
    stale_goals: [],
    top_blocked: [],
    warnings: [],
  }

  let creatingNote = false
  let noteDate = new Date().toISOString().split('T')[0]
  let selectedMode = ''
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

  function openNewPhaseEditor() {
    editingPhase = null
    showPhaseEditor = true
  }

  function openEditPhaseEditor(phase) {
    editingPhase = phase
    showPhaseEditor = true
  }

  function closePhaseEditor() {
    showPhaseEditor = false
    editingPhase = null
  }

  async function handlePhaseSaved() {
    toastMessage = editingPhase ? 'Phase updated successfully!' : 'Phase created successfully!'
    toastType = 'success'
    toastShow = true
    await loadDashboard()
  }

  async function handlePhaseActivated() {
    toastMessage = 'Phase activated successfully!'
    toastType = 'success'
    toastShow = true
    await loadDashboard()
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
        <div class="flex items-center justify-between mb-2">
          <div class="text-sm font-medium text-gray-500 dark:text-gray-400">Current Phase</div>
          {#if data.current_phase}
            <button
              class="px-2 py-1 bg-gray-600 hover:bg-gray-700 text-white text-xs rounded transition-colors"
              on:click={() => openEditPhaseEditor(data.current_phase)}
              disabled={devMode}
              title="Edit phase"
            >
              Edit
            </button>
          {:else}
            <button
              class="px-2 py-1 bg-blue-600 hover:bg-blue-700 text-white text-xs rounded transition-colors"
              on:click={openNewPhaseEditor}
              disabled={devMode}
            >
              New
            </button>
          {/if}
        </div>
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
          <h3 class="text-xl font-semibold text-gray-900 dark:text-white">Today’s Focus</h3>
          <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
            {#if data.latest_daily}
              Latest daily: {data.latest_daily.date} {#if data.latest_daily.mode}· {data.latest_daily.mode}{/if}
            {:else}
              No daily note found. Create one to anchor execution.
            {/if}
          </p>
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

      {#if data.latest_daily}
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
          <div>
            <div class="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400 mb-1">Goals</div>
            {#if data.latest_daily.goals.length === 0}
              <p class="text-sm text-gray-500 dark:text-gray-400">No goals linked.</p>
            {:else}
              <ul class="space-y-1 text-sm text-gray-900 dark:text-white">
                {#each data.latest_daily.goals as goal}
                  <li>• {goal}</li>
                {/each}
              </ul>
            {/if}
          </div>
          <div>
            <div class="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400 mb-1">Blockers</div>
            {#if data.latest_daily.blockers.length === 0}
              <p class="text-sm text-gray-500 dark:text-gray-400">None recorded.</p>
            {:else}
              <ul class="space-y-1 text-sm text-gray-900 dark:text-white">
                {#each data.latest_daily.blockers as blocker}
                  <li>• {blocker}</li>
                {/each}
              </ul>
            {/if}
          </div>
          <div>
            <div class="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400 mb-1">Decisions</div>
            {#if data.latest_daily.decisions.length === 0}
              <p class="text-sm text-gray-500 dark:text-gray-400">No decisions linked.</p>
            {:else}
              <ul class="space-y-1 text-sm text-gray-900 dark:text-white">
                {#each data.latest_daily.decisions as decision}
                  <li>• {decision}</li>
                {/each}
              </ul>
            {/if}
          </div>
        </div>
      {:else}
        <p class="text-sm text-gray-500 dark:text-gray-400 mt-3">Use the Daily Editor to seed today’s plan.</p>
      {/if}
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

    <div class="card mb-6">
      <div class="flex items-center justify-between mb-3">
        <h3 class="text-xl font-semibold text-gray-900 dark:text-white">Active Goals by Phase</h3>
        <span class="text-xs text-gray-500 dark:text-gray-400">Phase-aware</span>
      </div>
      {#if data.active_by_phase.length === 0}
        <p class="text-sm text-gray-500 dark:text-gray-400">No phases detected.</p>
      {:else}
        <div class="grid md:grid-cols-2 gap-4">
          {#each data.active_by_phase as bucket}
            <div class="p-4 rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800">
              <div class="flex items-center justify-between">
                <div class="text-sm font-semibold text-gray-900 dark:text-white">
                  {bucket.phase.phase_id} — {bucket.phase.title}
                </div>
                <span class="text-xs text-gray-500 dark:text-gray-400">{bucket.active_goals.length} active</span>
              </div>
              {#if bucket.active_goals.length === 0}
                <p class="text-xs text-gray-500 dark:text-gray-400 mt-2">No active goals.</p>
              {:else}
                <ul class="space-y-1 mt-2 text-sm text-gray-900 dark:text-white">
                  {#each bucket.active_goals as goal}
                    <li class="flex items-center gap-2">
                      <span class="font-mono text-xs text-primary-700 dark:text-primary-300">{goal.goal_id}</span>
                      <span class="badge {getStatusBadge(goal.status)}">{goal.status}</span>
                      <span>{goal.title}</span>
                    </li>
                  {/each}
                </ul>
              {/if}
            </div>
          {/each}
        </div>
      {/if}
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
      <div class="card">
        <h3 class="text-xl font-semibold text-gray-900 dark:text-white mb-3">Blocked Goals (Top 3)</h3>
        {#if data.top_blocked.length === 0}
          <p class="text-sm text-gray-500 dark:text-gray-400">No blocked goals.</p>
        {:else}
          <div class="space-y-2">
            {#each data.top_blocked as goal}
              <div class="p-3 rounded-lg border border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/20">
                <div class="flex items-center gap-2">
                  <span class="font-mono text-sm font-semibold text-red-700 dark:text-red-300">{goal.goal_id}</span>
                  <span class="badge {getStatusBadge(goal.status)}">{goal.status}</span>
                  {#if goal.phase}
                    <span class="text-xs text-red-700 dark:text-red-200">Phase {goal.phase}</span>
                  {/if}
                </div>
                <div class="text-sm text-gray-900 dark:text-white">{goal.title}</div>
              </div>
            {/each}
          </div>
        {/if}
      </div>
      <div class="card">
        <h3 class="text-xl font-semibold text-gray-900 dark:text-white mb-3">Orphaned Goals</h3>
        {#if data.orphaned_goals.length === 0}
          <p class="text-sm text-gray-500 dark:text-gray-400">All goals have a phase.</p>
        {:else}
          <ul class="space-y-1 text-sm text-gray-900 dark:text-white">
            {#each data.orphaned_goals as goal}
              <li class="flex items-center gap-2">
                <span class="font-mono text-xs text-orange-700 dark:text-orange-300">{goal.goal_id}</span>
                <span class="badge {getStatusBadge(goal.status)}">{goal.status}</span>
                <span>{goal.title}</span>
              </li>
            {/each}
          </ul>
        {/if}
      </div>
      <div class="card">
        <div class="flex items-center justify-between mb-1">
          <h3 class="text-xl font-semibold text-gray-900 dark:text-white">Stale Goals</h3>
          <span class="text-xs text-gray-500 dark:text-gray-400">>30 days</span>
        </div>
        {#if data.stale_goals.length === 0}
          <p class="text-sm text-gray-500 dark:text-gray-400">No stale goals detected.</p>
        {:else}
          <ul class="space-y-1 text-sm text-gray-900 dark:text-white">
            {#each data.stale_goals as goal}
              <li class="flex items-center justify-between">
                <div class="flex items-center gap-2">
                  <span class="font-mono text-xs text-gray-800 dark:text-gray-200">{goal.goal_id}</span>
                  <span class="badge {getStatusBadge(goal.status)}">{goal.status}</span>
                  <span>{goal.title}</span>
                </div>
                {#if goal.updated}
                  <span class="text-xs text-gray-500 dark:text-gray-400">Updated {formatDate(goal.updated)}</span>
                {:else}
                  <span class="text-xs text-gray-500 dark:text-gray-400">No update date</span>
                {/if}
              </li>
            {/each}
          </ul>
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
        {#if data.protocols.length > 0}
          <div class="mt-3">
            <div class="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400 mb-1">Protocols</div>
            <ul class="space-y-1">
              {#each data.protocols as doc}
                <li class="flex items-center justify-between p-2 rounded-md border border-gray-200 dark:border-gray-700">
                  <div class="font-semibold text-gray-900 dark:text-white">{doc.title}</div>
                  <span class="text-xs text-gray-500 dark:text-gray-400">{doc.file_path}</span>
                </li>
              {/each}
            </ul>
          </div>
        {/if}
      </div>
    </div>
  {/if}
</div>

{#if showPhaseEditor}
  <PhaseEditor
    phase={editingPhase}
    onClose={closePhaseEditor}
    on:saved={handlePhaseSaved}
    on:activated={handlePhaseActivated}
  />
{/if}

<Toast bind:show={toastShow} message={toastMessage} type={toastType} />
