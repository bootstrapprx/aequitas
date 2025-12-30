<script>
    import { onMount, afterUpdate } from "svelte";
    import { marked } from "marked";
    import DOMPurify from "dompurify";
    import mermaid from "mermaid";

    export let content = "";
    let container;

    mermaid.initialize({
        startOnLoad: false,
        theme: "dark", // Adjust based on preference or current theme detection
        securityLevel: "loose",
    });

    function render(text) {
        if (!text) return "";

        // Strip frontmatter if present using a robust regex
        // Matches --- at start, followed by anything, ending with --- and optional newline
        const frontmatterRegex = /^---\n([\s\S]*?)\n---\n/;
        const body = text.replace(frontmatterRegex, "");

        // Configure marked to highlight code if needed, but for now standard is fine.
        // We can add custom renderer for mermaid code blocks if we want to handle them specifically,
        // but usually mermaid scans the DOM.
        // However, marked usually renders ```mermaid as <pre><code class="language-mermaid">.
        // We need to transform that to <div class="mermaid"> for mermaid.js to pick it up easily,
        // OR tell mermaid to look for the code block.

        // WikiLinks support: [[Target]] or [[Target|Label]]
        // Transform to <a href="#" data-wikilink="Target" class="text-primary-600 hover:underline">Label</a>

        // Process wikilinks before markdown parsing to avoid conflicts with other syntax
        const wikiLinkRegex = /\[\[([^|\]]+)(?:\|([^\]]+))?\]\]/g;

        // We need to protect the replacement from being parsed as markdown link if possible,
        // or just produce HTML (which marked allows).

        const processedBody = body.replace(
            wikiLinkRegex,
            (match, target, label) => {
                const displayText = label || target;
                return `<a href="javascript:void(0)" data-wikilink="${target}" class="text-primary-600 hover:underline wikilink">${displayText}</a>`;
            },
        );

        // Configure marked to highlight code if needed
        const renderer = new marked.Renderer();
        renderer.code = ({ text, lang }) => {
            if (lang === "mermaid") {
                return `<div class="mermaid">${text}</div>`;
            }
            if (
                lang === "dataview" ||
                lang === "dataviewjs" ||
                lang === "dql"
            ) {
                // Simple syntax highlighting for Dataview DQL
                const keywords = [
                    "TABLE",
                    "LIST",
                    "TASK",
                    "CALENDAR",
                    "FROM",
                    "WHERE",
                    "SORT",
                    "GROUP BY",
                    "LIMIT",
                    "FLATTEN",
                    "AS",
                    "AND",
                    "OR",
                    "ASC",
                    "DESC",
                ];

                // Escape HTML first to prevent injection from content
                let highlighted = text
                    .replace(/&/g, "&amp;")
                    .replace(/</g, "&lt;")
                    .replace(/>/g, "&gt;");

                // Highlight keywords
                // We use a regex with word boundaries to avoid partial matches
                const keywordRegex = new RegExp(
                    `\\b(${keywords.join("|")})\\b`,
                    "gi",
                );
                highlighted = highlighted.replace(
                    keywordRegex,
                    '<span class="text-primary-400 font-bold">$1</span>',
                );

                // Highlight strings
                highlighted = highlighted.replace(
                    /"([^"]*)"/g,
                    '<span class="text-yellow-300">"$1"</span>',
                );

                return `
                    <div class="my-4 rounded-lg border border-primary-500/30 bg-gray-900 overflow-hidden shadow-sm">
                        <div class="px-3 py-1 bg-primary-900/20 border-b border-primary-500/20 flex items-center gap-2">
                             <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-primary-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><ellipse cx="12" cy="5" rx="9" ry="3"></ellipse><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"></path><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"></path></svg>
                             <span class="text-xs font-semibold text-primary-300 uppercase tracking-wider">Dataview Query</span>
                        </div>
                        <div class="p-3 overflow-x-auto text-sm font-mono text-gray-300 leading-relaxed">
                            ${highlighted}
                        </div>
                    </div>
                `;
            }
            return `<pre><code class="language-${lang}">${text}</code></pre>`;
        };

        marked.setOptions({ renderer });

        const rawHtml = marked.parse(processedBody);
        return DOMPurify.sanitize(rawHtml, {
            ADD_ATTR: ["data-wikilink", "target"], // Allow data-wikilink attribute
        });
    }

    async function processMermaid() {
        if (container) {
            try {
                await mermaid.run({
                    nodes: container.querySelectorAll(".mermaid"),
                });
            } catch (e) {
                console.error("Mermaid render error:", e);
            }
        }
    }

    function handleContainerClick(e) {
        const link = e.target.closest("a[data-wikilink]");
        if (link) {
            e.preventDefault();
            const target = link.dataset.wikilink;
            dispatch("navigate", target);
        }
    }

    $: htmlContent = render(content);

    afterUpdate(() => {
        processMermaid();
    });

    onMount(() => {
        processMermaid();
    });
</script>

<div
    class="markdown-body prose dark:prose-invert max-w-none"
    bind:this={container}
    on:click={handleContainerClick}
>
    {@html htmlContent}
</div>

<style>
    /* Add any specific markdown overrides here if tailwind typography isn't enough */
    :global(.mermaid) {
        background: transparent !important;
        display: flex;
        justify-content: center;
        margin: 1rem 0;
    }
</style>
