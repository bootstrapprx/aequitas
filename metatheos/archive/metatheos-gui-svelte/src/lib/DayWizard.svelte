<script lang="ts">
  import { invoke } from "@tauri-apps/api/core";
  import { createEventDispatcher, onMount } from "svelte";

  const dispatch = createEventDispatcher();

  // Wizard state
  let step = 1;
  let dayType: "light" | "heavy" | "review" | "rest" | null = null;
  let selectedPhase: string | null = null;
  let selectedGoals: { goal_id: string; required: boolean }[] = [];
  let isLoading = false;
  let error: string | null = null;

  // Data fetching
  let phases: any[] = [];
  let availableGoals: any[] = [];
  let activePhase: string | null = null;

  const dayTypes = [
    {
      value: "light",
      label: "Light Day",
      icon: "🌤️",
      description: "Maintenance, exploration, light execution. Goals optional.",
    },
    {
      value: "heavy",
      label: "Heavy Day",
      icon: "💪",
      description: "Deep execution. Exactly 2 required goals.",
    },
    {
      value: "review",
      label: "Review Day",
      icon: "📊",
      description: "Reflection and closure. Only done/partial goals.",
    },
    {
      value: "rest",
      label: "Rest Day",
      icon: "🌙",
      description: "No execution. No goals allowed.",
    },
  ];

  onMount(async () => {
    await loadPhases();
    await resolveActivePhase();
  });

  async function loadPhases() {
    try {
      phases = await invoke("get_all_phases");
    } catch (e) {
      error = `Failed to load phases: ${e}`;
    }
  }

  async function resolveActivePhase() {
    try {
      const active = await invoke("get_active_phase");
      if (active && active.phase_id) {
        activePhase = active.phase_id;
        selectedPhase = active.phase_id;
      }
    } catch (e) {
      // No active phase, user will select manually
    }
  }

  async function loadAvailableGoals() {
    if (!selectedPhase || !dayType) return;

    try {
      availableGoals = await invoke("get_available_goals_for_day", {
        phaseId: selectedPhase,
        dayType: dayType,
      });
    } catch (e) {
      error = `Failed to load goals: ${e}`;
    }
  }

  function selectDayType(type: string) {
    dayType = type as any;
    error = null;
  }

  function selectPhase(phaseId: string) {
    selectedPhase = phaseId;
    error = null;
  }

  function toggleGoal(goalId: string) {
    const index = selectedGoals.findIndex((g) => g.goal_id === goalId);
    if (index >= 0) {
      selectedGoals.splice(index, 1);
    } else {
      selectedGoals.push({ goal_id: goalId, required: dayType === "heavy" });
    }
    selectedGoals = [...selectedGoals];
    error = null;
  }

  function canProceedStep1(): boolean {
    return dayType !== null;
  }

  function canProceedStep2(): boolean {
    return selectedPhase !== null;
  }

  function canProceedStep3(): boolean {
    if (dayType === "heavy") {
      const requiredCount = selectedGoals.filter((g) => g.required).length;
      return requiredCount === 2;
    }
    if (dayType === "rest") {
      return selectedGoals.length === 0;
    }
    return true; // Light and Review have no hard constraints
  }

  async function nextStep() {
    error = null;

    if (step === 1 && !canProceedStep1()) {
      error = "Please select a day type";
      return;
    }

    if (step === 2 && !canProceedStep2()) {
      error = "Please select a phase";
      return;
    }

    if (step === 2) {
      // Load available goals when entering step 3
      await loadAvailableGoals();
    }

    if (step === 3 && !canProceedStep3()) {
      if (dayType === "heavy") {
        error = "Heavy day requires exactly 2 goals marked as required";
      } else if (dayType === "rest") {
        error = "Rest day cannot have goals";
      }
      return;
    }

    step++;
  }

  function prevStep() {
    if (step > 1) {
      step--;
      error = null;
    }
  }

  async function confirmAndCreateDay() {
    isLoading = true;
    error = null;

    try {
      const today = new Date().toISOString().split("T")[0]; // YYYY-MM-DD

      await invoke("create_day", {
        request: {
          date: today,
          phase_id: selectedPhase,
          day_type: dayType,
          selected_goals: selectedGoals,
        },
      });

      dispatch("dayCreated", { date: today });
    } catch (e) {
      error = `Failed to create day: ${e}`;
      isLoading = false;
    }
  }
</script>

