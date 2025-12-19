<script lang="ts">
  import { syncStatus, syncError } from '@/stores/cookie.svelte';

  function getStatusConfig(status: string, error: string | null) {
    switch (status) {
      case 'success':
        return {
          bg: 'bg-green-100 dark:bg-green-900',
          text: 'text-green-800 dark:text-green-200',
          border: 'border-green-300',
          icon: '✓',
          message: 'Sync successful!'
        };
      case 'error':
        return {
          bg: 'bg-red-100 dark:bg-red-900',
          text: 'text-red-800 dark:text-red-200',
          border: 'border-red-300',
          icon: '✗',
          message: error || 'Sync failed'
        };
      case 'syncing':
        return {
          bg: 'bg-blue-100 dark:bg-blue-900',
          text: 'text-blue-800 dark:text-blue-200',
          border: 'border-blue-300',
          icon: '⟳',
          message: 'Syncing...'
        };
      default:
        return null;
    }
  }

  $: statusConfig = getStatusConfig($syncStatus, $syncError);
</script>

{#if statusConfig}
  <div class={`${statusConfig.bg} ${statusConfig.text} border ${statusConfig.border} px-4 py-3 rounded-lg text-sm flex items-center gap-2 animate-fade-in`}>
    <span class="text-lg">{statusConfig.icon}</span>
    <span>{statusConfig.message}</span>
  </div>
{/if}

<style>
  @keyframes fade-in {
    from {
      opacity: 0;
      transform: translateY(-10px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  .animate-fade-in {
    animation: fade-in 0.3s ease-out;
  }
</style>
