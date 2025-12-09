/**
 * API client for backend communication
 */
import type { CookieSource, SyncCookieRequest, SyncCookieResponse } from '@/types';
import { logger } from './logger';

// Backend URL (changeable via env or config)
const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8080';
const API_VERSION = '/api/v1';

/**
 * Sync cookie to backend
 */
export async function syncCookieToBackend(
  source: CookieSource,
  cookie: string
): Promise<SyncCookieResponse> {
  try {
    const request: SyncCookieRequest = {
      source,
      cookie
    };

    const response = await fetch(`${BACKEND_URL}${API_VERSION}/cookie/sync`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include', // Tự động gửi cookies
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
 * Get cookie status from backend
 */
export async function getCookieStatus(): Promise<any> {
  try {
    const response = await fetch(`${BACKEND_URL}${API_VERSION}/cookie/status`, {
      method: 'GET',
      credentials: 'include'
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    logger.error('Failed to get cookie status:', error);
    throw error;
  }
}

/**
 * Test backend connection
 */
export async function testConnection(): Promise<boolean> {
  try {
    const response = await fetch(`${BACKEND_URL}/ping`, {
      method: 'GET'
    });
    return response.ok;
  } catch (error) {
    logger.error('Backend connection failed:', error);
    return false;
  }
}
