/**
 * Cookie manager for extracting and syncing cookies from various sources
 */
import browser from 'webextension-polyfill';
import type { CookieSource } from '@/types';
import { logger } from '@/lib/logger';

// Domain mapping for cookie sources
const DOMAIN_MAP: Record<CookieSource, string> = {
  daa: 'daa.uit.edu.vn',
  courses: 'courses.uit.edu.vn',
  drl: 'drl.uit.edu.vn'
};

/**
 * Extract cookies from a specific domain
 */
export async function extractCookies(source: CookieSource): Promise<string> {
  try {
    const domain = DOMAIN_MAP[source];

    if (!domain) {
      throw new Error(`Unknown cookie source: ${source}`);
    }

    logger.info(`Extracting cookies from ${domain}`);

    // Get all cookies for this domain
    const cookies = await browser.cookies.getAll({
      domain: domain
    });

    if (!cookies || cookies.length === 0) {
      logger.warn(`No cookies found for ${domain}`);
      return '';
    }

    // Serialize cookies to string format (name=value; name2=value2; ...)
    const cookieString = cookies
      .map(cookie => `${cookie.name}=${cookie.value}`)
      .join('; ');

    logger.info(`Extracted ${cookies.length} cookies from ${domain}`);
    logger.debug('Cookie string length:', cookieString.length);

    return cookieString;

  } catch (error) {
    logger.error(`Failed to extract cookies from ${source}:`, error);
    throw error;
  }
}

/**
 * Check if user is logged in to a specific site
 * (by checking if cookies exist)
 */
export async function isLoggedIn(source: CookieSource): Promise<boolean> {
  try {
    const domain = DOMAIN_MAP[source];
    const cookies = await browser.cookies.getAll({ domain });

    // Simple check: if we have cookies, assume logged in
    // TODO: Improve this by checking specific session cookies
    return cookies && cookies.length > 0;

  } catch (error) {
    logger.error(`Failed to check login status for ${source}:`, error);
    return false;
  }
}

/**
 * Listen for cookie changes on specific domains
 */
export function setupCookieListener(
  onCookieChanged: (source: CookieSource) => void
) {
  browser.cookies.onChanged.addListener((changeInfo) => {
    const domain = changeInfo.cookie.domain;

    // Check which source this cookie belongs to
    for (const [source, sourceDomain] of Object.entries(DOMAIN_MAP)) {
      if (domain.includes(sourceDomain)) {
        logger.debug(`Cookie changed for ${source}:`, changeInfo.cookie.name);
        onCookieChanged(source as CookieSource);
        break;
      }
    }
  });

  logger.info('Cookie change listener setup complete');
}
