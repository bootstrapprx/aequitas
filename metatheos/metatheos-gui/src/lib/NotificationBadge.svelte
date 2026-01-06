<script>
  import { invoke } from "@tauri-apps/api/core";
  import { onMount, onDestroy } from "svelte";

  let actionableEvents = [];
  let eventStats = null;
  let showDropdown = false;
  let loading = false;
  let pollInterval = null;

  onMount(async () => {
    await loadEvents();
    // Poll every 30 seconds
    pollInterval = setInterval(loadEvents, 30000);
  });

  onDestroy(() => {
    if (pollInterval) {
      clearInterval(pollInterval);
    }
  });

  async function loadEvents() {
    try {
      loading = true;
      const [events, stats] = await Promise.all([
        invoke("get_actionable_events"),
        invoke("get_event_stats"),
      ]);
      actionableEvents = events;
      eventStats = stats;
    } catch (err) {
      console.error("Failed to load events:", err);
    } finally {
      loading = false;
    }
  }

  function toggleDropdown() {
    showDropdown = !showDropdown;
  }

  function getEventIcon(event) {
    const type = event.payload?.type || "";
    if (type === "goal_ready_to_complete") return "✅";
    if (type === "phase_ready_to_close") return "🎯";
    if (type === "day_success") return "🌟";
    if (type === "day_progress") return "⏳";
    if (type === "phase_progress_updated") return "📊";
    return "ℹ️";
  }

  function getEventMessage(event) {
    const type = event.payload?.type || "";
    const entityId = event.entity_id;

    if (type === "goal_ready_to_complete") {
      const total = event.payload.total_tasks || 0;
      return `${entityId} is ready to complete (${total}/${total} tasks done)`;
    }
    if (type === "phase_ready_to_close") {
      return `${entityId} is ready to close (all goals complete)`;
    }
    if (type === "day_success") {
      const req = event.payload.required_goals || 0;
      return `Day ${entityId}: Success! (${req}/${req} goals)`;
    }
    if (type === "day_progress") {
      const completed = event.payload.completed_required_goals || 0;
      const required = event.payload.required_goals || 0;
      return `Day ${entityId}: Progress (${completed}/${required} goals)`;
    }
    if (type === "phase_progress_updated") {
      const done = event.payload.done_goals || 0;
      const total = event.payload.total_goals || 0;
      const pct = total > 0 ? Math.round((done / total) * 100) : 0;
      return `${entityId}: ${done}/${total} goals (${pct}%)`;
    }
    return `${entityId}: ${type}`;
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
      return date.toLocaleDateString();
    } catch {
      return "";
    }
  }

  function getEventPriority(event) {
    const type = event.payload?.type || "";
    if (type === "goal_ready_to_complete") return 1;
    if (type === "phase_ready_to_close") return 1;
    if (type === "day_success") return 2;
    return 3;
  }

  $: totalActionable = eventStats?.total_actionable || 0;
  $: sortedEvents = [...actionableEvents].sort(
    (a, b) =>
      getEventPriority(a) - getEventPriority(b) ||
      new Date(b.created_at) - new Date(a.created_at),
  );
</script>

