<script>
  import { invoke } from "@tauri-apps/api/core";
  import { onMount, onDestroy } from "svelte";
  import Toast from "./Toast.svelte";
  import GoalEditor from "./GoalEditor.svelte";
  import { setupLiveUpdates, cleanupLiveUpdates } from "./stores/governance";
  import { createEventDispatcher } from "svelte";

  const dispatch = createEventDispatcher();

  let loading = true;
  let error = null;
  let devMode = false;
  let goals = [];
  let groupedGoals = {};
  let statusFilter = "all";
  let searchQuery = "";
  let updatingGoalId = null;
  let showStatusMenu = null;

  let toastShow = false;
  let toastMessage = "";
  let toastType = "success";

  // Editor state
  let showEditor = false;
  let editingGoal = null;

  // Relationship highlighting state
  let hoveredGoalId = null;
  let highlightedDependencies = new Set();
  let highlightedReverseDeps = new Set();

  // Daily note references modal state
  let showDailyRefsModal = false;
  let selectedGoalForDailyRefs = null;
  let layoutOk = false;
  let layoutMissing = [];

  const statusOrder = [
    "planned",
    "active",
    "blocked",
    "partial",
    "done",
    "archived",
    "unknown",
  ];

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
    await verifyLayout();
    await loadGoals();

    // PHASE 2.3: Setup live updates for real-time sync
    await setupLiveUpdates({
      onGoalChange: async () => {
        console.log("[GoalExplorer] Goal changed, reloading...");
        await loadGoals();
      },
    });
  });

  onDestroy(async () => {
    // Clean up event listeners when component is destroyed
    await cleanupLiveUpdates();
  });

  async function verifyLayout() {
    // DB-Only Mode: We don't enforce file layout strictness in the GUI anymore
    // The DB is the source of truth.
    layoutOk = true;
    layoutMissing = [];
    /* 
    try {
      const result = await invoke("check_governance_layout");
      layoutOk = result.ok;
      layoutMissing = result.missing || [];
      if (!layoutOk) {
        toastMessage = `Governance layout incomplete: ${layoutMissing.join(", ")}`;
        toastType = "error";
        toastShow = true;
      }
    } catch (err) {
      console.warn("Layout check skipped/failed:", err);
      layoutOk = true; // Default to OK to not block user
    }
    */
  }

  async function loadGoals() {
    try {
      loading = true;
      // Phase-first: prefer active phase; if none, fall back to first available phase.
      let activePhase = await invoke("get_active_phase", { date: null });
      if (!activePhase) {
        const phases = await invoke("get_all_phases");
        if (phases && phases.length > 0) {
          activePhase = phases[0];
        }
      }

      if (activePhase) {
        const result = await invoke("get_goals_by_phase", {
          phase: activePhase.phase_id,
        });
        goals = result;
        toastMessage = `Loaded goals for ${activePhase.title}`;
        toastType = "success";
        toastShow = true;
      } else {
        goals = [];
        toastMessage = "No phase available in DB.";
        toastType = "info";
        toastShow = true;
      }

      applyFilters();
      error = null;
    } catch (err) {
      console.error("Failed to load goals:", err);
      error = err?.toString?.() ?? String(err);
      goals = [];
    } finally {
      loading = false;
    }
  }

  function applyFilters() {
    let filtered = goals;

    if (statusFilter !== "all") {
      filtered = filtered.filter(
        (goal) => goal.status.toLowerCase() === statusFilter,
      );
    }

    if (searchQuery) {
      filtered = filtered.filter((goal) => {
        const q = searchQuery.toLowerCase();
        return (
          goal.goal_id.toLowerCase().includes(q) ||
          goal.title.toLowerCase().includes(q) ||
          (goal.owner && goal.owner.toLowerCase().includes(q))
        );
      });
    }

    groupedGoals = groupByPhaseAndStatus(filtered);
  }

  function groupByPhaseAndStatus(goalList) {
    const grouped = {};
    for (const goal of goalList) {
      const phase = goal.phase || "Unassigned";
      const status = goal.status || "unknown";
      if (!grouped[phase]) grouped[phase] = {};
      if (!grouped[phase][status]) grouped[phase][status] = [];
      grouped[phase][status].push(goal);
    }
    return grouped;
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

  async function updateGoalStatus(goalId, newStatus) {
    if (devMode) {
      toastMessage = "Status changes require Tauri. Run `cargo tauri dev`.";
      toastType = "error";
      toastShow = true;
      return;
    }
    if (!layoutOk) {
      toastMessage =
        "Governance layout invalid; fix folders before changing status.";
      toastType = "error";
      toastShow = true;
      return;
    }

    if (!confirm(`Change status for ${goalId} to ${newStatus}?`)) {
      return;
    }

    try {
      updatingGoalId = goalId;
      await invoke("update_goal_status", {
        goalId,
        newStatus,
      });

      toastMessage = `Updated ${goalId} to ${newStatus}`;
      toastType = "success";
      toastShow = true;

      await loadGoals();
      showStatusMenu = null;
    } catch (err) {
      toastMessage = err?.toString?.() ?? String(err);
      toastType = "error";
      toastShow = true;
    } finally {
      updatingGoalId = null;
    }
  }

  function toggleStatusMenu(goalId) {
    showStatusMenu = showStatusMenu === goalId ? null : goalId;
  }

  function formatDate(value) {
    if (!value) return "n/a";
    return new Date(value).toLocaleDateString();
  }

  function computePhaseMetrics(phase) {
    const phaseGoals = Object.values(groupedGoals[phase] || {}).flat();
    const total = phaseGoals.length;
    const doneCount = phaseGoals.filter((g) => g.status === "done").length;
    const activeCount = phaseGoals.filter((g) => g.status === "active").length;
    const blockedCount = phaseGoals.filter((g) => g.completion_blocked).length;
    const partialCount = phaseGoals.filter(
      (g) => g.status === "partial",
    ).length;
    const completion = total > 0 ? Math.round((doneCount / total) * 100) : 0;

    return {
      total,
      doneCount,
      activeCount,
      blockedCount,
      partialCount,
      completion,
    };
  }

  function getPhaseColorClass(phase) {
    const colors = {
      P1: "bg-purple-100 dark:bg-purple-900/30 border-purple-300 dark:border-purple-700",
      P2: "bg-blue-100 dark:bg-blue-900/30 border-blue-300 dark:border-blue-700",
      P3: "bg-green-100 dark:bg-green-900/30 border-green-300 dark:border-green-700",
      P4: "bg-yellow-100 dark:bg-yellow-900/30 border-yellow-300 dark:border-yellow-700",
      P5: "bg-orange-100 dark:bg-orange-900/30 border-orange-300 dark:border-orange-700",
      P6: "bg-red-100 dark:bg-red-900/30 border-red-300 dark:border-red-700",
    };
    return (
      colors[phase] ||
      "bg-gray-100 dark:bg-gray-900/30 border-gray-300 dark:border-gray-700"
    );
  }

  function getPhaseBadgeClass(phase) {
    const colors = {
      P1: "bg-purple-600 text-white",
      P2: "bg-blue-600 text-white",
      P3: "bg-green-600 text-white",
      P4: "bg-yellow-600 text-white",
      P5: "bg-orange-600 text-white",
      P6: "bg-red-600 text-white",
    };
    return colors[phase] || "bg-gray-600 text-white";
  }

  function handleGoalHover(goal) {
    hoveredGoalId = goal.goal_id;
    highlightedDependencies = new Set(goal.dependencies);
    highlightedReverseDeps = new Set(goal.reverse_dependencies);
  }

  function handleGoalLeave() {
    hoveredGoalId = null;
    highlightedDependencies = new Set();
    highlightedReverseDeps = new Set();
  }

  function scrollToGoal(goalId) {
    const element = document.getElementById(`goal-${goalId}`);
    if (element) {
      element.scrollIntoView({ behavior: "smooth", block: "center" });
      // Flash the element briefly
      element.classList.add("ring-2", "ring-primary-500");
      setTimeout(() => {
        element.classList.remove("ring-2", "ring-primary-500");
      }, 2000);
    }
  }

  function openDailyRefsModal(goal) {
    selectedGoalForDailyRefs = goal;
    showDailyRefsModal = true;
  }

  function closeDailyRefsModal() {
    showDailyRefsModal = false;
    selectedGoalForDailyRefs = null;
  }

  function getHighlightClass(goalId) {
    if (hoveredGoalId === goalId) {
      return "ring-2 ring-primary-500 bg-primary-50 dark:bg-primary-900/20";
    }
    if (highlightedDependencies.has(goalId)) {
      return "ring-2 ring-blue-400 bg-blue-50 dark:bg-blue-900/20";
    }
    if (highlightedReverseDeps.has(goalId)) {
      return "ring-2 ring-green-400 bg-green-50 dark:bg-green-900/20";
    }
    return "";
  }

  function openNewGoalEditor() {
    editingGoal = null;
    showEditor = true;
  }

  function openEditGoalEditor(goal) {
    editingGoal = goal;
    showEditor = true;
  }

  function closeEditor() {
    showEditor = false;
    editingGoal = null;
  }

  async function handleGoalSaved() {
    toastMessage = editingGoal
      ? "Goal updated successfully!"
      : "Goal created successfully!";
    toastType = "success";
    toastShow = true;
    await loadGoals();
  }

  async function handleGoalDeleted() {
    toastMessage = "Goal deleted successfully!";
    toastType = "success";
    toastShow = true;
    await loadGoals();
  }

  $: {
    searchQuery;
    applyFilters();
  }

  const statuses = [
    { value: "all", label: "All" },
    { value: "planned", label: "Planned" },
    { value: "active", label: "Active" },
    { value: "blocked", label: "Blocked" },
    { value: "partial", label: "Partial" },
    { value: "done", label: "Done" },
  ];
</script>

<div>
  <div class="flex items-center justify-between mb-6">
    <div>
      <h2 class="text-3xl font-bold text-gray-900 dark:text-white">Goals</h2>
      <p class="text-sm text-gray-500 dark:text-gray-400">
        Goals are stored and managed in the database. Changes are immediately persistent.
      </p>
    </div>
    <div class="flex gap-3">
      <button
        class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded transition-colors flex items-center gap-2"
        on:click={openNewGoalEditor}
        disabled={devMode || !layoutOk}
      >
        <svg
          class="w-5 h-5"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M12 4v16m8-8H4"
          />
        </svg>
        New Goal
      </button>
      <button class="btn btn-secondary" on:click={loadGoals} disabled={loading}>
        {loading ? "Refreshing…" : "Refresh"}
      </button>
    </div>
  </div>

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
        Run <code>cargo tauri dev</code> to load and edit goals from the database.
      </p>
    </div>
  {:else if !layoutOk}
    <div
      class="card mb-6 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800"
    >
      <h3 class="text-lg font-semibold text-red-800 dark:text-red-200 mb-2">
        Governance layout check failed
      </h3>
      <p class="text-red-700 dark:text-red-200 text-sm">
        Missing folders: {layoutMissing.join(", ")}. Writes are disabled until
        the vault matches the expected structure.
      </p>
    </div>
  {/if}

  {#if loading}
    <div class="card">
      <p class="text-gray-500 dark:text-gray-400">Loading goals...</p>
    </div>
  {:else if error}
    <div
      class="card bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800"
    >
      <p class="text-red-800 dark:text-red-200">Error: {error}</p>
    </div>
  {:else}
    <!-- Filters -->
    <div class="card mb-6">
      <div class="flex flex-col md:flex-row gap-4">
        <div class="flex gap-2 flex-wrap">
          {#each statuses as status}
            <button
              class="px-4 py-2 rounded-md text-sm font-medium transition-colors {statusFilter ===
              status.value
                ? 'bg-primary-600 text-white'
                : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'}"
              on:click={() => {
                statusFilter = status.value;
                applyFilters();
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
        <p class="text-gray-500 dark:text-gray-400">
          No goals match the current filters.
        </p>
      </div>
    {:else}
      <div class="space-y-6">
        {#each Object.keys(groupedGoals).sort() as phase}
          {@const metrics = computePhaseMetrics(phase)}
          <div class="border-2 rounded-lg {getPhaseColorClass(phase)}">
            <!-- Phase Summary Panel -->
            <div class="p-4 border-b border-current/20">
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-3">
                  <span
                    class="px-3 py-1 rounded-md font-bold {getPhaseBadgeClass(
                      phase,
                    )}"
                  >
                    Phase {phase}
                  </span>
                  <div class="flex items-center gap-3 text-sm font-medium">
                    <span class="text-green-700 dark:text-green-300">
                      ✓ Done: {metrics.doneCount}
                    </span>
                    <span class="text-blue-700 dark:text-blue-300">
                      ● Active: {metrics.activeCount}
                    </span>
                    {#if metrics.blockedCount > 0}
                      <span
                        class="text-red-700 dark:text-red-300 font-semibold"
                      >
                        ⛔ Blocked: {metrics.blockedCount}
                      </span>
                    {/if}
                    {#if metrics.partialCount > 0}
                      <span class="text-yellow-700 dark:text-yellow-300">
                        ⧗ Partial: {metrics.partialCount}
                      </span>
                    {/if}
                  </div>
                </div>
                <div class="text-sm font-semibold">
                  <span class="text-gray-700 dark:text-gray-300">
                    Completion: {metrics.completion}%
                  </span>
                  <span class="text-gray-500 dark:text-gray-400 ml-2">
                    ({metrics.doneCount}/{metrics.total})
                  </span>
                </div>
              </div>
            </div>

            <div class="space-y-4">
              {#each statusOrder as status}
                {#if groupedGoals[phase][status]}
                  <div>
                    <div class="flex items-center gap-2 mb-2">
                      <span class="badge {getStatusBadge(status)}"
                        >{status}</span
                      >
                      <span class="text-xs text-gray-500 dark:text-gray-400">
                        {groupedGoals[phase][status].length} goal(s)
                      </span>
                    </div>
                    <div class="space-y-2">
                      {#each groupedGoals[phase][status] as goal}
                        <!-- svelte-ignore a11y-no-static-element-interactions -->
                        <div
                          id="goal-{goal.goal_id}"
                          class="p-3 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 hover:border-gray-400 dark:hover:border-gray-500 transition-all {getHighlightClass(
                            goal.goal_id,
                          )}"
                          on:mouseenter={() => handleGoalHover(goal)}
                          on:mouseleave={handleGoalLeave}
                        >
                          <div class="flex items-start justify-between gap-3">
                            <!-- Left: Goal Info -->
                            <div class="flex-1 space-y-2">
                              <!-- Header Row: ID, Title, Badges -->
                              <div class="flex items-start gap-2">
                                <span
                                  class="font-mono text-sm font-bold text-primary-600 dark:text-primary-400 shrink-0"
                                >
                                  {goal.goal_id}
                                </span>
                                <div class="flex-1">
                                  <div
                                    class="text-gray-900 dark:text-white font-medium leading-tight"
                                  >
                                    {goal.title}
                                  </div>
                                </div>
                              </div>

                              <!-- Metadata Row -->
                              <div class="flex items-center gap-3 text-xs">
                                {#if goal.phase}
                                  <span
                                    class="px-2 py-0.5 rounded {getPhaseBadgeClass(
                                      goal.phase,
                                    )} font-semibold"
                                  >
                                    {goal.phase}
                                  </span>
                                {/if}
                                <span
                                  class="badge {getStatusBadge(goal.status)}"
                                >
                                  {#if goal.status === "done"}
                                    🔒
                                  {/if}
                                  {goal.status}
                                </span>
                                {#if goal.updated}
                                  <span
                                    class="text-gray-500 dark:text-gray-400"
                                  >
                                    Updated {formatDate(goal.updated)}
                                  </span>
                                {/if}
                                {#if goal.is_canonical}
                                  <span
                                    class="px-2 py-0.5 bg-amber-100 dark:bg-amber-900/30 text-amber-800 dark:text-amber-200 rounded font-semibold"
                                    title="Canonical goal"
                                  >
                                    ★ Canon
                                  </span>
                                {/if}
                              </div>

                              <!-- Relationship Info -->
                              <div class="flex items-center gap-4 text-xs">
                                <!-- Dependencies -->
                                {#if goal.dependencies.length > 0}
                                  <div class="flex items-center gap-1">
                                    <span
                                      class="text-gray-600 dark:text-gray-400"
                                      >→</span
                                    >
                                    <span
                                      class="text-gray-700 dark:text-gray-300"
                                    >
                                      Depends: {goal.dependencies.length}
                                    </span>
                                    {#if goal.completion_blocked}
                                      <span
                                        class="text-red-600 dark:text-red-400 font-semibold"
                                      >
                                        (⛔ Blocked by {goal.blocked_by.length})
                                      </span>
                                    {/if}
                                    <div class="flex gap-1">
                                      {#each goal.dependencies.slice(0, 3) as depId}
                                        <button
                                          class="px-1 py-0.5 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded hover:bg-blue-200 dark:hover:bg-blue-800/40 transition-colors"
                                          on:click|stopPropagation={() =>
                                            scrollToGoal(depId)}
                                          title="Click to scroll to {depId}"
                                        >
                                          {depId}
                                        </button>
                                      {/each}
                                      {#if goal.dependencies.length > 3}
                                        <span
                                          class="text-gray-500 dark:text-gray-400"
                                          >+{goal.dependencies.length - 3}</span
                                        >
                                      {/if}
                                    </div>
                                  </div>
                                {/if}

                                <!-- Reverse Dependencies -->
                                {#if goal.reverse_dependencies.length > 0}
                                  <div class="flex items-center gap-1">
                                    <span
                                      class="text-gray-600 dark:text-gray-400"
                                      >←</span
                                    >
                                    <span
                                      class="text-gray-700 dark:text-gray-300"
                                    >
                                      {goal.reverse_dependencies.length} depend on
                                      this
                                    </span>
                                    <div class="flex gap-1">
                                      {#each goal.reverse_dependencies.slice(0, 2) as revDepId}
                                        <button
                                          class="px-1 py-0.5 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 rounded hover:bg-green-200 dark:hover:bg-green-800/40 transition-colors"
                                          on:click|stopPropagation={() =>
                                            scrollToGoal(revDepId)}
                                          title="Click to scroll to {revDepId}"
                                        >
                                          {revDepId}
                                        </button>
                                      {/each}
                                      {#if goal.reverse_dependencies.length > 2}
                                        <span
                                          class="text-gray-500 dark:text-gray-400"
                                          >+{goal.reverse_dependencies.length -
                                            2}</span
                                        >
                                      {/if}
                                    </div>
                                  </div>
                                {/if}

                                <!-- Daily References -->
                                {#if goal.daily_references.length > 0}
                                  <button
                                    class="flex items-center gap-1 hover:bg-gray-100 dark:hover:bg-gray-700 px-2 py-0.5 rounded transition-colors"
                                    on:click|stopPropagation={() =>
                                      openDailyRefsModal(goal)}
                                    title="Click to see daily notes"
                                  >
                                    <span
                                      class="text-gray-600 dark:text-gray-400"
                                      >📅</span
                                    >
                                    <span
                                      class="text-gray-700 dark:text-gray-300 underline decoration-dotted"
                                    >
                                      {goal.daily_references.length} daily note(s)
                                    </span>
                                  </button>
                                {/if}

                                <!-- Missing Dependencies Warning -->
                                {#if goal.missing_dependencies.length > 0}
                                  <div
                                    class="flex items-center gap-1 text-orange-600 dark:text-orange-400"
                                  >
                                    <span>⚠️</span>
                                    <span>
                                      {goal.missing_dependencies.length} missing
                                      dep(s)
                                    </span>
                                  </div>
                                {/if}
                              </div>

                              <!-- Blocked By Details -->
                              {#if goal.completion_blocked && goal.blocked_by.length > 0}
                                <div
                                  class="px-2 py-1 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded text-xs"
                                >
                                  <span
                                    class="text-red-800 dark:text-red-200 font-semibold"
                                  >
                                    Blocked by:
                                  </span>
                                  <span class="text-red-700 dark:text-red-300">
                                    {goal.blocked_by.join(", ")}
                                  </span>
                                </div>
                              {/if}
                            </div>

                            <!-- Right: Actions -->
                            <div class="flex gap-2 shrink-0">
                              <button
                                class="px-2 py-1 bg-primary-100 dark:bg-primary-900/40 hover:bg-primary-200 dark:hover:bg-primary-800/60 text-primary-800 dark:text-primary-200 text-xs rounded transition-colors"
                                on:click={() =>
                                  dispatch("openGoalDetail", {
                                    goalId: goal.goal_id,
                                  })}
                                aria-label="Open goal detail"
                              >
                                View
                              </button>
                              <button
                                class="px-2 py-1 bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 text-xs rounded transition-colors"
                                on:click={() => openEditGoalEditor(goal)}
                                disabled={devMode}
                                title="Edit goal"
                                aria-label="Edit goal"
                              >
                                <svg
                                  class="w-4 h-4"
                                  fill="none"
                                  stroke="currentColor"
                                  viewBox="0 0 24 24"
                                >
                                  <path
                                    stroke-linecap="round"
                                    stroke-linejoin="round"
                                    stroke-width="2"
                                    d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
                                  />
                                </svg>
                              </button>

                              <div class="relative">
                                <button
                                  class="px-2 py-1 bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 text-xs rounded transition-colors"
                                  on:click={() =>
                                    toggleStatusMenu(goal.goal_id)}
                                  disabled={updatingGoalId === goal.goal_id ||
                                    devMode ||
                                    goal.status === "done"}
                                  title={goal.status === "done"
                                    ? "Done goals are locked"
                                    : "Change status"}
                                >
                                  {updatingGoalId === goal.goal_id
                                    ? "..."
                                    : "⋮"}
                                </button>

                                {#if showStatusMenu === goal.goal_id && goal.status !== "done"}
                                  <div
                                    class="absolute right-0 mt-2 w-48 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 z-10"
                                  >
                                    <div class="py-1">
                                      {#each ["planned", "active", "blocked", "partial", "done"] as statusOption}
                                        {#if statusOption !== goal.status}
                                          <button
                                            class="w-full text-left px-4 py-2 text-sm hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors {getStatusBadge(
                                              statusOption,
                                            )}"
                                            on:click={() =>
                                              updateGoalStatus(
                                                goal.goal_id,
                                                statusOption,
                                              )}
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

{#if showDailyRefsModal && selectedGoalForDailyRefs}
  <div
    class="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
    role="button"
    tabindex="0"
    on:click={closeDailyRefsModal}
    on:keydown={(e) => e.key === "Escape" && closeDailyRefsModal()}
  >
    <div
      class="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-md w-full mx-4 p-6"
      role="dialog"
      aria-modal="true"
      tabindex="-1"
      on:click|stopPropagation
      on:keydown|stopPropagation
    >
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-xl font-semibold text-gray-900 dark:text-white">
          Daily Notes Referencing {selectedGoalForDailyRefs.goal_id}
        </h3>
        <button
          class="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
          on:click={closeDailyRefsModal}
          aria-label="Close"
        >
          <svg
            class="w-6 h-6"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </button>
      </div>

      <div class="mb-4">
        <p class="text-sm text-gray-600 dark:text-gray-400">
          This goal is referenced in the following daily notes:
        </p>
      </div>

      <div class="space-y-2 max-h-96 overflow-y-auto">
        {#each selectedGoalForDailyRefs.daily_references
          .sort()
          .reverse() as date}
          <div
            class="flex items-center gap-2 p-2 rounded bg-gray-50 dark:bg-gray-700 hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors"
          >
            <svg
              class="w-5 h-5 text-gray-600 dark:text-gray-400 shrink-0"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
              />
            </svg>
            <span class="font-mono text-sm text-gray-900 dark:text-white">
              {date}
            </span>
          </div>
        {/each}
      </div>

      <div class="mt-6 flex justify-end">
        <button
          class="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded transition-colors"
          on:click={closeDailyRefsModal}
        >
          Close
        </button>
      </div>
    </div>
  </div>
{/if}

<Toast bind:show={toastShow} message={toastMessage} type={toastType} />
