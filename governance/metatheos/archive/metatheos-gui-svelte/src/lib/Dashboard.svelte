<script>
  import { invoke } from "@tauri-apps/api/core";
  import { onMount } from "svelte";
  import Toast from "./Toast.svelte";
  import PhaseEditor from "./PhaseEditor.svelte";
  import GoalEditor from "./GoalEditor.svelte";
  import GovernanceGitPanel from "./GovernanceGitPanel.svelte";

  let loading = true;
  let error = null;
  let devMode = false;

  // Editor state
  let showPhaseEditor = false;
  let editingPhase = null;
  let data = {
    current_phase: null,
    active_goals: [],
    blocked_goals: [],
    total_goals: 0,
    completed_goals: 0,
    planned_goals: 0,
    archived_goals: 0,
    today_exists: false,
    today_path: "",
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
  };

  let creatingNote = false;
  let noteDate = new Date().toISOString().split("T")[0];
  let selectedMode = "";
  const modeOptions = [
    { value: "", label: "Unspecified" },
    { value: "light", label: "Light Day" },
    { value: "heavy", label: "Heavy Day" },
    { value: "review", label: "Review Day" },
  ];

  let toastShow = false;
  let toastMessage = "";
  let toastType = "success";

  const tauriAvailable = () => {
    if (typeof window === "undefined") return false;
    return Boolean(
      window.__TAURI__ || window.__TAURI_IPC__ || window.__TAURI_INTERNALS__,
    );
  };

  onMount(async () => {
    if (!tauriAvailable()) {
      devMode = true;
      loading = false;
      return;
    }
    await loadDashboard();
  });

  async function loadDashboard() {
    try {
      loading = true;
      data = await invoke("get_dashboard_data");
      selectedMode = data.today_mode || "";
      error = null;
    } catch (err) {
      error = err?.toString?.() ?? String(err);
    } finally {
      loading = false;
    }
  }

  function getStatusBadge(status) {
    const classes = {
      planned: "badge-planned",
      active: "badge-active",
      blocked: "badge-blocked",
      partial: "badge-partial",
      done: "badge-completed",
      archived: "badge-archived",
    };
    return classes[status] || "badge";
  }

  function formatDate(value) {
    if (!value) return "n/a";
    return new Date(value).toLocaleDateString();
  }

  function openNewPhaseEditor() {
    editingPhase = null;
    showPhaseEditor = true;
  }

  function openEditPhaseEditor(phase) {
    editingPhase = phase;
    showPhaseEditor = true;
  }

  function closePhaseEditor() {
    showPhaseEditor = false;
    editingPhase = null;
  }

  async function handlePhaseSaved() {
    toastMessage = editingPhase
      ? "Phase updated successfully!"
      : "Phase created successfully!";
    toastType = "success";
    toastShow = true;
    await loadDashboard();
  }

  async function handlePhaseActivated() {
    toastMessage = "Phase activated successfully!";
    toastType = "success";
    toastShow = true;
    await loadDashboard();
  }

  // Goal Editor state
  let showGoalEditor = false;
  let editingGoal = null;

  function openNewGoalEditor() {
    editingGoal = null;
    showGoalEditor = true;
  }

  function openEditGoalEditor(goal) {
    editingGoal = goal;
    showGoalEditor = true;
  }

  function closeGoalEditor() {
    showGoalEditor = false;
    editingGoal = null;
  }

  async function handleGoalSaved() {
    toastMessage = editingGoal
      ? "Goal updated successfully!"
      : "Goal created successfully!";
    toastType = "success";
    toastShow = true;
    await loadDashboard();
  }

  function handleCreateSubGoal(event) {
    const parentId = event.detail.parentId;
    // Close current editor
    closeGoalEditor();
    // Open new editor with parent_id set
    // We need to wait for the close animation/state update if any, but Svelte is sync enough here
    setTimeout(() => {
      editingGoal = { parent_id: parentId };
      showGoalEditor = true;
    }, 100);
  }

  async function createDailyNote() {
    if (devMode) {
      toastMessage =
        "Tauri is not available. Run `cargo tauri dev` to create notes.";
      toastType = "error";
      toastShow = true;
      return;
    }

    try {
      creatingNote = true;
      const path = await invoke("create_daily_note", { date: noteDate });
      if (selectedMode) {
        await setDailyMode(false);
      }
      toastMessage = `Daily note ready at ${path}`;
      toastType = "success";
      toastShow = true;
      await loadDashboard();
    } catch (err) {
      toastMessage = err?.toString?.() ?? String(err);
      toastType = "error";
      toastShow = true;
    } finally {
      creatingNote = false;
    }
  }

  async function setDailyMode(showToast = true) {
    if (devMode) {
      toastMessage =
        "Tauri is not available. Run `cargo tauri dev` to edit notes.";
      toastType = "error";
      toastShow = true;
      return;
    }
    try {
      await invoke("set_daily_mode", {
        date: noteDate,
        mode: selectedMode || null,
      });
      if (showToast) {
        toastMessage = selectedMode
          ? `Mode set to ${selectedMode} for ${noteDate}`
          : `Mode cleared for ${noteDate}`;
        toastType = "success";
        toastShow = true;
      }
      await loadDashboard();
    } catch (err) {
      if (showToast) {
        toastMessage = err?.toString?.() ?? String(err);
        toastType = "error";
        toastShow = true;
      }
    }
  }
