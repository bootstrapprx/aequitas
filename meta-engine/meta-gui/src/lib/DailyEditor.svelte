<script>
  import { invoke } from '@tauri-apps/api/core'
  import { onMount } from 'svelte'
  import Toast from './Toast.svelte'

  const todayIso = new Date().toISOString().split('T')[0]

  let devMode = false
  let loading = true
  let saving = false
  let autosaveStatus = ''
  let selectedDate = todayIso
  let dailyList = []

  let mode = ''
  let protocol = ''
  let goalsText = ''
  let blockersText = ''
  let decisionsText = ''
  let divergencesText = ''
  let content = ''

  let toastShow = false
  let toastMessage = ''
  let toastType = 'success'

  let autosaveTimer

  const modeOptions = [
    { value: '', label: 'Unspecified' },
    { value: 'light', label: 'Light Day' },
    { value: 'heavy', label: 'Heavy Day' },
    { value: 'review', label: 'Review Day' },
  ]

  const tauriAvailable = () => {
    if (typeof window === 'undefined') return false
    return Boolean(
      window.__TAURI__ ||
        window.__TAURI_IPC__ ||
        window.__TAURI_INTERNALS__
    )
  }

  onMount(async () => {
    if (!tauriAvailable()) {
      devMode = true
      loading = false
      return
    }
    await loadDailyList()
  })

  async function loadDailyList() {
    try {
      loading = true
      dailyList = await invoke('list_daily_notes')

      if (dailyList.length > 0 && !dailyList.find(d => d.date === selectedDate)) {
        selectedDate = dailyList[0].date
      }
      await loadNote(selectedDate)
    } catch (err) {
      showError(err)
    } finally {
      loading = false
    }
  }

  async function loadNote(date) {
    if (devMode) return
    try {
      loading = true
      const note = await invoke('get_daily_note', { date })
      if (note) {
        mode = note.mode || ''
        protocol = note.protocol || ''
        goalsText = (note.goals || []).join('\n')
        blockersText = (note.blockers || []).join('\n')
        decisionsText = (note.decisions || []).join('\n')
        divergencesText = (note.divergences || []).join('\n')
        content = note.content || ''
      } else {
        mode = ''
        protocol = ''
        goalsText = ''
        blockersText = ''
        decisionsText = ''
        divergencesText = ''
        content = ''
      }
      autosaveStatus = ''
    } catch (err) {
      showError(err)
    } finally {
      loading = false
    }
  }

  function toList(text) {
    return text
      .split('\n')
      .map(s => s.trim())
      .filter(Boolean)
  }

  function scheduleAutosave() {
    if (devMode) return
    clearTimeout(autosaveTimer)
    autosaveStatus = 'Saving…'
    autosaveTimer = setTimeout(() => saveDaily(false), 800)
  }

  async function saveDaily(showToast = true) {
    if (devMode) return
    try {
      saving = true
      await invoke('update_daily_note', {
        payload: {
          date: selectedDate,
          mode: mode || null,
          protocol: protocol || null,
          goals: toList(goalsText),
          blockers: toList(blockersText),
          decisions: toList(decisionsText),
          divergences: toList(divergencesText),
          content,
        },
      })
      autosaveStatus = 'Saved'
      if (showToast) {
        toastMessage = 'Daily note saved'
        toastType = 'success'
        toastShow = true
      }
      await loadDailyList()
    } catch (err) {
      autosaveStatus = 'Error'
      showError(err)
    } finally {
      saving = false
    }
  }

  function showError(err) {
    toastMessage = err?.toString?.() ?? String(err)
    toastType = 'error'
    toastShow = true
  }

  function onDateChange(newDate) {
    selectedDate = newDate
    loadNote(selectedDate)
  }

  function createIfMissing() {
    // Saving will create if missing because the backend ensures the file exists.
    saveDaily(true)
  }
</script>

