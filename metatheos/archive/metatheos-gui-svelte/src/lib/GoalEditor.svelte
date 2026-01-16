<script lang="ts">
  import { invoke } from "@tauri-apps/api/core";
  import { createEventDispatcher, onMount } from "svelte";
  import AnnotationPanel from "./AnnotationPanel.svelte";

  // Props
  export let goal: any = null; // If null, we're creating a new goal
  export let onClose: () => void;

  const dispatch = createEventDispatcher();

  // Form state
  let goalId = goal?.goal_id || "";
  let title = goal?.title || "";
  let status = goal?.status || "planned";
  let phase = goal?.phase || "";
  let owner = goal?.owner || "";
  let parentId = goal?.parent_id || "";
  let level = goal?.level || "goal";
  let dependencies = goal?.dependencies?.join(", ") || "";
  let canonList = goal?.canon || [];
  let tags = goal?.tags?.join(", ") || "";
  let content = goal?.content || "";

  // Work Items (Phase 4)
  let workItems: any[] = [];
  let subgoals: any[] = [];
  let orphanedTasks: any[] = [];
  let newItemTitle = "";
  let addingToSubgoal: string | null = null; // ID of subgoal being added to

  function addCanonRef() {
    canonList = [...canonList, ""];
  }

  function removeCanonRef(index: number) {
    canonList = canonList.filter((_, i) => i !== index);
  }

  // UI state
  let showPreview = false;
  let saving = false;
  let error = "";
  let validationErrors: Record<string, string> = {};

  // Available statuses
  const statuses = [
    { value: "planned", label: "Planned", color: "text-cyan-400" },
    { value: "active", label: "Active", color: "text-green-400" },
    { value: "blocked", label: "Blocked", color: "text-red-400" },
    { value: "partial", label: "Partial", color: "text-yellow-400" },
    { value: "done", label: "Done", color: "text-blue-400" },
    { value: "archived", label: "Archived", color: "text-gray-400" },
  ];

  const isEditMode = !!goal;
  const initialStatus = goal?.status || "planned";

  // Validation
  function validate(): boolean {
    validationErrors = {};

    if (!goalId.trim()) {
      validationErrors.goalId = "Goal ID is required";
    } else if (!/^[A-Za-z0-9-_]+$/.test(goalId)) {
      validationErrors.goalId =
        "Goal ID can only contain letters, numbers, hyphens, and underscores";
    }

    if (!title.trim()) {
      validationErrors.title = "Title is required";
    }

    if (!content.trim()) {
      validationErrors.content = "Content is required";
    }

    return Object.keys(validationErrors).length === 0;
  }

  // Parse comma-separated lists
  function parseList(str: string): string[] {
    return str
      .split(",")
      .map((s) => s.trim())
      .filter((s) => s.length > 0);
  }

  // Phase 4: Work Items Logic
  onMount(() => {
    if (isEditMode) {
      loadWorkItems();
    }
  });

  async function loadWorkItems() {
    try {
      const items: any[] = await invoke("get_work_items", { goalId });
      workItems = items || [];
      organizeItems();
    } catch (e) {
      console.error("Failed to load work items", e);
    }
  }

  function organizeItems() {
    subgoals = workItems.filter((i) => i.kind === "Subgoal");
    orphanedTasks = workItems.filter((i) => i.kind === "Task" && !i.parent_id);
    subgoals.forEach((sg) => {
      sg.tasks = workItems.filter(
        (i) => i.kind === "Task" && i.parent_id === sg.id,
      );
    });
    subgoals = subgoals;
    orphanedTasks = orphanedTasks;
  }

  async function addWorkItem(kind: string, parentId: string | null = null) {
    if (!newItemTitle.trim()) return;
    try {
      const item = await invoke("add_work_item", {
        goalId,
        phaseId: phase,
        parentId,
        kind,
        title: newItemTitle,
      });
      workItems = [...workItems, item];
      organizeItems();
      newItemTitle = "";
      addingToSubgoal = null;
    } catch (e) {
      error = String(e);
    }
  }

  async function toggleItem(id: string) {
    try {
      const updated: any = await invoke("toggle_work_item", { itemId: id });
      workItems = workItems.map((i) => (i.id === id ? updated : i));
      organizeItems();
      // Optional: Reload logic if we want propagating effects
      loadWorkItems();
    } catch (e) {
      error = String(e);
    }
  }

  // Save goal
  async function handleSave() {
    if (!validate()) {
      return;
    }

    saving = true;
    error = "";

    try {
      if (isEditMode && status !== initialStatus) {
        const ok = confirm(
          `Change status from "${initialStatus}" to "${status}"?`,
        );
        if (!ok) {
          saving = false;
          return;
        }
      }

      if (isEditMode) {
        // Update existing goal
        await invoke("update_goal", {
          goalId: goalId,
          request: {
            title: title.trim(),
            status,
            phase: phase.trim() || null,
            owner: owner.trim() || null,
            parent_id: parentId.trim() || null,
            level: level || "goal",
            dependencies: parseList(dependencies),
            canon: canonList.filter((s) => s.trim().length > 0),
            tags: tags.trim(),
            content: content.trim(),
          },
        });
      } else {
        // Create new goal
        await invoke("create_goal", {
          request: {
            goal_id: goalId.trim(),
            title: title.trim(),
            status,
            phase: phase.trim() || null,
            owner: owner.trim() || null,
            parent_id: parentId.trim() || null,
            level: level || "goal",
            dependencies: parseList(dependencies),
            canon: canonList.filter((s) => s.trim().length > 0),
            tags: parseList(tags),
            content: content.trim(),
          },
        });
      }

      dispatch("saved", { goalId });
      onClose();
    } catch (err: any) {
      error = err.toString();
    } finally {
      saving = false;
    }
  }

  // Delete goal
  async function handleDelete() {
    if (!confirm(`Are you sure you want to delete goal "${goalId}"?`)) {
      return;
    }

    saving = true;
    error = "";

    try {
      await invoke("delete_goal", { goalId });
      dispatch("deleted", { goalId });
      onClose();
    } catch (err: any) {
      error = err.toString();
    } finally {
      saving = false;
    }
  }

  // Render markdown preview (simple version)
  function renderMarkdown(text: string): string {
    // Basic markdown rendering - replace with proper library if needed
    return text
      .split("\n")
      .map((line) => {
        if (line.startsWith("# "))
          return `<h1 class="text-2xl font-bold mt-4 mb-2">${line.slice(2)}</h1>`;
        if (line.startsWith("## "))
          return `<h2 class="text-xl font-bold mt-3 mb-2">${line.slice(3)}</h2>`;
        if (line.startsWith("### "))
          return `<h3 class="text-lg font-bold mt-2 mb-1">${line.slice(4)}</h3>`;
        if (line.startsWith("- "))
          return `<li class="ml-4">${line.slice(2)}</li>`;
        if (line.trim() === "") return "<br/>";
        return `<p class="mb-2">${line}</p>`;
      })
      .join("\n");
  }
