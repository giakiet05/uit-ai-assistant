/**
 * Background service worker for UIT AI Assistant Extension
 *
 * Responsibilities:
 * - Listen for cookie changes
 * - Handle sync requests from popup
 * - Communicate with backend API
 * - Manage extension state
 */
import browser from 'webextension-polyfill';
import type { CookieSource, Message, SyncCookieMessage, SyncResultMessage, CookieState } from '@/types';
import { extractCookies, setupCookieListener, isLoggedIn } from './cookie-manager';
import { syncCookieToBackend } from '@/lib/api-client';
import { getCookieState, saveCookieState } from '@/lib/storage';
import { logger } from '@/lib/logger';

// Initialize background script
logger.info('Background service worker started');

// Initialize default cookie state
async function initializeCookieState() {
  let state = await getCookieState();

  if (!state) {
    // Create default state
    state = {
      daa: { enabled: true, lastSync: null, cookieValue: null },
      courses: { enabled: false, lastSync: null, cookieValue: null },
      drl: { enabled: false, lastSync: null, cookieValue: null }
    };
    await saveCookieState(state);
    logger.info('Initialized default cookie state');
  }

  return state;
}

// Handle sync cookie request
async function handleSyncCookie(source: CookieSource): Promise<SyncResultMessage> {
  try {
    logger.info(`Syncing cookies for ${source}...`);

    // Check if logged in
    const loggedIn = await isLoggedIn(source);
    if (!loggedIn) {
      throw new Error(`Not logged in to ${source}. Please login first.`);
    }

    // Extract cookies
    const cookieString = await extractCookies(source);

    if (!cookieString) {
      throw new Error(`Failed to extract cookies from ${source}`);
    }

    // Sync to backend
    const response = await syncCookieToBackend(source, cookieString);

    if (!response.success) {
      throw new Error(response.message || 'Sync failed');
    }

    // Update state
    const state = await getCookieState();
    if (state) {
      state[source] = {
        ...state[source],
        lastSync: new Date(),
        cookieValue: cookieString.substring(0, 50) + '...' // Store truncated version for debugging
      };
      await saveCookieState(state);
    }

    logger.info(`Successfully synced cookies for ${source}`);

    return {
      type: 'SYNC_RESULT',
      payload: {
        success: true,
        source
      }
    };

  } catch (error) {
    logger.error(`Failed to sync cookies for ${source}:`, error);

    return {
      type: 'SYNC_RESULT',
      payload: {
        success: false,
        source,
        error: error instanceof Error ? error.message : 'Unknown error'
      }
    };
  }
}

// Message handler for popup communication
browser.runtime.onMessage.addListener((message: unknown, _sender) => {
  const msg = message as Message;
  logger.debug('Received message:', msg.type);

  switch (msg.type) {
    case 'SYNC_COOKIE': {
      const { source } = (msg as SyncCookieMessage).payload;
      return handleSyncCookie(source);
    }

    case 'GET_COOKIE_STATE': {
      return getCookieState();
    }

    default:
      logger.warn('Unknown message type:', msg.type);
      return Promise.resolve({ error: 'Unknown message type' });
  }
});

// Setup cookie change listener
setupCookieListener((source) => {
  logger.info(`Cookie changed for ${source}, consider re-syncing`);
  // TODO: Auto-sync if enabled in settings
});

// Initialize on install
browser.runtime.onInstalled.addListener(async (details) => {
  logger.info('Extension installed:', details.reason);
  await initializeCookieState();
});

// Initialize on startup
initializeCookieState();

logger.info('Background service worker initialized');