<div>
  <div class="flex items-center justify-between mb-6">
    <div>
      <h2 class="text-3xl font-bold text-gray-900 dark:text-white">Daily Editor</h2>
      <p class="text-sm text-gray-500 dark:text-gray-400">
        Real-time editing of daily notes in governance/01_DAILY
      </p>
    </div>
    <div class="flex items-center gap-3">
      <div class="text-xs text-gray-500 dark:text-gray-400">
        {autosaveStatus}
      </div>
      <button class="btn btn-primary" on:click={() => saveDaily(true)} disabled={devMode || saving}>
        {saving ? 'Saving…' : 'Save now'}
      </button>
    </div>
  </div>

  {#if devMode}
    <div class="card mb-6 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800">
      <h3 class="text-lg font-semibold text-yellow-800 dark:text-yellow-200 mb-2">Tauri not detected</h3>
      <p class="text-yellow-700 dark:text-yellow-200 text-sm">
        Run <code>cargo tauri dev</code> to edit daily notes from this UI.
      </p>
    </div>
  {/if}

  {#if loading}
    <div class="card">
      <p class="text-gray-500 dark:text-gray-400">Loading daily notes…</p>
    </div>
  {:else}
    <div class="card mb-4">
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div class="flex flex-col gap-2">
          <label class="text-sm text-gray-500 dark:text-gray-400">Date</label>
          <input
            type="date"
            bind:value={selectedDate}
            class="px-3 py-2 rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            on:change={(e) => onDateChange(e.target.value)}
          />
        </div>
        <div class="flex flex-col gap-2">
          <label class="text-sm text-gray-500 dark:text-gray-400">Mode</label>
          <select
            class="px-3 py-2 rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            bind:value={mode}
            on:change={scheduleAutosave}
          >
            {#each modeOptions as option}
              <option value={option.value}>{option.label}</option>
            {/each}
          </select>
        </div>
        <div class="flex flex-col gap-2">
          <label class="text-sm text-gray-500 dark:text-gray-400">Protocol (optional)</label>
          <input
            type="text"
            bind:value={protocol}
            class="px-3 py-2 rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            on:input={scheduleAutosave}
            placeholder="e.g., LIGHT_DAY_PROTOCOL"
          />
        </div>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mt-4">
        <div class="flex flex-col gap-2 md:col-span-2">
          <label class="text-sm text-gray-500 dark:text-gray-400">Goals (one per line)</label>
          <textarea
            rows="6"
            bind:value={goalsText}
            class="w-full px-3 py-2 rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm"
            on:input={scheduleAutosave}
          />
        </div>
        <div class="flex flex-col gap-2">
          <label class="text-sm text-gray-500 dark:text-gray-400">Blockers</label>
          <textarea
            rows="6"
            bind:value={blockersText}
            class="w-full px-3 py-2 rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm"
            on:input={scheduleAutosave}
          />
        </div>
        <div class="flex flex-col gap-2">
          <label class="text-sm text-gray-500 dark:text-gray-400">Decisions</label>
          <textarea
            rows="6"
            bind:value={decisionsText}
            class="w-full px-3 py-2 rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm"
            on:input={scheduleAutosave}
          />
        </div>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
        <div class="flex flex-col gap-2">
          <label class="text-sm text-gray-500 dark:text-gray-400">Divergences</label>
          <textarea
            rows="4"
            bind:value={divergencesText}
            class="w-full px-3 py-2 rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm"
            on:input={scheduleAutosave}
          />
        </div>
        <div class="flex flex-col gap-2">
          <label class="text-sm text-gray-500 dark:text-gray-400">Existing note</label>
          <div class="text-xs text-gray-600 dark:text-gray-400">
            {#if dailyList.length > 0}
              {#each dailyList.slice(0, 5) as note}
                <div class="flex justify-between">
                  <span>{note.date}</span>
                  <span class="text-gray-500">{note.mode || '–'}</span>
                </div>
              {/each}
            {:else}
              No daily notes found yet.
            {/if}
          </div>
        </div>
      </div>

      <div class="flex flex-col gap-2 mt-4">
        <label class="text-sm text-gray-500 dark:text-gray-400">Body (markdown)</label>
        <textarea
          rows="10"
          bind:value={content}
          class="w-full px-3 py-2 rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm font-mono"
          on:input={scheduleAutosave}
        />
      </div>

      <div class="flex justify-end gap-3 mt-4">
        <button class="btn btn-secondary" on:click={createIfMissing} disabled={devMode || saving}>
          Create if missing
        </button>
        <button class="btn btn-primary" on:click={() => saveDaily(true)} disabled={devMode || saving}>
          {saving ? 'Saving…' : 'Save'}
        </button>
      </div>
    </div>
  {/if}
</div>

<Toast bind:show={toastShow} message={toastMessage} type={toastType} />
