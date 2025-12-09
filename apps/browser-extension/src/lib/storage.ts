/**
 * Chrome storage wrapper utilities
 */
import browser from 'webextension-polyfill';
import type { CookieState } from '@/types';

const STORAGE_KEYS = {
  COOKIE_STATE: 'cookieState',
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
 * Clear all storage
 */
export async function clearStorage(): Promise<void> {
  await browser.storage.local.clear();
}
