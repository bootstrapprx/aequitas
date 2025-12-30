<script lang="ts">
import { invoke } from '@tauri-apps/api/core';
import { createEventDispatcher } from 'svelte';

// Props
export let goal: any = null; // If null, we're creating a new goal
export let onClose: () => void;

const dispatch = createEventDispatcher();

// Form state
let goalId = goal?.goal_id || '';
let title = goal?.title || '';
let status = goal?.status || 'planned';
let phase = goal?.phase || '';
let owner = goal?.owner || '';
let dependencies = goal?.dependencies?.join(', ') || '';
let canon = goal?.canon?.join(', ') || '';
let tags = goal?.tags?.join(', ') || '';
let content = goal?.content || '';

// UI state
let showPreview = false;
let saving = false;
let error = '';
let validationErrors: Record<string, string> = {};

// Available statuses
const statuses = [
  { value: 'planned', label: 'Planned', color: 'text-cyan-400' },
  { value: 'active', label: 'Active', color: 'text-green-400' },
  { value: 'blocked', label: 'Blocked', color: 'text-red-400' },
  { value: 'partial', label: 'Partial', color: 'text-yellow-400' },
  { value: 'done', label: 'Done', color: 'text-blue-400' },
  { value: 'archived', label: 'Archived', color: 'text-gray-400' }
];

const isEditMode = !!goal;
const initialStatus = goal?.status || 'planned';

// Validation
function validate(): boolean {
  validationErrors = {};

  if (!goalId.trim()) {
    validationErrors.goalId = 'Goal ID is required';
  } else if (!/^[A-Za-z0-9-_]+$/.test(goalId)) {
    validationErrors.goalId = 'Goal ID can only contain letters, numbers, hyphens, and underscores';
  }

  if (!title.trim()) {
    validationErrors.title = 'Title is required';
  }

  if (!content.trim()) {
    validationErrors.content = 'Content is required';
  }

  return Object.keys(validationErrors).length === 0;
}

// Parse comma-separated lists
function parseList(str: string): string[] {
  return str.split(',').map(s => s.trim()).filter(s => s.length > 0);
}

// Save goal
async function handleSave() {
  if (!validate()) {
    return;
  }

  saving = true;
  error = '';

  try {
    if (isEditMode && status !== initialStatus) {
      const ok = confirm(`Change status from "${initialStatus}" to "${status}"?`);
      if (!ok) {
        saving = false;
        return;
      }
    }

    if (isEditMode) {
      // Update existing goal
      await invoke('update_goal', {
        goalId: goalId,
        request: {
          title: title.trim(),
          status,
          phase: phase.trim() || null,
          owner: owner.trim() || null,
          dependencies: parseList(dependencies),
          canon: parseList(canon),
          tags: tags.trim(),
          content: content.trim()
        }
      });
    } else {
      // Create new goal
      await invoke('create_goal', {
        request: {
          goal_id: goalId.trim(),
          title: title.trim(),
          status,
          phase: phase.trim() || null,
          owner: owner.trim() || null,
          dependencies: parseList(dependencies),
          canon: parseList(canon),
          tags: parseList(tags),
          content: content.trim()
        }
      });
    }

    dispatch('saved', { goalId });
    onClose();
  } catch (err: any) {
    error = err.toString();
  } finally {
    saving = false;
  }
}

// Delete goal
async function handleDelete() {
  if (!confirm(`Are you sure you want to delete goal "${goalId}"?`)) {
    return;
  }

  saving = true;
  error = '';

  try {
    await invoke('delete_goal', { goalId });
    dispatch('deleted', { goalId });
    onClose();
  } catch (err: any) {
    error = err.toString();
  } finally {
    saving = false;
  }
}

// Render markdown preview (simple version)
function renderMarkdown(text: string): string {
  // Basic markdown rendering - replace with proper library if needed
  return text
    .split('\n')
    .map(line => {
      if (line.startsWith('# ')) return `<h1 class="text-2xl font-bold mt-4 mb-2">${line.slice(2)}</h1>`;
      if (line.startsWith('## ')) return `<h2 class="text-xl font-bold mt-3 mb-2">${line.slice(3)}</h2>`;
      if (line.startsWith('### ')) return `<h3 class="text-lg font-bold mt-2 mb-1">${line.slice(4)}</h3>`;
      if (line.startsWith('- ')) return `<li class="ml-4">${line.slice(2)}</li>`;
      if (line.trim() === '') return '<br/>';
      return `<p class="mb-2">${line}</p>`;
    })
    .join('\n');
}
</script>

