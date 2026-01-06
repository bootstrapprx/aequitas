<script>
  import { invoke } from "@tauri-apps/api/core";
  import { onMount } from "svelte";
  import { createEventDispatcher } from "svelte";

  export let goalId;

  const dispatch = createEventDispatcher();

  let readyEvent = null;
  let dismissed = false;

  onMount(async () => {
    await checkIfReady();
  });

  async function checkIfReady() {
    try {
      const events = await invoke("get_events_by_entity", {
        entityType: "goal",
        entityId: goalId,
      });

      readyEvent = events.find(
        (e) => e.payload?.type === "goal_ready_to_complete",
      );
    } catch (err) {
      console.error("Failed to check goal readiness:", err);
    }
  }

  async function markAsComplete() {
    try {
      await invoke("update_goal_status", {
        goalId: goalId,
        newStatus: "done",
      });
      dispatch("completed");
      dismissed = true;
    } catch (err) {
      console.error("Failed to mark goal as complete:", err);
      alert(`Error: ${err}`);
    }
  }

  function dismiss() {
    dismissed = true;
  }
</script>

{#if readyEvent && !dismissed}
  <div class="completion-banner">
    <div class="banner-icon">✅</div>
    <div class="banner-content">
      <div class="banner-title">Ready to Complete</div>
      <div class="banner-message">
        All {readyEvent.payload.total_tasks || 0} tasks are done. Mark this goal
        as complete?
      </div>
    </div>
    <div class="banner-actions">
      <button class="btn-primary" on:click={markAsComplete}>
        Mark as Done
      </button>
      <button class="btn-secondary" on:click={dismiss}> Dismiss </button>
    </div>
  </div>
{/if}

<style>
  .completion-banner {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 16px;
    background: rgba(34, 197, 94, 0.1);
    border: 1px solid rgba(34, 197, 94, 0.3);
    border-radius: 8px;
    margin-bottom: 16px;
  }

  .banner-icon {
    font-size: 32px;
    flex-shrink: 0;
  }

  .banner-content {
    flex: 1;
  }

  .banner-title {
    font-size: 16px;
    font-weight: 600;
    color: rgb(34, 197, 94);
    margin-bottom: 4px;
  }

  .banner-message {
    font-size: 14px;
    color: rgba(255, 255, 255, 0.8);
  }

  .banner-actions {
    display: flex;
    gap: 8px;
  }

  .btn-primary,
  .btn-secondary {
    padding: 8px 16px;
    border-radius: 6px;
    font-size: 14px;
    font-weight: 500;
    cursor: pointer;
    border: none;
    transition: all 0.2s ease;
  }

  .btn-primary {
    background: rgb(34, 197, 94);
    color: white;
  }

  .btn-primary:hover {
    background: rgb(22, 163, 74);
  }

  .btn-secondary {
    background: rgba(255, 255, 255, 0.1);
    color: rgba(255, 255, 255, 0.8);
    border: 1px solid rgba(255, 255, 255, 0.2);
  }

  .btn-secondary:hover {
    background: rgba(255, 255, 255, 0.15);
  }
</style>
