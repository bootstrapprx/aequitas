<script>
    import { onMount, onDestroy, createEventDispatcher } from "svelte";
    import { EditorView, basicSetup } from "codemirror";
    import { EditorState } from "@codemirror/state";
    import { markdown } from "@codemirror/lang-markdown";
    import { oneDark } from "@codemirror/theme-one-dark";

    export let value = "";
    export let readonly = false;

    const dispatch = createEventDispatcher();
    let editorContainer;
    let view;

    onMount(() => {
        const state = EditorState.create({
            doc: value,
            extensions: [
                basicSetup,
                markdown(),
                oneDark,
                EditorView.updateListener.of((update) => {
                    if (update.docChanged) {
                        const newValue = update.state.doc.toString();
                        dispatch("change", newValue);
                    }
                }),
                EditorState.readOnly.of(readonly),
            ],
        });

        view = new EditorView({
            state,
            parent: editorContainer,
        });
    });

    onDestroy(() => {
        if (view) {
            view.destroy();
        }
    });

    // React to external value changes (optional, be careful of loops)
    $: if (view && value !== view.state.doc.toString()) {
        const transaction = view.state.update({
            changes: { from: 0, to: view.state.doc.length, insert: value },
        });
        view.dispatch(transaction);
    }
</script>

<div
    class="h-full w-full overflow-hidden text-base"
    bind:this={editorContainer}
></div>

<style>
    div :global(.cm-editor) {
        height: 100%;
    }
    div :global(.cm-scroller) {
        overflow: auto;
    }
</style>
