<script>
  import { invoke } from '@tauri-apps/api/core'
  import { onMount } from 'svelte'

  let loading = true
  let error = null
  let data = {
    current_phase: null,
    active_goals: [],
    blocked_goals: [],
    total_goals: 0,
    error_count: 0,
    warning_count: 0,
  }

  onMount(async () => {
    try {
      data = await invoke('get_dashboard_data')
      loading = false
    } catch (err) {
      error = err
      loading = false
    }
  })

  function getStatusBadge(status) {
    const classes = {
      active: 'badge-active',
      blocked: 'badge-blocked',
      completed: 'badge-completed',
      archived: 'badge-archived',
    }
    return classes[status] || 'badge'
  }
</script>

<div>
  <h2 class="text-3xl font-bold text-gray-900 dark:text-white mb-6">Dashboard</h2>

  {#if loading}
    <div class="card">
      <p class="text-gray-500 dark:text-gray-400">Loading governance data...</p>
    </div>
  {:else if error}
    <div class="card bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800">
      <p class="text-red-800 dark:text-red-200">Error: {error}</p>
    </div>
  {:else}
    <!-- Stats Grid -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
      <div class="card">
        <div class="text-sm font-medium text-gray-500 dark:text-gray-400">Current Phase</div>
        <div class="text-3xl font-bold text-gray-900 dark:text-white mt-2">
          {data.current_phase ?? 'N/A'}
        </div>
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

    <!-- Active Goals -->
    {#if data.active_goals.length > 0}
      <div class="card mb-6">
        <h3 class="text-xl font-semibold text-gray-900 dark:text-white mb-4">Active Goals</h3>
        <div class="space-y-3">
          {#each data.active_goals as goal}
            <div class="flex items-start justify-between p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
              <div class="flex-1">
                <div class="flex items-center gap-2">
                  <span class="font-mono text-sm font-medium text-primary-600 dark:text-primary-400">
                    {goal.goal_id}
                  </span>
                  <span class="badge {getStatusBadge(goal.status)}">
                    {goal.status}
                  </span>
                  {#if goal.phase}
                    <span class="text-xs text-gray-500 dark:text-gray-400">
                      Phase {goal.phase}
                    </span>
                  {/if}
                </div>
                <p class="text-gray-900 dark:text-white mt-1">{goal.title}</p>
                {#if goal.owner}
                  <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
                    Owner: {goal.owner}
                  </p>
                {/if}
              </div>
            </div>
          {/each}
        </div>
      </div>
    {/if}

    <!-- Blocked Goals -->
    {#if data.blocked_goals.length > 0}
      <div class="card mb-6">
        <h3 class="text-xl font-semibold text-gray-900 dark:text-white mb-4">Blockers</h3>
        <div class="space-y-3">
          {#each data.blocked_goals as goal}
            <div class="flex items-start justify-between p-4 bg-red-50 dark:bg-red-900/20 rounded-lg border border-red-200 dark:border-red-800">
              <div class="flex-1">
                <div class="flex items-center gap-2">
                  <span class="font-mono text-sm font-medium text-red-600 dark:text-red-400">
                    {goal.goal_id}
                  </span>
                  <span class="badge {getStatusBadge(goal.status)}">
                    {goal.status}
                  </span>
                </div>
                <p class="text-gray-900 dark:text-white mt-1">{goal.title}</p>
              </div>
            </div>
          {/each}
        </div>
      </div>
    {/if}

    <!-- Governance Health -->
    <div class="card">
      <h3 class="text-xl font-semibold text-gray-900 dark:text-white mb-4">Governance Health</h3>
      <div class="grid grid-cols-2 gap-4">
        <div class="flex items-center gap-3">
          <div class="text-2xl">{data.error_count === 0 ? '✓' : '❌'}</div>
          <div>
            <div class="text-sm font-medium text-gray-500 dark:text-gray-400">Errors</div>
            <div class="text-lg font-semibold text-gray-900 dark:text-white">
              {data.error_count}
            </div>
          </div>
        </div>
        <div class="flex items-center gap-3">
          <div class="text-2xl">{data.warning_count === 0 ? '✓' : '⚠'}</div>
          <div>
            <div class="text-sm font-medium text-gray-500 dark:text-gray-400">Warnings</div>
            <div class="text-lg font-semibold text-gray-900 dark:text-white">
              {data.warning_count}
            </div>
          </div>
        </div>
      </div>
    </div>
  {/if}
</div>
