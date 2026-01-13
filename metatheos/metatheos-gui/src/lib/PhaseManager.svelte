<script>
  import { invoke } from "@tauri-apps/api/core";
  import { onMount, createEventDispatcher } from "svelte";
  import PhaseEditor from "./PhaseEditor.svelte";
  import PhaseProgressBar from "./PhaseProgressBar.svelte";

  const dispatch = createEventDispatcher();

  export let activePhase = null;

  let phases = [];
  let loading = true;
  let error = null;
  let showEditor = false;
  let editingPhase = null;

  onMount(async () => {
    await loadPhases();
  });

  async function loadPhases() {
    try {
      console.log("🔵 [PhaseManager] Calling get_all_phases...");
      loading = true;
      phases = await invoke("get_all_phases");
      console.log("🔵 [PhaseManager] Received phases:", phases);
      console.log("🔵 [PhaseManager] Phase count:", phases ? phases.length : 0);
      error = null;
    } catch (e) {
      console.error("🔴 [PhaseManager] Error loading phases:", e);
      error = e?.toString?.() ?? String(e);
    } finally {
      loading = false;
    }
  }

  async function selectPhase(phase) {
    try {
      await invoke("set_active_phase_db", { phaseId: phase.phase_id });
      dispatch("phaseChanged", { phase });
    } catch (e) {
      error = e?.toString?.() ?? String(e);
    }
  }

  function getStatusColor(status) {
    const s = (status || "").toLowerCase();
    if (s === "active")
      return "bg-green-100 text-green-800 dark:bg-green-900/40 dark:text-green-200";
    if (s === "planned")
      return "bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-200";
    if (s === "closed" || s === "archived")
      return "bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300";
    return "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/40 dark:text-yellow-200";
  }

  function openNewPhase() {
    editingPhase = null;
    showEditor = true;
  }

  function openEditPhase(phase) {
    editingPhase = phase;
    showEditor = true;
  }

  function closeEditor() {
    showEditor = false;
    editingPhase = null;
    loadPhases();
  }

  function getPhaseIcon(phaseId) {
    const icons = {
      "P0": "🏗️",  // Foundation Stone - building/construction
      "P1": "📜",  // Canon - rules/doctrine
      "P2": "⚙️",  // The Engine - machinery/mechanics
      "P3": "⏰",  // Time & Events - temporal tracking
      "P4": "✨",  // Materialization - manifestation
      "P5": "🧩",  // Operational Modules - modular components
      "P6": "👁️",  // The Observer - observation/monitoring
      "P7": "✅",  // Verification - validation/testing
      "P8": "🛡️",  // Hardening - protection/security
      "P9": "🌅",  // Horizon - future vision
    };
    return icons[phaseId] || "📐";  // Default to triangle if unknown
  }
</script>

