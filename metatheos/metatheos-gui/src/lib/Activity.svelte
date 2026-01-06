<script>
  import { invoke } from "@tauri-apps/api/core";
  import { onMount } from "svelte";
  import EventFeed from "./EventFeed.svelte";

  let scanReport = null;
  let scanning = false;
  let scanError = null;
  let lastScanTime = null;
  let autoScanEnabled = false;
  let autoScanInterval = null;

  onMount(() => {
    runScan(); // Initial scan on mount
  });

  async function runScan() {
    try {
      scanning = true;
      scanError = null;
      scanReport = await invoke("run_consequence_scan");
      lastScanTime = new Date();
    } catch (err) {
      scanError = err?.toString?.() ?? String(err);
      console.error("Scan failed:", err);
    } finally {
      scanning = false;
    }
  }

  function toggleAutoScan() {
    autoScanEnabled = !autoScanEnabled;
    if (autoScanEnabled) {
      autoScanInterval = setInterval(runScan, 300000); // Every 5 minutes
    } else if (autoScanInterval) {
      clearInterval(autoScanInterval);
      autoScanInterval = null;
    }
  }

  function getTotalIssues() {
    if (!scanReport) return 0;
    return (
      scanReport.blocked_goals.length +
      scanReport.stale_goals.length +
      scanReport.complex_goals.length +
      scanReport.phases_ready.length
    );
  }
</script>

