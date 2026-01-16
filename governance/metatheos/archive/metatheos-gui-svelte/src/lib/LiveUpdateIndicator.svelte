<script>
  import { updateInProgress, recentUpdates } from "./stores/governance";
  import { fade, fly } from "svelte/transition";

  let showRecentUpdate = false;
  let recentUpdateMessage = "";
  let hideTimer = null;

  // Watch for new updates and show notification
  $: if ($recentUpdates.length > 0) {
    const latest = $recentUpdates[0];
    recentUpdateMessage = latest.message;
    showRecentUpdate = true;

    // Clear existing timer
    if (hideTimer) clearTimeout(hideTimer);

    // Auto-hide after 3 seconds
    hideTimer = setTimeout(() => {
      showRecentUpdate = false;
    }, 3000);
  }
</script>

<!-- Update in progress spinner -->
{#if $updateInProgress}
  <div class="fixed top-4 right-4 z-50" transition:fade={{ duration: 200 }}>
    <div
      class="flex items-center gap-2 bg-blue-500 text-white px-4 py-2 rounded-lg shadow-lg"
    >
      <div class="animate-spin">
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24">
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
      </div>
      <span class="text-sm font-medium">Syncing...</span>
    </div>
  </div>
{/if}

<!-- Recent update notification (toast) -->
{#if showRecentUpdate}
  <div
    class="fixed top-4 right-4 z-50"
    transition:fly={{ y: -20, duration: 300 }}
  >
    <div
      class="flex items-center gap-3 bg-green-500 text-white px-4 py-3 rounded-lg shadow-lg max-w-md"
    >
      <div class="flex-shrink-0">
        <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
          <path
            fill-rule="evenodd"
            d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
            clip-rule="evenodd"
          />
        </svg>
      </div>
      <div class="flex-1">
        <p class="text-sm font-medium">{recentUpdateMessage}</p>
        <p class="text-xs opacity-90">Governance data refreshed</p>
      </div>
      <button
        class="flex-shrink-0 text-white hover:text-green-100 transition-colors"
        aria-label="Dismiss"
        on:click={() => (showRecentUpdate = false)}
      >
        <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
          <path
            fill-rule="evenodd"
            d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
            clip-rule="evenodd"
          />
        </svg>
      </button>
    </div>
  </div>
{/if}

<style>
  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }
  .animate-spin {
    animation: spin 1s linear infinite;
  }
</style>
