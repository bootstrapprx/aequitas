<script>
  import { themeStore } from './stores/theme';

  function toggleTheme() {
    themeStore.toggle();
  }

  $: isDark = $themeStore.theme === 'dark';
</script>

<button
  class="theme-toggle"
  on:click={toggleTheme}
  aria-label="Toggle theme"
  title={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
>
  <span class="theme-icon" class:rotate={!isDark}>
    {#if isDark}
      <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M10 2C10 1.44772 10.4477 1 11 1C15.9706 1 20 5.02944 20 10C20 14.9706 15.9706 19 11 19C10.4477 19 10 18.5523 10 18C10 17.4477 10.4477 17 11 17C14.866 17 18 13.866 18 10C18 6.13401 14.866 3 11 3C10.4477 3 10 2.55228 10 2Z" fill="currentColor"/>
        <path d="M8.5 2C8.5 1.17157 7.82843 0.5 7 0.5C3.13401 0.5 0 3.63401 0 7.5C0 11.366 3.13401 14.5 7 14.5C7.82843 14.5 8.5 13.8284 8.5 13C8.5 12.1716 7.82843 11.5 7 11.5C4.79086 11.5 3 9.70914 3 7.5C3 5.29086 4.79086 3.5 7 3.5C7.82843 3.5 8.5 2.82843 8.5 2Z" fill="currentColor" opacity="0.4"/>
      </svg>
    {:else}
      <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
        <circle cx="10" cy="10" r="3" fill="currentColor"/>
        <path d="M10 0V3M10 17V20M20 10H17M3 10H0M17.071 2.929L14.95 5.05M5.05 14.95L2.929 17.071M17.071 17.071L14.95 14.95M5.05 5.05L2.929 2.929" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
      </svg>
    {/if}
  </span>
</button>

<style>
  .theme-toggle {
    position: relative;
    display: flex;
    align-items: center;
    justify-content: center;
    width: 36px;
    height: 36px;
    border-radius: 8px;
    background: var(--color-surface);
    border: 1px solid var(--color-border);
    color: var(--color-text-secondary);
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .theme-toggle:hover {
    background: var(--color-surface-hover);
    border-color: var(--color-border-hover);
    color: var(--color-accent);
    transform: translateY(-1px);
  }

  .theme-toggle:active {
    transform: translateY(0);
  }

  .theme-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    transition: transform 0.3s cubic-bezier(0.68, -0.55, 0.265, 1.55);
  }

  .theme-icon.rotate {
    transform: rotate(180deg);
  }
</style>
