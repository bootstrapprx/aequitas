<script>
  import { invoke } from "@tauri-apps/api/core";
  import { onMount, tick } from "svelte";
  import Toast from "./Toast.svelte";

  const todayIso = new Date().toISOString().split("T")[0];

  let devMode = false;
  let loading = true;
  let saving = false;
  let autosaveStatus = "";
  let selectedDate = todayIso;
  let dailyList = [];

  let mode = "";
  let protocol = "";
  let divergencesText = "";
  let content = "";

  let activePhase = null;
  let inPhaseGoals = [];
  let outOfPhaseGoals = [];
  let goalRelations = {};
  let recentDecisions = [];
  let blockedGoals = [];
  let activeGoalCount = 0;
  let blockedGoalCount = 0;

  let selectedGoals = [];
  let selectedDecisions = [];
  let manualBlockers = [];
  let blockerInput = "";

  let toastShow = false;
  let toastMessage = "";
  let toastType = "success";

  let autosaveTimer;

  const modeOptions = [
    { value: "", label: "Unspecified" },
    { value: "light", label: "Light Day" },
    { value: "heavy", label: "Heavy Day" },
    { value: "review", label: "Review Day" },
  ];

  const protocolOptions = [
    { value: "", label: "None / Ad-hoc" },
    { value: "LIGHT_DAY_PROTOCOL", label: "Light Day (Maintenance)" },
    { value: "HEAVY_DAY_PROTOCOL", label: "Heavy Day (Deep Work)" },
    { value: "REVIEW_DAY_PROTOCOL", label: "Review Day (Reflection)" },
  ];

  const statusOrder = [
    "active",
    "planned",
    "blocked",
    "partial",
    "done",
    "archived",
    "unknown",
  ];

  onMount(async () => {
    if (typeof window !== "undefined" && !window.__TAURI__) {
      devMode = true;
      loading = false;
      return;
    }
    await loadDailyList();
  });

  async function loadDailyList() {
    try {
      loading = true;
      dailyList = await invoke("list_daily_notes");
      if (
        dailyList.length > 0 &&
        !dailyList.find((d) => d.date === selectedDate)
      ) {
        selectedDate = dailyList[0].date;
      }
      await loadContext(selectedDate);
    } catch (err) {
      showError(err);
    } finally {
      loading = false;
    }
  }

  async function loadContext(date) {
    if (devMode) return;
    try {
      loading = true;
      const ctx = await invoke("get_daily_context", { date });

      activePhase = ctx.active_phase;
      inPhaseGoals = ctx.in_phase_goals || [];
      outOfPhaseGoals = ctx.out_of_phase_goals || [];
      // Build relation map
      goalRelations = {};
      if (ctx.goal_relations) {
        for (const rel of ctx.goal_relations) {
          goalRelations[rel.goal.goal_id.toLowerCase()] = rel;
        }
      }

      recentDecisions = ctx.recent_decisions || [];
      blockedGoals = ctx.blocked_goals || [];
      activeGoalCount = ctx.active_goal_count || 0;
      blockedGoalCount = ctx.blocked_goal_count || 0;

      const note = ctx.note;
      mode = note?.mode || "";
      protocol = note?.protocol || "";
      selectedGoals = note?.goals || [];
      selectedDecisions = note?.decisions || [];
      manualBlockers = note?.blockers || [];
      divergencesText = (note?.divergences || []).join("\n");
      content = note?.content || "";
      autosaveStatus = "";

      syncDerivedSections();
    } catch (err) {
      showError(err);
    } finally {
      loading = false;
    }
  }

  function groupGoals(goals) {
    const grouped = {};
    for (const goal of goals) {
      const key = (goal.status || "unknown").toLowerCase();
      if (!grouped[key]) grouped[key] = [];
      grouped[key].push(goal);
    }
    return grouped;
  }

  function getRootGoals(goals) {
    const allIds = new Set(goals.map((g) => g.goal_id));
    return goals.filter((g) => !g.parent_id || !allIds.has(g.parent_id));
  }

  function getChildren(goals, parentId) {
    return goals.filter((g) => g.parent_id === parentId);
  }

  function getGoal(id) {
    const all = [...inPhaseGoals, ...outOfPhaseGoals];
    return all.find((g) => g.goal_id.toLowerCase() === id.toLowerCase());
  }

  // Reactive derivations
  $: selectedGoalObjects = selectedGoals
    .map((id) => getGoal(id))
    .filter(Boolean);

  $: selectedRelations = selectedGoals
    .map((id) => goalRelations[id.toLowerCase()])
    .filter(Boolean);

  $: derivedDecisions = dedupeDecisions([
    ...selectedRelations.flatMap((rel) => rel.decisions || []),
  ]);

  $: recentLinkedDecisions = derivedDecisions.filter((decision) => {
    const cutoff = new Date();
    cutoff.setDate(cutoff.getDate() - 30);
    const reference = decision.updated || decision.date;
    if (!reference) return true;
    return new Date(reference) >= cutoff;
  });

  $: derivedAudits = dedupeAudits([
    ...selectedRelations.flatMap((rel) => rel.audits || []),
  ]).filter((a) => {
    if (!a.date) return true;
    const auditDate = new Date(a.date);
    const today = new Date();
    return auditDate >= today;
  });

  $: structuralBlockers = selectedRelations.flatMap((rel) =>
    (rel.missing_dependencies || []).map((dep) => ({
      goal_id: rel.goal.goal_id,
      title: rel.goal.title,
      dependency: dep,
    })),
  );

  $: automaticGoalBlockers = blockedGoals.filter((goal) =>
    selectedGoals
      .map((g) => g.toLowerCase())
      .includes(goal.goal_id.toLowerCase()),
  );

  $: warnings = selectedGoalObjects
    .filter((goal) => goalRelations[goal.goal_id.toLowerCase()]?.out_of_phase)
    .map(
      (goal) =>
        `${goal.goal_id} is outside active phase ${activePhase?.phase_id || "n/a"}`,
    );

  function dedupeDecisions(list) {
    const map = new Map();
    for (const d of list || []) {
      map.set((d.decision_id || "").toLowerCase(), d);
    }
    return Array.from(map.values());
  }

  function dedupeAudits(list) {
    const map = new Map();
    for (const a of list || []) {
      map.set(a.file_path || a.title, a);
    }
    return Array.from(map.values());
  }

  function scheduleAutosave() {
    if (devMode) return;
    clearTimeout(autosaveTimer);
    autosaveStatus = "Saving…";
    autosaveTimer = setTimeout(() => saveDaily(false), 800);
  }

  function buildBlockersForSave() {
    const combined = [
      ...automaticGoalBlockers.map(
        (g) => `Goal blocker: ${g.goal_id} — ${g.title}`,
      ),
      ...structuralBlockers.map(
        (b) => `Structural: ${b.goal_id} missing ${b.dependency}`,
      ),
      ...manualBlockers,
    ];
    const seen = new Set();
    return combined.filter((item) => {
      const key = item.toLowerCase();
      if (seen.has(key)) return false;
      seen.add(key);
      return item.trim().length > 0;
    });
  }

  function rewriteDerivedBlock(text, marker, block) {
    const start = `<!-- ${marker}_START -->`;
    const end = `<!-- ${marker}_END -->`;
    const startIdx = text.indexOf(start);
    const endIdx = text.indexOf(end);

    if (!block) {
      if (startIdx !== -1 && endIdx !== -1 && endIdx > startIdx) {
        return `${text.slice(0, startIdx).trimEnd()}\n\n${text
          .slice(endIdx + end.length)
          .trimStart()}`.trim();
      }
      return text;
    }

    if (startIdx !== -1 && endIdx !== -1 && endIdx > startIdx) {
      return `${text.slice(0, startIdx)}${block}${text.slice(endIdx + end.length)}`;
    }
    const prefix = text.trim().length > 0 ? `${text.trim()}\n\n` : "";
    return `${prefix}${block}`;
  }

  function renderLinksBlock(marker, title, lines) {
    if (!lines || lines.length === 0) return "";
    return `<!-- ${marker}_START -->\n## ${title}\n${lines
      .map((line) => `- ${line}`)
      .join("\n")}\n<!-- ${marker}_END -->`;
  }

  function syncDerivedSections() {
    const goalLines = selectedGoals.map((id) => {
      const goal = getGoal(id);
      return goal ? `[[${goal.goal_id}]] — ${goal.title}` : `[[${id}]]`;
    });

    const decisionLookup = new Map();
    for (const dec of dedupeDecisions([
      ...selectedRelations.flatMap((rel) => rel.decisions || []),
      ...recentDecisions,
    ])) {
      decisionLookup.set(dec.decision_id.toLowerCase(), dec);
    }
    const decisionLines = selectedDecisions.map((id) => {
      const dec = decisionLookup.get(id.toLowerCase());
      return dec ? `[[${dec.decision_id}]] — ${dec.title}` : `[[${id}]]`;
    });

    const goalsBlock = renderLinksBlock(
      "DERIVED_GOALS",
      "Linked Goals",
      goalLines,
    );
    const decisionsBlock = renderLinksBlock(
      "DERIVED_DECISIONS",
      "Linked Decisions",
      decisionLines,
    );

    let nextContent = rewriteDerivedBlock(content, "DERIVED_GOALS", goalsBlock);
    nextContent = rewriteDerivedBlock(
      nextContent,
      "DERIVED_DECISIONS",
      decisionsBlock,
    );
    content = nextContent;
  }

  async function saveDaily(showToast = true) {
    if (devMode) return;

    // Validation
    if (mode === "heavy" && selectedGoals.length < 2) {
      if (
        !confirm(
          "Heavy Days typically require at least 2 objectives. Save anyway?",
        )
      ) {
        saving = false;
        return;
      }
    }

    try {
      saving = true;
      await invoke("update_daily_note", {
        payload: {
          date: selectedDate,
          mode: mode || null,
          protocol: protocol || null,
          goals: selectedGoals,
          blockers: buildBlockersForSave(),
          decisions: selectedDecisions,
          divergences: divergencesText
            .split("\n")
            .map((line) => line.trim())
            .filter(Boolean),
          content,
        },
      });
      autosaveStatus = "Saved";
      if (showToast) {
        toastMessage = "Daily note saved";
        toastType = "success";
        toastShow = true;
      }
      await loadDailyList();
    } catch (err) {
      autosaveStatus = "Error";
      showError(err);
    } finally {
      saving = false;
    }
  }

  function toggleGoal(goalId) {
    if (selectedGoals.includes(goalId)) {
      selectedGoals = selectedGoals.filter((id) => id !== goalId);
    } else {
      selectedGoals = [...selectedGoals, goalId];
    }
    syncDerivedSections();
    scheduleAutosave();
  }

  function toggleDecision(decisionId) {
    if (selectedDecisions.includes(decisionId)) {
      selectedDecisions = selectedDecisions.filter((id) => id !== decisionId);
    } else {
      selectedDecisions = [...selectedDecisions, decisionId];
    }
    syncDerivedSections();
    scheduleAutosave();
  }

  function addDecisionStub() {
    const stubId = `DECISION — ${selectedDate} — NEW`;
    if (!selectedDecisions.includes(stubId)) {
      selectedDecisions = [...selectedDecisions, stubId];
      syncDerivedSections();
      scheduleAutosave();
      toastMessage = "Decision stub added to daily note";
      toastType = "success";
      toastShow = true;
    }
  }

  function addManualBlocker() {
    if (!blockerInput.trim()) return;
    manualBlockers = [...manualBlockers, blockerInput.trim()];
    blockerInput = "";
    scheduleAutosave();
  }

  function removeManualBlocker(item) {
    manualBlockers = manualBlockers.filter((b) => b !== item);
    scheduleAutosave();
  }

  function showError(err) {
    toastMessage = err?.toString?.() ?? String(err);
    toastType = "error";
    toastShow = true;
  }

  function onDateChange(newDate) {
    selectedDate = newDate;
    loadContext(selectedDate);
  }

  function createIfMissing() {
    saveDaily(true);
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
    return classes[status?.toLowerCase()] || "badge";
  }

  function formatDate(value) {
    if (!value) return "n/a";
    return new Date(value).toLocaleDateString();
  }
