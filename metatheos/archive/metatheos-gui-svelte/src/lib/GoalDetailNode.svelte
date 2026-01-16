<script>
  import { createEventDispatcher } from "svelte";
  import AnnotationPanel from "./AnnotationPanel.svelte";

  export let node;
  export let collapsed;

  const dispatch = createEventDispatcher();

  const badge = {
    goal: "bg-purple-100 text-purple-800 dark:bg-purple-900/40 dark:text-purple-200",
    subgoal: "bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-200",
    task: "bg-green-100 text-green-800 dark:bg-green-900/40 dark:text-green-200",
  };

  const childOptions = {
    goal: ["subgoal", "task"],
    subgoal: ["task"],
    task: [],
  };

  function toggle(id) {
    dispatch("toggleCollapse", id);
  }

  function statusChange(id, status) {
    dispatch("statusChange", { id, status });
  }

  function addChildRequest(item, level) {
    dispatch("addChild", { item, level });
  }
</script>

<div class="border rounded p-3 bg-white dark:bg-gray-800">
  <div class="flex items-start gap-3">
    <button class="text-lg" on:click={() => toggle(node.item.id)}>
      {#if collapsed.has(node.item.id)}▸{:else}▾{/if}
    </button>
    <div class="flex-1">
      <div class="flex items-center gap-2">
        <span class={`px-2 py-0.5 rounded text-xs font-semibold ${badge[node.item.level]}`}>
          {node.item.level.toUpperCase()}
        </span>
        <span class="font-medium text-gray-900 dark:text-white">{node.item.title}</span>
        <select
          class="text-xs border rounded px-2 py-1 bg-white dark:bg-gray-900"
          bind:value={node.item.status}
          on:change={(e) => statusChange(node.item.id, e.target.value)}
        >
          {#each ["open", "active", "blocked", "done"] as status}
            <option value={status}>{status}</option>
          {/each}
        </select>
      </div>
      {#if node.item.description}
        <p class="text-sm text-gray-600 dark:text-gray-300 mt-1">
          {node.item.description}
        </p>
      {/if}
      <div class="flex gap-2 mt-2">
        {#if childOptions[node.item.level]?.includes("subgoal")}
          <button
            class="text-xs px-2 py-1 bg-blue-100 dark:bg-blue-900/40 rounded"
            on:click={() => addChildRequest(node.item, "subgoal")}
          >
            ➕ Add Subgoal
          </button>
        {/if}
        {#if childOptions[node.item.level]?.includes("task")}
          <button
            class="text-xs px-2 py-1 bg-green-100 dark:bg-green-900/40 rounded"
            on:click={() => addChildRequest(node.item, "task")}
          >
            ➕ Add Task
          </button>
        {/if}
      </div>
      <div class="mt-2">
        <AnnotationPanel
          scopeType="work_item"
          scopeId={node.item.id}
          heading="Notes"
          compact={true}
        />
      </div>
    </div>
  </div>
  {#if !collapsed.has(node.item.id) && node.children.length > 0}
    <div class="mt-2 ml-6 space-y-2">
      {#each node.children as child}
        <svelte:self node={child} {collapsed} />
      {/each}
    </div>
  {/if}
</div>
