<script lang="ts">
  import { invoke } from "@tauri-apps/api/core";

  export let scopeType: string; // "day", "goal", "work_item", "phase"
  export let scopeId: string;
  export let heading = "Timeline";
  export let collapsedInitially = false;
  export let compact = false;

  interface TimelineItem {
    kind: "event" | "annotation";
    timestamp: string;
    title: string;
    body: string;
    entity_type: string;
    entity_id: string;
    author: string | null;
  }

  let timelineItems: TimelineItem[] = [];
  let loading = false;
  let error: string | null = null;
  let expanded = !collapsedInitially;

  async function load() {
    if (!scopeId || !scopeType) return;
    loading = true;
    error = null;
    try {
      const commandMap = {
        day: "get_timeline_for_day",
        goal: "get_timeline_for_goal",
        work_item: "get_timeline_for_work_item",
        phase: "get_timeline_for_phase",
      };

      const command = commandMap[scopeType];
      if (!command) {
        throw new Error(`Invalid scope type: ${scopeType}`);
      }

      timelineItems = await invoke(command, {
        [`${scopeType}_id`]: scopeId,
      });
    } catch (e) {
      error = e?.toString?.() ?? String(e);
    } finally {
      loading = false;
    }
  }

  function formatDate(timestamp: string): string {
    try {
      return new Date(timestamp).toLocaleString();
    } catch {
      return timestamp;
    }
  }

  $: if (scopeId) load();
</script>

<div class={`timeline-panel ${compact ? "compact" : ""}`}>
  <button class="header" on:click={() => (expanded = !expanded)}>
    <div class="title">
      <span>📜</span>
      <span>{heading}</span>
      {#if loading}
        <span class="pill">Loading</span>
      {:else}
        <span class="pill">{timelineItems.length}</span>
      {/if}
    </div>
    <span class="chevron">{expanded ? "▾" : "▸"}</span>
  </button>

  {#if expanded}
    <div class="content">
      {#if error}
        <div class="error">{error}</div>
      {/if}

      <div class="list">
        {#if timelineItems.length === 0 && !loading}
          <div class="empty">No timeline entries yet.</div>
        {/if}
        {#each timelineItems as item}
          <div class={`timeline-item ${item.kind}`}>
            <div class="item-header">
              <span class={`kind-badge ${item.kind}`}>
                {item.kind === "event" ? "🧱 Event" : "📝 Note"}
              </span>
              {#if item.author}
                <span class={`author ${item.author === "ai" ? "ai" : ""}`}>
                  {item.author}
                </span>
              {/if}
              <span class="timestamp">{formatDate(item.timestamp)}</span>
            </div>
            <div class="item-title">{item.title}</div>
            {#if item.body && item.kind === "annotation"}
              <div class="item-body">{item.body}</div>
            {/if}
            <div class="item-meta">
              <span class="scope"
                >{item.entity_type}:{item.entity_id.substring(0, 12)}</span
              >
            </div>
          </div>
        {/each}
      </div>
    </div>
  {/if}
</div>

<style>
  .timeline-panel {
    border: 1px solid rgba(107, 114, 128, 0.4);
    border-radius: 8px;
    background: rgba(17, 24, 39, 0.5);
    color: #e5e7eb;
  }
  .timeline-panel.compact {
    background: rgba(17, 24, 39, 0.2);
  }
  .header {
    width: 100%;
    padding: 8px 12px;
    background: transparent;
    border: none;
    color: inherit;
    display: flex;
    justify-content: space-between;
    align-items: center;
    cursor: pointer;
  }
  .title {
    display: flex;
    gap: 8px;
    align-items: center;
    font-weight: 700;
    letter-spacing: 0.02em;
    text-transform: uppercase;
    font-size: 12px;
  }
  .pill {
    background: rgba(59, 130, 246, 0.15);
    color: #93c5fd;
    padding: 2px 8px;
    border-radius: 999px;
    font-size: 11px;
  }
  .chevron {
    font-size: 14px;
  }
  .content {
    padding: 0 12px 12px;
    display: flex;
    flex-direction: column;
    gap: 10px;
  }
  .list {
    display: flex;
    flex-direction: column;
    gap: 12px;
    max-height: 500px;
    overflow: auto;
  }
  .timeline-item {
    background: rgba(31, 41, 55, 0.6);
    border-left: 3px solid rgba(55, 65, 81, 0.7);
    border-radius: 6px;
    padding: 10px;
    transition: all 0.2s ease;
  }
  .timeline-item.event {
    border-left-color: #3b82f6;
  }
  .timeline-item.annotation {
    border-left-color: #a78bfa;
  }
  .item-header {
    display: flex;
    gap: 8px;
    align-items: center;
    font-size: 11px;
    margin-bottom: 6px;
  }
  .kind-badge {
    text-transform: uppercase;
    font-weight: 700;
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 10px;
  }
  .kind-badge.event {
    background: rgba(59, 130, 246, 0.2);
    color: #93c5fd;
  }
  .kind-badge.annotation {
    background: rgba(167, 139, 250, 0.2);
    color: #c4b5fd;
  }
  .author {
    text-transform: uppercase;
    font-weight: 700;
    color: #60a5fa;
    font-size: 10px;
  }
  .author.ai {
    color: #a78bfa;
  }
  .timestamp {
    color: #9ca3af;
    font-size: 11px;
    margin-left: auto;
  }
  .item-title {
    font-size: 14px;
    font-weight: 600;
    color: #f3f4f6;
    margin-bottom: 4px;
  }
  .item-body {
    font-size: 13px;
    white-space: pre-wrap;
    color: #d1d5db;
    margin-bottom: 6px;
    padding-left: 8px;
    border-left: 2px solid rgba(107, 114, 128, 0.3);
  }
  .item-meta {
    font-size: 10px;
    color: #6b7280;
    display: flex;
    gap: 6px;
  }
  .scope {
    font-family: monospace;
    background: rgba(55, 65, 81, 0.5);
    padding: 1px 4px;
    border-radius: 3px;
  }
  .empty {
    text-align: center;
    font-size: 13px;
    color: #9ca3af;
    padding: 12px;
  }
  .error {
    color: #fca5a5;
    font-size: 13px;
    padding: 8px;
    background: rgba(248, 113, 113, 0.1);
    border-radius: 4px;
  }
</style>
