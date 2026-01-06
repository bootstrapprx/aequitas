<script lang="ts">
  import { invoke } from "@tauri-apps/api/core";

  export let scopeType: string;
  export let scopeId: string;
  export let heading = "Notes";
  export let collapsedInitially = true;
  export let compact = false;
  export let allowDelete = false;

  let annotations: any[] = [];
  let loading = false;
  let error: string | null = null;
  let body = "";
  let expanded = !collapsedInitially;

  async function load() {
    if (!scopeId || !scopeType) return;
    loading = true;
    error = null;
    try {
      annotations = await invoke("get_annotations", {
        scope_type: scopeType,
        scope_id: scopeId,
      });
    } catch (e) {
      error = e?.toString?.() ?? String(e);
    } finally {
      loading = false;
    }
  }

  async function add() {
    if (!body.trim() || !scopeId) return;
    try {
      const item = await invoke("add_annotation", {
        scope_type: scopeType,
        scope_id: scopeId,
        body: body.trim(),
        author: "user",
      });
      annotations = [item, ...annotations];
      body = "";
      expanded = true;
    } catch (e) {
      error = e?.toString?.() ?? String(e);
    }
  }

  async function remove(id: string) {
    try {
      await invoke("delete_annotation", { id });
      annotations = annotations.filter((a) => a.id !== id);
    } catch (e) {
      error = e?.toString?.() ?? String(e);
    }
  }

  $: if (scopeId) load();
</script>

<div class={`annotation-panel ${compact ? "compact" : ""}`}>
  <button class="header" on:click={() => (expanded = !expanded)}>
    <div class="title">
      <span>📝</span>
      <span>{heading}</span>
      {#if loading}
        <span class="pill">Loading</span>
      {:else}
        <span class="pill">{annotations.length}</span>
      {/if}
    </div>
    <span class="chevron">{expanded ? "▾" : "▸"}</span>
  </button>

  {#if expanded}
    <div class="content">
      {#if error}
        <div class="error">{error}</div>
      {/if}

      <div class="list">
        {#if annotations.length === 0 && !loading}
          <div class="empty">No annotations yet.</div>
        {/if}
        {#each annotations as note}
          <div class="note">
            <div class="note-meta">
              <span class={`author ${note.author_type === "ai" ? "ai" : ""}`}>
                {note.author_type || "user"}
              </span>
              <span>{new Date(note.created_at).toLocaleString()}</span>
              {#if allowDelete}
                <button class="delete" on:click={() => remove(note.id)}>✕</button>
              {/if}
            </div>
            <div class="note-body">{note.content}</div>
          </div>
        {/each}
      </div>

      <div class="composer">
        <textarea
          rows={compact ? 2 : 3}
          bind:value={body}
          placeholder="Add a quick note…"
          on:keydown={(e) => e.key === "Enter" && e.ctrlKey && add()}
        ></textarea>
        <div class="actions">
          <button on:click={add} disabled={!body.trim() || loading}>Add</button>
        </div>
      </div>
    </div>
  {/if}
</div>

<style>
  .annotation-panel {
    border: 1px solid rgba(107, 114, 128, 0.4);
    border-radius: 8px;
    background: rgba(17, 24, 39, 0.5);
    color: #e5e7eb;
  }
  .annotation-panel.compact {
    background: rgba(17, 24, 39, 0.2);
  }
  .header {
    width: 100%;
    padding: 8px 12px;
    background: transparent;
    border: none;
    color: inherit;
    display: flex;
    justify-content: space-between;
    align-items: center;
    cursor: pointer;
  }
  .title {
    display: flex;
    gap: 8px;
    align-items: center;
    font-weight: 700;
    letter-spacing: 0.02em;
    text-transform: uppercase;
    font-size: 12px;
  }
  .pill {
    background: rgba(59, 130, 246, 0.15);
    color: #93c5fd;
    padding: 2px 8px;
    border-radius: 999px;
    font-size: 11px;
  }
  .chevron {
    font-size: 14px;
  }
  .content {
    padding: 0 12px 12px;
    display: flex;
    flex-direction: column;
    gap: 10px;
  }
  .list {
    display: flex;
    flex-direction: column;
    gap: 8px;
    max-height: 240px;
    overflow: auto;
  }
  .note {
    background: rgba(31, 41, 55, 0.6);
    border: 1px solid rgba(55, 65, 81, 0.7);
    border-radius: 6px;
    padding: 8px;
  }
  .note-meta {
    display: flex;
    gap: 8px;
    align-items: center;
    font-size: 11px;
    color: #9ca3af;
    border-bottom: 1px dashed rgba(75, 85, 99, 0.7);
    padding-bottom: 4px;
    margin-bottom: 4px;
  }
  .author {
    text-transform: uppercase;
    font-weight: 700;
    color: #60a5fa;
  }
  .author.ai {
    color: #a78bfa;
  }
  .delete {
    margin-left: auto;
    color: #fca5a5;
    background: transparent;
    border: none;
    cursor: pointer;
  }
  .note-body {
    font-size: 14px;
    white-space: pre-wrap;
    color: #e5e7eb;
  }
  .composer textarea {
    width: 100%;
    background: rgba(31, 41, 55, 0.8);
    border: 1px solid rgba(75, 85, 99, 0.8);
    color: #f9fafb;
    border-radius: 6px;
    padding: 6px 8px;
    resize: vertical;
    font-size: 14px;
  }
  .actions {
    display: flex;
    justify-content: flex-end;
    margin-top: 6px;
  }
  .actions button {
    background: #2563eb;
    color: #fff;
    border: none;
    border-radius: 4px;
    padding: 6px 12px;
    cursor: pointer;
    font-weight: 600;
  }
  .actions button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
  .empty {
    text-align: center;
    font-size: 13px;
    color: #9ca3af;
    padding: 6px;
  }
  .error {
    color: #fca5a5;
    font-size: 13px;
  }
</style>
