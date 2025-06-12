<script lang="ts">
  import { apiClient } from "$lib/api";
  import type { Font } from "$lib/types";

  let {
    svgFileId,
    fonts,
    refreshTrigger = 0,
  } = $props<{
    svgFileId: number | null;
    fonts: Font[];
    refreshTrigger?: number;
  }>();

  let isLoading = $state(false);
  let liveContent = $state<string>("");
  let originalContent = $state<string>("");
  let error = $state<string | null>(null);

  async function loadOriginalSvg() {
    if (!svgFileId) {
      originalContent = "";
      liveContent = "";
      return;
    }

    error = null;
    isLoading = true;

    try {
      const response = await apiClient.getSourceOfTruthSvg(svgFileId);
      originalContent = response.source_of_truth_content;
      processLivePreview();
    } catch (err) {
      error = err instanceof Error ? err.message : "Failed to load SVG content";
    } finally {
      isLoading = false;
    }
  }

  function processLivePreview() {
    if (!originalContent) {
      liveContent = "";
      return;
    }

    let processedContent = originalContent;

    for (const font of fonts) {
      for (const glyph of font.glyphs) {
        if (
          glyph.mapping &&
          glyph.mapping.trim() &&
          glyph.codepoint.startsWith("U+")
        ) {
          try {
            const unicode_val = parseInt(glyph.codepoint.replace("U+", ""), 16);
            const encoded_char = String.fromCharCode(unicode_val);
            processedContent = processedContent.replaceAll(
              encoded_char,
              glyph.mapping
            );
          } catch (error) {
            continue;
          }
        }
      }
    }

    liveContent = processedContent;
  }

  $effect(() => {
    loadOriginalSvg();
  });

  $effect(() => {
    refreshTrigger;
    processLivePreview();
  });
</script>

<div class="h-full p-4">
  <div class="h-full bg-white border border-border rounded-lg overflow-auto">
    <div class="min-h-full p-4 font-fallback">
      {#if isLoading}
        <div class="flex items-center justify-center h-48">
          <div class="text-center">
            <div
              class="animate-spin rounded-full h-8 w-8 border-b-2 border-green-600 mx-auto mb-2"
            ></div>
            <p class="text-sm text-gray-600">Loading Live Preview...</p>
          </div>
        </div>
      {:else if error}
        <div class="flex items-center justify-center h-48">
          <div class="text-center text-red-600">
            <p class="font-medium">Error Loading Live Preview</p>
            <p class="text-sm mt-1">{error}</p>
          </div>
        </div>
      {:else if !liveContent}
        <div class="flex items-center justify-center h-48">
          <div class="text-center text-gray-500">
            <p class="font-medium">📖 Live Preview (Decoded)</p>
            <p class="text-sm mt-1">Upload SVG to see live decoded preview</p>
          </div>
        </div>
      {:else}
        {@html liveContent}
      {/if}
    </div>
  </div>
</div>
