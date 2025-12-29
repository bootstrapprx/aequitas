<script>
  export let message = ''
  export let type = 'success' // success, error, info
  export let show = false
  export let duration = 3000

  let timeoutId

  $: if (show && duration > 0) {
    clearTimeout(timeoutId)
    timeoutId = setTimeout(() => {
      show = false
    }, duration)
  }

  function getClasses() {
    const base = 'fixed bottom-4 right-4 px-6 py-4 rounded-lg shadow-lg transition-all duration-300 transform z-50'
    const types = {
      success: 'bg-green-600 text-white',
      error: 'bg-red-600 text-white',
      info: 'bg-blue-600 text-white',
    }
    const visibility = show ? 'translate-y-0 opacity-100' : 'translate-y-4 opacity-0 pointer-events-none'
    return `${base} ${types[type]} ${visibility}`
  }
</script>

<div class={getClasses()}>
  <div class="flex items-center gap-3">
    {#if type === 'success'}
      <span class="text-2xl">✓</span>
    {:else if type === 'error'}
      <span class="text-2xl">✕</span>
    {:else}
      <span class="text-2xl">ℹ</span>
    {/if}
    <span class="font-medium">{message}</span>
  </div>
</div>
