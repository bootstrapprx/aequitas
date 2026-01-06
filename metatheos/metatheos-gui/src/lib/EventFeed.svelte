<script>
  import { invoke } from "@tauri-apps/api/core";
  import { onMount, onDestroy } from "svelte";

  export let entityType = null; // Optional filter
  export let entityId = null; // Optional filter
  export let actor = null; // Optional filter: 'user', 'system', 'ai'
  export let limit = 50;
  export let autoRefresh = false;

  let events = [];
  let loading = true;
  let error = null;
  let expandedEvents = new Set();
  let pollInterval = null;

  onMount(async () => {
    await loadEvents();
    if (autoRefresh) {
      pollInterval = setInterval(loadEvents, 30000); // Refresh every 30s
    }
  });

  onDestroy(() => {
    if (pollInterval) {
      clearInterval(pollInterval);
    }
  });

  async function loadEvents() {
    try {
      loading = true;
      error = null;

      if (entityType && entityId) {
        events = await invoke("get_events_by_entity", {
          entityType,
          entityId,
        });
      } else {
        events = await invoke("get_recent_events", {
          limit,
          entityType,
          actor,
        });
      }
    } catch (err) {
      error = err?.toString?.() ?? String(err);
      console.error("Failed to load events:", err);
    } finally {
      loading = false;
    }
  }

  function toggleExpand(eventId) {
    if (expandedEvents.has(eventId)) {
      expandedEvents.delete(eventId);
    } else {
      expandedEvents.add(eventId);
    }
    expandedEvents = expandedEvents; // Trigger reactivity
  }

  function getEventIcon(event) {
    const type = event.payload?.type || "";
    // Reactive consequence events
    if (type === "goal_ready_to_complete") return "✅";
    if (type === "phase_ready_to_close") return "🎯";
    if (type === "phase_progress_updated") return "📊";
    if (type === "day_success") return "🌟";
    if (type === "day_progress") return "⏳";

    // Proactive scan events
    if (type === "goal_blocked") return "🚫";
    if (type === "goal_stale") return "⏰";
    if (type === "goal_high_complexity") return "🧩";
    if (type === "phase_ready_to_activate") return "🎯";

    const action = event.action?.toLowerCase() || "";
    if (action === "create") return "➕";
    if (action === "update") return "✏️";
    if (action === "complete") return "✔️";
    if (action === "delete") return "🗑️";
    if (action === "link") return "🔗";

    return "📌";
  }

  function getEventTitle(event) {
    const type = event.payload?.type || "";
    // Reactive consequence events
    if (type === "goal_ready_to_complete") return "Goal Ready to Complete";
    if (type === "phase_ready_to_close") return "Phase Ready to Close";
    if (type === "phase_progress_updated") return "Phase Progress Updated";
    if (type === "day_success") return "Day Completed Successfully";
    if (type === "day_progress") return "Day in Progress";

    // Proactive scan events
    if (type === "goal_blocked") return "Goal Blocked";
    if (type === "goal_stale") return "Goal Stale (No Activity)";
    if (type === "goal_high_complexity") return "Goal Too Complex";
    if (type === "phase_ready_to_activate") return "Phase Ready to Activate";

    const action = event.action?.toLowerCase() || "";
    const entityType = event.entity_type || "";
    return `${action.charAt(0).toUpperCase() + action.slice(1)} ${entityType}`;
  }

  function formatTimestamp(timestamp) {
    try {
      const date = new Date(timestamp);
      const now = new Date();
      const diff = now - date;
      const minutes = Math.floor(diff / 60000);
      const hours = Math.floor(diff / 3600000);
      const days = Math.floor(diff / 86400000);

      if (minutes < 1) return "just now";
      if (minutes < 60) return `${minutes}m ago`;
      if (hours < 24) return `${hours}h ago`;
      if (days < 7) return `${days}d ago`;

      return date.toLocaleString();
    } catch {
      return "";
    }
  }

  function getActorColor(actor) {
    if (actor === "system") return "bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-200";
    if (actor === "ai") return "bg-purple-100 text-purple-800 dark:bg-purple-900/40 dark:text-purple-200";
    return "bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300";
  }

  $: isExpanded = (eventId) => expandedEvents.has(eventId);
</script>

