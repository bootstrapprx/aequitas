<script>
  import { invoke } from '@tauri-apps/api/core'
  import { onMount } from 'svelte'
  import Toast from './Toast.svelte'
  import GoalEditor from './GoalEditor.svelte'

  let loading = true
  let error = null
  let devMode = false
  let goals = []
  let groupedGoals = {}
  let statusFilter = 'all'
  let searchQuery = ''
  let updatingGoalId = null
  let showStatusMenu = null

  let toastShow = false
  let toastMessage = ''
  let toastType = 'success'

  // Editor state
  let showEditor = false
  let editingGoal = null

  const statusOrder = ['planned', 'active', 'blocked', 'partial', 'done', 'archived', 'unknown']

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
    await loadGoals()
  })

  async function loadGoals() {
    try {
      loading = true
      const result = await invoke('get_all_goals')
      goals = result
      applyFilters()
      error = null
    } catch (err) {
      error = err?.toString?.() ?? String(err)
    } finally {
      loading = false
    }
  }

  function applyFilters() {
    let filtered = goals

    if (statusFilter !== 'all') {
      filtered = filtered.filter(goal => goal.status.toLowerCase() === statusFilter)
    }

    if (searchQuery) {
      filtered = filtered.filter(goal => {
        const q = searchQuery.toLowerCase()
        return (
          goal.goal_id.toLowerCase().includes(q) ||
          goal.title.toLowerCase().includes(q) ||
          (goal.owner && goal.owner.toLowerCase().includes(q))
        )
      })
    }

    groupedGoals = groupByPhaseAndStatus(filtered)
  }

  function groupByPhaseAndStatus(goalList) {
    const grouped = {}
    for (const goal of goalList) {
      const phase = goal.phase || 'Unassigned'
      const status = goal.status || 'unknown'
      if (!grouped[phase]) grouped[phase] = {}
      if (!grouped[phase][status]) grouped[phase][status] = []
      grouped[phase][status].push(goal)
    }
    return grouped
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

  async function updateGoalStatus(goalId, newStatus) {
    if (devMode) {
      toastMessage = 'Status changes require Tauri. Run `cargo tauri dev`.'
      toastType = 'error'
      toastShow = true
      return
    }

    try {
      updatingGoalId = goalId
      await invoke('update_goal_status', {
        goalId,
        newStatus,
      })

      toastMessage = `Updated ${goalId} to ${newStatus}`
      toastType = 'success'
      toastShow = true

      await loadGoals()
      showStatusMenu = null
    } catch (err) {
      toastMessage = err?.toString?.() ?? String(err)
      toastType = 'error'
      toastShow = true
    } finally {
      updatingGoalId = null
    }
  }

  function toggleStatusMenu(goalId) {
    showStatusMenu = showStatusMenu === goalId ? null : goalId
  }

  function formatDate(value) {
    if (!value) return 'n/a'
    return new Date(value).toLocaleDateString()
  }

  function openNewGoalEditor() {
    editingGoal = null
    showEditor = true
  }

  function openEditGoalEditor(goal) {
    editingGoal = goal
    showEditor = true
  }

  function closeEditor() {
    showEditor = false
    editingGoal = null
  }

  async function handleGoalSaved() {
    toastMessage = editingGoal ? 'Goal updated successfully!' : 'Goal created successfully!'
    toastType = 'success'
    toastShow = true
    await loadGoals()
  }

  async function handleGoalDeleted() {
    toastMessage = 'Goal deleted successfully!'
    toastType = 'success'
    toastShow = true
    await loadGoals()
  }

  $: {
    searchQuery
    applyFilters()
  }

  const statuses = [
    { value: 'all', label: 'All' },
    { value: 'planned', label: 'Planned' },
    { value: 'active', label: 'Active' },
    { value: 'blocked', label: 'Blocked' },
    { value: 'partial', label: 'Partial' },
    { value: 'done', label: 'Done' },
  ]
</script>

<div>
  <div class="flex items-center justify-between mb-6">
    <div>
      <h2 class="text-3xl font-bold text-gray-900 dark:text-white">Goals</h2>
      <p class="text-sm text-gray-500 dark:text-gray-400">
        Grouped by phase and status from 03_GOALS_EPICS
      </p>
    </div>
    <div class="flex gap-3">
      <button
        class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded transition-colors flex items-center gap-2"
        on:click={openNewGoalEditor}
        disabled={devMode}
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
        </svg>
        New Goal
      </button>
      <button class="btn btn-secondary" on:click={loadGoals} disabled={loading}>
        {loading ? 'Refreshing…' : 'Refresh'}
      </button>
    </div>
  </div>

  {#if devMode}
    <div class="card mb-6 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800">
      <h3 class="text-lg font-semibold text-yellow-800 dark:text-yellow-200 mb-2">Tauri not detected</h3>
      <p class="text-yellow-700 dark:text-yellow-200 text-sm">
        Run <code>cargo tauri dev</code> to load and edit goals from the Governance Vault.
      </p>
    </div>
  {/if}

  {#if loading}
    <div class="card">
      <p class="text-gray-500 dark:text-gray-400">Loading goals...</p>
    </div>
  {:else if error}
    <div class="card bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800">
      <p class="text-red-800 dark:text-red-200">Error: {error}</p>
    </div>
  {:else}
    <!-- Filters -->
    <div class="card mb-6">
      <div class="flex flex-col md:flex-row gap-4">
        <div class="flex gap-2 flex-wrap">
          {#each statuses as status}
            <button
              class="px-4 py-2 rounded-md text-sm font-medium transition-colors {statusFilter === status.value
                ? 'bg-primary-600 text-white'
                : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'}"
              on:click={() => {
                statusFilter = status.value
                applyFilters()
              }}
            >
              {status.label}
            </button>
          {/each}
        </div>

        <div class="flex-1">
          <input
            type="text"
            placeholder="Search goals..."
            bind:value={searchQuery}
            class="w-full px-4 py-2 rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
          />
        </div>
      </div>
    </div>

    {#if Object.keys(groupedGoals).length === 0}
      <div class="card text-center py-12">
        <p class="text-gray-500 dark:text-gray-400">No goals match the current filters.</p>
      </div>
    {:else}
      <div class="space-y-6">
        {#each Object.keys(groupedGoals).sort() as phase}
          <div class="card">
            <div class="flex items-center justify-between mb-3">
              <div>
                <h3 class="text-xl font-semibold text-gray-900 dark:text-white">
                  Phase {phase}
                </h3>
                <p class="text-xs text-gray-500 dark:text-gray-400">
                  Status groups sorted by workflow order
                </p>
              </div>
              <div class="text-sm text-gray-500 dark:text-gray-400">
                {Object.values(groupedGoals[phase]).reduce((acc, list) => acc + list.length, 0)} goals
              </div>
            </div>

            <div class="space-y-4">
              {#each statusOrder as status}
                {#if groupedGoals[phase][status]}
                  <div>
                    <div class="flex items-center gap-2 mb-2">
                      <span class="badge {getStatusBadge(status)}">{status}</span>
                      <span class="text-xs text-gray-500 dark:text-gray-400">
                        {groupedGoals[phase][status].length} goal(s)
                      </span>
                    </div>
                    <div class="space-y-3">
                      {#each groupedGoals[phase][status] as goal}
                        <div class="p-4 rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800">
                          <div class="flex items-start justify-between gap-3">
                            <div class="flex-1">
                              <div class="flex items-center gap-2">
                                <span class="font-mono text-sm font-bold text-primary-600 dark:text-primary-300">
                                  {goal.goal_id}
                                </span>
                                <span class="badge {getStatusBadge(goal.status)}">{goal.status}</span>
                                {#if goal.phase}
                                  <span class="text-xs text-gray-500 dark:text-gray-400">Phase {goal.phase}</span>
                                {/if}
                                {#if goal.updated}
                                  <span class="text-xs text-gray-500 dark:text-gray-400">
                                    Updated {formatDate(goal.updated)}
                                  </span>
                                {/if}
                              </div>
                              <div class="text-gray-900 dark:text-white font-semibold mt-1">
                                {goal.title}
                              </div>
                              <div class="text-xs text-gray-500 dark:text-gray-400 mt-1">
                                Dependencies:
                                {goal.dependencies.length > 0
                                  ? goal.dependencies.join(', ')
                                  : 'None'}
                              </div>
                              <div class="text-xs text-gray-500 dark:text-gray-400 mt-1">
                                Canon: {goal.canon.length > 0 ? goal.canon.join(', ') : 'None'}
                              </div>
                            </div>

                            <div class="flex gap-2">
                              <button
                                class="px-3 py-1 bg-gray-600 hover:bg-gray-700 text-white text-sm rounded transition-colors"
                                on:click={() => openEditGoalEditor(goal)}
                                disabled={devMode}
                                title="Edit goal"
                              >
                                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
                                </svg>
                              </button>

                              <div class="relative">
                                <button
                                  class="btn btn-secondary text-sm"
                                  on:click={() => toggleStatusMenu(goal.goal_id)}
                                  disabled={updatingGoalId === goal.goal_id || devMode}
                                >
                                  {updatingGoalId === goal.goal_id ? 'Updating...' : 'Change Status'}
                                </button>

                                {#if showStatusMenu === goal.goal_id}
                                <div class="absolute right-0 mt-2 w-48 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 z-10">
                                  <div class="py-1">
                                    {#each ['planned', 'active', 'blocked', 'partial', 'done'] as statusOption}
                                      {#if statusOption !== goal.status}
                                        <button
                                          class="w-full text-left px-4 py-2 text-sm hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors {getStatusBadge(statusOption)}"
                                          on:click={() => updateGoalStatus(goal.goal_id, statusOption)}
                                        >
                                          {statusOption}
                                        </button>
                                      {/if}
                                    {/each}
                                  </div>
                                </div>
                              {/if}
                              </div>
                            </div>
                          </div>
                          <div class="text-[11px] text-gray-500 dark:text-gray-400 mt-2 font-mono">
                            {goal.file_path}
                          </div>
                        </div>
                      {/each}
                    </div>
                  </div>
                {/if}
              {/each}
            </div>
          </div>
        {/each}
      </div>
    {/if}
  {/if}
</div>

{#if showEditor}
  <GoalEditor
    goal={editingGoal}
    onClose={closeEditor}
    on:saved={handleGoalSaved}
    on:deleted={handleGoalDeleted}
  />
{/if}

<Toast bind:show={toastShow} message={toastMessage} type={toastType} />
