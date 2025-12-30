<script>
    import { getFileIcon } from "./utils.js";
    import FileTreeNode from "./FileTreeNode.svelte";

    export let node;
    export let expandedFolders;
    export let selectFile;
    export let selectedFile;
    export let level = 0;

    $: isExpanded = expandedFolders.has(node.path);
    $: isSelected = selectedFile?.path === node.path;
</script>

<div class="mb-1">
    <button
        class="w-full text-left px-2 py-1 rounded flex items-center gap-2 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors {isSelected
            ? 'bg-primary-50 dark:bg-primary-900/20'
            : ''}"
        style="padding-left: {level * 16 + 8}px"
        on:click={() => selectFile(node)}
    >
        {#if node.is_directory}
            <span class="text-gray-500 dark:text-gray-400 text-xs">
                {isExpanded ? "▼" : "▶"}
            </span>
        {:else}
            <span class="w-3"></span>
        {/if}

        <span class="text-lg">{getFileIcon(node.file_type)}</span>

        <span
            class="flex-1 text-sm font-medium text-gray-900 dark:text-white truncate"
        >
            {node.name}
        </span>

        {#if !node.is_writable && !node.is_directory}
            <span class="text-xs text-red-600 dark:text-red-400">🔒</span>
        {/if}
    </button>

    {#if node.is_directory && isExpanded && node.children}
        {#each node.children as child}
            <svelte:self
                node={child}
                {expandedFolders}
                {selectFile}
                {selectedFile}
                level={level + 1}
            />
        {/each}
    {/if}
</div>
