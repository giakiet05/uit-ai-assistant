/**
 * Svelte 5 store for cookie state management
 */
import browser from 'webextension-polyfill';
import type { CookieState, CookieSource, SyncStatus } from '@/types';
import { logger } from '@/lib/logger';

// Reactive state using Svelte 5 runes
export const cookieState = $state<CookieState>({
  daa: { enabled: true, lastSync: null, cookieValue: null },
  courses: { enabled: false, lastSync: null, cookieValue: null },
  drl: { enabled: false, lastSync: null, cookieValue: null }
});

export const syncStatus = $state<SyncStatus>('idle');
export const syncError = $state<string | null>(null);

/**
 * Initialize store by loading state from background
 */
export async function initCookieStore() {
  try {
    const state = await browser.runtime.sendMessage({
      type: 'GET_COOKIE_STATE'
    });

    if (state) {
      Object.assign(cookieState, state);
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
    syncStatus.value = 'syncing';
    syncError.value = null;

    logger.info(`Syncing ${source}...`);

    const result = await browser.runtime.sendMessage({
      type: 'SYNC_COOKIE',
      payload: { source }
    });

    if (result.payload.success) {
      syncStatus.value = 'success';
      cookieState[source].lastSync = new Date();
      logger.info(`${source} synced successfully`);
    } else {
      syncStatus.value = 'error';
      syncError.value = result.payload.error || 'Sync failed';
      logger.error(`${source} sync failed:`, result.payload.error);
    }

    // Reset status after 3 seconds
    setTimeout(() => {
      syncStatus.value = 'idle';
    }, 3000);

  } catch (error) {
    syncStatus.value = 'error';
    syncError.value = error instanceof Error ? error.message : 'Unknown error';
    logger.error('Sync error:', error);

    setTimeout(() => {
      syncStatus.value = 'idle';
    }, 3000);
  }
}

/**
 * Sync all enabled sources
 */
export async function syncAll() {
  const enabledSources = Object.entries(cookieState)
    .filter(([_, state]) => state.enabled)
    .map(([source, _]) => source as CookieSource);

  for (const source of enabledSources) {
    await syncCookie(source);
  }
}

/**
 * Toggle source enabled/disabled
 */
export function toggleSource(source: CookieSource) {
  cookieState[source].enabled = !cookieState[source].enabled;
  logger.info(`${source} ${cookieState[source].enabled ? 'enabled' : 'disabled'}`);
}

/**
 * Get time elapsed since last sync
 */
export function getTimeSinceSync(source: CookieSource): string {
  const lastSync = cookieState[source].lastSync;

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
