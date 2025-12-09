/**
 * Simple logger utility for extension
 */

const PREFIX = '[UIT Extension]';

export const logger = {
  info: (...args: any[]) => {
    console.log(PREFIX, ...args);
  },

  warn: (...args: any[]) => {
    console.warn(PREFIX, ...args);
  },

  error: (...args: any[]) => {
    console.error(PREFIX, ...args);
  },

  debug: (...args: any[]) => {
    if (import.meta.env.DEV) {
      console.debug(PREFIX, '[DEBUG]', ...args);
    }
  }
};
