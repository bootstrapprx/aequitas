<script>
    import { createEventDispatcher } from "svelte";

    export let orientation = "vertical"; // 'vertical' (w-resize) or 'horizontal' (n-resize)

    const dispatch = createEventDispatcher();
    let isDragging = false;

    function startDrag(e) {
        isDragging = true;
        dispatch("dragstart");

        window.addEventListener("mousemove", onMouseMove);
        window.addEventListener("mouseup", onMouseUp);

        // Prevent text selection during drag
        document.body.style.userSelect = "none";
        document.body.style.cursor =
            orientation === "vertical" ? "col-resize" : "row-resize";
    }

    function onMouseMove(e) {
        if (!isDragging) return;
        dispatch("resize", {
            x: e.movementX,
            y: e.movementY,
            clientX: e.clientX,
            clientY: e.clientY,
        });
    }

    function onMouseUp() {
        isDragging = false;
        dispatch("dragend");

        window.removeEventListener("mousemove", onMouseMove);
        window.removeEventListener("mouseup", onMouseUp);

        document.body.style.userSelect = "";
        document.body.style.cursor = "";
    }
</script>

<!-- svelte-ignore a11y-no-static-element-interactions -->
<div
    class="resize-handle {orientation} {isDragging ? 'dragging' : ''}"
    on:mousedown={startDrag}
>
    <div class="visual-handle"></div>
</div>

<style>
    .resize-handle {
        flex: 0 0 3px; /* Hit area width/height */
        display: flex;
        justify-content: center;
        align-items: center;
        background-color: transparent;
        transition: background-color 0.2s;
        z-index: 10;
    }

    .resize-handle:hover,
    .resize-handle.dragging {
        background-color: theme("colors.primary.500");
    }

    .resize-handle.vertical {
        width: 4px;
        height: 100%;
        cursor: col-resize;
        border-right: 1px solid theme("colors.gray.200");
    }
    :global(.dark) .resize-handle.vertical {
        border-right-color: theme("colors.gray.700");
    }

    .resize-handle.horizontal {
        height: 4px;
        width: 100%;
        cursor: row-resize;
        border-bottom: 1px solid theme("colors.gray.200");
    }
    :global(.dark) .resize-handle.horizontal {
        border-bottom-color: theme("colors.gray.700");
    }

    .resize-handle:hover .visual-handle,
    .resize-handle.dragging .visual-handle {
        opacity: 1;
    }

    .visual-handle {
        background-color: theme("colors.primary.500");
        opacity: 0;
        transition: opacity 0.2s;
    }

    .vertical .visual-handle {
        width: 2px;
        height: 100%;
    }

    .horizontal .visual-handle {
        height: 2px;
        width: 100%;
    }
</style>
