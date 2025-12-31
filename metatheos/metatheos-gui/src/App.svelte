<script>
  import AequitasDashboard from "./lib/AequitasDashboard.svelte";
  import Dashboard from "./lib/Dashboard.svelte";
  import GovernanceExplorer from "./lib/GovernanceExplorer.svelte";
  import GoalExplorer from "./lib/GoalExplorer.svelte";
  import AuditExplorer from "./lib/AuditExplorer.svelte";
  import PromptLibrary from "./lib/PromptLibrary.svelte";
  import DailyEditor from "./lib/DailyEditor.svelte";
  import Assistant from "./lib/Assistant.svelte";
  import ChatDock from "./lib/ChatDock.svelte";
  import CurrentDay from "./lib/CurrentDay.svelte";
  import ChatDockToggle from "./lib/ChatDockToggle.svelte";
  import { chatDockStore } from "./lib/stores/chatDock";

  let currentView = "dashboard";
  let sidebarCollapsed = false;

  const views = [
    { id: "dashboard", label: "Dashboard", icon: "📊" },
    { id: "explorer", label: "Explorer", icon: "📁" },
    { id: "daily", label: "Daily", icon: "📅" },
    { id: "current-day", label: "Current Day", icon: "☀️" },
    { id: "goals", label: "Goals", icon: "🎯" },
    { id: "audits", label: "Audits", icon: "🔍" },
    { id: "prompts", label: "Prompts", icon: "💡" },
    { id: "assistant", label: "Assistant", icon: "🤖" },
  ];

  function switchView(viewId) {
    currentView = viewId;
  }

  function handleSwitchToAssistant() {
    currentView = "assistant";
  }

  function openDock() {
    chatDockStore.setMode("bottom");
    chatDockStore.setOpen(true);
  }

  function handleDashboardNav(event) {
    const { view, filter, goalId } = event.detail;
    if (view) {
      currentView = view;
      // TODO: Apply filters/goalId when navigating to goals view
      console.log("Navigate to:", view, { filter, goalId });
    }
  }
</script>

<div class="flex h-screen bg-gray-50 dark:bg-gray-900">
  <!-- Sidebar -->
  <aside
    class={`sidebar ${sidebarCollapsed ? "collapsed" : ""} bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700`}
  >
    <div class="p-6 flex items-center justify-between">
      <div class="flex items-center gap-3">
        <img
          src="/metatheos-logo.png"
          alt="Metatheos Logo"
          class="w-10 h-10 rounded-lg"
        />
        {#if !sidebarCollapsed}
          <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
            Metatheos
          </h1>
        {/if}
      </div>
      <button
        class="collapse-btn"
        title="Toggle sidebar"
        on:click={() => (sidebarCollapsed = !sidebarCollapsed)}
      >
        {sidebarCollapsed ? "»" : "«"}
      </button>
    </div>
    {#if !sidebarCollapsed}
      <p class="text-sm text-gray-500 dark:text-gray-400 ml-6 mb-2">
        Governance Engine
      </p>
    {/if}

    <nav class="mt-6">
      {#each views as view}
        <button
          class={`nav-btn ${currentView === view.id ? "active" : ""} ${sidebarCollapsed ? "icon-only" : ""} ${
            currentView === view.id
              ? "bg-primary-50 dark:bg-primary-900/20 text-primary-700 dark:text-primary-400 border-r-4 border-primary-600"
              : "text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
          }`}
          on:click={() => switchView(view.id)}
        >
          <span class="text-xl">{view.icon}</span>
          {#if !sidebarCollapsed}
            <span class="font-medium">{view.label}</span>
          {/if}
        </button>
      {/each}
    </nav>

    <div class="sidebar-footer">
      {#if !sidebarCollapsed}
        <p class="text-xs text-gray-500 dark:text-gray-400">
          Metatheos v0.5.0<br />
          Aequitas Governance Engine
        </p>
      {/if}
    </div>
  </aside>

  <!-- Main content -->
  <main class="flex-1 overflow-hidden app-shell">
    <div class="app-topbar glass-panel">
      <div class="flex items-center gap-3">
        <div class="pill">Metatheos</div>
        <div class="text-sm text-gray-300">
          Governance Engine · Vault control
        </div>
      </div>
      <div class="flex items-center gap-2">
        <span class="pill">Local</span>
        <button class="btn btn-secondary text-sm" on:click={openDock}
          >Chat Dock</button
        >
      </div>
    </div>
    {#if currentView === "explorer"}
      <GovernanceExplorer />
    {:else}
      <div class="p-8 overflow-y-auto h-full">
        {#if currentView === "dashboard"}
          <AequitasDashboard on:navigate={handleDashboardNav} />
        {:else if currentView === "daily"}
          <DailyEditor />
        {:else if currentView === "current-day"}
          <CurrentDay />
        {:else if currentView === "goals"}
          <GoalExplorer />
        {:else if currentView === "audits"}
          <AuditExplorer />
        {:else if currentView === "prompts"}
          <PromptLibrary />
        {:else if currentView === "assistant"}
          <Assistant />
        {/if}
      </div>
    {/if}
  </main>

  <ChatDock onSwitchToAssistant={handleSwitchToAssistant} />
  <ChatDockToggle />
</div>

<style>
  .sidebar {
    width: 256px;
    transition: width 0.2s ease;
    position: relative;
  }
  .sidebar.collapsed {
    width: 72px;
  }
  .sidebar-footer {
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    padding: 16px;
    border-top: 1px solid rgba(255, 255, 255, 0.08);
    width: 100%;
  }
  .collapse-btn {
    border: 1px solid rgba(0, 0, 0, 0.1);
    background: transparent;
    color: #4b5563;
    border-radius: 6px;
    padding: 6px 10px;
  }
  .nav-btn {
    width: 100%;
    text-align: left;
    padding: 12px 24px;
    display: flex;
    align-items: center;
    gap: 12px;
    transition: background-color 0.15s ease;
  }
  .nav-btn.icon-only {
    justify-content: center;
    padding: 12px;
  }
  .app-shell {
    position: relative;
    padding: 24px;
  }
  .app-topbar {
    @apply flex items-center justify-between mb-6;
  }
</style>
