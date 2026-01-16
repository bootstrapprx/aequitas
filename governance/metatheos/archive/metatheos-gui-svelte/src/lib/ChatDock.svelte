<script>
  import { onMount, onDestroy } from "svelte";
  import { chatDockStore } from "./stores/chatDock";
  import { defaultProviders } from "./chat/providers";
  import AssistantPanel from "./AssistantPanel.svelte";
  import { invoke } from "@tauri-apps/api/core";
  import { get } from "svelte/store";

  export let activePhase = null;
  export let activeDay = null;

  let state;
  const unsubscribe = chatDockStore.subscribe((v) => (state = v));

  let dragging = false;
  let startY = 0;
  let startX = 0;
  let startSize = 40;

  let copyStatus = "";

  onDestroy(() => unsubscribe());

  onMount(() => {
    const handler = (e) => {
      if (e.ctrlKey && e.shiftKey && e.code === "Space") {
        toggleOpen();
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  });

  function toggleOpen() {
    chatDockStore.setOpen(!(state?.open && state?.mode !== "hidden"));
  }

  function setMode(mode) {
    chatDockStore.setMode(mode);
  }

  function setProvider(id) {
    // If user selects Ollama, we now stay in the dock (Sidebar/Bottom mode)
    // instead of switching views.
    chatDockStore.setProvider(id);
  }

  function currentProvider() {
    const p = defaultProviders.find((p) => p.id === state?.provider);
    return p || defaultProviders[0];
  }

  function currentUrl() {
    const p = currentProvider();
    if (state?.customUrls && state.customUrls[p.id]) {
      return state.customUrls[p.id];
    }
    return p.url;
  }

  async function copyContext() {
    try {
      const payload = await invoke("get_context_clipboard_payload", {
        selected_goals: state.selectedGoals || [],
        current_path: state.lastPath || null,
      });
      await navigator.clipboard.writeText(payload);
      copyStatus = "Copied";
      setTimeout(() => (copyStatus = ""), 1500);
    } catch (err) {
      copyStatus = `Error: ${err}`;
    }
  }

  function startDrag(event) {
    dragging = true;
    startY = event.clientY;
    startX = event.clientX;
    startSize = state.size || 40;
    window.addEventListener("mousemove", onDrag);
    window.addEventListener("mouseup", endDrag);
  }

  function onDrag(event) {
    if (!dragging) return;
    let delta;
    if (state.mode === "bottom") {
      delta = startY - event.clientY;
    } else {
      delta = event.clientX - startX;
    }
    const newSize = Math.min(80, Math.max(20, startSize + delta / 5));
    chatDockStore.setSize(newSize);
  }

  function endDrag() {
    dragging = false;
    window.removeEventListener("mousemove", onDrag);
    window.removeEventListener("mouseup", endDrag);
  }
</script>

{#if state && state.open}
  <div
    class={`chat-dock ${state.mode}`}
    style={state.mode === "bottom"
      ? `height:${state.size}vh`
      : state.mode === "right"
        ? `width:${state.size}vw`
        : ""}
  >
    <div class="chat-dock__header">
      <div class="left">
        <button class="btn-icon" title="Hide dock" on:click={toggleOpen}
          >✕</button
        >
        <select
          class="provider"
          bind:value={state.provider}
          on:change={(e) => setProvider(e.target.value)}
        >
          {#each defaultProviders as provider}
            <option value={provider.id}>{provider.label}</option>
          {/each}
        </select>
      </div>
      <div class="right">
        <button class="btn-secondary" on:click={copyContext}>
          Copy Context
        </button>
        <select
          class="select"
          bind:value={state.mode}
          on:change={(e) => setMode(e.target.value)}
        >
          <option value="bottom">Bottom</option>
          <option value="right">Right</option>
          <option value="floating">Floating</option>
          <option value="hidden">Hide</option>
        </select>
        {#if copyStatus}
          <span class="text-xs text-green-600 dark:text-green-300"
            >{copyStatus}</span
          >
        {/if}
      </div>
    </div>

    <div class="banner">
      <strong>Web Chat:</strong> no governance context. Copy/paste context manually.
      Do not request auto-writes; drafts only.
    </div>

    {#if currentProvider().id === "ollama-assistant"}
      <div class="chat-dock__body p-0 bg-gray-900">
        <AssistantPanel {activePhase} {activeDay} />
      </div>
    {:else if currentProvider().webOnly}
      <div class="chat-dock__body">
        <iframe
          title="chat-dock"
          src={currentUrl()}
          class="w-full h-full border-0"
          sandbox="allow-scripts allow-same-origin allow-forms allow-popups allow-presentation"
        ></iframe>
      </div>
    {:else}
      <div
        class="chat-dock__body flex items-center justify-center text-sm text-gray-700 dark:text-gray-200"
      >
        Use the Governance Assistant tab for vault-aware reasoning.
      </div>
    {/if}

    <!-- svelte-ignore a11y-no-noninteractive-tabindex -->
    <!-- svelte-ignore a11y-no-noninteractive-element-interactions -->
    <div
      class={`resize-handle ${state.mode === "bottom" ? "horizontal" : "vertical"}`}
      role="separator"
      tabindex="0"
      aria-orientation={state.mode === "bottom" ? "horizontal" : "vertical"}
      aria-valuenow={state.size}
      aria-valuemin="20"
      aria-valuemax="80"
      on:mousedown={startDrag}
      on:keydown={(e) => {
        if (state.mode === "bottom") {
          if (e.key === "ArrowUp")
            chatDockStore.setSize(Math.min(80, state.size + 5));
          if (e.key === "ArrowDown")
            chatDockStore.setSize(Math.max(20, state.size - 5));
        } else {
          if (e.key === "ArrowLeft")
            chatDockStore.setSize(Math.min(80, state.size + 5));
          if (e.key === "ArrowRight")
            chatDockStore.setSize(Math.max(20, state.size - 5));
        }
      }}
    ></div>
  </div>
{/if}

<style>
  .chat-dock {
    position: fixed;
    background: #0b1220;
    color: #e5e7eb;
    border-top: 1px solid rgba(255, 255, 255, 0.06);
    border-left: 1px solid rgba(255, 255, 255, 0.04);
    border-right: 1px solid rgba(255, 255, 255, 0.04);
    box-shadow: 0 -6px 18px rgba(0, 0, 0, 0.3);
    z-index: 50;
  }
  .chat-dock.bottom {
    left: 0;
    right: 0;
    bottom: 0;
  }
  .chat-dock.right {
    top: 0;
    right: 0;
    bottom: 0;
  }
  .chat-dock.floating {
    width: 420px;
    height: 520px;
    bottom: 16px;
    right: 16px;
    border-radius: 12px;
    overflow: hidden;
  }
  .chat-dock__header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 8px 12px;
    background: rgba(255, 255, 255, 0.04);
    border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  }
  .chat-dock__header .left,
  .chat-dock__header .right {
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .chat-dock__body {
    height: calc(100% - 96px);
    background: #0f172a;
  }
  .banner {
    background: #f4e5b5;
    color: #4a3600;
    padding: 6px 12px;
    font-size: 12px;
    border-bottom: 1px solid #dcbf6c;
  }
  .btn-icon {
    border: 1px solid rgba(255, 255, 255, 0.15);
    background: transparent;
    color: #e5e7eb;
    width: 28px;
    height: 28px;
    border-radius: 6px;
    font-size: 14px;
  }
  .btn-secondary {
    padding: 6px 10px;
    border-radius: 6px;
    border: 1px solid rgba(255, 255, 255, 0.12);
    background: rgba(255, 255, 255, 0.06);
    color: #e5e7eb;
    font-size: 12px;
  }
  .select,
  .provider {
    border: 1px solid rgba(255, 255, 255, 0.14);
    border-radius: 6px;
    padding: 4px 6px;
    font-size: 12px;
    background: rgba(255, 255, 255, 0.04);
    color: #e5e7eb;
  }
  .resize-handle {
    position: absolute;
    background: transparent;
  }
  .resize-handle.horizontal {
    top: 0;
    left: 0;
    right: 0;
    height: 6px;
    cursor: ns-resize;
  }
  .resize-handle.vertical {
    top: 0;
    bottom: 0;
    left: 0;
    width: 6px;
    cursor: ew-resize;
  }
  .chat-dock.right .chat-dock__body {
    height: calc(100% - 96px);
  }
  .chat-dock.bottom .chat-dock__body {
    height: calc(100% - 96px);
  }
</style>
