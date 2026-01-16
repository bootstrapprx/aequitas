import { writable, derived, get } from 'svelte/store';
import { listen, type UnlistenFn } from '@tauri-apps/api/event';
import { invoke } from '@tauri-apps/api/core';

/**
 * Store for tracking live update state and providing real-time sync capabilities
 */

// Track last update timestamp for each entity type
export const lastUpdate = writable<Record<string, Date>>({});

// Track if an update is currently in progress (for visual indicators)
export const updateInProgress = writable<boolean>(false);

// Track recent update notifications
export const recentUpdates = writable<Array<{
  entityType: string;
  timestamp: Date;
  message: string;
}>>([]);

// Event listener cleanup functions
let unlistenFns: UnlistenFn[] = [];

/**
 * Debouncer for refresh events
 */
class RefreshDebouncer {
  private pendingRefresh: Map<string, NodeJS.Timeout> = new Map();
  private debounceMs: number;

  constructor(debounceMs: number = 200) {
    this.debounceMs = debounceMs;
  }

  scheduleRefresh(entityType: string, callback: () => void) {
    // Cancel existing timer for this entity type
    const existing = this.pendingRefresh.get(entityType);
    if (existing) {
      clearTimeout(existing);
    }

    // Schedule new refresh
    const timer = setTimeout(() => {
      this.pendingRefresh.delete(entityType);
      callback();
    }, this.debounceMs);

    this.pendingRefresh.set(entityType, timer);
  }

  clear() {
    this.pendingRefresh.forEach(timer => clearTimeout(timer));
    this.pendingRefresh.clear();
  }
}

const refreshDebouncer = new RefreshDebouncer(200); // 200ms debounce

/**
 * Setup live update listeners for governance data
 * This should be called once when the app initializes
 */
export async function setupLiveUpdates(callbacks?: {
  onGoalChange?: () => void | Promise<void>;
  onPhaseChange?: () => void | Promise<void>;
  onAuditChange?: () => void | Promise<void>;
  onPromptChange?: () => void | Promise<void>;
  onDailyNoteChange?: () => void | Promise<void>;
  onAnyChange?: (entityType: string) => void | Promise<void>;
}) {
  // Clean up existing listeners
  await cleanupLiveUpdates();

  try {
    // Listen for general governance_changed event
    const unlistenGeneral = await listen<string>('governance_changed', async (event) => {
      const entityType = event.payload;

      console.log(`[Live Update] Governance changed: ${entityType}`);

      // Update last update timestamp
      lastUpdate.update(updates => ({
        ...updates,
        [entityType]: new Date()
      }));

      // Add to recent updates (keep last 10)
      recentUpdates.update(updates => {
        const newUpdate = {
          entityType,
          timestamp: new Date(),
          message: `${entityType} updated`
        };
        return [newUpdate, ...updates].slice(0, 10);
      });

      // Call entity-specific callback (debounced)
      if (callbacks) {
        refreshDebouncer.scheduleRefresh(entityType, async () => {
          updateInProgress.set(true);
          try {
            switch (entityType) {
              case 'goal':
                if (callbacks.onGoalChange) await callbacks.onGoalChange();
                break;
              case 'phase':
                if (callbacks.onPhaseChange) await callbacks.onPhaseChange();
                break;
              case 'audit':
                if (callbacks.onAuditChange) await callbacks.onAuditChange();
                break;
              case 'prompt':
                if (callbacks.onPromptChange) await callbacks.onPromptChange();
                break;
              case 'daily_note':
                if (callbacks.onDailyNoteChange) await callbacks.onDailyNoteChange();
                break;
            }

            // Call general callback if provided
            if (callbacks.onAnyChange) {
              await callbacks.onAnyChange(entityType);
            }
          } finally {
            updateInProgress.set(false);
          }
        });
      }
    });

    unlistenFns.push(unlistenGeneral);

    // Listen for specific entity events
    const entityTypes = ['goal', 'phase', 'audit', 'prompt', 'daily_note', 'decision', 'canon'];

    for (const entityType of entityTypes) {
      const unlisten = await listen<string>(`${entityType}_changed`, async (event) => {
        const path = event.payload;
        console.log(`[Live Update] ${entityType} file changed: ${path}`);

        // Update timestamp for this specific entity
        lastUpdate.update(updates => ({
          ...updates,
          [entityType]: new Date()
        }));
      });

      unlistenFns.push(unlisten);
    }

    console.log('[Live Update] Event listeners initialized');
  } catch (error) {
    console.error('[Live Update] Failed to setup event listeners:', error);
  }
}

/**
 * Clean up event listeners
 */
export async function cleanupLiveUpdates() {
  // Call all unlisten functions
  for (const unlisten of unlistenFns) {
    unlisten();
  }
  unlistenFns = [];

  // Clear debouncer
  refreshDebouncer.clear();

  console.log('[Live Update] Event listeners cleaned up');
}

/**
 * Helper to check if an entity type was recently updated
 */
export function wasRecentlyUpdated(entityType: string, withinMs: number = 3000): boolean {
  const updates = get(lastUpdate);
  const lastUpdateTime = updates[entityType];

  if (!lastUpdateTime) return false;

  const timeSinceUpdate = Date.now() - lastUpdateTime.getTime();
  return timeSinceUpdate < withinMs;
}

/**
 * Create a reactive store that tracks whether a specific entity type is recently updated
 */
export function createRecentUpdateStore(entityType: string, withinMs: number = 3000) {
  return derived(lastUpdate, $updates => {
    const lastUpdateTime = $updates[entityType];
    if (!lastUpdateTime) return false;

    const timeSinceUpdate = Date.now() - lastUpdateTime.getTime();
    return timeSinceUpdate < withinMs;
  });
}

/**
 * Show a toast notification for governance updates
 * (This is a helper that components can use)
 */
export function showUpdateToast(entityType: string, message?: string) {
  const displayMessage = message || `${entityType} data updated`;
  console.log(`[Toast] ${displayMessage}`);

  // Components can listen to recentUpdates store to display toasts
  recentUpdates.update(updates => {
    const newUpdate = {
      entityType,
      timestamp: new Date(),
      message: displayMessage
    };
    return [newUpdate, ...updates].slice(0, 10);
  });
}