<div class="day-wizard">
  <div class="wizard-header">
    <h1>Begin Your Day</h1>
    <div class="step-indicator">
      <span class:active={step === 1}>1. Day Type</span>
      <span class:active={step === 2}>2. Phase</span>
      {#if dayType !== "rest"}
        <span class:active={step === 3}>3. Focus Goals</span>
      {/if}
      <span class:active={step === 4 || (dayType === "rest" && step === 3)}
        >4. Confirm</span
      >
    </div>
  </div>

  {#if error}
    <div class="error-message">
      {error}
    </div>
  {/if}

  {#if step === 1}
    <div class="wizard-step">
      <h2>Select Day Type</h2>
      <div class="day-type-cards">
        {#each dayTypes as type}
          <button
            class="day-type-card {type.value}"
            class:selected={dayType === type.value}
            on:click={() => selectDayType(type.value)}
          >
            <div class="icon">{type.icon}</div>
            <h3>{type.label}</h3>
            <p>{type.description}</p>
          </button>
        {/each}
      </div>
    </div>
  {/if}

  {#if step === 2}
    <div class="wizard-step">
      <h2>Resolve Phase</h2>
      {#if activePhase}
        <p class="hint">Active phase: <strong>{activePhase}</strong></p>
      {/if}
      <div class="phase-list">
        {#each phases as phase}
          <button
            class="phase-item"
            class:selected={selectedPhase === phase.phase_id}
            on:click={() => selectPhase(phase.phase_id)}
          >
            <span class="phase-id">{phase.phase_id}</span>
            <span class="phase-title">{phase.title}</span>
            <span class="phase-status badge">{phase.status || "active"}</span>
          </button>
        {/each}
      </div>
    </div>
  {/if}

  {#if step === 3 && dayType !== "rest"}
    <div class="wizard-step">
      <h2>Select Focus Goals</h2>
      {#if dayType === "heavy"}
        <p class="hint">Heavy day: Select exactly 2 goals (both required)</p>
      {:else if dayType === "review"}
        <p class="hint">Review day: Select done or partial goals</p>
      {:else}
        <p class="hint">Light day: Select any number of goals (optional)</p>
      {/if}

      <div class="goal-list">
        {#each availableGoals as goal}
          <button
            class="goal-item"
            class:selected={selectedGoals.some(
              (g) => g.goal_id === goal.goal_id,
            )}
            on:click={() => toggleGoal(goal.goal_id)}
          >
            <input
              type="checkbox"
              checked={selectedGoals.some((g) => g.goal_id === goal.goal_id)}
              readonly
            />
            <div class="goal-info">
              <span class="goal-id">{goal.goal_id}</span>
              <span class="goal-title">{goal.title}</span>
              <span class="goal-status badge">{goal.status}</span>
            </div>
          </button>
        {/each}

        {#if availableGoals.length === 0}
          <p class="no-goals">
            No goals available for this day type and phase.
          </p>
        {/if}
      </div>

      <div class="selection-summary">
        Selected: {selectedGoals.length} goal{selectedGoals.length !== 1
          ? "s"
          : ""}
        {#if dayType === "heavy"}
          (Required: 2)
        {/if}
      </div>
    </div>
  {/if}

  {#if step === (dayType === "rest" ? 3 : 4)}
    <div class="wizard-step">
      <h2>Confirm Day Context</h2>
      <div class="confirmation-card">
        <div class="confirm-row">
          <span class="label">📅 Date:</span>
          <span class="value">{new Date().toLocaleDateString()}</span>
        </div>
        <div class="confirm-row">
          <span class="label">⚙️ Day Type:</span>
          <span class="value">
            {dayTypes.find((t) => t.value === dayType)?.label || dayType}
          </span>
        </div>
        <div class="confirm-row">
          <span class="label">🧭 Phase:</span>
          <span class="value">
            {phases.find((p) => p.phase_id === selectedPhase)?.title ||
              selectedPhase}
          </span>
        </div>
        {#if selectedGoals.length > 0}
          <div class="confirm-row">
            <span class="label">🎯 Focus Goals:</span>
            <div class="value goals-list">
              {#each selectedGoals as goal}
                {@const goalData = availableGoals.find(
                  (g) => g.goal_id === goal.goal_id,
                )}
                <div class="goal-summary">
                  <span>{goal.goal_id} — {goalData?.title || "Unknown"}</span>
                  {#if goal.required}
                    <span class="badge required">required</span>
                  {/if}
                </div>
              {/each}
            </div>
          </div>
        {/if}
      </div>
    </div>
  {/if}

  <div class="wizard-actions">
    {#if step > 1}
      <button
        class="btn btn-secondary"
        on:click={prevStep}
        disabled={isLoading}
      >
        ← Back
      </button>
    {/if}

    {#if step < (dayType === "rest" ? 3 : 4)}
      <button class="btn btn-primary" on:click={nextStep} disabled={isLoading}>
        Next →
      </button>
    {:else}
      <button
        class="btn btn-success"
        on:click={confirmAndCreateDay}
        disabled={isLoading}
      >
        {isLoading ? "Creating..." : "✅ Confirm & Start Day"}
      </button>
    {/if}
  </div>
</div>

<style>
  .day-wizard {
    max-width: 800px;
    margin: 0 auto;
    padding: 24px;
  }

  .wizard-header {
    text-align: center;
    margin-bottom: 32px;
  }

  .wizard-header h1 {
    font-size: 2rem;
    font-weight: 700;
    margin-bottom: 16px;
  }

  .step-indicator {
    display: flex;
    justify-content: center;
    gap: 16px;
    flex-wrap: wrap;
  }

  .step-indicator span {
    padding: 8px 16px;
    border-radius: 16px;
    background: #f0f0f0;
    font-size: 14px;
    color: #666;
  }

  .step-indicator span.active {
    background: #a8d0e6; /* Sky */
    color: #374785; /* Navy */
    font-weight: 600;
  }

  .error-message {
    padding: 12px 16px;
    margin-bottom: 24px;
    background: #fee;
    border: 1px solid #fcc;
    border-radius: 8px;
    color: #c33;
    font-weight: 500;
  }

  .wizard-step {
    min-height: 400px;
  }

  .wizard-step h2 {
    font-size: 1.5rem;
    font-weight: 600;
    margin-bottom: 16px;
  }

  .hint {
    color: #cbd5e1; /* slate-300 */
    margin-bottom: 16px;
  }

  .day-type-cards {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 16px;
  }

  .day-type-card {
    padding: 24px;
    border: 2px solid transparent; /* Changed from #ddd */
    border-radius: 12px;
    background: rgba(255, 255, 255, 0.1); /* Fallback */
    cursor: pointer;
    transition: all 0.2s;
    text-align: center;
  }

  .day-type-card.heavy {
    background: #f76c6c; /* Coral */
    color: white;
  }
  .day-type-card.light {
    background: #f8e9a1; /* Cream */
    color: #374785; /* Navy */
  }
  .day-type-card.review {
    background: #a8d0e6; /* Sky */
    color: #374785; /* Navy */
  }
  .day-type-card.rest {
    background: #4d5d9a; /* Navy Light */
    color: white;
  }

  .day-type-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 16px rgba(0, 0, 0, 0.3);
  }

  .day-type-card.selected {
    border-color: white;
    box-shadow:
      0 0 0 2px white,
      0 8px 16px rgba(0, 0, 0, 0.4);
  }

  .day-type-card .icon {
    font-size: 3rem;
    margin-bottom: 12px;
  }

  .day-type-card h3 {
    font-size: 1.1rem;
    font-weight: 700;
    margin-bottom: 8px;
  }

  .day-type-card p {
    font-size: 0.9rem;
    opacity: 0.9;
  }

  .phase-list,
  .goal-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .phase-item,
  .goal-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 16px;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    background: rgba(255, 255, 255, 0.05);
    cursor: pointer;
    transition: all 0.2s;
    text-align: left;
    color: white;
  }

  .phase-item:hover,
  .goal-item:hover {
    border-color: #a8d0e6;
    background: #f9f9f9;
  }

  .phase-item.selected,
  .goal-item.selected {
    border-color: #a8d0e6;
    background: rgba(168, 208, 230, 0.2);
  }

  .phase-id,
  .goal-id {
    font-family: monospace;
    font-weight: 600;
    color: #a8d0e6; /* Sky */
  }

  .phase-title,
  .goal-title {
    flex: 1;
  }

  .goal-info {
    display: flex;
    align-items: center;
    gap: 12px;
    flex: 1;
  }

  .badge {
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 12px;
    font-weight: 600;
    text-transform: uppercase;
  }

  .phase-status.badge {
    background: rgba(40, 167, 69, 0.2);
    color: #4cd964;
  }

  .goal-status.badge {
    background: #fff3cd;
    color: #856404;
  }

  .required.badge {
    background: #ff6b6b;
    color: white;
  }

  .no-goals {
    text-align: center;
    color: #94a3b8; /* slate-400 */
    padding: 32px;
  }

  .selection-summary {
    margin-top: 16px;
    padding: 12px;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    font-weight: 500;
    color: white;
  }

  .confirmation-card {
    padding: 24px;
    border: 2px solid #a8d0e6; /* Sky */
    border-radius: 12px;
    background: rgba(255, 255, 255, 0.05);
    color: white;
  }

  .confirm-row {
    display: flex;
    gap: 16px;
    margin-bottom: 16px;
    align-items: flex-start;
  }

  .confirm-row:last-child {
    margin-bottom: 0;
  }

  .confirm-row .label {
    font-weight: 600;
    min-width: 120px;
  }

  .confirm-row .value {
    flex: 1;
  }

  .goals-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .goal-summary {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 6px;
  }

  .wizard-actions {
    display: flex;
    justify-content: space-between;
    margin-top: 32px;
    padding-top: 24px;
    border-top: 1px solid #ddd;
  }

  .btn {
    padding: 12px 24px;
    border: none;
    border-radius: 8px;
    font-size: 1rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
  }

  .btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .btn-secondary {
    background: rgba(255, 255, 255, 0.1);
    color: white;
  }

  .btn-secondary:hover:not(:disabled) {
    background: rgba(255, 255, 255, 0.2);
  }

  .btn-primary {
    background: #a8d0e6; /* Sky */
    color: #374785; /* Navy */
  }

  .btn-primary:hover:not(:disabled) {
    background: #98c0d6;
  }

  .btn-success {
    background: #28a745;
    color: white;
  }

  .btn-success:hover:not(:disabled) {
    background: #218838;
  }
</style>
