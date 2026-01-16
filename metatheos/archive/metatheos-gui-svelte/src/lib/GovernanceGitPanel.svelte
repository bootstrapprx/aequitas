<script>
  import { invoke } from "@tauri-apps/api/core";
  import { onMount } from "svelte";
  import Toast from "./Toast.svelte";

  let loading = false;
  let gitStatus = null;
  let showCommitModal = false;
  let commitMessage = "";
  let relatedIds = "";
  let committing = false;

  let toastShow = false;
  let toastMessage = "";
  let toastType = "success";

  const tauriAvailable = () => {
    if (typeof window === "undefined") return false;
    return Boolean(
      window.__TAURI__ || window.__TAURI_IPC__ || window.__TAURI_INTERNALS__,
    );
  };

  onMount(async () => {
    if (!tauriAvailable()) {
      return;
    }
    await refreshGitStatus();
  });

  async function refreshGitStatus() {
    try {
      loading = true;
      gitStatus = await invoke("get_governance_git_status");
    } catch (err) {
      showToast(`Failed to get Git status: ${err}`, "error");
    } finally {
      loading = false;
    }
  }

  function openCommitModal() {
    if (!gitStatus || gitStatus.is_clean) {
      showToast("No changes to commit", "info");
      return;
    }
    commitMessage = "";
    relatedIds = "";
    showCommitModal = true;
  }

  function closeCommitModal() {
    showCommitModal = false;
    commitMessage = "";
    relatedIds = "";
  }

  async function confirmCommit() {
    if (commitMessage.trim() === "") {
      showToast("Commit message is required", "error");
      return;
    }

    try {
      committing = true;
      const result = await invoke("commit_governance_changes", {
        message: commitMessage.trim(),
        relatedIds: relatedIds.trim() || null,
      });

      showToast(
        `${result.message}. Commit: ${result.commit_hash?.substring(0, 7) || "unknown"}`,
        "success",
      );
      closeCommitModal();
      await refreshGitStatus();
    } catch (err) {
      showToast(`Commit failed: ${err}`, "error");
    } finally {
      committing = false;
    }
  }

  function showToast(message, type = "success") {
    toastMessage = message;
    toastType = type;
    toastShow = true;
  }
</script>

<div
  class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4"