<div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
  <div class="bg-gray-800 rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
    <!-- Header -->
    <div class="bg-gray-900 px-6 py-4 border-b border-gray-700 flex items-center justify-between">
      <h2 class="text-xl font-bold text-white">
        {isEditMode ? 'Edit Goal' : 'New Goal'}
      </h2>
      <button
        on:click={onClose}
        class="text-gray-400 hover:text-white transition-colors"
        aria-label="Close"
      >
        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
        </svg>
      </button>
    </div>

    <!-- Error message -->
    {#if error}
      <div class="bg-red-900 bg-opacity-50 text-red-200 px-6 py-3 border-b border-red-700">
        <strong>Error:</strong> {error}
      </div>
    {/if}

    <!-- Form content -->
    <div class="flex-1 overflow-y-auto px-6 py-4">
      <div class="space-y-4">
        <!-- Goal ID -->
        <div>
          <label class="block text-sm font-medium text-gray-300 mb-1">
            Goal ID <span class="text-red-400">*</span>
          </label>
          <input
            type="text"
            bind:value={goalId}
            disabled={isEditMode}
            class="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
            placeholder="e.g., G-101 or goal-authentication"
          />
          {#if validationErrors.goalId}
            <p class="text-red-400 text-sm mt-1">{validationErrors.goalId}</p>
          {/if}
          {#if !isEditMode}
            <p class="text-gray-400 text-sm mt-1">Unique identifier for this goal (cannot be changed after creation)</p>
          {/if}
        </div>

        <!-- Title -->
        <div>
          <label class="block text-sm font-medium text-gray-300 mb-1">
            Title <span class="text-red-400">*</span>
          </label>
          <input
            type="text"
            bind:value={title}
            class="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Brief descriptive title"
          />
          {#if validationErrors.title}
            <p class="text-red-400 text-sm mt-1">{validationErrors.title}</p>
          {/if}
        </div>

        <!-- Status and Phase (side by side) -->
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-300 mb-1">
              Status <span class="text-red-400">*</span>
            </label>
            <select
              bind:value={status}
              class="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {#each statuses as s}
                <option value={s.value}>{s.label}</option>
              {/each}
            </select>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-300 mb-1">
              Phase
            </label>
            <input
              type="text"
              bind:value={phase}
              class="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="e.g., phase_1"
            />
          </div>
        </div>

        <!-- Owner -->
        <div>
          <label class="block text-sm font-medium text-gray-300 mb-1">
            Owner
          </label>
          <input
            type="text"
            bind:value={owner}
            class="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Team or person responsible"
          />
        </div>

        <!-- Dependencies -->
        <div>
          <label class="block text-sm font-medium text-gray-300 mb-1">
            Dependencies
          </label>
          <input
            type="text"
            bind:value={dependencies}
            class="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Comma-separated goal IDs (e.g., G-100, G-101)"
          />
          <p class="text-gray-400 text-sm mt-1">Goals that must be completed before this one</p>
        </div>

        <!-- Canon References -->
        <div>
          <label class="block text-sm font-medium text-gray-300 mb-1">
            Canon References
          </label>
          <input
            type="text"
            bind:value={canon}
            class="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Comma-separated references"
          />
          <p class="text-gray-400 text-sm mt-1">Related canonical documents or sources</p>
        </div>

        <!-- Tags -->
        <div>
          <label class="block text-sm font-medium text-gray-300 mb-1">
            Tags
          </label>
          <input
            type="text"
            bind:value={tags}
            class="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Comma-separated tags (e.g., backend, security, phase-1)"
          />
        </div>

        <!-- Content with Preview Toggle -->
        <div>
          <div class="flex items-center justify-between mb-1">
            <label class="block text-sm font-medium text-gray-300">
              Content <span class="text-red-400">*</span>
            </label>
            <button
              type="button"
              on:click={() => showPreview = !showPreview}
              class="text-sm text-blue-400 hover:text-blue-300 transition-colors"
            >
              {showPreview ? 'Edit' : 'Preview'}
            </button>
          </div>

          {#if showPreview}
            <div class="w-full min-h-[200px] px-3 py-2 bg-gray-900 border border-gray-600 rounded text-white overflow-auto prose prose-invert max-w-none">
              {@html renderMarkdown(content)}
            </div>
          {:else}
            <textarea
              bind:value={content}
              rows="12"
              class="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
              placeholder="Markdown content describing the goal, implementation plan, acceptance criteria, etc."
            ></textarea>
          {/if}

          {#if validationErrors.content}
            <p class="text-red-400 text-sm mt-1">{validationErrors.content}</p>
          {/if}
          <p class="text-gray-400 text-sm mt-1">Supports markdown formatting</p>
        </div>
      </div>
    </div>

    <!-- Footer -->
    <div class="bg-gray-900 px-6 py-4 border-t border-gray-700 flex items-center justify-between">
      <div>
        {#if isEditMode}
          <button
            type="button"
            on:click={handleDelete}
            disabled={saving}
            class="px-4 py-2 bg-red-600 hover:bg-red-700 disabled:bg-red-800 disabled:cursor-not-allowed text-white rounded transition-colors"
          >
            Delete Goal
          </button>
        {/if}
      </div>

      <div class="flex gap-3">
        <button
          type="button"
          on:click={onClose}
          disabled={saving}
          class="px-4 py-2 bg-gray-700 hover:bg-gray-600 disabled:bg-gray-800 disabled:cursor-not-allowed text-white rounded transition-colors"
        >
          Cancel
        </button>
        <button
          type="button"
          on:click={handleSave}
          disabled={saving}
          class="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-800 disabled:cursor-not-allowed text-white rounded transition-colors flex items-center gap-2"
        >
          {#if saving}
            <svg class="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            Saving...
          {:else}
            {isEditMode ? 'Save Changes' : 'Create Goal'}
          {/if}
        </button>
      </div>
    </div>
  </div>
</div>
