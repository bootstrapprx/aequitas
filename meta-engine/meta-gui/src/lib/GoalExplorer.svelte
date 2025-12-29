<script>
  import { invoke } from '@tauri-apps/api/core'
  import { onMount } from 'svelte'

  let loading = true
  let error = null
  let goals = []
  let filteredGoals = []
  let statusFilter = 'all'
  let searchQuery = ''

  onMount(async () => {
    await loadGoals()
  })

  async function loadGoals() {
    try {
      loading = true
      goals = await invoke('get_all_goals')
      applyFilters()
      loading = false
    } catch (err) {
      error = err
      loading = false
    }
  }

  async function filterByStatus(status) {
    statusFilter = status
    if (status === 'all') {
      await loadGoals()
    } else {
      try {
        loading = true
        goals = await invoke('get_goals_by_status', { status })
        applyFilters()
        loading = false
      } catch (err) {
        error = err
        loading = false
      }
    }
  }

  function applyFilters() {
    filteredGoals = goals.filter(goal => {
      const matchesSearch = searchQuery === '' ||
        goal.goal_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
        goal.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (goal.owner && goal.owner.toLowerCase().includes(searchQuery.toLowerCase()))
      return matchesSearch
    })
  }

  $: {
    searchQuery
    applyFilters()
  }

  function getStatusBadge(status) {
    const classes = {
      active: 'badge-active',
      blocked: 'badge-blocked',
      completed: 'badge-completed',
      archived: 'badge-archived',
    }
    return classes[status] || 'badge'
  }

  const statuses = [
    { value: 'all', label: 'All', count: goals.length },
    { value: 'active', label: 'Active' },
    { value: 'blocked', label: 'Blocked' },
    { value: 'completed', label: 'Completed' },
    { value: 'archived', label: 'Archived' },
  ]
</script>

<div>
  <div class="flex items-center justify-between mb-6">
    <h2 class="text-3xl font-bold text-gray-900 dark:text-white">Goals</h2>
    <button class="btn btn-secondary" on:click={loadGoals}>
      Refresh
    </button>
  </div>

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
        <!-- Status Tabs -->
        <div class="flex gap-2 flex-wrap">
          {#each statuses as status}
            <button
              class="px-4 py-2 rounded-md text-sm font-medium transition-colors {statusFilter === status.value
                ? 'bg-primary-600 text-white'
                : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'}"
              on:click={() => filterByStatus(status.value)}
            >
              {status.label}
            </button>
          {/each}
        </div>

        <!-- Search -->
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

    <!-- Goals List -->
    {#if filteredGoals.length === 0}
      <div class="card text-center py-12">
        <p class="text-gray-500 dark:text-gray-400">No goals found</p>
      </div>
    {:else}
      <div class="space-y-4">
        {#each filteredGoals as goal}
          <div class="card hover:shadow-lg transition-shadow">
            <div class="flex items-start justify-between">
              <div class="flex-1">
                <div class="flex items-center gap-3 mb-2">
                  <span class="font-mono text-lg font-bold text-primary-600 dark:text-primary-400">
                    {goal.goal_id}
                  </span>
                  <span class="badge {getStatusBadge(goal.status)}">
                    {goal.status}
                  </span>
                  {#if goal.phase}
                    <span class="text-sm text-gray-500 dark:text-gray-400">
                      Phase {goal.phase}
                    </span>
                  {/if}
                </div>

                <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                  {goal.title}
                </h3>

                <div class="flex flex-wrap gap-4 text-sm text-gray-600 dark:text-gray-400">
                  {#if goal.owner}
                    <div class="flex items-center gap-1">
                      <span class="font-medium">Owner:</span>
                      <span>{goal.owner}</span>
                    </div>
                  {/if}

                  {#if goal.dependencies.length > 0}
                    <div class="flex items-center gap-1">
                      <span class="font-medium">Dependencies:</span>
                      <span>{goal.dependencies.length}</span>
                    </div>
                  {/if}

                  {#if goal.tags.length > 0}
                    <div class="flex items-center gap-2">
                      {#each goal.tags as tag}
                        <span class="px-2 py-0.5 bg-gray-100 dark:bg-gray-700 rounded text-xs">
                          {tag}
                        </span>
                      {/each}
                    </div>
                  {/if}
                </div>

                <div class="mt-3 text-xs text-gray-400 dark:text-gray-500 font-mono">
                  {goal.file_path}
                </div>
              </div>
            </div>
          </div>
        {/each}
      </div>

      <div class="mt-6 text-center text-sm text-gray-500 dark:text-gray-400">
        Showing {filteredGoals.length} of {goals.length} goals
      </div>
    {/if}
  {/if}
</div>