>
  <Toast bind:show={toastShow} message={toastMessage} type={toastType} />

  <!-- Header -->
  <div class="flex items-center justify-between mb-4">
    <div class="flex items-center gap-2">
      <span class="text-xl">📦</span>
      <h3 class="text-lg font-bold text-gray-900 dark:text-white">
        Governance State
      </h3>
    </div>
    <button
      class="px-3 py-1 text-sm bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
      on:click={refreshGitStatus}
      disabled={loading}
    >
      {loading ? "Refreshing..." : "🔄 Refresh"}
    </button>
  </div>

  {#if loading}
    <div class="flex items-center justify-center py-8">
      <div
        class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"
      ></div>
    </div>
  {:else if gitStatus}
    {#if !gitStatus.is_repo}
      <div
        class="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4"
      >
        <p class="text-yellow-800 dark:text-yellow-200 text-sm">
          {gitStatus.error || "Governance directory is not a Git repository"}
        </p>
      </div>
    {:else}
      <!-- Git Status Info -->
      <div class="space-y-3">
        <!-- Branch -->
        <div class="flex items-center justify-between">
          <span class="text-sm font-medium text-gray-600 dark:text-gray-400"
            >Branch:</span
          >
          <span
            class="px-2 py-1 text-sm font-mono bg-gray-100 dark:bg-gray-900 text-gray-900 dark:text-white rounded"
          >
            {gitStatus.current_branch || "unknown"}
          </span>
        </div>

        <!-- Clean/Dirty Status -->
        <div class="flex items-center justify-between">
          <span class="text-sm font-medium text-gray-600 dark:text-gray-400"
            >Status:</span
          >
          <span
            class="px-2 py-1 text-sm font-semibold rounded {gitStatus.is_clean
              ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300'
              : 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-300'}"
          >
            {gitStatus.is_clean ? "✓ Clean" : "● Dirty"}
          </span>
        </div>

        <!-- Modified Files Count -->
        {#if !gitStatus.is_clean}
          <div class="flex items-center justify-between">
            <span class="text-sm font-medium text-gray-600 dark:text-gray-400"
              >Modified Files:</span
            >
            <span class="text-sm font-semibold text-gray-900 dark:text-white">
              {gitStatus.modified_files.length}
            </span>
          </div>

          <!-- Modified Files List -->
          <div
            class="mt-3 bg-gray-50 dark:bg-gray-900 rounded border border-gray-200 dark:border-gray-700 p-3 max-h-40 overflow-y-auto"
          >
            <p
              class="text-xs font-medium text-gray-600 dark:text-gray-400 mb-2"
            >
              Changed files:
            </p>
            {#each gitStatus.modified_files as file}
              <div
                class="text-xs font-mono text-gray-700 dark:text-gray-300 py-0.5"
              >
                {file}
              </div>
            {/each}
          </div>

          <!-- Info Banner -->
          <div
            class="mt-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-3"
          >
            <p class="text-xs text-blue-800 dark:text-blue-200">
              ℹ️ Governance changes are local until explicitly committed.
            </p>
          </div>

          <!-- Commit Button -->
          <button
            class="w-full mt-3 px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white font-medium rounded-lg transition-colors flex items-center justify-center gap-2"
            on:click={openCommitModal}
          >
            📦 Commit Governance Changes
          </button>
        {/if}
      </div>
    {/if}
  {/if}
</div>

<!-- Commit Modal -->
{#if showCommitModal}
  <div
    class="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4"
    role="button"
    tabindex="0"
    on:click={closeCommitModal}
    on:keydown={(e) => e.key === "Escape" && closeCommitModal()}
  >
    <div
      class="bg-white dark:bg-gray-800 rounded-lg shadow-2xl max-w-2xl w-full flex flex-col max-h-[80vh]"
      role="dialog"
      aria-modal="true"
      tabindex="-1"
      on:click|stopPropagation
      on:keydown|stopPropagation
    >
      <!-- Modal Header -->
      <div class="border-b border-gray-200 dark:border-gray-700 px-6 py-4">
        <div class="flex items-center justify-between">
          <div>
            <h2 class="text-2xl font-bold text-gray-900 dark:text-white">
              Commit Governance Action
            </h2>
            <p class="text-sm text-gray-600 dark:text-gray-400 mt-1">
              Create an authoritative governance record
            </p>
          </div>
          <button
            on:click={closeCommitModal}
            class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 text-2xl"
          >
            ✕
          </button>
        </div>
      </div>

      <!-- Modal Body -->
      <div class="flex-1 overflow-y-auto p-6 space-y-4">
        <!-- Warning Banner -->
        <div
          class="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg p-4"
        >
          <div class="flex items-start gap-3">
            <span class="text-2xl">⚠️</span>
            <div>
              <p class="font-semibold text-amber-900 dark:text-amber-200 mb-1">
                Governance Authority
              </p>
              <p class="text-sm text-amber-800 dark:text-amber-300">
                A commit represents an authoritative governance action. This
                creates a permanent forensic anchor in the governance history.
              </p>
            </div>
          </div>
        </div>

        <!-- Changed Files -->
        <div>
          <label
            for="commit-files"
            class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
          >
            Files to be committed ({gitStatus?.modified_files.length || 0}):
          </label>
          <div
            id="commit-files"
            class="bg-gray-50 dark:bg-gray-900 rounded border border-gray-200 dark:border-gray-700 p-3 max-h-32 overflow-y-auto"
          >
            {#each gitStatus?.modified_files || [] as file}
              <div
                class="text-sm font-mono text-gray-700 dark:text-gray-300 py-0.5"
              >
                {file}
              </div>
            {/each}
          </div>
        </div>

        <!-- Commit Message -->
        <div>
          <label
            for="commit-message"
            class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
          >
            Commit Message <span class="text-red-500">*</span>
          </label>
          <textarea
            id="commit-message"
            class="w-full h-24 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
            placeholder="Describe the governance action being recorded..."
            bind:value={commitMessage}
          ></textarea>
        </div>

        <!-- Related IDs -->
        <div>
          <label
            for="related-ids"
            class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
          >
            Related Goal / Decision IDs <span class="text-gray-500"
              >(optional)</span
            >
          </label>
          <input
            id="related-ids"
            type="text"
            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            placeholder="e.g., goal-phase-3, decision-git-integration"
            bind:value={relatedIds}
          />
          <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">
            Free text field for governance traceability
          </p>
        </div>
      </div>

      <!-- Modal Actions -->
      <div
        class="border-t border-gray-200 dark:border-gray-700 px-6 py-4 flex items-center justify-end gap-3 bg-gray-50 dark:bg-gray-900"
      >
        <button
          class="px-5 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 font-medium rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
          on:click={closeCommitModal}
          disabled={committing}
        >
          Cancel
        </button>
        <button
          class="px-5 py-2 bg-primary-600 hover:bg-primary-700 text-white font-medium rounded-lg transition-colors flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
          on:click={confirmCommit}
          disabled={committing || commitMessage.trim() === ""}
        >
          {committing ? "Committing..." : "📦 Commit"}
        </button>
      </div>
    </div>
  </div>
{/if}
