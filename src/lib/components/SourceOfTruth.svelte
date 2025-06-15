<script lang="ts">
  import { apiClient } from '$lib/api';

  let { svgFileId } = $props<{
    svgFileId: number | null;
  }>();

  let isLoading = $state(false);
  let svgContent = $state<string>('');
  let error = $state<string | null>(null);

  $effect(() => {
    if (!svgFileId) {
      svgContent = '';
      return;
    }

    isLoading = true;
    error = null;

    (async () => {
      try {
        const response = await apiClient.getSourceOfTruthSvg(svgFileId);
        svgContent = response.source_of_truth_content;
      } catch (err) {
        error = err instanceof Error ? err.message : 'Failed to load SVG';
      } finally {
        isLoading = false;
      }
    })();
  });
</script>

<div class="flex h-full flex-col p-4">
  <div class="border-border flex-1 overflow-hidden rounded-lg border bg-white">
    {#if isLoading}
      <div class="flex h-full items-center justify-center">
        <div class="text-center">
          <div
            class="mx-auto mb-2 h-8 w-8 animate-spin rounded-full border-b-2 border-blue-600"
          ></div>
          <p class="text-sm text-gray-600">Loading Source of Truth...</p>
        </div>
      </div>
    {:else if error}
      <div class="flex h-full items-center justify-center">
        <div class="text-center text-red-600">
          <p class="font-medium">Error Loading Source of Truth</p>
          <p class="mt-1 text-sm">{error}</p>
        </div>
      </div>
    {:else if !svgContent}
      <div class="flex h-full items-center justify-center">
        <div class="text-center text-gray-500">
          <p class="font-medium">🔍 Source of Truth (Raw Symbols)</p>
          <p class="mt-1 text-sm">Upload SVG to see raw obfuscated symbols</p>
        </div>
      </div>
    {:else}
      <iframe srcdoc={svgContent} class="h-full w-full border-0" title="Source of Truth SVG Preview"
      ></iframe>
    {/if}
  </div>
</div>