<div class="space-y-6">
  <!-- Header -->
  <div class="flex items-center justify-between">
    <div>
      <h2 class="text-3xl font-bold text-gray-900 dark:text-white">Activity & Insights</h2>
      <p class="text-sm text-gray-600 dark:text-gray-300 mt-1">
        System-detected events, consequences, and actionable insights
      </p>
    </div>
    <div class="flex items-center gap-3">
      <label class="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
        <input
          type="checkbox"
          checked={autoScanEnabled}
          on:change={toggleAutoScan}
          class="rounded"
        />
        Auto-scan (5min)
      </label>
      <button
        on:click={runScan}
        disabled={scanning}
        class="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-800 disabled:cursor-not-allowed text-white rounded text-sm font-semibold transition-colors"
      >
        {scanning ? "Scanning..." : "Run Scan"}
      </button>
    </div>
  </div>

  {#if scanError}
    <div class="bg-red-900/20 border border-red-800 text-red-200 px-4 py-3 rounded">
      <strong>Scan Error:</strong> {scanError}
    </div>
  {/if}

  {#if lastScanTime}
    <div class="text-xs text-gray-500 dark:text-gray-400">
      Last scanned: {lastScanTime.toLocaleTimeString()}
    </div>
  {/if}

  <!-- Scan Results Summary -->
  {#if scanReport}
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      <!-- Blocked Goals -->
      <div class="card bg-yellow-50 dark:bg-yellow-900/20 border-l-4 border-yellow-500">
        <div class="flex items-center gap-3">
          <span class="text-3xl">🚫</span>
          <div>
            <div class="text-2xl font-bold text-gray-900 dark:text-white">
              {scanReport.blocked_goals.length}
            </div>
            <div class="text-sm text-gray-600 dark:text-gray-300">Blocked Goals</div>
          </div>
        </div>
        {#if scanReport.blocked_goals.length > 0}
          <ul class="mt-3 space-y-1 text-sm text-gray-700 dark:text-gray-300">
            {#each scanReport.blocked_goals.slice(0, 3) as goalId}
              <li class="font-mono text-xs truncate">{goalId}</li>
            {/each}
            {#if scanReport.blocked_goals.length > 3}
              <li class="text-xs text-gray-500">+{scanReport.blocked_goals.length - 3} more</li>
            {/if}
          </ul>
        {/if}
      </div>

      <!-- Stale Goals -->
      <div class="card bg-orange-50 dark:bg-orange-900/20 border-l-4 border-orange-500">
        <div class="flex items-center gap-3">
          <span class="text-3xl">⏰</span>
          <div>
            <div class="text-2xl font-bold text-gray-900 dark:text-white">
              {scanReport.stale_goals.length}
            </div>
            <div class="text-sm text-gray-600 dark:text-gray-300">Stale Goals</div>
          </div>
        </div>
        {#if scanReport.stale_goals.length > 0}
          <ul class="mt-3 space-y-1 text-sm text-gray-700 dark:text-gray-300">
            {#each scanReport.stale_goals.slice(0, 3) as goalId}
              <li class="font-mono text-xs truncate">{goalId}</li>
            {/each}
            {#if scanReport.stale_goals.length > 3}
              <li class="text-xs text-gray-500">+{scanReport.stale_goals.length - 3} more</li>
            {/if}
          </ul>
        {/if}
      </div>

      <!-- Complex Goals -->
      <div class="card bg-purple-50 dark:bg-purple-900/20 border-l-4 border-purple-500">
        <div class="flex items-center gap-3">
          <span class="text-3xl">🧩</span>
          <div>
            <div class="text-2xl font-bold text-gray-900 dark:text-white">
              {scanReport.complex_goals.length}
            </div>
            <div class="text-sm text-gray-600 dark:text-gray-300">Complex Goals</div>
          </div>
        </div>
        {#if scanReport.complex_goals.length > 0}
          <ul class="mt-3 space-y-1 text-sm text-gray-700 dark:text-gray-300">
            {#each scanReport.complex_goals.slice(0, 3) as goalId}
              <li class="font-mono text-xs truncate">{goalId}</li>
            {/each}
            {#if scanReport.complex_goals.length > 3}
              <li class="text-xs text-gray-500">+{scanReport.complex_goals.length - 3} more</li>
            {/if}
          </ul>
        {/if}
      </div>

      <!-- Phases Ready -->
      <div class="card bg-green-50 dark:bg-green-900/20 border-l-4 border-green-500">
        <div class="flex items-center gap-3">
          <span class="text-3xl">🎯</span>
          <div>
            <div class="text-2xl font-bold text-gray-900 dark:text-white">
              {scanReport.phases_ready.length}
            </div>
            <div class="text-sm text-gray-600 dark:text-gray-300">Phases Ready</div>
          </div>
        </div>
        {#if scanReport.phases_ready.length > 0}
          <ul class="mt-3 space-y-1 text-sm text-gray-700 dark:text-gray-300">
            {#each scanReport.phases_ready.slice(0, 3) as phaseId}
              <li class="font-mono text-xs truncate">{phaseId}</li>
            {/each}
            {#if scanReport.phases_ready.length > 3}
              <li class="text-xs text-gray-500">+{scanReport.phases_ready.length - 3} more</li>
            {/if}
          </ul>
        {/if}
      </div>
    </div>
  {/if}

  <!-- Event Feed -->
  <div class="card">
    <div class="flex items-center justify-between mb-4">
      <h3 class="text-xl font-bold text-gray-900 dark:text-white">Recent Events</h3>
      <span class="text-xs text-gray-500 dark:text-gray-400">
        Auto-refreshes every 30s
      </span>
    </div>
    <EventFeed limit={100} autoRefresh={true} />
  </div>

  <!-- Insights Panel -->
  {#if scanReport && getTotalIssues() > 0}
    <div class="card bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800">
      <div class="flex items-start gap-3">
        <span class="text-2xl">💡</span>
        <div>
          <p class="font-semibold text-blue-900 dark:text-blue-200 mb-2">
            System Insights
          </p>
          <ul class="text-sm text-blue-800 dark:text-blue-300 space-y-2">
            {#if scanReport.blocked_goals.length > 0}
              <li>
                • <strong>{scanReport.blocked_goals.length} goal{scanReport.blocked_goals.length > 1 ? "s" : ""}</strong> blocked by unmet dependencies. Review goal dependencies and update statuses.
              </li>
            {/if}
            {#if scanReport.stale_goals.length > 0}
              <li>
                • <strong>{scanReport.stale_goals.length} goal{scanReport.stale_goals.length > 1 ? "s have" : " has"}</strong> no activity in 7+ days. Consider archiving or reactivating these goals.
              </li>
            {/if}
            {#if scanReport.complex_goals.length > 0}
              <li>
                • <strong>{scanReport.complex_goals.length} goal{scanReport.complex_goals.length > 1 ? "s have" : " has"}</strong> 15+ tasks. Consider breaking into smaller subgoals for better tracking.
              </li>
            {/if}
            {#if scanReport.phases_ready.length > 0}
              <li>
                • <strong>{scanReport.phases_ready.length} phase{scanReport.phases_ready.length > 1 ? "s are" : " is"}</strong> ready to activate (dependencies complete).
              </li>
            {/if}
          </ul>
        </div>
      </div>
    </div>
  {:else if scanReport && getTotalIssues() === 0}
    <div class="card bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800">
      <div class="flex items-center gap-3">
        <span class="text-2xl">✅</span>
        <p class="text-green-800 dark:text-green-200">
          All clear! No issues detected. System is healthy.
        </p>
      </div>
    </div>
  {/if}
</div>

<style>
  .card {
    background: white;
    border: 1px solid rgba(107, 114, 128, 0.2);
    border-radius: 12px;
    padding: 20px;
  }

  @media (prefers-color-scheme: dark) {
    .card {
      background: rgba(31, 41, 55, 0.8);
      border-color: rgba(75, 85, 99, 0.5);
    }
  }
</style>
