<script>
  import { invoke } from '@tauri-apps/api/core'
  import { onMount } from 'svelte'
  import Toast from './Toast.svelte'

  let loading = true
  let error = null
  let devMode = false

  let governanceTree = null
  let selectedFile = null
  let fileContent = ''
  let fileBacklinks = null
  let expandedFolders = new Set()

  let toastShow = false
  let toastMessage = ''
  let toastType = 'success'

  // View mode: 'tree', 'content', 'split', 'edit'
  let viewMode = 'split'
  let editingFile = null
  let editedContent = ''
  let showPreviewModal = false
  let previewDiff = []

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
    await loadGovernanceTree()
  })

  async function loadGovernanceTree() {
    try {
      loading = true
      governanceTree = await invoke('get_governance_tree')

      // Auto-expand governance folders
      if (governanceTree && governanceTree.children) {
        governanceTree.children.forEach(child => {
          if (child.is_directory) {
            expandedFolders.add(child.path)
          }
        })
      }

      error = null
    } catch (err) {
      error = err?.toString?.() ?? String(err)
    } finally {
      loading = false
    }
  }

  async function selectFile(file) {
    if (file.is_directory) {
      toggleFolder(file.path)
      return
    }

    selectedFile = file

    try {
      // Load file content
      fileContent = await invoke('get_file_content', { filePath: file.path })

      // Load backlinks
      fileBacklinks = await invoke('get_file_backlinks', { filePath: file.path })
    } catch (err) {
      showToast(`Failed to load file: ${err}`, 'error')
    }
  }

  function toggleFolder(path) {
    if (expandedFolders.has(path)) {
      expandedFolders.delete(path)
    } else {
      expandedFolders.add(path)
    }
    expandedFolders = expandedFolders // Trigger reactivity
  }

  function getFileIcon(fileType) {
    switch (fileType) {
      case 'Canon':
        return '🧠'
      case 'Goal':
        return '🎯'
      case 'Phase':
        return '🧭'
      case 'Decision':
        return '⚖'
      case 'Audit':
        return '🧪'
      case 'Prompt':
        return '💡'
      case 'Daily':
        return '📝'
      case 'Archive':
        return '📦'
      case 'Constitution':
        return '📜'
      case 'Directory':
        return '📁'
      default:
        return '📄'
    }
  }

  function getBadgeClass(fileType, isWritable) {
    if (!isWritable) {
      return 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300'
    }

    switch (fileType) {
      case 'Canon':
      case 'Constitution':
        return 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300'
      case 'Goal':
        return 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300'
      case 'Phase':
        return 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300'
      case 'Decision':
        return 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-300'
      case 'Audit':
        return 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-300'
      case 'Prompt':
        return 'bg-pink-100 text-pink-700 dark:bg-pink-900/30 dark:text-pink-300'
      case 'Daily':
        return 'bg-teal-100 text-teal-700 dark:bg-teal-900/30 dark:text-teal-300'
      default:
        return 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300'
    }
  }

  function formatFileSize(bytes) {
    if (!bytes) return ''
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  function formatDate(isoString) {
    if (!isoString) return ''
    try {
      return new Date(isoString).toLocaleString()
    } catch {
      return isoString
    }
  }

  function showToast(message, type = 'success') {
    toastMessage = message
    toastType = type
    toastShow = true
  }

  function renderMarkdown(content) {
    // Strip frontmatter for display
    let body = content
    if (content.startsWith('---\n')) {
      const parts = content.split('\n---\n')
      if (parts.length > 1) {
        body = parts.slice(1).join('\n---\n').trim()
      }
    }
    return body
  }

  function startEditing() {
    if (!selectedFile || !selectedFile.is_writable) {
      showToast('This file is read-only and cannot be edited', 'error')
      return
    }
    editingFile = selectedFile
    editedContent = fileContent
    viewMode = 'edit'
  }

  function cancelEditing() {
    editingFile = null
    editedContent = ''
    viewMode = 'split'
  }

  function openPreview() {
    if (!editingFile || editedContent === fileContent) {
      showToast('No changes detected', 'info')
      return
    }

    // Generate simple line-by-line diff
    const oldLines = fileContent.split('\n')
    const newLines = editedContent.split('\n')
    const maxLen = Math.max(oldLines.length, newLines.length)

    previewDiff = []
    for (let i = 0; i < maxLen; i++) {
      const oldLine = oldLines[i] ?? ''
      const newLine = newLines[i] ?? ''

      if (oldLine !== newLine) {
        if (oldLine && !newLine) {
          previewDiff.push({ type: 'remove', line: i + 1, content: oldLine })
        } else if (!oldLine && newLine) {
          previewDiff.push({ type: 'add', line: i + 1, content: newLine })
        } else {
          previewDiff.push({ type: 'remove', line: i + 1, content: oldLine })
          previewDiff.push({ type: 'add', line: i + 1, content: newLine })
        }
      } else {
        previewDiff.push({ type: 'context', line: i + 1, content: oldLine })
      }
    }

    showPreviewModal = true
  }

  function closePreview() {
    showPreviewModal = false
    previewDiff = []
  }

  async function confirmWrite() {
    try {
      const result = await invoke('safe_write_file', {
        filePath: editingFile.path,
        newContent: editedContent
      })

      showToast(result, 'success')

      // Refresh file content to match what was written
      fileContent = editedContent

      // Close modals and exit edit mode
      closePreview()
      cancelEditing()

      // Reload the file to get fresh metadata
      await selectFile(editingFile)

    } catch (err) {
      showToast(`Write failed: ${err}`, 'error')
    }
  }
</script>

<div class="h-screen flex flex-col bg-gray-50 dark:bg-gray-900">
  <Toast bind:show={toastShow} message={toastMessage} type={toastType} />

  <!-- Header -->
  <div class="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6 py-4">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Governance Explorer</h1>
        <p class="text-sm text-gray-600 dark:text-gray-400 mt-1">
          Phase 2 — Safe Edit Mode · Navigate and edit with governance safeguards
        </p>
      </div>
      <div class="flex items-center gap-2">
        <button
          class="px-3 py-1 text-sm rounded {viewMode === 'tree' ? 'bg-primary-600 text-white' : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300'}"
          on:click={() => viewMode = 'tree'}
        >
          Tree Only
        </button>
        <button
          class="px-3 py-1 text-sm rounded {viewMode === 'split' ? 'bg-primary-600 text-white' : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300'}"
          on:click={() => viewMode = 'split'}
        >
          Split View
        </button>
        <button
          class="px-3 py-1 text-sm rounded {viewMode === 'content' ? 'bg-primary-600 text-white' : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300'}"
          on:click={() => viewMode = 'content'}
        >
          Content Only
        </button>
      </div>
    </div>
  </div>

  {#if devMode}
    <div class="m-4 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
      <p class="text-yellow-800 dark:text-yellow-200">
        🔧 Development Mode — Tauri not available. Run with <code class="bg-yellow-100 dark:bg-yellow-800 px-1 rounded">cargo tauri dev</code>
      </p>
    </div>
  {/if}

  {#if error}
    <div class="m-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
      <p class="text-red-800 dark:text-red-200 font-medium">Error loading governance tree:</p>
      <p class="text-red-700 dark:text-red-300 mt-1">{error}</p>
    </div>
  {/if}

  <!-- Main Content Area -->
  <div class="flex-1 flex overflow-hidden">
    {#if loading}
      <div class="flex-1 flex items-center justify-center">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    {:else}
      <!-- Tree View -->
      {#if viewMode === 'tree' || viewMode === 'split'}
        <div class="w-full {viewMode === 'split' ? 'md:w-1/3' : ''} border-r border-gray-200 dark:border-gray-700 overflow-y-auto bg-white dark:bg-gray-800">
          {#if governanceTree}
            <div class="p-4">
              <FileTreeNode node={governanceTree} {expandedFolders} {selectFile} {selectedFile} level={0} />
            </div>
          {:else}
            <p class="p-4 text-gray-500 dark:text-gray-400">No governance data found</p>
          {/if}
        </div>
      {/if}

      <!-- Content View -->
      {#if (viewMode === 'content' || viewMode === 'split') && selectedFile}
        <div class="flex-1 overflow-y-auto bg-white dark:bg-gray-800 p-6">
          <!-- File Header -->
          <div class="mb-6 pb-4 border-b border-gray-200 dark:border-gray-700">
            <div class="flex items-start justify-between mb-3">
              <div class="flex items-center gap-3">
                <span class="text-3xl">{getFileIcon(selectedFile.file_type)}</span>
                <div>
                  <h2 class="text-2xl font-bold text-gray-900 dark:text-white">{selectedFile.name}</h2>
                  <p class="text-sm text-gray-500 dark:text-gray-400 font-mono mt-1">{selectedFile.path}</p>
                </div>
              </div>
              <div class="flex items-center gap-3">
                <div class="flex flex-col items-end gap-2">
                  <span class="px-3 py-1 text-xs font-semibold rounded {getBadgeClass(selectedFile.file_type, selectedFile.is_writable)}">
                    {selectedFile.file_type}
                    {#if !selectedFile.is_writable}
                      🔒 READ-ONLY
                    {/if}
                  </span>
                  {#if selectedFile.size}
                    <span class="text-xs text-gray-500 dark:text-gray-400">{formatFileSize(selectedFile.size)}</span>
                  {/if}
                </div>
                {#if selectedFile.is_writable}
                  <button
                    class="px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white font-medium rounded-lg transition-colors flex items-center gap-2"
                    on:click={startEditing}
                  >
                    ✏️ Safe Edit
                  </button>
                {/if}
              </div>
            </div>

            {#if selectedFile.modified}
              <p class="text-xs text-gray-500 dark:text-gray-400">
                Modified: {formatDate(selectedFile.modified)}
              </p>
            {/if}
          </div>

          <!-- Frontmatter Panel -->
          {#if selectedFile.frontmatter && Object.keys(selectedFile.frontmatter).length > 0}
            <div class="mb-6">
              <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-3">Frontmatter</h3>
              <div class="bg-gray-50 dark:bg-gray-900 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
                <pre class="text-sm text-gray-800 dark:text-gray-200 whitespace-pre-wrap">{JSON.stringify(selectedFile.frontmatter, null, 2)}</pre>
              </div>
            </div>
          {/if}

          <!-- Backlinks Panel -->
          {#if fileBacklinks}
            <div class="mb-6">
              <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-3">References</h3>
              <div class="grid grid-cols-2 gap-4">
                <!-- Forward Links -->
                <div>
                  <h4 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Forward Links ({fileBacklinks.forward_links.length})
                  </h4>
                  {#if fileBacklinks.forward_links.length === 0}
                    <p class="text-sm text-gray-500 dark:text-gray-400 italic">None</p>
                  {:else}
                    <div class="space-y-1">
                      {#each fileBacklinks.forward_links as link}
                        <div class="text-sm bg-blue-50 dark:bg-blue-900/20 px-2 py-1 rounded text-blue-700 dark:text-blue-300">
                          → {link}
                        </div>
                      {/each}
                    </div>
                  {/if}
                </div>

                <!-- Backlinks -->
                <div>
                  <h4 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Referenced By ({fileBacklinks.backlinks.length})
                  </h4>
                  {#if fileBacklinks.backlinks.length === 0}
                    <p class="text-sm text-gray-500 dark:text-gray-400 italic">None</p>
                  {:else}
                    <div class="space-y-1">
                      {#each fileBacklinks.backlinks.slice(0, 10) as backlink}
                        <div class="text-sm bg-green-50 dark:bg-green-900/20 px-2 py-1 rounded text-green-700 dark:text-green-300 truncate">
                          ← {backlink.split('/').pop()}
                        </div>
                      {/each}
                      {#if fileBacklinks.backlinks.length > 10}
                        <p class="text-xs text-gray-500 dark:text-gray-400">
                          +{fileBacklinks.backlinks.length - 10} more
                        </p>
                      {/if}
                    </div>
                  {/if}
                </div>
              </div>
            </div>
          {/if}

          <!-- Content Panel -->
          <div>
            <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-3">Content</h3>
            <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
              <pre class="text-sm text-gray-800 dark:text-gray-200 whitespace-pre-wrap leading-relaxed">{renderMarkdown(fileContent)}</pre>
            </div>
          </div>
        </div>
      {:else if viewMode === 'content' || viewMode === 'split'}
        <div class="flex-1 flex items-center justify-center text-gray-500 dark:text-gray-400">
          <div class="text-center">
            <p class="text-lg mb-2">No file selected</p>
            <p class="text-sm">Select a file from the tree view to view its content</p>
          </div>
        </div>
      {/if}

      <!-- Edit View -->
      {#if viewMode === 'edit' && editingFile}
        <div class="flex-1 flex flex-col bg-white dark:bg-gray-800">
          <!-- Edit Header -->
          <div class="border-b border-gray-200 dark:border-gray-700 px-6 py-4">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-3">
                <span class="text-2xl">{getFileIcon(editingFile.file_type)}</span>
                <div>
                  <h2 class="text-xl font-bold text-gray-900 dark:text-white">Editing: {editingFile.name}</h2>
                  <p class="text-xs text-gray-500 dark:text-gray-400 font-mono mt-1">{editingFile.path}</p>
                </div>
              </div>
              <div class="flex items-center gap-2">
                <button
                  class="px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 font-medium rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
                  on:click={cancelEditing}
                >
                  Cancel
                </button>
                <button
                  class="px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white font-medium rounded-lg transition-colors flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                  on:click={openPreview}
                  disabled={editedContent === fileContent}
                >
                  👁️ Preview Changes
                </button>
              </div>
            </div>
            <div class="mt-3 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg p-3">
              <p class="text-sm text-amber-800 dark:text-amber-200">
                ⚠️ <strong>Governance Safeguard:</strong> All changes require preview and confirmation before writing to disk. Canon and Constitution files are permanently read-only.
              </p>
            </div>
          </div>

          <!-- Editor Area -->
          <div class="flex-1 p-6 overflow-hidden">
            <textarea
              class="w-full h-full font-mono text-sm bg-white dark:bg-gray-900 border border-gray-300 dark:border-gray-700 rounded-lg p-4 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
              bind:value={editedContent}
              placeholder="Edit file content..."
            ></textarea>
          </div>
        </div>
      {/if}
    {/if}
  </div>
</div>

<!-- File Tree Node Component -->
{#snippet FileTreeNode({ node, expandedFolders, selectFile, selectedFile, level })}
  {@const isExpanded = expandedFolders.has(node.path)}
  {@const isSelected = selectedFile?.path === node.path}

  <div class="mb-1">
    <button
      class="w-full text-left px-2 py-1 rounded flex items-center gap-2 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors {isSelected ? 'bg-primary-50 dark:bg-primary-900/20' : ''}"
      style="padding-left: {level * 16 + 8}px"
      on:click={() => selectFile(node)}
    >
      {#if node.is_directory}
        <span class="text-gray-500 dark:text-gray-400 text-xs">
          {isExpanded ? '▼' : '▶'}
        </span>
      {:else}
        <span class="w-3"></span>
      {/if}

      <span class="text-lg">{getFileIcon(node.file_type)}</span>

      <span class="flex-1 text-sm font-medium text-gray-900 dark:text-white truncate">
        {node.name}
      </span>

      {#if !node.is_writable && !node.is_directory}
        <span class="text-xs text-red-600 dark:text-red-400">🔒</span>
      {/if}
    </button>

    {#if node.is_directory && isExpanded && node.children}
      {#each node.children as child}
        <FileTreeNode node={child} {expandedFolders} {selectFile} {selectedFile} level={level + 1} />
      {/each}
    {/if}
  </div>
{/snippet}

<!-- Write Preview Modal -->
{#if showPreviewModal && editingFile}
  <div
    class="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4"
    on:click={closePreview}
  >
    <div
      class="bg-white dark:bg-gray-800 rounded-lg shadow-2xl max-w-5xl w-full max-h-[85vh] flex flex-col"
      on:click|stopPropagation
    >
      <!-- Modal Header -->
      <div class="border-b border-gray-200 dark:border-gray-700 px-6 py-4">
        <div class="flex items-center justify-between">
          <div>
            <h2 class="text-2xl font-bold text-gray-900 dark:text-white">Preview Changes</h2>
            <p class="text-sm text-gray-600 dark:text-gray-400 mt-1 font-mono">
              {editingFile.path}
            </p>
          </div>
          <button
            on:click={closePreview}
            class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 text-2xl"
          >
            ✕
          </button>
        </div>
      </div>

      <!-- Diff Display -->
      <div class="flex-1 overflow-y-auto p-6">
        <div class="bg-gray-50 dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
          <div class="font-mono text-sm">
            {#each previewDiff as diffLine}
              {#if diffLine.type === 'remove'}
                <div class="bg-red-50 dark:bg-red-900/20 text-red-800 dark:text-red-300 px-3 py-1 border-l-4 border-red-500">
                  <span class="text-gray-500 dark:text-gray-500 mr-4">{diffLine.line}</span>
                  <span class="mr-2">-</span>
                  <span>{diffLine.content}</span>
                </div>
              {:else if diffLine.type === 'add'}
                <div class="bg-green-50 dark:bg-green-900/20 text-green-800 dark:text-green-300 px-3 py-1 border-l-4 border-green-500">
                  <span class="text-gray-500 dark:text-gray-500 mr-4">{diffLine.line}</span>
                  <span class="mr-2">+</span>
                  <span>{diffLine.content}</span>
                </div>
              {:else}
                <div class="text-gray-700 dark:text-gray-300 px-3 py-1">
                  <span class="text-gray-500 dark:text-gray-500 mr-4">{diffLine.line}</span>
                  <span class="mr-3"> </span>
                  <span>{diffLine.content}</span>
                </div>
              {/if}
            {/each}
          </div>
        </div>

        <!-- Warning Banner -->
        <div class="mt-6 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg p-4">
          <div class="flex items-start gap-3">
            <span class="text-2xl">⚠️</span>
            <div>
              <p class="font-semibold text-amber-900 dark:text-amber-200 mb-1">
                Governance Write Operation
              </p>
              <p class="text-sm text-amber-800 dark:text-amber-300">
                This will create a timestamped backup at <code class="bg-amber-100 dark:bg-amber-800 px-1 rounded">{editingFile.name}.backup</code> and atomically write the new content.
                This operation cannot be undone from the UI (manual file recovery required).
              </p>
            </div>
          </div>
        </div>
      </div>

      <!-- Modal Actions -->
      <div class="border-t border-gray-200 dark:border-gray-700 px-6 py-4 flex items-center justify-between bg-gray-50 dark:bg-gray-900">
        <div class="text-sm text-gray-600 dark:text-gray-400">
          {previewDiff.filter(d => d.type === 'add').length} additions ·
          {previewDiff.filter(d => d.type === 'remove').length} deletions
        </div>
        <div class="flex items-center gap-3">
          <button
            class="px-5 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 font-medium rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
            on:click={closePreview}
          >
            Cancel
          </button>
          <button
            class="px-5 py-2 bg-red-600 hover:bg-red-700 text-white font-medium rounded-lg transition-colors flex items-center gap-2"
            on:click={confirmWrite}
          >
            💾 Confirm Write to Disk
          </button>
        </div>
      </div>
    </div>
  </div>
{/if}