<div class="event-feed">
  <div class="feed-header">
    <h3>Event Timeline</h3>
    <button class="refresh-btn" on:click={loadEvents} disabled={loading}>
      {loading ? "⏳" : "🔄"}
    </button>
  </div>

  {#if loading && events.length === 0}
    <div class="feed-loading">Loading events...</div>
  {:else if error}
    <div class="feed-error">{error}</div>
  {:else if events.length === 0}
    <div class="feed-empty">
      <p>No events found</p>
    </div>
  {:else}
    <div class="event-list">
      {#each events as event (event.id)}
        <div class="event-item" class:expanded={isExpanded(event.id)}>
          <div class="event-main" on:click={() => toggleExpand(event.id)}>
            <div class="event-icon">{getEventIcon(event)}</div>
            <div class="event-header-content">
              <div class="event-title">{getEventTitle(event)}</div>
              <div class="event-meta">
                <span class="event-entity">{event.entity_id}</span>
                <span class="event-time">{formatTimestamp(event.created_at)}</span>
                <span class={`event-actor ${getActorColor(event.actor)}`}>
                  {event.actor}
                </span>
              </div>
            </div>
            <div class="expand-icon">{isExpanded(event.id) ? "▼" : "▶"}</div>
          </div>

          {#if isExpanded(event.id)}
            <div class="event-details">
              <div class="detail-section">
                <span class="detail-label">Entity Type:</span>
                <span class="detail-value">{event.entity_type}</span>
              </div>
              <div class="detail-section">
                <span class="detail-label">Entity ID:</span>
                <span class="detail-value">{event.entity_id}</span>
              </div>
              <div class="detail-section">
                <span class="detail-label">Action:</span>
                <span class="detail-value">{event.action}</span>
              </div>
              <div class="detail-section">
                <span class="detail-label">Actor:</span>
                <span class="detail-value">{event.actor}</span>
              </div>
              <div class="detail-section">
                <span class="detail-label">Timestamp:</span>
                <span class="detail-value"
                  >{new Date(event.created_at).toLocaleString()}</span
                >
              </div>
              {#if event.payload && Object.keys(event.payload).length > 0}
                <div class="detail-section full-width">
                  <span class="detail-label">Payload:</span>
                  <pre class="payload-content">{JSON.stringify(
                      event.payload,
                      null,
                      2,
                    )}</pre>
                </div>
              {/if}
            </div>
          {/if}
        </div>
      {/each}
    </div>
  {/if}
</div>

<style>
  .event-feed {
    background: rgb(30, 41, 59);
    border-radius: 8px;
    border: 1px solid rgba(255, 255, 255, 0.1);
    overflow: hidden;
  }

  .feed-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  }

  .feed-header h3 {
    margin: 0;
    font-size: 16px;
    font-weight: 600;
    color: white;
  }

  .refresh-btn {
    background: transparent;
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 4px;
    padding: 4px 8px;
    color: rgba(255, 255, 255, 0.8);
    cursor: pointer;
    font-size: 16px;
    transition: all 0.2s ease;
  }

  .refresh-btn:hover:not(:disabled) {
    background: rgba(255, 255, 255, 0.05);
    border-color: rgba(255, 255, 255, 0.3);
  }

  .refresh-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .feed-loading,
  .feed-error,
  .feed-empty {
    padding: 32px;
    text-align: center;
    color: rgba(255, 255, 255, 0.6);
  }

  .feed-error {
    color: rgb(239, 68, 68);
  }

  .event-list {
    max-height: 600px;
    overflow-y: auto;
  }

  .event-item {
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    transition: background 0.2s ease;
  }

  .event-item:hover {
    background: rgba(255, 255, 255, 0.02);
  }

  .event-main {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 16px;
    cursor: pointer;
  }

  .event-icon {
    font-size: 20px;
    flex-shrink: 0;
  }

  .event-header-content {
    flex: 1;
    min-width: 0;
  }

  .event-title {
    color: rgba(255, 255, 255, 0.9);
    font-size: 14px;
    font-weight: 500;
    margin-bottom: 4px;
  }

  .event-meta {
    display: flex;
    gap: 8px;
    align-items: center;
    flex-wrap: wrap;
  }

  .event-entity {
    font-family: monospace;
    font-size: 12px;
    color: rgba(255, 255, 255, 0.6);
  }

  .event-time {
    font-size: 11px;
    color: rgba(255, 255, 255, 0.5);
  }

  .event-actor {
    font-size: 11px;
    padding: 2px 6px;
    border-radius: 4px;
    font-weight: 500;
  }

  .expand-icon {
    color: rgba(255, 255, 255, 0.5);
    font-size: 12px;
    flex-shrink: 0;
  }

  .event-details {
    padding: 12px 16px 16px 48px;
    background: rgba(0, 0, 0, 0.2);
    border-top: 1px solid rgba(255, 255, 255, 0.05);
  }

  .detail-section {
    display: flex;
    gap: 12px;
    margin-bottom: 8px;
    font-size: 13px;
  }

  .detail-section.full-width {
    flex-direction: column;
    gap: 4px;
  }

  .detail-label {
    color: rgba(255, 255, 255, 0.5);
    min-width: 100px;
    font-weight: 500;
  }

  .detail-value {
    color: rgba(255, 255, 255, 0.9);
    font-family: monospace;
  }

  .payload-content {
    background: rgba(0, 0, 0, 0.3);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 4px;
    padding: 8px;
    font-size: 12px;
    color: rgba(255, 255, 255, 0.8);
    overflow-x: auto;
    margin: 0;
  }
</style>
