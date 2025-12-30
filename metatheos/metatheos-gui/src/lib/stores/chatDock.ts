import { writable } from 'svelte/store'
import type { ChatProviderId } from '../chat/providers'

export type DockMode = 'hidden' | 'bottom' | 'right' | 'floating'

export interface ChatDockState {
  open: boolean
  mode: DockMode
  provider: ChatProviderId
  customUrls: Record<string, string>
  size: number // percent for dock height/width
  lastPath?: string
  selectedGoals: string[]
}

const defaultState: ChatDockState = {
  open: false,
  mode: 'hidden',
  provider: 'chatgpt',
  customUrls: {},
  size: 40,
  selectedGoals: [],
}

function createPersistedStore() {
  const stored = typeof localStorage !== 'undefined' ? localStorage.getItem('chatDockState') : null
  const initial = stored ? { ...defaultState, ...JSON.parse(stored) } : defaultState
  const { subscribe, update, set } = writable<ChatDockState>(initial)

  subscribe((value) => {
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem('chatDockState', JSON.stringify(value))
    }
  })

  return {
    subscribe,
    set,
    update,
    setOpen(open: boolean) {
      update((s) => ({ ...s, open, mode: open ? (s.mode === 'hidden' ? 'bottom' : s.mode) : 'hidden' }))
    },
    setMode(mode: DockMode) {
      update((s) => ({ ...s, mode, open: mode !== 'hidden' }))
    },
    setProvider(provider: ChatProviderId) {
      update((s) => ({ ...s, provider }))
    },
    setSize(size: number) {
      update((s) => ({ ...s, size }))
    },
    setCustomUrl(id: string, url: string) {
      update((s) => ({ ...s, customUrls: { ...s.customUrls, [id]: url } }))
    },
    setContext(selectedGoals: string[], lastPath?: string) {
      update((s) => ({ ...s, selectedGoals, lastPath }))
    },
  }
}

export const chatDockStore = createPersistedStore()
