<script lang="ts">
  import type { CookieSource } from '@/types';
  import { cookieState, getTimeSinceSync, toggleSource } from '@/stores/cookie.svelte';

  interface Props {
    source: CookieSource;
    disabled?: boolean;
  }

  let { source, disabled = false }: Props = $props();

  const state = $derived(cookieState[source]);
  const timeSinceSync = $derived(getTimeSinceSync(source));
  const statusColor = $derived(state.lastSync ? 'text-green-600' : 'text-gray-500');

  function handleToggle() {
    if (!disabled) {
      toggleSource(source);
    }
  }
</script>

<div class="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg {disabled ? 'opacity-50' : ''}">
  <div class="flex-1">
    <div class="flex items-center gap-2">
      <h3 class="font-semibold text-sm uppercase">{source}</h3>
      <span class={`text-xs ${statusColor}`}>
        {state.enabled ? '●' : '○'}
      </span>
      {#if disabled}
        <span class="text-xs text-yellow-600 dark:text-yellow-400 font-medium">(Coming Soon)</span>
      {/if}
    </div>
    <p class="text-xs text-gray-600 dark:text-gray-400 mt-1">
      Last sync: {timeSinceSync}
    </p>
  </div>

  <label class="relative inline-flex items-center {disabled ? 'cursor-not-allowed' : 'cursor-pointer'}">
    <input
      type="checkbox"
      checked={state.enabled}
      onchange={handleToggle}
      disabled={disabled}
      class="sr-only peer"
    />
    <div class="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600 {disabled ? 'peer-disabled:opacity-50' : ''}"></div>
  </label>
</div>
