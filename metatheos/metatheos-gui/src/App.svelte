<script>
  import { onMount } from "svelte";
  import { invoke } from "@tauri-apps/api/core";
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
  import GoalDetail from "./lib/GoalDetail.svelte";
  import ChatDockToggle from "./lib/ChatDockToggle.svelte";
  import LiveUpdateIndicator from "./lib/LiveUpdateIndicator.svelte";
  import DayWizard from "./lib/DayWizard.svelte";
  import PhaseManager from "./lib/PhaseManager.svelte";
  import NotificationBadge from "./lib/NotificationBadge.svelte";
  import Activity from "./lib/Activity.svelte";
  import { chatDockStore } from "./lib/stores/chatDock";

  let currentView = "dashboard";
  let selectedGoalId = null;
  let sidebarCollapsed = false;
  let showDayWizard = false;
  let checkingDay = true;
  let hasActiveDay = false;
  let diagnostics = null;
  let diagError = null;
  let activePhase = null;
  let activeDayData = null;
  let allPhases = [];

  const views = [
    { id: "dashboard", label: "Dashboard", icon: "📊" },
    { id: "current-day", label: "Current Day", icon: "☀️" },
    { id: "activity", label: "Activity", icon: "⚡", badge: true },
    { id: "phases", label: "Phases", icon: "📐", section: "structure" },
    { id: "goals", label: "Phase Goals", icon: "🎯", section: "structure" },
    { id: "explorer", label: "Files", icon: "📁", section: "tools" },
    { id: "daily", label: "Daily Notes", icon: "📅", section: "tools" },
    { id: "audits", label: "Audits", icon: "🔍", section: "tools" },
    { id: "prompts", label: "Prompts", icon: "💡", section: "tools" },
    { id: "assistant", label: "Assistant", icon: "🤖", section: "tools" },
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
      // Special handling for "createDay" view - trigger Day Wizard
      if (view === "createDay") {
        startNewDay();
        return;
      }

      currentView = view;
      // TODO: Apply filters/goalId when navigating to goals view
      console.log("Navigate to:", view, { filter, goalId });
      if (goalId) {
        selectedGoalId = goalId;
      }
    }
  }

  function handleOpenGoalDetail(event) {
    selectedGoalId = event.detail.goalId;
    currentView = "goal_detail";
  }

  function backToGoals() {
    currentView = "goals";
  }

  onMount(async () => {
    await checkTodayDay();
    await initializeState();
  });

  async function checkTodayDay() {
    try {
      const today = await invoke("get_today_day");
      activeDayData = today;
      hasActiveDay = !!today;
      showDayWizard = false; // Never force wizard
    } catch (e) {
      console.error("Failed to check today's day:", e);
      hasActiveDay = false;
      showDayWizard = false;
    } finally {
      checkingDay = false;
    }
  }

  function handleDayCreated() {
    showDayWizard = false;
    hasActiveDay = true;
    currentView = "dashboard"; // Redirect to dashboard after day creation
  }

  function startNewDay() {
    showDayWizard = true;
  }

  async function initializeState() {
    try {
      diagnostics = await invoke("diagnose_store_state");
      diagError = null;
      // Load all phases
      allPhases = await invoke("get_all_phases");
      if (allPhases && allPhases.length > 0) {
        // Get or set active phase
        activePhase = await invoke("get_active_phase", { date: null });
        if (!activePhase) {
          const best = pickBestPhase(allPhases);
          if (best) {
            await invoke("set_active_phase_db", { phaseId: best.phase_id });
            activePhase = best;
          }
        }
      } else {
        activePhase = null;
      }
    } catch (e) {
      diagError = e?.toString?.() ?? String(e);
    }
  }

  function pickBestPhase(phases) {
    if (!phases || phases.length === 0) return null;
    const priority = (status) => {
      const s = (status || "").toLowerCase();
      if (s.includes("active")) return 0;
      if (s.includes("planned")) return 1;
      if (s.includes("open")) return 1;
      if (s.includes("done") || s.includes("closed")) return 2;
      return 3;
    };
    return [...phases].sort(
      (a, b) => priority(a.status) - priority(b.status),
    )[0];
  }

  async function seedDefaultPhase() {
    try {
      await invoke("seed_default_phase_db");
      await initializeState();
      currentView = "phases";
    } catch (e) {
      diagError = e?.toString?.() ?? String(e);
    }
  }

  async function setActivePhase(phase) {
    try {
      await invoke("set_active_phase_db", { phaseId: phase.phase_id });
      activePhase = phase;
    } catch (e) {
      console.error("Failed to set active phase:", e);
    }
  }

  async function repairDatabase() {
    try {
      await invoke("ingest_roadmap");
      await initializeState();
      // Show success toast or alert? For now just refresh.
    } catch (e) {
      console.error("Failed to repair database:", e);
      diagError = e?.toString?.() ?? String(e);
    }
  }

  function handlePhaseChanged(event) {
    activePhase = event.detail.phase;
    // Optionally switch to goals view after selecting a phase
    if (currentView === "phases") {
      currentView = "goals";
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
      <div class="flex items-center gap-2">
        <button
          class="collapse-btn"
          title="Toggle sidebar"
          on:click={() => (sidebarCollapsed = !sidebarCollapsed)}
        >
          {sidebarCollapsed ? "»" : "«"}
        </button>
      </div>
    </div>
    {#if !sidebarCollapsed}
      <div class="px-6 py-3 mb-2">
        <p
          class="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400 font-semibold mb-1"
        >
          Active Phase
        </p>
        {#if activePhase}
          <div class="phase-badge">
            <span class="phase-badge-icon">📐</span>
            <div class="flex-1 min-w-0">
              <div
                class="font-semibold text-sm text-gray-900 dark:text-white truncate"
              >
                {activePhase.title}
              </div>
              <div class="text-xs text-gray-500 dark:text-gray-400">
                {activePhase.status}
              </div>
            </div>
          </div>
        {:else}
          <div class="text-sm text-gray-400 dark:text-gray-500 italic">
            No active phase
          </div>
        {/if}
      </div>
    {/if}

    <nav class="mt-2">
      {#each views as view, i}
        {#if !sidebarCollapsed && i > 0 && views[i - 1].section !== view.section}
          <div class="nav-divider"></div>
        {/if}
        <button
          class={`nav-btn ${currentView === view.id ? "active" : ""} ${sidebarCollapsed ? "icon-only" : ""} ${
            currentView === view.id
              ? "bg-primary-50 dark:bg-primary-900/20 text-primary-700 dark:text-primary-400 border-r-4 border-primary-600"
              : "text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
          }`}
          on:click={() => switchView(view.id)}
          title={sidebarCollapsed ? view.label : ""}
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
    {#if checkingDay}
      <div class="p-8 flex items-center justify-center h-full">
        <p class="text-gray-500">Checking today's day...</p>
      </div>
    {:else}
      <!-- Soft Gate: App Shell always loads -->

      <!-- Topbar -->
      <div class="app-topbar glass-panel">
        <div class="flex items-center gap-3">
          <div class="pill">Metatheos</div>
          <div class="text-sm text-gray-300">
            Governance Engine · Vault control
          </div>
        </div>
        <div class="flex items-center gap-2">
          <NotificationBadge />
          {#if !showDayWizard}
            <button class="btn btn-primary text-sm" on:click={startNewDay}
              >New Day</button
            >
          {/if}
          <span class="pill">Local</span>
          <button class="btn btn-secondary text-sm" on:click={openDock}
            >Chat Dock</button
          >
        </div>
      </div>

      <!-- Banner if no day and not in wizard -->
      {#if showDayWizard}
        <div
          class="p-8 overflow-y-auto h-full bg-slate-900/50 absolute inset-0 z-50 backdrop-blur-sm"
        >
          <div class="max-w-4xl mx-auto mt-10 relative">
            <button
              class="absolute top-4 right-4 text-gray-400 hover:text-white"
              on:click={() => (showDayWizard = false)}>✕</button
            >
            <DayWizard on:dayCreated={handleDayCreated} />
          </div>
        </div>
      {:else if !hasActiveDay && !showDayWizard}
        <div
          class="bg-blue-600 text-white px-4 py-2 text-center text-sm font-medium shadow-md relative z-10 transition-all"
        >
          No active day. <button
            class="underline ml-1 font-bold hover:text-blue-100"
            on:click={startNewDay}>Start your day</button
          > to enable tracking.
        </div>
      {/if}
      {#if currentView === "explorer"}
        <GovernanceExplorer />
      {:else}
        <div class="p-8 overflow-y-auto h-full">
          {#if diagError}
            <div
              class="card mb-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-800 dark:text-red-200"
            >
              Diagnostics failed: {diagError}
            </div>
          {:else if diagnostics}
            <div class="card mb-4">
              <div class="flex items-center justify-between">
                <div>
                  <div class="text-sm text-gray-600 dark:text-gray-300">
                    DB path: {diagnostics.db_path}
                  </div>
                  {#if diagnostics.counts}
                    <div class="text-sm text-gray-600 dark:text-gray-300">
                      Counts — phases: {diagnostics.counts["phase"] || 0},
                      goals: {diagnostics.counts["goal"] || 0}, work_items: {diagnostics
                        .counts["work_item"] || 0}
                    </div>
                  {/if}
                </div>
                <div class="flex gap-2">
                  {#if (diagnostics.counts.phase || 0) === 0}
                    <button
                      class="btn btn-primary text-sm"
                      on:click={seedDefaultPhase}
                    >
                      Initialize default phase
                    </button>
                  {/if}
                  <button
                    class="btn btn-secondary text-sm"
                    on:click={initializeState}
                  >
                    Re-run diagnostics
                  </button>
                  <button
                    class="btn btn-secondary text-sm"
                    on:click={repairDatabase}
                    title="Fix missing fields (e.g. phase_id)"
                  >
                    Repair Database
                  </button>
                </div>
              </div>
            </div>
          {/if}
          {#if currentView === "dashboard"}
            <AequitasDashboard on:navigate={handleDashboardNav} />
          {:else if currentView === "current-day"}
            <CurrentDay />
          {:else if currentView === "activity"}
            <Activity />
          {:else if currentView === "phases"}
            <PhaseManager {activePhase} on:phaseChanged={handlePhaseChanged} />
          {:else if currentView === "goals"}
            <GoalExplorer on:openGoalDetail={handleOpenGoalDetail} />
          {:else if currentView === "goal_detail"}
            <GoalDetail goalId={selectedGoalId} on:back={backToGoals} />
          {:else if currentView === "explorer"}
            <GovernanceExplorer />
          {:else if currentView === "daily"}
            <DailyEditor />
          {:else if currentView === "audits"}
            <AuditExplorer />
          {:else if currentView === "prompts"}
            <PromptLibrary />
          {:else if currentView === "assistant"}
            <Assistant />
          {/if}
        </div>
      {/if}
    {/if}
  </main>

  <ChatDock
    onSwitchToAssistant={handleSwitchToAssistant}
    {activePhase}
    activeDay={hasActiveDay
      ? {
          /* constructed day object if needed, or pass null and let Assistant fetch */
        }
      : null}
  />
  <ChatDockToggle />

  <!-- PHASE 2.3: Live update notifications -->
  <LiveUpdateIndicator />
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
  .phase-badge {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 12px;
    background: rgba(59, 130, 246, 0.1);
    border: 1px solid rgba(59, 130, 246, 0.3);
    border-radius: 8px;
    transition: all 0.2s ease;
  }
  .phase-badge:hover {
    background: rgba(59, 130, 246, 0.15);
    border-color: rgba(59, 130, 246, 0.4);
  }
  .phase-badge-icon {
    font-size: 20px;
    flex-shrink: 0;
  }
  .nav-divider {
    height: 1px;
    background: rgba(107, 114, 128, 0.2);
    margin: 8px 16px;
  }
  .app-shell {
    position: relative;
    padding: 24px;
  }
  .app-topbar {
    @apply flex items-center justify-between mb-6;
  }
</style>