</script>

<div>
  <div class="flex items-center justify-between mb-6">
    <div>
      <h2 class="text-3xl font-bold text-gray-900 dark:text-white">
        Daily Editor
      </h2>
      <p class="text-sm text-gray-500 dark:text-gray-400">
        Relational editing of daily notes in governance/01_DAILY
      </p>
    </div>
    <div class="flex items-center gap-3">
      <div class="text-xs text-gray-500 dark:text-gray-400">
        {autosaveStatus}
      </div>
      <button
        class="btn btn-primary"
        on:click={() => saveDaily(true)}
        disabled={devMode || saving}
      >
        {saving ? "Saving…" : "Save now"}
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
        Run <code>cargo tauri dev</code> to hydrate the Daily Editor from the Governance
        Vault.
      </p>
    </div>
  {/if}

  {#if loading}
    <div class="card">
      <p class="text-gray-500 dark:text-gray-400">
        Loading governance context…
      </p>
    </div>
  {:else}
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div class="lg:col-span-2 space-y-4">
        <div class="card">
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div class="flex flex-col gap-2">
              <label
                for="daily-date"
                class="text-sm text-gray-500 dark:text-gray-400">Date</label
              >
              <input
                id="daily-date"
                type="date"
                bind:value={selectedDate}
                class="px-3 py-2 rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                on:change={(e) => onDateChange(e.target.value)}
              />
            </div>
            <div class="flex flex-col gap-2">
              <label
                for="daily-mode"
                class="text-sm text-gray-500 dark:text-gray-400">Mode</label
              >
              <select
                id="daily-mode"
                class="px-3 py-2 rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                bind:value={mode}
                on:change={scheduleAutosave}
              >
                {#each modeOptions as option}
                  <option value={option.value}>{option.label}</option>
                {/each}
              </select>
            </div>
            <div class="flex flex-col gap-2">
              <label
                for="daily-protocol"
                class="text-sm text-gray-500 dark:text-gray-400"
                >Protocol (optional)</label
              >
              <select
                id="daily-protocol"
                bind:value={protocol}
                class="px-3 py-2 rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                on:change={scheduleAutosave}
              >
                {#each protocolOptions as opt}
                  <option value={opt.value}>{opt.label}</option>
                {/each}
              </select>
            </div>
          </div>
          {#if warnings.length > 0}
            <div class="mt-3 text-xs text-yellow-700 dark:text-yellow-200">
              {#each warnings as w}
                <div>⚠ {w}</div>
              {/each}
            </div>
          {/if}
        </div>

        <div class="card">
          <div class="flex items-center justify-between mb-2">
            <div>
              <h3 class="text-xl font-semibold text-gray-900 dark:text-white">
                Goals
              </h3>
              <p class="text-sm text-gray-500 dark:text-gray-400">
                Select goals for {activePhase
                  ? `Phase ${activePhase.phase_id}`
                  : "current day"}
              </p>
            </div>
            <div class="text-xs text-gray-500 dark:text-gray-400">
              {selectedGoals.length} selected
            </div>
          </div>
          {#if inPhaseGoals.length === 0}
            <p class="text-sm text-gray-500 dark:text-gray-400">
              No goals detected for the active phase.
            </p>
          {:else}
            {#each statusOrder as status}
              {#if groupGoals(inPhaseGoals)[status]?.length}
                {@const statusGoals = groupGoals(inPhaseGoals)[status]}
                {@const rootGoals = getRootGoals(statusGoals)}
                {#if rootGoals.length > 0}
                  <div class="mt-3">
                    <div
                      class="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400 mb-2"
                    >
                      {status}
                    </div>
                    <div class="flex flex-col gap-2">
                      {#each rootGoals as goal}
                        <!-- Root Goal -->
                        <div
                          class="rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden"
                        >
                          <button
                            class="w-full flex items-center justify-between p-3 text-left transition-colors {selectedGoals.includes(
                              goal.goal_id,
                            )
                              ? 'bg-primary-50 dark:bg-primary-900/20'
                              : 'hover:bg-gray-50 dark:hover:bg-gray-800'}"
                            on:click={() => toggleGoal(goal.goal_id)}
                          >
                            <div>
                              <div class="flex items-center gap-2">
                                <span
                                  class="font-mono text-sm font-semibold text-primary-700 dark:text-primary-300"
                                  >{goal.goal_id}</span
                                >
                                <span
                                  class="badge {getStatusBadge(goal.status)}"
                                  >{goal.status}</span
                                >
                              </div>
                              <div
                                class="text-gray-900 dark:text-white font-semibold"
                              >
                                {goal.title}
                              </div>
                            </div>
                            {#if selectedGoals.includes(goal.goal_id)}
                              <span
                                class="text-primary-600 dark:text-primary-300"
                                >✓</span
                              >
                            {/if}
                          </button>

                          <!-- Children -->
                          {#each getChildren(inPhaseGoals, goal.goal_id) as child}
                            <div
                              class="border-t border-gray-100 dark:border-gray-700 bg-gray-50/50 dark:bg-gray-800/50 pl-8 pr-3 py-2"
                            >
                              <button
                                class="w-full flex items-center gap-3 text-left"
                                on:click={() => toggleGoal(child.goal_id)}
                              >
                                <div
                                  class="w-4 h-4 rounded border flex items-center justify-center transition-colors {selectedGoals.includes(
                                    child.goal_id,
                                  )
                                    ? 'bg-primary-600 border-primary-600'
                                    : 'border-gray-400 dark:border-gray-500 bg-white dark:bg-gray-700'}"
                                >
                                  {#if selectedGoals.includes(child.goal_id)}
                                    <svg
                                      class="w-3 h-3 text-white"
                                      fill="none"
                                      viewBox="0 0 24 24"
                                      stroke="currentColor"
                                      ><path
                                        stroke-linecap="round"
                                        stroke-linejoin="round"
                                        stroke-width="3"
                                        d="M5 13l4 4L19 7"
                                      /></svg
                                    >
                                  {/if}
                                </div>
                                <div>
                                  <div
                                    class="text-sm text-gray-900 dark:text-white"
                                  >
                                    {child.title}
                                  </div>
                                  <div class="text-xs text-gray-500 font-mono">
                                    {child.goal_id} · {child.status}
                                  </div>
                                </div>
                              </button>
                            </div>
                          {/each}
                        </div>
                      {/each}
                    </div>
                  </div>
                {/if}
              {/if}
            {/each}
          {/if}

          {#if outOfPhaseGoals.length > 0}
            <div
              class="mt-4 border-t border-dashed border-gray-200 dark:border-gray-700 pt-3"
            >
              <div
                class="flex items-center gap-2 text-sm text-yellow-700 dark:text-yellow-200 mb-2"
              >
                <span class="text-lg">⚠</span>
                <span>Out-of-phase goals (allowed, but monitored)</span>
              </div>
              <div class="grid md:grid-cols-2 gap-2">
                {#each outOfPhaseGoals as goal}
                  <button
                    class="p-3 rounded-lg border text-left {selectedGoals.includes(
                      goal.goal_id,
                    )
                      ? 'border-yellow-500 bg-yellow-50 dark:bg-yellow-900/20'
                      : 'border-gray-200 dark:border-gray-700 hover:border-yellow-400'}"
                    on:click={() => toggleGoal(goal.goal_id)}
                  >
                    <div class="flex items-center gap-2">
                      <span
                        class="font-mono text-sm font-semibold text-yellow-800 dark:text-yellow-200"
                        >{goal.goal_id}</span
                      >
                      <span class="badge {getStatusBadge(goal.status)}"
                        >{goal.status}</span
                      >
                    </div>
                    <div class="text-gray-900 dark:text-white font-semibold">
                      {goal.title}
                    </div>
                    {#if goal.phase}
                      <div class="text-xs text-gray-500 dark:text-gray-400">
                        Phase {goal.phase}
                      </div>
                    {/if}
                  </button>
                {/each}
              </div>
            </div>
          {/if}
        </div>

        <div class="card">
          <div class="flex items-center justify-between mb-2">
            <div>
              <h3 class="text-xl font-semibold text-gray-900 dark:text-white">
                Decisions
              </h3>
              <p class="text-sm text-gray-500 dark:text-gray-400">
                Link existing decisions or add a stub
              </p>
            </div>
            <button
              class="btn btn-secondary"
              on:click={addDecisionStub}
              disabled={devMode}
            >
              + Decision stub
            </button>
          </div>
          <div class="grid md:grid-cols-2 gap-3">
            <div>
              <div
                class="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400 mb-1"
              >
                Linked to selected goals
              </div>
              {#if derivedDecisions.length === 0}
                <p class="text-sm text-gray-500 dark:text-gray-400">
                  No linked decisions detected.
                </p>
              {:else}
                <div class="space-y-2">
                  {#each derivedDecisions as decision}
                    <button
                      class="w-full p-3 rounded-lg border text-left {selectedDecisions.includes(
                        decision.decision_id,
                      )
                        ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                        : 'border-gray-200 dark:border-gray-700 hover:border-primary-400'}"
                      on:click={() => toggleDecision(decision.decision_id)}
                    >
                      <div class="flex items-center justify-between">
                        <div>
                          <div
                            class="font-semibold text-gray-900 dark:text-white"
                          >
                            {decision.title}
                          </div>
                          <div class="text-xs text-gray-500 dark:text-gray-400">
                            {decision.decision_id}
                          </div>
                        </div>
                        {#if decision.status}
                          <span class="badge badge-secondary text-xs"
                            >{decision.status}</span
                          >
                        {/if}
                      </div>
                    </button>
                  {/each}
                </div>
              {/if}
            </div>
            <div>
              <div
                class="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400 mb-1"
              >
                Recent (30 days)
              </div>
              {#if recentDecisions.length === 0}
                <p class="text-sm text-gray-500 dark:text-gray-400">
                  No recent decisions detected.
                </p>
              {:else}
                <div class="space-y-2">
                  {#each recentDecisions as decision}
                    <button
                      class="w-full p-3 rounded-lg border text-left {selectedDecisions.includes(
                        decision.decision_id,
                      )
                        ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                        : 'border-gray-200 dark:border-gray-700 hover:border-primary-400'}"
                      on:click={() => toggleDecision(decision.decision_id)}
                    >
                      <div class="flex items-center justify-between">
                        <div>
                          <div
                            class="font-semibold text-gray-900 dark:text-white"
                          >
                            {decision.title}
                          </div>
                          <div class="text-xs text-gray-500 dark:text-gray-400">
                            {decision.decision_id}
                          </div>
                        </div>
                        <div class="text-xs text-gray-500 dark:text-gray-400">
                          {formatDate(decision.updated || decision.date)}
                        </div>
                      </div>
                    </button>
                  {/each}
                </div>
              {/if}
            </div>
          </div>
          {#if selectedDecisions.length > 0}
            <div class="mt-3 text-xs text-gray-500 dark:text-gray-400">
              Writing linked decisions into the daily note via wiki links.
            </div>
          {/if}
        </div>

        <div class="card">
          <div class="flex items-center justify-between mb-2">
            <div>
              <h3 class="text-xl font-semibold text-gray-900 dark:text-white">
                Blockers
              </h3>
              <p class="text-sm text-gray-500 dark:text-gray-400">
                Automatic detection plus manual notes
              </p>
            </div>
          </div>
          <div class="grid md:grid-cols-3 gap-3">
            <div>
              <div
                class="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400 mb-1"
              >
                Goal blockers
              </div>
              {#if automaticGoalBlockers.length === 0}
                <p class="text-sm text-gray-500 dark:text-gray-400">
                  None detected.
                </p>
              {:else}
                <ul class="space-y-1 text-sm text-red-700 dark:text-red-300">
                  {#each automaticGoalBlockers as goal}
                    <li>• {goal.goal_id} — {goal.title}</li>
                  {/each}
                </ul>
              {/if}
            </div>
            <div>
              <div
                class="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400 mb-1"
              >
                Structural blockers
              </div>
              {#if structuralBlockers.length === 0}
                <p class="text-sm text-gray-500 dark:text-gray-400">
                  No missing dependencies detected.
                </p>
              {:else}
                <ul
                  class="space-y-1 text-sm text-yellow-800 dark:text-yellow-200"
                >
                  {#each structuralBlockers as blocker}
                    <li>• {blocker.goal_id}: missing {blocker.dependency}</li>
                  {/each}
                </ul>
              {/if}
            </div>
            <div>
              <div
                class="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400 mb-1"
              >
                External blockers
              </div>
              <div class="flex gap-2 mb-2">
                <input
                  type="text"
                  bind:value={blockerInput}
                  class="flex-1 px-3 py-2 rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm"
                  placeholder="Add a blocker"
                />
                <button class="btn btn-secondary" on:click={addManualBlocker}
                  >Add</button
                >
              </div>
              {#if manualBlockers.length === 0}
                <p class="text-sm text-gray-500 dark:text-gray-400">
                  No external blockers noted.
                </p>
              {:else}
                <ul class="space-y-1 text-sm text-gray-900 dark:text-white">
                  {#each manualBlockers as blocker}
                    <li class="flex items-center justify-between">
                      <span>• {blocker}</span>
                      <button
                        class="text-xs text-red-600 dark:text-red-300"
                        on:click={() => removeManualBlocker(blocker)}
                        >Remove</button
                      >
                    </li>
                  {/each}
                </ul>
              {/if}
            </div>
          </div>
        </div>

        <div class="card">
          <div class="flex items-center justify-between mb-2">
            <h3 class="text-xl font-semibold text-gray-900 dark:text-white">
              Divergences
            </h3>
            <span class="text-xs text-gray-500 dark:text-gray-400"
              >Optional</span
            >
          </div>
          <textarea
            rows="4"
            bind:value={divergencesText}
            class="w-full px-3 py-2 rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm"
            on:input={scheduleAutosave}
            placeholder="One divergence per line"
          ></textarea>
        </div>

        <div class="card">
          <div class="flex items-center justify-between mb-2">
            <h3 class="text-xl font-semibold text-gray-900 dark:text-white">
              Daily body (markdown)
            </h3>
            <span class="text-xs text-gray-500 dark:text-gray-400"
              >Derived links auto-inserted</span
            >
          </div>
          <textarea
            rows="12"
            bind:value={content}
            class="w-full px-3 py-2 rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm font-mono"
            on:input={scheduleAutosave}
          ></textarea>
          <div class="flex justify-end gap-3 mt-4">
            <button
              class="btn btn-secondary"
              on:click={createIfMissing}
              disabled={devMode || saving}
            >
              Create if missing
            </button>
            <button
              class="btn btn-primary"
              on:click={() => saveDaily(true)}
              disabled={devMode || saving}
            >
              {saving ? "Saving…" : "Save"}
            </button>
          </div>
        </div>
      </div>

      <div class="space-y-4">
        <div class="card">
          <div class="flex items-center justify-between mb-2">
            <h3 class="text-xl font-semibold text-gray-900 dark:text-white">
              Derived Context
            </h3>
            <span
              class="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400"
              >read-only</span
            >
          </div>
          <dl class="space-y-2 text-sm text-gray-900 dark:text-white">
            <div class="flex justify-between">
              <dt>Active phase</dt>
              <dd>
                {activePhase
                  ? `${activePhase.phase_id} — ${activePhase.title}`
                  : "Unknown"}
              </dd>
            </div>
            <div class="flex justify-between">
              <dt>Active goals</dt>
              <dd>{activeGoalCount}</dd>
            </div>
            <div class="flex justify-between">
              <dt>Blocked goals</dt>
              <dd>{blockedGoalCount}</dd>
            </div>
          </dl>
          {#if derivedAudits.length > 0}
            <div class="mt-3">
              <div
                class="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400 mb-1"
              >
                Audits touching selected goals
              </div>
              <ul class="space-y-1 text-sm text-gray-900 dark:text-white">
                {#each derivedAudits as audit}
                  <li>
                    • {audit.title}
                    {#if audit.date}<span class="text-gray-500"
                        >({formatDate(audit.date)})</span
                      >{/if}
                  </li>
                {/each}
              </ul>
            </div>
          {/if}
          {#if recentLinkedDecisions.length > 0}
            <div class="mt-3">
              <div
                class="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400 mb-1"
              >
                Decisions affecting today’s goals
              </div>
              <ul class="space-y-1 text-sm text-gray-900 dark:text-white">
                {#each recentLinkedDecisions as decision}
                  <li>• {decision.decision_id} — {decision.title}</li>
                {/each}
              </ul>
            </div>
          {/if}
        </div>

        <div class="card">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">
            Recent daily notes
          </h3>
          {#if dailyList.length === 0}
            <p class="text-sm text-gray-500 dark:text-gray-400">
              No daily notes found.
            </p>
          {:else}
            <div class="space-y-1 text-sm text-gray-900 dark:text-white">
              {#each dailyList.slice(0, 7) as note}
                <div class="flex justify-between items-center">
                  <span>{note.date}</span>
                  <span class="text-gray-500">{note.mode || "–"}</span>
                </div>
              {/each}
            </div>
          {/if}
        </div>
      </div>
    </div>
  {/if}
</div>

<Toast bind:show={toastShow} message={toastMessage} type={toastType} />
