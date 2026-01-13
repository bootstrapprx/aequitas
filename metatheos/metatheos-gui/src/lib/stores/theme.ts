import { writable } from 'svelte/store'

export type Theme = 'light' | 'dark'

export interface ThemeState {
  theme: Theme
}

const defaultState: ThemeState = {
  theme: 'dark', // Default to dark as Metatheos is night-focused
}

function createPersistedThemeStore() {
  const stored = typeof localStorage !== 'undefined' ? localStorage.getItem('metatheosTheme') : null
  const initial: ThemeState = stored ? { theme: stored as Theme } : defaultState

  const { subscribe, set, update } = writable<ThemeState>(initial)

  // Apply theme to document
  const applyTheme = (theme: Theme) => {
    if (typeof document !== 'undefined') {
      document.documentElement.setAttribute('data-theme', theme)
      document.documentElement.classList.remove('light', 'dark')
      document.documentElement.classList.add(theme)
    }
  }

  // Apply initial theme immediately
  applyTheme(initial.theme)

  subscribe((value) => {
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem('metatheosTheme', value.theme)
    }
    applyTheme(value.theme)
  })

  return {
    subscribe,
    set,
    update,
    toggle() {
      update((s) => ({ theme: s.theme === 'dark' ? 'light' : 'dark' }))
    },
    setTheme(theme: Theme) {
      set({ theme })
    },
  }
}

export const themeStore = createPersistedThemeStore()
