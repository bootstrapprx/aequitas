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

        // Strip frontmatter if present
        let body = text;
        if (text.startsWith("---\n")) {
            const parts = text.split("\n---\n");
            if (parts.length > 1) {
                body = parts.slice(1).join("\n---\n").trim();
            }
        }

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