<div class="notification-container">
  <button
    class="notification-button"
    class:has-notifications={totalActionable > 0}
    on:click={toggleDropdown}
    title="System notifications"
  >
    <span class="icon">🔔</span>
    {#if totalActionable > 0}
      <span class="badge">{totalActionable}</span>
    {/if}
  </button>

  {#if showDropdown}
    <div
      class="dropdown"
      on:click|stopPropagation
      on:keydown|stopPropagation
      role="menu"
      tabindex="-1"
    >
      <div class="dropdown-header">
        <h3>System Insights</h3>
        <button class="close-btn" on:click={toggleDropdown}>✕</button>
      </div>

      {#if loading}
        <div class="loading">Loading events...</div>
      {:else if sortedEvents.length === 0}
        <div class="empty-state">
          <p>✨ All caught up!</p>
          <p class="empty-subtitle">No pending actions right now.</p>
        </div>
      {:else}
        <div class="event-list">
          {#each sortedEvents as event (event.id)}
            <div class="event-item" data-priority={getEventPriority(event)}>
              <div class="event-icon">{getEventIcon(event)}</div>
              <div class="event-content">
                <div class="event-message">{getEventMessage(event)}</div>
                <div class="event-meta">
                  <span class="event-time"
                    >{formatTimestamp(event.created_at)}</span
                  >
                  <span class="event-actor">via {event.actor}</span>
                </div>
              </div>
            </div>
          {/each}
        </div>

        {#if eventStats}
          <div class="stats-footer">
            <div class="stat">
              <strong>{eventStats.goals_ready_to_complete}</strong> goals ready
            </div>
            <div class="stat">
              <strong>{eventStats.phases_ready_to_close}</strong> phases ready
            </div>
          </div>
        {/if}
      {/if}
    </div>
  {/if}
</div>

<style>
  .notification-container {
    position: relative;
  }

  .notification-button {
    position: relative;
    background: transparent;
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 8px;
    padding: 8px 12px;
    color: rgba(255, 255, 255, 0.8);
    cursor: pointer;
    transition: all 0.2s ease;
    font-size: 18px;
  }

  .notification-button:hover {
    background: rgba(255, 255, 255, 0.05);
    border-color: rgba(255, 255, 255, 0.3);
  }

  .notification-button.has-notifications {
    border-color: rgba(59, 130, 246, 0.5);
    color: rgb(59, 130, 246);
  }

  .notification-button.has-notifications:hover {
    background: rgba(59, 130, 246, 0.1);
  }

  .badge {
    position: absolute;
    top: -4px;
    right: -4px;
    background: rgb(239, 68, 68);
    color: white;
    border-radius: 12px;
    padding: 2px 6px;
    font-size: 11px;
    font-weight: 600;
    min-width: 18px;
    text-align: center;
  }

  .dropdown {
    position: absolute;
    top: calc(100% + 8px);
    right: 0;
    background: rgb(30, 41, 59);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
    width: 420px;
    max-height: 600px;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    z-index: 1000;
  }

  .dropdown-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  }

  .dropdown-header h3 {
    margin: 0;
    font-size: 16px;
    font-weight: 600;
    color: white;
  }

  .close-btn {
    background: transparent;
    border: none;
    color: rgba(255, 255, 255, 0.5);
    font-size: 20px;
    cursor: pointer;
    padding: 4px 8px;
    line-height: 1;
  }

  .close-btn:hover {
    color: rgba(255, 255, 255, 0.8);
  }

  .loading,
  .empty-state {
    padding: 32px;
    text-align: center;
    color: rgba(255, 255, 255, 0.6);
  }

  .empty-state p {
    margin: 0;
    font-size: 18px;
  }

  .empty-subtitle {
    font-size: 14px !important;
    margin-top: 8px !important;
  }

  .event-list {
    max-height: 400px;
    overflow-y: auto;
  }

  .event-item {
    display: flex;
    gap: 12px;
    padding: 12px 16px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    transition: background 0.2s ease;
  }

  .event-item:hover {
    background: rgba(255, 255, 255, 0.02);
  }

  .event-item[data-priority="1"] {
    background: rgba(59, 130, 246, 0.05);
  }

  .event-icon {
    font-size: 20px;
    flex-shrink: 0;
  }

  .event-content {
    flex: 1;
    min-width: 0;
  }

  .event-message {
    color: rgba(255, 255, 255, 0.9);
    font-size: 14px;
    line-height: 1.4;
    margin-bottom: 4px;
  }

  .event-meta {
    display: flex;
    gap: 12px;
    font-size: 12px;
    color: rgba(255, 255, 255, 0.5);
  }

  .stats-footer {
    display: flex;
    gap: 16px;
    padding: 12px 16px;
    background: rgba(0, 0, 0, 0.2);
    border-top: 1px solid rgba(255, 255, 255, 0.1);
  }

  .stat {
    flex: 1;
    font-size: 13px;
    color: rgba(255, 255, 255, 0.7);
  }

  .stat strong {
    color: rgb(59, 130, 246);
    font-size: 16px;
  }
</style>
