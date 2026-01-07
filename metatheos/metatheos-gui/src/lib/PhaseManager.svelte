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
              <span class="text-2xl">📐</span>
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
    padding: 16px;
    border: 2px solid rgba(107, 114, 128, 0.2);
    border-radius: 12px;
    background: white;
    transition: all 0.2s ease;
    cursor: pointer;
  }

  .phase-card:hover {
    border-color: rgba(59, 130, 246, 0.5);
    background: rgba(59, 130, 246, 0.05);
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  }

  .phase-card.active {
    border-color: rgba(59, 130, 246, 0.8);
    background: rgba(59, 130, 246, 0.1);
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2);
  }

  .active-badge {
    background: rgba(34, 197, 94, 0.15);
    color: rgb(21, 128, 61);
    padding: 4px 8px;
    border-radius: 6px;
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
  }

  .status-badge {
    padding: 4px 10px;
    border-radius: 6px;
    font-size: 12px;
    font-weight: 600;
    text-transform: capitalize;
  }

  @media (prefers-color-scheme: dark) {
    .phase-card {
      background: rgba(31, 41, 55, 0.8);
      border-color: rgba(75, 85, 99, 0.5);
    }

    .phase-card:hover {
      background: rgba(59, 130, 246, 0.1);
      border-color: rgba(59, 130, 246, 0.6);
    }

    .phase-card.active {
      background: rgba(59, 130, 246, 0.15);
      border-color: rgba(59, 130, 246, 0.8);
    }

    .active-badge {
      background: rgba(34, 197, 94, 0.2);
      color: rgb(134, 239, 172);
    }
  }
</style>
