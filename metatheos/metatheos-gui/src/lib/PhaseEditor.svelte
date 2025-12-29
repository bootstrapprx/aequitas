<script lang="ts">
import { invoke } from '@tauri-apps/api/core';
import { createEventDispatcher } from 'svelte';

// Props
export let phase: any = null; // If null, we're creating a new phase
export let onClose: () => void;

const dispatch = createEventDispatcher();

// Form state
let phaseId = phase?.phase_id || '';
let title = phase?.title || '';
let status = phase?.status || 'planned';
let startDate = phase?.start_date || '';
let targetDate = phase?.target_date || '';
let dependencies = phase?.dependencies?.join(', ') || '';
let content = phase?.content || '';

// UI state
let showPreview = false;
let saving = false;
let error = '';
let validationErrors: Record<string, string> = {};

// Available statuses
const statuses = [
  { value: 'planned', label: 'Planned' },
  { value: 'active', label: 'Active' },
  { value: 'inactive', label: 'Inactive' },
  { value: 'completed', label: 'Completed' },
  { value: 'archived', label: 'Archived' }
];

const isEditMode = !!phase;
const canActivate = isEditMode && status !== 'active';

// Validation
function validate(): boolean {
  validationErrors = {};

  if (!phaseId.trim()) {
    validationErrors.phaseId = 'Phase ID is required';
  } else if (!/^[A-Za-z0-9-_]+$/.test(phaseId)) {
    validationErrors.phaseId = 'Phase ID can only contain letters, numbers, hyphens, and underscores';
  }

  if (!title.trim()) {
    validationErrors.title = 'Title is required';
  }

  // Validate dates if provided
  if (startDate && targetDate) {
    const start = new Date(startDate);
    const target = new Date(targetDate);
    if (target < start) {
      validationErrors.targetDate = 'Target date must be after start date';
    }
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

// Save phase
async function handleSave() {
  if (!validate()) {
    return;
  }

  saving = true;
  error = '';

  try {
    if (isEditMode) {
      // Update existing phase
      await invoke('update_phase', {
        phaseId: phaseId,
        request: {
          title: title.trim(),
          status,
          start_date: startDate || null,
          target_date: targetDate || null,
          dependencies: parseList(dependencies),
          content: content.trim()
        }
      });
    } else {
      // Create new phase
      await invoke('create_phase', {
        request: {
          phase_id: phaseId.trim(),
          title: title.trim(),
          status,
          start_date: startDate || null,
          target_date: targetDate || null,
          dependencies: parseList(dependencies),
          content: content.trim()
        }
      });
    }

    dispatch('saved', { phaseId });
    onClose();
  } catch (err: any) {
    error = err.toString();
  } finally {
    saving = false;
  }
}

// Activate phase
async function handleActivate() {
  if (!confirm(`Set "${title}" as the active phase?`)) {
    return;
  }

  saving = true;
  error = '';

  try {
    await invoke('set_active_phase', { phaseId });
    dispatch('activated', { phaseId });
    onClose();
  } catch (err: any) {
    error = err.toString();
  } finally {
    saving = false;
  }
}

// Render markdown preview (simple version)
function renderMarkdown(text: string): string {
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

// Format date for input (YYYY-MM-DD)
function formatDateForInput(dateStr: string): string {
  if (!dateStr) return '';
  try {
    const date = new Date(dateStr);
    return date.toISOString().split('T')[0];
  } catch {
    return dateStr;
  }
}

// Initialize date inputs with proper format
$: if (phase) {
  startDate = formatDateForInput(phase.start_date);
  targetDate = formatDateForInput(phase.target_date);
}
</script>

<div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
  <div class="bg-gray-800 rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
    <!-- Header -->
    <div class="bg-gray-900 px-6 py-4 border-b border-gray-700 flex items-center justify-between">
      <h2 class="text-xl font-bold text-white">
        {isEditMode ? 'Edit Phase' : 'New Phase'}
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
        <!-- Phase ID -->
        <div>
          <label class="block text-sm font-medium text-gray-300 mb-1">
            Phase ID <span class="text-red-400">*</span>
          </label>
          <input
            type="text"
            bind:value={phaseId}
            disabled={isEditMode}
            class="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
            placeholder="e.g., phase_1 or foundation-phase"
          />
          {#if validationErrors.phaseId}
            <p class="text-red-400 text-sm mt-1">{validationErrors.phaseId}</p>
          {/if}
          {#if !isEditMode}
            <p class="text-gray-400 text-sm mt-1">Unique identifier for this phase (cannot be changed after creation)</p>
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

        <!-- Status -->
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
          <p class="text-gray-400 text-sm mt-1">
            Note: Use "Activate" button to set as active phase (deactivates other phases)
          </p>
        </div>

        <!-- Dates (side by side) -->
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-300 mb-1">
              Start Date
            </label>
            <input
              type="date"
              bind:value={startDate}
              class="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-300 mb-1">
              Target Date
            </label>
            <input
              type="date"
              bind:value={targetDate}
              class="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            {#if validationErrors.targetDate}
              <p class="text-red-400 text-sm mt-1">{validationErrors.targetDate}</p>
            {/if}
          </div>
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
            placeholder="Comma-separated phase IDs (e.g., phase_1, phase_2)"
          />
          <p class="text-gray-400 text-sm mt-1">Phases that must be completed before this one</p>
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
              placeholder="Markdown content describing the phase objectives, deliverables, timeline, etc."
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
        {#if canActivate}
          <button
            type="button"
            on:click={handleActivate}
            disabled={saving}
            class="px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-green-800 disabled:cursor-not-allowed text-white rounded transition-colors flex items-center gap-2"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
            </svg>
            Activate Phase
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
            {isEditMode ? 'Save Changes' : 'Create Phase'}
          {/if}
        </button>
      </div>
    </div>
  </div>
</div>