<div class="space-y-6">
  <div class="flex items-center justify-between">
    <div>
      <h2 class="text-3xl font-bold text-gray-900 dark:text-white">Phases</h2>
      <p class="text-sm text-gray-600 dark:text-gray-300 mt-1">
        Phases define scope. Goals exist within phases. Select a phase to set
        the working context.
      </p>
    </div>
    <div class="flex gap-2">
      <button
        class="px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded text-sm font-semibold"
        on:click={openNewPhase}
      >
        New Phase
      </button>
      {#if activePhase}
        <button
          class="px-3 py-2 bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-white rounded text-sm"
          on:click={() => openEditPhase(activePhase)}
        >
          Edit Active
        </button>
      {/if}
    </div>
  </div>

  {#if loading}
    <div class="card">Loading phases…</div>
  {:else if error}
    <div
      class="card bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-800 dark:text-red-200"
    >
      {error}
    </div>
  {:else if phases.length === 0}
    <div
      class="card bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 text-yellow-800 dark:text-yellow-200"
    >
      <p class="font-semibold mb-2">No phases found</p>
      <p class="text-sm">
        Initialize a default phase from the diagnostics panel to get started.
      </p>
    </div>
  {:else}
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {#each phases as phase}
        <div
          role="button"
          tabindex="0"
          class={`phase-card ${activePhase && activePhase.phase_id === phase.phase_id ? "active" : ""}`}
          on:click={() => selectPhase(phase)}
          on:keydown={(e) =>
            (e.key === "Enter" || e.key === " ") && selectPhase(phase)}
        >
          <div class="flex items-start justify-between mb-3">
            <div class="flex items-center gap-2">
              <span class="text-2xl">{getPhaseIcon(phase.phase_id)}</span>
              <div>
                <div class="font-bold text-lg text-gray-900 dark:text-white">
                  {phase.title}
                </div>
                <div class="text-xs font-mono text-gray-500 dark:text-gray-400">
                  {phase.phase_id}
                </div>
              </div>
            </div>
            {#if activePhase && activePhase.phase_id === phase.phase_id}
              <span class="active-badge">Active</span>
            {/if}
          </div>

          {#if phase.description}
            <p class="text-sm text-gray-600 dark:text-gray-300 mb-3">
              {phase.description}
            </p>
          {/if}

          <div class="mb-3">
            <PhaseProgressBar phaseId={phase.phase_id} compact={true} />
          </div>

          <div class="flex items-center gap-2">
            <span class={`status-badge ${getStatusColor(phase.status)}`}>
              {phase.status}
            </span>
            <span class="text-xs text-gray-500 dark:text-gray-400">
              Order: {phase.order_index}
            </span>
            <span
              class="ml-auto text-xs px-2 py-1 bg-gray-200 dark:bg-gray-700 rounded cursor-pointer"
              role="button"
              tabindex="0"
              on:click|stopPropagation={() => openEditPhase(phase)}
              on:keydown|stopPropagation={(e) =>
                (e.key === "Enter" || e.key === " ") && openEditPhase(phase)}
            >
              Edit
            </span>
          </div>
        </div>
      {/each}
    </div>

    <div
      class="card bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800"
    >
      <div class="flex items-start gap-3">
        <span class="text-2xl">💡</span>
        <div>
          <p class="font-semibold text-blue-900 dark:text-blue-200 mb-1">
            Phase-First Architecture
          </p>
          <p class="text-sm text-blue-800 dark:text-blue-300">
            Phases are the structural spine of Metatheos. All goals, work items,
            and daily execution exist <em>within</em> a phase. Click a phase above
            to set it as your active working context.
          </p>
        </div>
      </div>
    </div>
  {/if}

  {#if showEditor}
    <PhaseEditor
      phase={editingPhase}
      onClose={closeEditor}
      on:saved={closeEditor}
      on:activated={closeEditor}
    />
  {/if}
</div>

<style>
  .phase-card {
    text-align: left;
    padding: 18px;
    border: 2px solid var(--color-border);
    border-radius: 12px;
    background: var(--color-surface);
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    cursor: pointer;
    position: relative;
  }

  .phase-card:hover {
    border-color: var(--color-accent);
    background: var(--color-surface-hover);
    transform: translateY(-3px);
    box-shadow: 0 8px 20px rgba(0, 0, 0, 0.12);
  }

  .phase-card.active {
    border-color: var(--color-phase-active-border);
    background: var(--color-phase-active-bg);
    box-shadow: 0 0 0 3px var(--color-emphasis-soft);
  }

  .phase-card.active::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 4px;
    background: linear-gradient(90deg, var(--color-phase-active), var(--color-accent));
    border-radius: 12px 12px 0 0;
  }

  .active-badge {
    background: var(--color-success-bg);
    color: var(--color-success);
    padding: 5px 10px;
    border-radius: 6px;
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    border: 1px solid var(--color-success);
  }

  .status-badge {
    padding: 5px 12px;
    border-radius: 6px;
    font-size: 12px;
    font-weight: 600;
    text-transform: capitalize;
  }
</style>
