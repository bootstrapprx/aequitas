<script>
  import { chatDockStore } from './stores/chatDock'

  function openDock() {
    chatDockStore.setMode('bottom')
    chatDockStore.setOpen(true)
  }
</script>

<button class="chat-toggle" title="Open Chat Dock (Ctrl+Shift+Space)" on:click={openDock}>
  💬
</button>

<style>
  .chat-toggle {
    position: fixed;
    right: 16px;
    bottom: 16px;
    width: 42px;
    height: 42px;
    border-radius: 12px;
    background: #0f172a;
    color: #fff;
    border: 1px solid rgba(255,255,255,0.08);
    box-shadow: 0 6px 16px rgba(0,0,0,0.25);
    cursor: pointer;
    z-index: 40;
    font-size: 16px;
  }
  .chat-toggle:hover {
    transform: translateY(-1px);
  }
</style>
