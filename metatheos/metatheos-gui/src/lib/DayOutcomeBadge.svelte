<script>
  import { invoke } from "@tauri-apps/api/core";
  import { onMount } from "svelte";

  export let dayId;

  let outcome = null;
  let loading = true;

  onMount(async () => {
    await checkOutcome();
  });

  async function checkOutcome() {
    try {
      loading = true;
      const events = await invoke("get_events_by_entity", {
        entityType: "day",
        entityId: dayId,
      });

      // Find the most recent day outcome event
      outcome = events.find(
        (e) =>
          e.payload?.type === "day_success" ||
          e.payload?.type === "day_progress",
      );
    } catch (err) {
      console.error("Failed to check day outcome:", err);
    } finally {
      loading = false;
    }
  }

  $: isSuccess = outcome?.payload?.type === "day_success";
  $: required = outcome?.payload?.required_goals || 0;
  $: completed = outcome?.payload?.completed_required_goals || 0;
</script>

{#if !loading && outcome}
  <div class="day-outcome-badge" class:success={isSuccess}>
    <span class="badge-icon">{isSuccess ? "✅" : "⏳"}</span>
    <div class="badge-content">
      <div class="badge-label">
        {isSuccess ? "Success" : "In Progress"}
      </div>
      <div class="badge-stats">{completed}/{required} required goals</div>
    </div>
  </div>
{/if}

<style>
  .day-outcome-badge {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 12px 16px;
    background: rgba(234, 179, 8, 0.1);
    border: 1px solid rgba(234, 179, 8, 0.3);
    border-radius: 8px;
  }

  .day-outcome-badge.success {
    background: rgba(34, 197, 94, 0.1);
    border-color: rgba(34, 197, 94, 0.3);
  }

  .badge-icon {
    font-size: 24px;
  }

  .badge-content {
    flex: 1;
  }

  .badge-label {
    font-size: 14px;
    font-weight: 600;
    color: rgba(255, 255, 255, 0.9);
    margin-bottom: 2px;
  }

  .day-outcome-badge.success .badge-label {
    color: rgb(34, 197, 94);
  }

  .badge-stats {
    font-size: 12px;
    color: rgba(255, 255, 255, 0.6);
  }
</style>
