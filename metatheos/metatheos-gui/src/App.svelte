<script>
  import Dashboard from './lib/Dashboard.svelte'
  import GovernanceExplorer from './lib/GovernanceExplorer.svelte'
  import GoalExplorer from './lib/GoalExplorer.svelte'
  import AuditExplorer from './lib/AuditExplorer.svelte'
  import PromptLibrary from './lib/PromptLibrary.svelte'
  import DailyEditor from './lib/DailyEditor.svelte'
  import Assistant from './lib/Assistant.svelte'

  let currentView = 'dashboard'

  const views = [
    { id: 'dashboard', label: 'Dashboard', icon: '📊' },
    { id: 'explorer', label: 'Explorer', icon: '📁' },
    { id: 'daily', label: 'Daily', icon: '📅' },
    { id: 'goals', label: 'Goals', icon: '🎯' },
    { id: 'audits', label: 'Audits', icon: '🔍' },
    { id: 'prompts', label: 'Prompts', icon: '💡' },
    { id: 'assistant', label: 'Assistant', icon: '🤖' },
  ]

  function switchView(viewId) {
    currentView = viewId
  }
</script>

<div class="flex h-screen bg-gray-50 dark:bg-gray-900">
  <!-- Sidebar -->
  <aside class="w-64 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700">
    <div class="p-6">
      <div class="flex items-center gap-3 mb-2">
        <img
          src="/metatheos-logo.png"
          alt="Metatheos Logo"
          class="w-10 h-10 rounded-lg"
        />
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
          Metatheos
        </h1>
      </div>
      <p class="text-sm text-gray-500 dark:text-gray-400 ml-13">Governance Engine</p>
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
  <main class="flex-1 overflow-hidden">
    {#if currentView === 'explorer'}
      <GovernanceExplorer />
    {:else}
      <div class="p-8 overflow-y-auto h-full">
        {#if currentView === 'dashboard'}
          <Dashboard />
        {:else if currentView === 'daily'}
          <DailyEditor />
        {:else if currentView === 'goals'}
          <GoalExplorer />
        {:else if currentView === 'audits'}
          <AuditExplorer />
        {:else if currentView === 'prompts'}
          <PromptLibrary />
        {:else if currentView === 'assistant'}
          <Assistant />
        {/if}
      </div>
    {/if}
  </main>
</div>
