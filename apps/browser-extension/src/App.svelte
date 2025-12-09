<script lang="ts">
  import { onMount } from 'svelte';
  import { initCookieStore, syncAll } from '@/stores/cookie.svelte';
  import CookieStatus from '@/popup/components/CookieStatus.svelte';
  import SyncButton from '@/popup/components/SyncButton.svelte';
  import StatusBanner from '@/popup/components/StatusBanner.svelte';

  onMount(async () => {
    await initCookieStore();
  });

  async function handleSyncAll() {
    await syncAll();
  }
</script>

<main class="w-96 min-h-[400px] bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100">
  <div class="p-6 space-y-6">
    <!-- Header -->
    <div class="text-center space-y-2">
      <h1 class="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
        UIT AI Assistant
      </h1>
      <p class="text-sm text-gray-600 dark:text-gray-400">
        Cookie Sync Manager
      </p>
    </div>

    <!-- Status Banner -->
    <StatusBanner />

    <!-- Cookie Sources -->
    <div class="space-y-3">
      <h2 class="text-sm font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wide">
        Cookie Sources
      </h2>

      <CookieStatus source="daa" />
      <CookieStatus source="courses" disabled={true} />
      <CookieStatus source="drl" disabled={true} />
    </div>

    <!-- Actions -->
    <div class="space-y-3">
      <SyncButton source="daa" fullWidth={true} />

      <div class="grid grid-cols-3 gap-2 opacity-50">
        <SyncButton source="daa" disabled={false} />
        <SyncButton source="courses" disabled={true} />
        <SyncButton source="drl" disabled={true} />
      </div>
    </div>

    <!-- Footer -->
    <div class="pt-4 border-t border-gray-200 dark:border-gray-700">
      <p class="text-xs text-gray-500 dark:text-gray-400 text-center">
        Make sure you're logged in to the respective sites before syncing.
      </p>
    </div>
  </div>
</main>
