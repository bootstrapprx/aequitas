<script>
  import { onMount, createEventDispatcher } from "svelte";
  import { invoke } from "@tauri-apps/api/core";
  import GoalDetailNode from "./GoalDetailNode.svelte";
  import AnnotationPanel from "./AnnotationPanel.svelte";
  import Timeline from "./Timeline.svelte";
  import GoalCompletionPrompt from "./GoalCompletionPrompt.svelte";

  export let goalId;

  const dispatch = createEventDispatcher();

  let loading = true;
  let error = null;
  let detail = null;
  let collapsed = new Set();
  let progress = { done: 0, total: 0, pct: 0 };

  const childOptions = {
    goal: ["subgoal", "task"],
    subgoal: ["task"],
    task: [],
  };

  onMount(load);
  $: if (goalId) {
    load();
  }

  async function load() {
    if (!goalId) return;
    loading = true;
    error = null;
    try {
      detail = await invoke("get_goal_detail", { goalId });
    } catch (err) {
      error = err?.toString?.() ?? String(err);
      detail = null;
    } finally {
      loading = false;
    }
  }

  async function changeStatus(id, status) {
    try {
      await invoke("set_work_item_status", { id, status });
      await load();
    } catch (err) {
      error = err?.toString?.() ?? String(err);
    }
  }

  async function addChild(item, level) {
    if (!childOptions[item.level]?.includes(level)) {
      error = "Invalid child level for parent";
      return;
    }
    const title = prompt(`Create ${level}`, "");
    if (!title) return;
    try {
      await invoke("create_work_item", {
        req: {
          parent_id: item.id,
          goal_id: item.goal_id,
          level,
          title,
          description: null,
          order_index: null,
        },
      });
      await load();
    } catch (err) {
      error = err?.toString?.() ?? String(err);
    }
  }

  function toggleCollapse(id) {
    const next = new Set(collapsed);
    if (next.has(id)) {
      next.delete(id);
    } else {
      next.add(id);
    }
    collapsed = next;
  }

  function computeProgress(nodes) {
    let done = 0;
    let total = 0;
    function walk(list) {
      for (const n of list) {
        if (n.item.level === "task") {
          total += 1;
          if (n.item.status === "done") done += 1;
        }
        walk(n.children);
      }
    }
    walk(nodes);
    return { done, total, pct: total === 0 ? 0 : Math.round((done / total) * 100) };
  }

  $: progress = detail ? computeProgress(detail.tree) : { done: 0, total: 0, pct: 0 };

  function back() {
    dispatch("back");
  }
</script>

<div class="space-y-6">
  <div class="flex items-center justify-between">
    <div>
      <button class="text-sm text-primary-700 hover:underline" on:click={back}>
        ← Back to Goals
      </button>
      {#if detail}
        <h2 class="text-3xl font-bold text-gray-900 dark:text-white mt-2">
          {detail.goal.title}
        </h2>
        <div class="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-300 mt-1">
          <span class="font-mono px-2 py-1 bg-gray-100 dark:bg-gray-800 rounded">
            {detail.goal.id}
          </span>
          {#if detail.phase}
            <span class="px-2 py-1 rounded bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-200">
              Phase {detail.phase.phase_id}
            </span>
          {/if}
          <span class="px-2 py-1 rounded bg-gray-200 dark:bg-gray-700">
            {detail.goal.status}
          </span>
        </div>
      {/if}
    </div>
    {#if detail}
      <div class="text-right">
        <div class="text-2xl font-semibold text-gray-900 dark:text-white">
          {progress.pct}%
        </div>
        <div class="text-sm text-gray-600 dark:text-gray-300">
          {progress.done}/{progress.total} tasks done
        </div>
      </div>
    {/if}
  </div>

  {#if loading}
    <div class="card">Loading goal…</div>
  {:else if error}
    <div class="card bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-800 dark:text-red-200">
      {error}
    </div>
  {:else if detail}
    <GoalCompletionPrompt goalId={detail.goal.id} on:completed={load} />
    <AnnotationPanel
      heading="Goal Notes"
      scopeType="goal"
      scopeId={detail.goal.id}
      collapsedInitially={false}
    />
    <Timeline
      heading="Goal Timeline"
      scopeType="goal"
      scopeId={detail.goal.id}
      collapsedInitially={true}
    />
    <div class="card">
      <h3 class="text-lg font-semibold mb-4 text-gray-900 dark:text-white">
        Execution Tree
      </h3>
      {#if detail.tree.length === 0}
        <p class="text-sm text-gray-600 dark:text-gray-300">
          No work items yet. Add subgoals or tasks to begin.
        </p>
      {:else}
        <div class="space-y-2">
          {#each detail.tree as node}
            <GoalDetailNode
              {node}
              {collapsed}
              on:toggleCollapse={(e) => toggleCollapse(e.detail)}
              on:statusChange={(e) => changeStatus(e.detail.id, e.detail.status)}
              on:addChild={(e) => addChild(e.detail.item, e.detail.level)}
            />
          {/each}
        </div>
      {/if}
    </div>
  {/if}
</div>