</script>

<div
  class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
  on:click={(e) => e.target === e.currentTarget && onClose()}
  on:keydown={(e) => e.key === "Escape" && onClose()}
  role="button"
  tabindex="0"
>
  <div
    class="bg-gray-800 rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col"
  >
    <!-- Header -->
    <div
      class="bg-gray-900 px-6 py-4 border-b border-gray-700 flex items-center justify-between"
    >
      <h2 class="text-xl font-bold text-white">
        {isEditMode ? "Edit Goal" : "New Goal"}
      </h2>
      <button
        on:click={onClose}
        class="text-gray-400 hover:text-white transition-colors"
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

    <!-- Error message -->
    {#if error}
      <div
        class="bg-red-900 bg-opacity-50 text-red-200 px-6 py-3 border-b border-red-700"
      >
        <strong>Error:</strong>
        {error}
      </div>
    {/if}

    <!-- Form content -->
    <div class="flex-1 overflow-y-auto px-6 py-4">
      <div class="space-y-4">
        <!-- Goal ID -->
        <div>
          <label
            for="goal-id"
            class="block text-sm font-medium text-gray-300 mb-1"
          >
            Goal ID <span class="text-red-400">*</span>
          </label>
          <input
            id="goal-id"
            type="text"
            bind:value={goalId}
            disabled={isEditMode}
            class="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
            placeholder="e.g., G-101 or goal-authentication"
          />
          {#if validationErrors.goalId}
            <p class="text-red-400 text-sm mt-1">{validationErrors.goalId}</p>
          {/if}
          {#if !isEditMode}
            <p class="text-gray-400 text-sm mt-1">
              Unique identifier for this goal (cannot be changed after creation)
            </p>
          {/if}
        </div>

        <!-- Title -->
        <div>
          <label
            for="goal-title"
            class="block text-sm font-medium text-gray-300 mb-1"
          >
            Title <span class="text-red-400">*</span>
          </label>
          <input
            id="goal-title"
            type="text"
            bind:value={title}
            class="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Brief descriptive title"
          />
          {#if validationErrors.title}
            <p class="text-red-400 text-sm mt-1">{validationErrors.title}</p>
          {/if}
        </div>

        <!-- Status and Phase (side by side) -->
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label
              for="goal-status"
              class="block text-sm font-medium text-gray-300 mb-1"
            >
              Status <span class="text-red-400">*</span>
            </label>
            <select
              id="goal-status"
              bind:value={status}
              class="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {#each statuses as s}
                <option value={s.value}>{s.label}</option>
              {/each}
            </select>
          </div>

          <div>
            <label
              for="goal-phase"
              class="block text-sm font-medium text-gray-300 mb-1"
            >
              Phase
            </label>
            <input
              id="goal-phase"
              type="text"
              bind:value={phase}
              class="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="e.g., phase_1"
            />
          </div>
        </div>

        <!-- Level and Owner (side by side) -->
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label
              for="goal-level"
              class="block text-sm font-medium text-gray-300 mb-1"
            >
              Level
            </label>
            <select
              id="goal-level"
              bind:value={level}
              class="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="objective">Objective</option>
              <option value="goal">Goal</option>
              <option value="task">Task</option>
            </select>
          </div>

          <div>
            <label
              for="goal-owner"
              class="block text-sm font-medium text-gray-300 mb-1"
            >
              Owner
            </label>
            <input
              id="goal-owner"
              type="text"
              bind:value={owner}
              class="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Team or person responsible"
            />
          </div>
        </div>

        <!-- Parent Goal and Dependencies -->
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label
              for="goal-parent"
              class="block text-sm font-medium text-gray-300 mb-1"
            >
              Parent Goal
            </label>
            <input
              id="goal-parent"
              type="text"
              bind:value={parentId}
              class="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Parent ID (e.g. G-000)"
            />
          </div>

          <div>
            <label
              for="goal-dependencies"
              class="block text-sm font-medium text-gray-300 mb-1"
            >
              Dependencies
            </label>
            <input
              id="goal-dependencies"
              type="text"
              bind:value={dependencies}
              class="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Comma-separated IDs"
            />
          </div>
        </div>

        <!-- Canon References (List Builder) -->
        <div>
          <div class="block text-sm font-medium text-gray-300 mb-2">
            Canon References
          </div>

          <div class="space-y-2 mb-2">
            {#each canonList as ref, i}
              <div class="flex gap-2">
                <input
                  type="text"
                  bind:value={canonList[i]}
                  class="flex-1 px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Reference (e.g. CANON-I)"
                />
                <button
                  type="button"
                  on:click={() => removeCanonRef(i)}
                  class="px-3 py-2 bg-red-900/50 hover:bg-red-900 text-red-200 rounded transition-colors"
                  aria-label="Remove reference"
                >
                  ✕
                </button>
              </div>
            {/each}
          </div>

          <button
            type="button"
            on:click={addCanonRef}
            class="text-sm text-blue-400 hover:text-blue-300 flex items-center gap-1"
          >
            <span>+ Add Reference</span>
          </button>
        </div>

        <!-- Tags -->
        <div>
          <label
            for="goal-tags"
            class="block text-sm font-medium text-gray-300 mb-1"
          >
            Tags
          </label>
          <input
            id="goal-tags"
            type="text"
            bind:value={tags}
            class="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Comma-separated tags (e.g., backend, security, phase-1)"
          />
        </div>

        <!-- Execution Tree (Phase 4) -->
        {#if isEditMode}
          <div
            class="border-t border-gray-700 pt-4 mt-6 bg-gray-800/30 p-4 rounded-lg border border-gray-700/50"
          >
            <h3
              class="text-sm font-bold text-gray-400 uppercase tracking-widest mb-4 flex items-center gap-2"
            >
              <span>⚡</span> <span>Action Plan</span>
            </h3>

            <div class="space-y-4">
              <!-- Root Tasks / Subgoals List -->
              {#each subgoals as sg}
                <div
                  class="bg-gray-800 rounded p-3 border border-gray-700 shadow-sm"
                >
                  <div class="flex items-center gap-3 mb-2">
                    <input
                      type="checkbox"
                      checked={sg.status === "Done"}
                      on:change={() => toggleItem(sg.id)}
                      class="w-5 h-5 rounded bg-gray-700 border-gray-600 text-blue-600 focus:ring-blue-500 cursor-pointer"
                    />
                    <span
                      class="font-bold text-gray-100 flex-1 {sg.status ===
                      'Done'
                        ? 'line-through text-gray-500'
                        : ''}">{sg.title}</span
                    >
                    <span
                      class="text-[10px] uppercase font-bold text-purple-400 bg-purple-900/30 px-2 py-0.5 rounded"
                      >Subgoal</span
                    >
                  </div>

                  <!-- Subgoal Tasks -->
                  <div
                    class="ml-2 pl-4 border-l-2 border-gray-700 space-y-2 mt-2"
                  >
                    {#if sg.tasks}
                      {#each sg.tasks as task}
                        <div class="flex items-center gap-3 py-1 group">
                          <input
                            type="checkbox"
                            checked={task.status === "Done"}
                            on:change={() => toggleItem(task.id)}
                            class="w-4 h-4 rounded bg-gray-700 border-gray-600 text-blue-600 focus:ring-blue-500 cursor-pointer"
                          />
                          <span
                            class="text-sm text-gray-300 flex-1 {task.status ===
                            'Done'
                              ? 'line-through text-gray-500'
                              : ''} group-hover:text-white transition-colors"
                            >{task.title}</span
                          >
                        </div>
                      {/each}
                    {/if}

                    <!-- Add Task Input -->
                    {#if addingToSubgoal === sg.id}
                      <div class="flex gap-2 items-center mt-2 animate-fade-in">
                        <input
                          type="text"
                          bind:value={newItemTitle}
                          placeholder="Task title..."
                          class="flex-1 px-3 py-1 bg-gray-900 border border-purple-500/50 rounded text-sm text-white focus:outline-none focus:border-purple-500 transition-colors"
                          on:keydown={(e) =>
                            e.key === "Enter" && addWorkItem("Task", sg.id)}
                        />
                        <button
                          type="button"
                          on:click={() => addWorkItem("Task", sg.id)}
                          class="px-3 py-1 bg-purple-600 hover:bg-purple-500 text-white rounded text-xs font-bold transition-colors"
                          >Add</button
                        >
                        <button
                          type="button"
                          on:click={() => {
                            addingToSubgoal = null;
                            newItemTitle = "";
                          }}
                          class="text-gray-400 hover:text-gray-200 text-xs px-2 transition-colors"
                          >Cancel</button
                        >
                      </div>
                    {:else}
                      <button
                        type="button"
                        on:click={() => {
                          addingToSubgoal = sg.id;
                          newItemTitle = "";
                        }}
                        class="text-xs text-gray-500 hover:text-purple-400 flex items-center gap-1 mt-2 transition-colors py-1"
                      >
                        + Add Task
                      </button>
                    {/if}
                  </div>
                </div>
              {/each}

              <!-- Allocating Orphaned Tasks (Tasks without parent) -->
              {#each orphanedTasks as task}
                <div
                  class="bg-gray-800 rounded p-3 border border-gray-700 flex items-center gap-3"
                >
                  <input
                    type="checkbox"
                    checked={task.status === "Done"}
                    on:change={() => toggleItem(task.id)}
                    class="w-4 h-4 rounded bg-gray-700 border-gray-600 text-blue-600 focus:ring-blue-500 cursor-pointer"
                  />
                  <span
                    class="text-gray-200 flex-1 {task.status === 'Done'
                      ? 'line-through text-gray-500'
                      : ''}">{task.title}</span
                  >
                  <span
                    class="text-[10px] uppercase font-bold text-gray-500 bg-gray-900/50 px-2 py-0.5 rounded"
                    >Task</span
                  >
                </div>
              {/each}

              <!-- Add Subgoal / Root Task -->
              {#if !addingToSubgoal}
                <div class="flex gap-2 pt-4 border-t border-gray-700/50 mt-4">
                  <div class="flex-1 relative">
                    <input
                      type="text"
                      bind:value={newItemTitle}
                      placeholder="Create new item..."
                      class="w-full px-4 py-2 bg-gray-900 border border-gray-700 rounded text-white focus:outline-none focus:border-blue-500 transition-colors"
                    />
                  </div>
                  <div class="flex gap-1">
                    <button
                      type="button"
                      on:click={() => addWorkItem("Subgoal")}
                      class="px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white rounded text-sm font-bold transition-colors shadow-lg shadow-purple-900/20"
                      >Subgoal</button
                    >
                    <button
                      type="button"
                      on:click={() => addWorkItem("Task")}
                      class="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded text-sm font-medium transition-colors border border-gray-600"
                      >Task</button
                    >
                  </div>
                </div>
              {/if}
            </div>
          </div>
        {/if}

        <div class="h-6"></div>

        <!-- Content with Preview Toggle -->
        <div>
          <div class="flex items-center justify-between mb-1">
            <label
              for="goal-content"
              class="block text-sm font-medium text-gray-300"
            >
              Content <span class="text-red-400">*</span>
            </label>
            <button
              type="button"
              on:click={() => (showPreview = !showPreview)}
              class="text-sm text-blue-400 hover:text-blue-300 transition-colors"
            >
              {showPreview ? "Edit" : "Preview"}
            </button>
          </div>

          {#if showPreview}
            <div
              class="w-full min-h-[200px] px-3 py-2 bg-gray-900 border border-gray-600 rounded text-white overflow-auto prose prose-invert max-w-none"
            >
              {@html renderMarkdown(content)}
            </div>
          {:else}
            <textarea
              id="goal-content"
              bind:value={content}
              rows="12"
              class="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
              placeholder="Markdown content describing the goal, implementation plan, acceptance criteria, etc."
            ></textarea>
          {/if}

          {#if validationErrors.content}
            <p class="text-red-400 text-sm mt-1">{validationErrors.content}</p>
          {/if}
          <p class="text-gray-400 text-sm mt-1">Supports markdown formatting</p>
        </div>

        <!-- Annotations (Phase 5) -->
        {#if isEditMode}
          <div class="border-t border-gray-700 pt-6 mt-6">
            <AnnotationPanel
              scopeType="goal"
              scopeId={goalId}
              heading="Goal Notes"
              collapsedInitially={false}
            />
          </div>
        {/if}
      </div>
    </div>

    <!-- Footer -->
    <div
      class="bg-gray-900 px-6 py-4 border-t border-gray-700 flex items-center justify-between"
    >
      <div>
        {#if isEditMode}
          <div class="flex gap-2">
            <button
              type="button"
              on:click={handleDelete}
              disabled={saving}
              class="px-4 py-2 bg-red-600 hover:bg-red-700 disabled:bg-red-800 disabled:cursor-not-allowed text-white rounded transition-colors"
            >
              Delete
            </button>
            <button
              type="button"
              on:click={() => dispatch("create-subgoal", { parentId: goalId })}
              disabled={saving}
              class="px-4 py-2 bg-purple-600 hover:bg-purple-700 disabled:bg-purple-800 disabled:cursor-not-allowed text-white rounded transition-colors"
            >
              Add Sub-goal
            </button>
          </div>
        {/if}
      </div>

      <div class="flex gap-3">
        <button
          type="button"
          on:click={onClose}
          disabled={saving}
          class="px-4 py-2 bg-gray-700 hover:bg-gray-600 disabled:bg-gray-800 disabled:cursor-not-allowed text-white rounded transition-colors"
        >
          Cancel
        </button>
        <button
          type="button"
          on:click={handleSave}
          disabled={saving}
          class="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-800 disabled:cursor-not-allowed text-white rounded transition-colors flex items-center gap-2"
        >
          {#if saving}
            <svg
              class="animate-spin h-4 w-4"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                class="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                stroke-width="4"
              ></circle>
              <path
                class="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              ></path>
            </svg>
            Saving...
          {:else}
            {isEditMode ? "Save Changes" : "Create Goal"}
          {/if}
        </button>
      </div>
    </div>
  </div>
</div>
