/**
 * Svelte store for cookie state management
 */
import { writable, get } from 'svelte/store';
import browser from 'webextension-polyfill';
import type { CookieState, CookieSource, SyncStatus } from '@/types';
import { logger } from '@/lib/logger';

// Reactive state using Svelte writable stores
export const cookieState = writable<CookieState>({
  daa: { enabled: true, lastSync: null, cookieValue: null },
  courses: { enabled: false, lastSync: null, cookieValue: null },
  drl: { enabled: false, lastSync: null, cookieValue: null }
});

export const syncStatus = writable<SyncStatus>('idle');
export const syncError = writable<string | null>(null);

/**
 * Initialize store by loading state from background
 */
export async function initCookieStore() {
  try {
    const state = await browser.runtime.sendMessage({
      type: 'GET_COOKIE_STATE'
    });

    if (state) {
      cookieState.set(state);
      logger.info('Cookie store initialized');
    }
  } catch (error) {
    logger.error('Failed to initialize cookie store:', error);
  }
}

/**
 * Sync cookies for a specific source
 */
export async function syncCookie(source: CookieSource) {
  try {
    syncStatus.set('syncing');
    syncError.set(null);

    logger.info(`Syncing ${source}...`);

    const result = await browser.runtime.sendMessage({
      type: 'SYNC_COOKIE',
      payload: { source }
    });

    if (result.payload.success) {
      syncStatus.set('success');

      // Update cookieState
      cookieState.update(state => {
        state[source].lastSync = new Date();
        return state;
      });

      logger.info(`${source} synced successfully`);
    } else {
      syncStatus.set('error');
      syncError.set(result.payload.error || 'Sync failed');
      logger.error(`${source} sync failed:`, result.payload.error);
    }

    // Reset status after 3 seconds
    setTimeout(() => {
      syncStatus.set('idle');
    }, 3000);

  } catch (error) {
    syncStatus.set('error');
    syncError.set(error instanceof Error ? error.message : 'Unknown error');
    logger.error('Sync error:', error);

    setTimeout(() => {
      syncStatus.set('idle');
    }, 3000);
  }
}

/**
 * Sync all enabled sources
 */
export async function syncAll() {
  const state = get(cookieState);
  const enabledSources = Object.entries(state)
    .filter(([_, sourceState]) => sourceState.enabled)
    .map(([source, _]) => source as CookieSource);

  for (const source of enabledSources) {
    await syncCookie(source);
  }
}

/**
 * Toggle source enabled/disabled
 */
export function toggleSource(source: CookieSource) {
  cookieState.update(state => {
    state[source].enabled = !state[source].enabled;
    logger.info(`${source} ${state[source].enabled ? 'enabled' : 'disabled'}`);
    return state;
  });
}

/**
 * Get time elapsed since last sync
 */
export function getTimeSinceSync(source: CookieSource): string {
  const state = get(cookieState);
  const lastSync = state[source].lastSync;

  if (!lastSync) {
    return 'Never';
  }

  const now = Date.now();
  const elapsed = now - new Date(lastSync).getTime();
  const minutes = Math.floor(elapsed / 60000);

  if (minutes < 1) return 'Just now';
  if (minutes < 60) return `${minutes}m ago`;

  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;

  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}
