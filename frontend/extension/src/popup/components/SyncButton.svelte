<script lang="ts">
  import type { CookieSource } from '@/types';
  import { syncCookie, syncStatus } from '@/stores/cookie.svelte';

  interface Props {
    source: CookieSource;
    disabled?: boolean;
    fullWidth?: boolean;
  }

  let { source, disabled = false, fullWidth = false }: Props = $props();

  async function handleSync() {
    await syncCookie(source);
  }
</script>

<button
  onclick={handleSync}
  disabled={disabled || $syncStatus === 'syncing'}
  class="{fullWidth ? 'w-full' : ''} px-4 py-{fullWidth ? '3' : '2'} bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors duration-200 font-medium text-sm"
>
  {#if $syncStatus === 'syncing'}
    <span class="flex items-center gap-2 justify-center">
      <svg class="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
      </svg>
      Syncing...
    </span>
  {:else}
    Sync {source.toUpperCase()}
  {/if}
</button>
