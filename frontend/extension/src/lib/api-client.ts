/**
 * API client for backend communication
 */
import type { CookieSource, SyncCookieRequest, SyncCookieResponse } from '@/types';
import { getAuthToken } from './storage';
import { logger } from './logger';

// Backend URL (changeable via env or config)
const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8080';

/**
 * Sync cookie to backend
 */
export async function syncCookieToBackend(
  source: CookieSource,
  cookie: string
): Promise<SyncCookieResponse> {
  try {
    const authToken = await getAuthToken();

    if (!authToken) {
      throw new Error('No auth token found. Please login to web app first.');
    }

    const request: SyncCookieRequest = {
      source,
      cookie
    };

    const response = await fetch(`${BACKEND_URL}/api/sync-daa-cookie`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authToken}`
      },
      body: JSON.stringify(request)
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.message || `HTTP error! status: ${response.status}`);
    }

    const data: SyncCookieResponse = await response.json();
    logger.info('Cookie synced successfully:', source);
    return data;

  } catch (error) {
    logger.error('Failed to sync cookie:', error);
    throw error;
  }
}

/**
 * Test backend connection
 */
export async function testConnection(): Promise<boolean> {
  try {
    const response = await fetch(`${BACKEND_URL}/api/health`, {
      method: 'GET'
    });
    return response.ok;
  } catch (error) {
    logger.error('Backend connection failed:', error);
    return false;
  }
}