</script>

<div>
  <div class="flex items-center justify-between mb-6">
    <div>
      <h2 class="text-3xl font-bold text-gray-900 dark:text-white">
        Dashboard
      </h2>
      <p class="text-sm text-gray-500 dark:text-gray-400">
        Live view of the Governance Vault
      </p>
    </div>
    <button
      class="btn btn-secondary"
      on:click={loadDashboard}
      disabled={loading}
    >
      {loading ? "Refreshing…" : "Refresh"}
    </button>
  </div>

  {#if !devMode}
    <div
      class="card mb-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800"
    >
      <p class="text-sm text-blue-900 dark:text-blue-100">
        Governance write mode active. Changes will write to the vault after
        confirmation.
      </p>
    </div>
  {/if}

  {#if devMode}
    <div
      class="card mb-6 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800"
    >
      <h3
        class="text-lg font-semibold text-yellow-800 dark:text-yellow-200 mb-2"
      >
        Tauri not detected
      </h3>
      <p class="text-yellow-700 dark:text-yellow-200 text-sm">
        Launch with <code>cargo tauri dev</code> to hydrate the dashboard from the
        Governance Vault.
      </p>
      <p class="text-yellow-700 dark:text-yellow-200 text-sm mt-2">
        The UI remains available for layout verification; data loading is
        disabled in this mode.
      </p>
    </div>
  {/if}

  {#if loading}
    <div class="card">
      <p class="text-gray-500 dark:text-gray-400">Loading governance data...</p>
    </div>
  {:else if error}
    <div
      class="card bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800"
    >
      <p class="text-red-800 dark:text-red-200">Error: {error}</p>
    </div>
  {:else}
    <!-- Mission Progress -->
    {#if data.total_goals > 0}
      {@const plannedPct = (data.planned_goals / data.total_goals) * 100}
      {@const activePct = (data.active_goals.length / data.total_goals) * 100}
      {@const blockedPct = (data.blocked_goals.length / data.total_goals) * 100}
      {@const completedPct = (data.completed_goals / data.total_goals) * 100}

      <div
        class="card mb-8 p-6 bg-gradient-to-r from-gray-900 to-gray-800 border-none shadow-xl"
      >
        <div class="flex items-center justify-between mb-4">
          <div>
            <h3 class="text-xl font-bold text-white tracking-tight">
              System Aequitas Conclusion
            </h3>
            <p class="text-gray-400 text-sm">
              Overall system completion status
            </p>
          </div>
          <div class="text-right">
            <span class="text-3xl font-bold text-white"
              >{Math.round(completedPct)}%</span
            >
            <span class="text-gray-400 text-sm block">Completed</span>
          </div>
        </div>

        <div
          class="h-4 w-full bg-gray-700/50 rounded-full overflow-hidden flex"
        >
          {#if completedPct > 0}
            <div
              class="h-full bg-green-500 shadow-[0_0_10px_rgba(34,197,94,0.5)]"
              style="width: {completedPct}%"
              title="Completed: {data.completed_goals}"
            ></div>
          {/if}
          {#if activePct > 0}
            <div
              class="h-full bg-blue-500 shadow-[0_0_10px_rgba(59,130,246,0.5)]"
              style="width: {activePct}%"
              title="Active: {data.active_goals.length}"
            ></div>
          {/if}
          {#if blockedPct > 0}
            <div
              class="h-full bg-red-500 shadow-[0_0_10px_rgba(239,68,68,0.5)]"
              style="width: {blockedPct}%"
              title="Blocked: {data.blocked_goals.length}"
            ></div>
          {/if}
          {#if plannedPct > 0}
            <div
              class="h-full bg-gray-600"
              style="width: {plannedPct}%"
              title="Planned: {data.planned_goals}"
            ></div>
          {/if}
        </div>

        <div
          class="flex justify-between mt-3 text-xs text-gray-400 font-medium"
        >
          <div class="flex items-center gap-2">
            <div class="w-2 h-2 rounded-full bg-green-500"></div>
            <span>Done ({data.completed_goals})</span>
          </div>
          <div class="flex items-center gap-2">
            <div class="w-2 h-2 rounded-full bg-blue-500"></div>
            <span>Active ({data.active_goals.length})</span>
          </div>
          <div class="flex items-center gap-2">
            <div class="w-2 h-2 rounded-full bg-red-500"></div>
            <span>Blocked ({data.blocked_goals.length})</span>
          </div>
          <div class="flex items-center gap-2">
            <div class="w-2 h-2 rounded-full bg-gray-600"></div>
            <span>Planned ({data.planned_goals})</span>
          </div>
        </div>
      </div>
    {/if}

    <!-- Key Metrics -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
      <div class="card border-l-4 border-l-blue-500">
        <div class="flex items-center justify-between mb-2">
          <div
            class="text-sm font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider"
          >
            Current Phase
          </div>
          {#if data.current_phase}
            <button
              class="px-2 py-0.5 bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-600 dark:text-gray-300 text-xs rounded transition-colors"
              on:click={() => openEditPhaseEditor(data.current_phase)}
              disabled={devMode}
            >
              Edit
            </button>
          {:else}
            <button
              class="px-2 py-0.5 bg-blue-100 hover:bg-blue-200 dark:bg-blue-900/30 dark:hover:bg-blue-900/50 text-blue-700 dark:text-blue-300 text-xs rounded transition-colors"
              on:click={openNewPhaseEditor}
              disabled={devMode}
            >
              New
            </button>
          {/if}
        </div>
        <div
          class="text-2xl font-bold text-gray-900 dark:text-white mt-1 truncate"
        >
          {#if data.current_phase}
            {data.current_phase.phase_id}
            <span class="text-lg font-normal text-gray-500 dark:text-gray-400"
              >— {data.current_phase.title}</span
            >
          {:else}
            <span class="text-gray-400 italic">Not set</span>
          {/if}
        </div>
      </div>

      <div class="card border-l-4 border-l-green-500">
        <div
          class="text-sm font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider flex justify-between items-center pr-2"
        >
          <span>Active Goals</span>
          <button
            class="px-1.5 py-0.5 rounded bg-green-100 hover:bg-green-200 dark:bg-green-900/40 dark:hover:bg-green-900/60 text-green-700 dark:text-green-300 text-[10px] transition-colors"
            on:click={openNewGoalEditor}
            disabled={devMode}
          >
            NEW
          </button>
        </div>
        <div class="text-3xl font-bold text-green-600 dark:text-green-400 mt-1">
          {data.active_goals.length}
        </div>
        <div class="text-xs text-gray-400 mt-1">Focus items</div>
      </div>

      <div class="card border-l-4 border-l-red-500">
        <div
          class="text-sm font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider"
        >
          Blocked
        </div>
        <div class="text-3xl font-bold text-red-600 dark:text-red-400 mt-1">
          {data.blocked_goals.length}
        </div>
        <div class="text-xs text-gray-400 mt-1">Require attention</div>
      </div>

      <div class="card border-l-4 border-l-purple-500">
        <div
          class="text-sm font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider"
        >
          Total Goals
        </div>
        <div
          class="text-3xl font-bold text-purple-600 dark:text-purple-400 mt-1"
        >
          {data.total_goals}
        </div>
        <div class="text-xs text-gray-400 mt-1">In vault</div>
      </div>
    </div>

    <!-- Governance State (Phase 3) -->
    <div class="mb-6">
      <GovernanceGitPanel />
    </div>

    <!-- Today -->
    <div class="card mb-6">
      <div class="flex items-center justify-between gap-4">
        <div>
          <h3 class="text-xl font-semibold text-gray-900 dark:text-white">
            Today’s Focus
          </h3>
          <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
            {#if data.latest_daily}
              Latest daily: {data.latest_daily.date}
              {#if data.latest_daily.mode}· {data.latest_daily.mode}{/if}
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
          <button
            class="btn btn-primary"
            on:click={createDailyNote}
            disabled={creatingNote || devMode}
          >
            {creatingNote
              ? "Creating..."
              : data.today_exists
                ? "Re-create"
                : "Create note"}
          </button>
        </div>
      </div>

      {#if data.latest_daily}
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
          <div>
            <div
              class="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400 mb-1"
            >
              Goals
            </div>
            {#if data.latest_daily.goals.length === 0}
              <p class="text-sm text-gray-500 dark:text-gray-400">
                No goals linked.
              </p>
            {:else}
              <ul class="space-y-1 text-sm text-gray-900 dark:text-white">
                {#each data.latest_daily.goals as goal}
                  <li>• {goal}</li>
                {/each}
              </ul>
            {/if}
          </div>
          <div>
            <div
              class="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400 mb-1"
            >
              Blockers
            </div>
            {#if data.latest_daily.blockers.length === 0}
              <p class="text-sm text-gray-500 dark:text-gray-400">
                None recorded.
              </p>
            {:else}
              <ul class="space-y-1 text-sm text-gray-900 dark:text-white">
                {#each data.latest_daily.blockers as blocker}
                  <li>• {blocker}</li>
                {/each}
              </ul>
            {/if}
          </div>
          <div>
            <div
              class="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400 mb-1"
            >
              Decisions
            </div>
            {#if data.latest_daily.decisions.length === 0}
              <p class="text-sm text-gray-500 dark:text-gray-400">
                No decisions linked.
              </p>
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
        <p class="text-sm text-gray-500 dark:text-gray-400 mt-3">
          Use the Daily Editor to seed today’s plan.
        </p>
      {/if}
    </div>

    <!-- Governance Warnings -->
    <div class="card mb-6">
      <h3 class="text-xl font-semibold text-gray-900 dark:text-white mb-3">
        Governance Warnings
      </h3>
      {#if data.warnings.length === 0}
        <p class="text-sm text-gray-500 dark:text-gray-400">
          No gaps detected.
        </p>
      {:else}
        <div class="space-y-2">
          {#each data.warnings as warning}
            <div
              class="p-3 rounded-md border border-yellow-200 dark:border-yellow-800 bg-yellow-50 dark:bg-yellow-900/20"
            >
              <div
                class="text-xs uppercase tracking-wide text-yellow-700 dark:text-yellow-200 font-semibold"
              >
                {warning.kind}
              </div>
              <div class="text-sm text-gray-800 dark:text-gray-100">
                {warning.message}
              </div>
            </div>
          {/each}
        </div>
      {/if}
    </div>

    <div class="card mb-6">
      <div class="flex items-center justify-between mb-3">
        <h3 class="text-xl font-semibold text-gray-900 dark:text-white">
          Active Goals by Phase
        </h3>
        <span class="text-xs text-gray-500 dark:text-gray-400">Phase-aware</span
        >
      </div>
      {#if data.active_by_phase.length === 0}
        <p class="text-sm text-gray-500 dark:text-gray-400">
          No phases detected.
        </p>
      {:else}
        <div class="grid md:grid-cols-2 gap-4">
          {#each data.active_by_phase as bucket}
            <div
              class="p-4 rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800"
            >
              <div class="flex items-center justify-between">
                <div
                  class="text-sm font-semibold text-gray-900 dark:text-white"
                >
                  {bucket.phase.phase_id} — {bucket.phase.title}
                </div>
                <span class="text-xs text-gray-500 dark:text-gray-400"
                  >{bucket.active_goals.length} active</span
                >
              </div>
              {#if bucket.active_goals.length === 0}
                <p class="text-xs text-gray-500 dark:text-gray-400 mt-2">
                  No active goals.
                </p>
              {:else}
                <ul
                  class="space-y-3 mt-2 text-sm text-gray-900 dark:text-white"
                >
                  {#each bucket.active_goals as goal}
                    <li class="flex flex-col gap-1">
                      <button
                        class="flex flex-col gap-1 w-full text-left group"
                        on:click={() => openEditGoalEditor(goal)}
                      >
                        <div class="flex items-center gap-2">
                          <span
                            class="font-mono text-xs text-primary-700 dark:text-primary-300 group-hover:underline"
                            >{goal.goal_id}</span
                          >
                          <span class="badge {getStatusBadge(goal.status)}"
                            >{goal.status}</span
                          >
                          <span
                            class="text-gray-900 dark:text-white group-hover:text-primary-600 dark:group-hover:text-primary-400 transition-colors"
                            >{goal.title}</span
                          >
                        </div>
                        <!-- Goal Progress -->
                        <div
                          class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1.5 mt-0.5"
                        >
                          <div
                            class="bg-blue-600 h-1.5 rounded-full"
                            style="width: {goal.completion_pct || 0}%"
                          ></div>
                        </div>
                      </button>
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
        <h3 class="text-xl font-semibold text-gray-900 dark:text-white mb-3">
          Blocked Goals (Top 3)
        </h3>
        {#if data.top_blocked.length === 0}
          <p class="text-sm text-gray-500 dark:text-gray-400">
            No blocked goals.
          </p>
        {:else}
          <div class="space-y-2">
            {#each data.top_blocked as goal}
              <button
                class="w-full text-left p-3 rounded-lg border border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/20 hover:bg-red-100 dark:hover:bg-red-900/40 transition-colors"
                on:click={() => openEditGoalEditor(goal)}
              >
                <div class="flex items-center gap-2">
                  <span
                    class="font-mono text-sm font-semibold text-red-700 dark:text-red-300"
                    >{goal.goal_id}</span
                  >
                  <span class="badge {getStatusBadge(goal.status)}"
                    >{goal.status}</span
                  >
                  {#if goal.phase}
                    <span class="text-xs text-red-700 dark:text-red-200"
                      >Phase {goal.phase}</span
                    >
                  {/if}
                </div>
                <div class="text-sm text-gray-900 dark:text-white">
                  {goal.title}
                </div>
              </button>
            {/each}
          </div>
        {/if}
      </div>
      <div class="card">
        <h3 class="text-xl font-semibold text-gray-900 dark:text-white mb-3">
          Orphaned Goals
        </h3>
        {#if data.orphaned_goals.length === 0}
          <p class="text-sm text-gray-500 dark:text-gray-400">
            All goals have a phase.
          </p>
        {:else}
          <ul class="space-y-1 text-sm text-gray-900 dark:text-white">
            {#each data.orphaned_goals as goal}
              <li class="flex items-center gap-2">
                <button
                  class="flex items-center gap-2 w-full text-left hover:bg-gray-50 dark:hover:bg-gray-800 p-1 rounded"
                  on:click={() => openEditGoalEditor(goal)}
                >
                  <span
                    class="font-mono text-xs text-orange-700 dark:text-orange-300"
                    >{goal.goal_id}</span
                  >
                  <span class="badge {getStatusBadge(goal.status)}"
                    >{goal.status}</span
                  >
                  <span class="text-gray-900 dark:text-white">{goal.title}</span
                  >
                </button>
              </li>
            {/each}
          </ul>
        {/if}
      </div>
      <div class="card">
        <div class="flex items-center justify-between mb-1">
          <h3 class="text-xl font-semibold text-gray-900 dark:text-white">
            Stale Goals
          </h3>
          <span class="text-xs text-gray-500 dark:text-gray-400">>30 days</span>
        </div>
        {#if data.stale_goals.length === 0}
          <p class="text-sm text-gray-500 dark:text-gray-400">
            No stale goals detected.
          </p>
        {:else}
          <ul class="space-y-1 text-sm text-gray-900 dark:text-white">
            {#each data.stale_goals as goal}
              <li
                class="flex items-center justify-between hover:bg-gray-50 dark:hover:bg-gray-800 p-1 rounded"
              >
                <button
                  class="flex items-center gap-2 w-full text-left"
                  on:click={() => openEditGoalEditor(goal)}
                >
                  <span
                    class="font-mono text-xs text-gray-800 dark:text-gray-200"
                    >{goal.goal_id}</span
                  >
                  <span class="badge {getStatusBadge(goal.status)}"
                    >{goal.status}</span
                  >
                  <span class="text-gray-900 dark:text-white">{goal.title}</span
                  >
                </button>
                {#if goal.updated}
                  <span
                    class="text-xs text-gray-500 dark:text-gray-400 whitespace-nowrap ml-2"
                    >Updated {formatDate(goal.updated)}</span
                  >
                {:else}
                  <span
                    class="text-xs text-gray-500 dark:text-gray-400 whitespace-nowrap ml-2"
                    >No update date</span
                  >
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
        <h3 class="text-xl font-semibold text-gray-900 dark:text-white mb-3">
          Recent Decisions
        </h3>
        {#if data.recent_decisions.length === 0}
          <p class="text-sm text-gray-500 dark:text-gray-400">
            No decisions found.
          </p>
        {:else}
          <div class="space-y-2">
            {#each data.recent_decisions as decision}
              <div
                class="p-3 rounded-md border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800"
              >
                <div class="flex items-center justify-between">
                  <div>
                    <div class="font-semibold text-gray-900 dark:text-white">
                      {decision.title}
                    </div>
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
          <h3 class="text-xl font-semibold text-gray-900 dark:text-white">
            Canon Snapshot
          </h3>
          <span
            class="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400"
            >Immutable</span
          >
        </div>
        {#if data.canon_docs.length === 0}
          <p class="text-sm text-gray-500 dark:text-gray-400">
            No canon documents found under canon/.
          </p>
        {:else}
          <ul class="space-y-2">
            {#each data.canon_docs as doc}
              <li
                class="flex items-center justify-between p-3 rounded-md border border-gray-200 dark:border-gray-700"
              >
                <div>
                  <div class="font-semibold text-gray-900 dark:text-white">
                    {doc.title}
                  </div>
                  <div
                    class="text-xs font-mono text-gray-500 dark:text-gray-400"
                  >
                    {doc.file_path}
                  </div>
                </div>
                <span class="text-xs text-gray-500 dark:text-gray-400"
                  >read-only</span
                >
              </li>
            {/each}
          </ul>
        {/if}
        {#if data.protocols.length > 0}
          <div class="mt-3">
            <div
              class="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400 mb-1"
            >
              Protocols
            </div>
            <ul class="space-y-1">
              {#each data.protocols as doc}
                <li
                  class="flex items-center justify-between p-2 rounded-md border border-gray-200 dark:border-gray-700"
                >
                  <div class="font-semibold text-gray-900 dark:text-white">
                    {doc.title}
                  </div>
                  <span class="text-xs text-gray-500 dark:text-gray-400"
                    >{doc.file_path}</span
                  >
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
  />
{/if}

{#if showGoalEditor}
  <GoalEditor
    goal={editingGoal}
    onClose={closeGoalEditor}
    on:saved={handleGoalSaved}
    on:create-subgoal={handleCreateSubGoal}
  />
{/if}

<Toast bind:show={toastShow} message={toastMessage} type={toastType} />
