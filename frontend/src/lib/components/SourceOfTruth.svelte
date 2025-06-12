<script lang="ts">
  import { apiClient } from "$lib/api";

  let { svgFileId } = $props<{
    svgFileId: number | null;
  }>();

  let isLoading = $state(false);
  let svgContent = $state<string>("");
  let error = $state<string | null>(null);

  $effect(() => {
    if (!svgFileId) {
      svgContent = "";
      return;
    }

    isLoading = true;
    error = null;

    (async () => {
      try {
        const response = await apiClient.getSourceOfTruthSvg(svgFileId);
        svgContent = response.source_of_truth_content;
      } catch (err) {
        error = err instanceof Error ? err.message : "Failed to load SVG";
      } finally {
        isLoading = false;
      }
    })();
  });
</script>

<div class="h-full p-4 flex flex-col">
  <div class="flex-1 bg-white border border-border rounded-lg overflow-hidden">
    {#if isLoading}
      <div class="flex items-center justify-center h-full">
        <div class="text-center">
          <div
            class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-2"
          ></div>
          <p class="text-sm text-gray-600">Loading Source of Truth...</p>
        </div>
      </div>
    {:else if error}
      <div class="flex items-center justify-center h-full">
        <div class="text-center text-red-600">
          <p class="font-medium">Error Loading Source of Truth</p>
          <p class="text-sm mt-1">{error}</p>
        </div>
      </div>
    {:else if !svgContent}
      <div class="flex items-center justify-center h-full">
        <div class="text-center text-gray-500">
          <p class="font-medium">🔍 Source of Truth (Raw Symbols)</p>
          <p class="text-sm mt-1">Upload SVG to see raw obfuscated symbols</p>
        </div>
      </div>
    {:else}
      <iframe
        srcdoc={svgContent}
        class="w-full h-full border-0"
        title="Source of Truth SVG Preview"
      ></iframe>
    {/if}
  </div>
</div>
