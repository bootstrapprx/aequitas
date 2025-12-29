<script>
  import Dashboard from './lib/Dashboard.svelte'
  import GoalExplorer from './lib/GoalExplorer.svelte'
  import AuditViewer from './lib/AuditViewer.svelte'
  import DailyEditor from './lib/DailyEditor.svelte'
  import Assistant from './lib/Assistant.svelte'

  let currentView = 'dashboard'

  const views = [
    { id: 'dashboard', label: 'Dashboard', icon: '📊' },
    { id: 'daily', label: 'Daily', icon: '📅' },
    { id: 'goals', label: 'Goals', icon: '🎯' },
    { id: 'assistant', label: 'Assistant', icon: '🤖' },
    { id: 'audit', label: 'Audit', icon: '✓' },
  ]

  function switchView(viewId) {
    currentView = viewId
  }
</script>

<div class="flex h-screen bg-gray-50 dark:bg-gray-900">
  <!-- Sidebar -->
  <aside class="w-64 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700">
    <div class="p-6">
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
        Metatheos
      </h1>
      <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">Governance Engine</p>
    </div>

    <nav class="mt-6">
      {#each views as view}
        <button
          class="w-full text-left px-6 py-3 flex items-center gap-3 transition-colors {currentView === view.id
            ? 'bg-primary-50 dark:bg-primary-900/20 text-primary-700 dark:text-primary-400 border-r-4 border-primary-600'
            : 'text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'}"
          on:click={() => switchView(view.id)}
        >
          <span class="text-xl">{view.icon}</span>
          <span class="font-medium">{view.label}</span>
        </button>
      {/each}
    </nav>

    <div class="absolute bottom-0 left-0 right-0 p-6 border-t border-gray-200 dark:border-gray-700 w-64">
      <p class="text-xs text-gray-500 dark:text-gray-400">
        Metatheos v0.5.0<br />
        Aequitas Governance Engine
      </p>
    </div>
  </aside>

  <!-- Main content -->
  <main class="flex-1 overflow-y-auto">
    <div class="p-8">
      {#if currentView === 'dashboard'}
        <Dashboard />
      {:else if currentView === 'daily'}
        <DailyEditor />
      {:else if currentView === 'goals'}
        <GoalExplorer />
      {:else if currentView === 'assistant'}
        <Assistant />
      {:else if currentView === 'audit'}
        <AuditViewer />
      {/if}
    </div>
  </main>
</div>
