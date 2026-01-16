<script>
    import { invoke } from "@tauri-apps/api/core";
    import { createEventDispatcher, onMount } from "svelte";
    import Toast from "./Toast.svelte";

    const dispatch = createEventDispatcher();

    let step = 1; // 1: Type, 2: Phase, 3: Goals
    let selectedType = "";
    let selectedPhase = null;
    let selectedGoals = []; // Array of strings (IDs)
    let phases = [];
    let phaseGoals = [];

    let loading = false;
    let error = null;

    // Constants
    const MODES = [
        {
            id: "Heavy",
            label: "Heavy",
            desc: "Deep work. Max 2 goals.",
            color: "bg-coral text-white",
        },
        {
            id: "Light",
            label: "Light",
            desc: "Maintenance/Small tasks.",
            color: "bg-cream text-navy-dark",
        },
        {
            id: "Review",
            label: "Review",
            desc: "Planning & Audit.",
            color: "bg-sky text-navy-dark",
        },
        {
            id: "Off",
            label: "Off",
            desc: "Rest.",
            color: "bg-navy-light text-white",
        },
    ];

    async function loadPhases() {
        try {
            phases = await invoke("get_all_phases");
            // Pre-select active if possible
            const active = await invoke("get_active_phase", { date: null });
            if (active) {
                selectedPhase = active;
                // If active phase exists, we might skip selection? OR meaningful choice?
                // User requirement: "Choose phase". So let them choose.
            }
        } catch (e) {
            error = e.toString();
        }
    }

    async function loadGoals(phaseId) {
        if (!phaseId) return;
        loading = true;
        try {
            phaseGoals = await invoke("get_goals_by_phase", { phase: phaseId });
            selectedGoals = [];
        } catch (e) {
            error = e.toString();
        } finally {
            loading = false;
        }
    }

    function selectType(type) {
        selectedType = type;
        if (type === "Off") {
            // Skip other steps?
            submit();
        } else {
            step = 2;
            loadPhases();
        }
    }

    function selectPhase(phase) {
        selectedPhase = phase;
        step = 3;
        loadGoals(phase.phase_id);
    }

    function toggleGoal(goalId) {
        if (selectedGoals.includes(goalId)) {
            selectedGoals = selectedGoals.filter((id) => id !== goalId);
        } else {
            if (selectedType === "Heavy" && selectedGoals.length >= 2) {
                // Constraint check visually (though backend enforces too)
                // Maybe shake or toast?
                return;
            }
            selectedGoals = [...selectedGoals, goalId];
        }
    }

    async function submit() {
        try {
            loading = true;
            await invoke("begin_day", {
                dayType: selectedType,
                phaseId: selectedPhase ? selectedPhase.phase_id : "none",
                selectedGoals,
            });
            dispatch("dayStarted");
        } catch (e) {
            error = e.toString();
        } finally {
            loading = false;
        }
    }
</script>

<div class="begin-day-container p-6">
    {#if error}
        <div class="error p-4 bg-red-900/50 text-red-200 mb-4 rounded">
            {error}
        </div>
    {/if}

    {#if step === 1}
        <h2 class="text-xl font-bold mb-4">Choose Day Mode</h2>
        <div class="grid grid-cols-2 gap-4">
            {#each MODES as mode}
                <button
                    class="p-4 rounded-lg text-left transition hover:scale-105 {mode.color}"
                    on:click={() => selectType(mode.id)}
                >
                    <div class="font-bold text-lg">{mode.label}</div>
                    <div class="text-sm opacity-80">{mode.desc}</div>
                </button>
            {/each}
        </div>
    {:else if step === 2}
        <h2 class="text-xl font-bold mb-4">Select Focus Phase</h2>
        <div class="space-y-2">
            {#each phases as phase}
                <button
                    class="w-full text-left p-3 rounded bg-navy-light/50 hover:bg-navy-light border border-navy-dark transition-colors"
                    on:click={() => selectPhase(phase)}
                >
                    <span class="font-bold">{phase.phase_id}</span>: {phase.title}
                </button>
            {/each}
        </div>
        <button
            class="mt-4 text-sm text-gray-400 hover:text-white"
            on:click={() => (step = 1)}>Back</button
        >
    {:else if step === 3}
        <h2 class="text-xl font-bold mb-4">
            Select Goals ({selectedGoals.length}/{selectedType === "Heavy"
                ? 2
                : "Any"})
        </h2>
        {#if phaseGoals.length === 0}
            <div class="text-gray-400">No active goals in this phase.</div>
        {:else}
            <div class="space-y-2 max-h-96 overflow-y-auto custom-scrollbar">
                {#each phaseGoals as goal}
                    <label
                        class="flex items-center space-x-3 p-3 rounded hover:bg-navy-light/30 cursor-pointer border border-navy-dark/50 transition-colors"
                    >
                        <input
                            type="checkbox"
                            checked={selectedGoals.includes(goal.goal_id)}
                            on:change={() => toggleGoal(goal.goal_id)}
                            disabled={selectedType === "Heavy" &&
                                !selectedGoals.includes(goal.goal_id) &&
                                selectedGoals.length >= 2}
                            class="w-4 h-4 rounded bg-navy-dark border-navy-light text-sky focus:ring-sky"
                        />
                        <div>
                            <div class="font-bold">{goal.title}</div>
                            <div class="text-xs text-gray-400">
                                {goal.status}
                            </div>
                        </div>
                    </label>
                {/each}
            </div>
        {/if}

        <div class="flex justify-between mt-6">
            <button
                class="text-gray-400 hover:text-white"
                on:click={() => (step = 2)}>Back</button
            >
            <button
                class="bg-sky text-navy-dark hover:bg-sky-hover px-6 py-2 rounded font-bold disabled:opacity-50 transition-colors shadow-lg shadow-sky/20"
                disabled={selectedType === "Heavy" &&
                    selectedGoals.length !== 2}
                on:click={submit}
            >
                Begin Day
            </button>
        </div>
    {/if}
</div>
