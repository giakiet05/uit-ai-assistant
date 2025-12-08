/**
 * Chrome storage wrapper utilities
 */
import browser from 'webextension-polyfill';
import type { CookieState } from '@/types';

const STORAGE_KEYS = {
  COOKIE_STATE: 'cookieState',
  AUTH_TOKEN: 'authToken',
} as const;

/**
 * Get cookie state from storage
 */
export async function getCookieState(): Promise<CookieState | null> {
  const result = await browser.storage.local.get(STORAGE_KEYS.COOKIE_STATE);
  return result[STORAGE_KEYS.COOKIE_STATE] || null;
}

/**
 * Save cookie state to storage
 */
export async function saveCookieState(state: CookieState): Promise<void> {
  await browser.storage.local.set({ [STORAGE_KEYS.COOKIE_STATE]: state });
}

/**
 * Get auth token from storage
 */
export async function getAuthToken(): Promise<string | null> {
  const result = await browser.storage.local.get(STORAGE_KEYS.AUTH_TOKEN);
  return result[STORAGE_KEYS.AUTH_TOKEN] || null;
}

/**
 * Save auth token to storage
 */
export async function saveAuthToken(token: string): Promise<void> {
  await browser.storage.local.set({ [STORAGE_KEYS.AUTH_TOKEN]: token });
}

/**
 * Clear all storage
 */
export async function clearStorage(): Promise<void> {
  await browser.storage.local.clear();
}
