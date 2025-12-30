<script>
    export let frontmatter = {};

    // Helper to format values
    function formatValue(key, value) {
        if (value === null || value === undefined) return "";
        if (Array.isArray(value)) {
            if (key === "tags") {
                return value.map((tag) => `#${tag}`).join(" ");
            }
            return value.join(", ");
        }
        if (typeof value === "object") return JSON.stringify(value);
        if (key === "date" || key.endsWith("_date")) {
            // Simple date check
            return new Date(value).toLocaleDateString();
        }
        return String(value);
    }

    // Filter out internal keys if needed, or just show everything
    $: entries = Object.entries(frontmatter).filter(
        ([key]) => key !== "content",
    );
</script>

<div
    class="mb-6 rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 p-4"
>
    <div
        class="text-xs font-semibold uppercase tracking-wider text-gray-400 mb-3"
    >
        Properties
    </div>

    <div class="grid grid-cols-[120px_1fr] gap-y-2 text-sm">
        {#each entries as [key, value]}
            <div
                class="text-gray-500 dark:text-gray-400 font-medium truncate py-1"
            >
                {key}
            </div>
            <div class="text-gray-900 dark:text-gray-200 py-1 break-words">
                {#if key === "tags" && Array.isArray(value)}
                    <div class="flex flex-wrap gap-1">
                        {#each value as tag}
                            <span
                                class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-primary-100 text-primary-800 dark:bg-primary-900 dark:text-primary-200"
                            >
                                #{tag}
                            </span>
                        {/each}
                    </div>
                {:else if key === "url" || String(value).startsWith("http")}
                    <a
                        href={String(value)}
                        target="_blank"
                        rel="noopener noreferrer"
                        class="text-primary-600 hover:underline"
                    >
                        {String(value)}
                    </a>
                {:else}
                    {formatValue(key, value)}
                {/if}
            </div>
        {/each}
    </div>
</div>
