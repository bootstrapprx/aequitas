<script>
  import { invoke } from "@tauri-apps/api/core";
  import { onMount } from "svelte";

  export let phaseId;
  export let compact = false;

  let loading = true;
  let total = 0;
  let done = 0;
  let pct = 0;

  onMount(async () => {
    await loadProgress();
  });

  async function loadProgress() {
    try {
      loading = true;
      // Get the most recent phase_progress_updated event for this phase
      const events = await invoke("get_events_by_entity", {
        entityType: "phase",
        entityId: phaseId,
      });

      const progressEvent = events.find(
        (e) => e.payload?.type === "phase_progress_updated",
      );

      if (progressEvent) {
        total = progressEvent.payload.total_goals || 0;
        done = progressEvent.payload.done_goals || 0;
        pct = total > 0 ? Math.round((done / total) * 100) : 0;
      } else {
        // Fallback: calculate from current goal statuses
        // (This would require a new query - for now just show 0)
        total = 0;
        done = 0;
        pct = 0;
      }
    } catch (err) {
      console.error("Failed to load phase progress:", err);
    } finally {
      loading = false;
    }
  }

  $: progressColor = pct === 100 ? "bg-green-500" : pct >= 50 ? "bg-blue-500" : "bg-yellow-500";
</script>

{#if !loading && total > 0}
  <div class="phase-progress" class:compact>
    <div class="progress-bar-container">
      <div class="progress-bar-fill {progressColor}" style="width: {pct}%">
      </div>
    </div>
    {#if !compact}
      <div class="progress-label">
        <span class="progress-text">{done}/{total} goals</span>
        <span class="progress-pct">{pct}%</span>
      </div>
    {:else}
      <span class="progress-pct-compact">{pct}%</span>
    {/if}
  </div>
{/if}

<style>
  .phase-progress {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .phase-progress.compact {
    gap: 6px;
  }

  .progress-bar-container {
    flex: 1;
    height: 8px;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 4px;
    overflow: hidden;
  }

  .compact .progress-bar-container {
    height: 6px;
  }

  .progress-bar-fill {
    height: 100%;
    transition: width 0.3s ease;
    border-radius: 4px;
  }

  .progress-label {
    display: flex;
    gap: 8px;
    font-size: 13px;
    color: rgba(255, 255, 255, 0.8);
    white-space: nowrap;
  }

  .progress-text {
    color: rgba(255, 255, 255, 0.6);
  }

  .progress-pct {
    font-weight: 600;
    color: rgba(255, 255, 255, 0.9);
  }

  .progress-pct-compact {
    font-size: 12px;
    font-weight: 600;
    color: rgba(255, 255, 255, 0.7);
  }
</style>
