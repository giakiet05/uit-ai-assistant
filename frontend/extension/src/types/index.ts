/**
 * Type definitions for UIT AI Assistant Extension
 */

// Cookie source types
export type CookieSource = 'daa' | 'courses' | 'drl';

// Cookie state for a single source
export interface CookieSourceState {
  enabled: boolean;
  lastSync: Date | null;
  cookieValue: string | null;
}

// Overall cookie store state
export interface CookieState {
  daa: CookieSourceState;
  courses: CookieSourceState;
  drl: CookieSourceState;
}

// Sync status
export type SyncStatus = 'idle' | 'syncing' | 'success' | 'error';

// Message types for background <-> popup communication
export type MessageType =
  | 'SYNC_COOKIE'
  | 'GET_COOKIE_STATE'
  | 'COOKIE_STATE_UPDATED'
  | 'SYNC_RESULT';

export interface Message {
  type: MessageType;
  payload?: any;
}

export interface SyncCookieMessage extends Message {
  type: 'SYNC_COOKIE';
  payload: {
    source: CookieSource;
  };
}

export interface SyncResultMessage extends Message {
  type: 'SYNC_RESULT';
  payload: {
    success: boolean;
    source: CookieSource;
    error?: string;
  };
}

// Backend API types
export interface SyncCookieRequest {
  source: CookieSource;
  cookie: string;
}

export interface SyncCookieResponse {
  success: boolean;
  message: string;
}
