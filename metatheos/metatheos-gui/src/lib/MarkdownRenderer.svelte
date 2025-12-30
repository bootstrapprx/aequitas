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
        // Let's use a standard render and let mermaid find `.mermaid` classes.

        // However, marked usually renders ```mermaid as <pre><code class="language-mermaid">.
        // We need to transform that to <div class="mermaid"> for mermaid.js to pick it up easily,
        // OR tell mermaid to look for the code block.

        // Custom renderer for code blocks
        const renderer = new marked.Renderer();
        renderer.code = ({ text, lang }) => {
            if (lang === "mermaid") {
                return `<div class="mermaid">${text}</div>`;
            }
            return `<pre><code class="language-${lang}">${text}</code></pre>`;
        };

        marked.setOptions({ renderer });

        const rawHtml = marked.parse(body);
        return DOMPurify.sanitize(rawHtml);
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
