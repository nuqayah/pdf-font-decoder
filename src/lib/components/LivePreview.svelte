<script lang="ts">
  import { apiClient } from '$lib/api';
  import type { Font } from '$lib/types';

  let {
    fonts,
    svgFileId,
    refreshTrigger = 0,
  } = $props<{
    fonts: Font[];
    svgFileId: number | null;
    refreshTrigger?: number;
  }>();

  let isLoading = $state(false);
  let liveContent = $state<string>('');
  let error = $state<string | null>(null);
  let originalContent = $state<string>('');

  async function loadOriginalSvg() {
    if (!svgFileId) {
      originalContent = '';
      liveContent = '';
      return;
    }

    error = null;
    isLoading = true;

    try {
      const response = await apiClient.getSourceOfTruthSvg(svgFileId);
      originalContent = response.source_of_truth_content;
      processLivePreview();
    } catch (err) {
      error = err instanceof Error ? err.message : 'Failed to load SVG content';
    } finally {
      isLoading = false;
    }
  }

  function processLivePreview() {
    if (!originalContent) {
      liveContent = '';
      return;
    }

    let processedContent = originalContent;

    for (const font of fonts) {
      for (const glyph of font.glyphs) {
        if (glyph.mapping && glyph.mapping.trim() && glyph.codepoint.startsWith('U+')) {
          try {
            const unicode_val = parseInt(glyph.codepoint.replace('U+', ''), 16);
            const encoded_char = String.fromCharCode(unicode_val);
            processedContent = processedContent.replaceAll(encoded_char, glyph.mapping);
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
  <div class="border-border h-full overflow-auto rounded-lg border bg-white">
    <div class="font-fallback min-h-full p-4">
      {#if isLoading}
        <div class="flex h-48 items-center justify-center">
          <div class="text-center">
            <div
              class="mx-auto mb-2 h-8 w-8 animate-spin rounded-full border-b-2 border-green-600"
            ></div>
            <p class="text-sm text-gray-600">Loading Live Preview...</p>
          </div>
        </div>
      {:else if error}
        <div class="flex h-48 items-center justify-center">
          <div class="text-center text-red-600">
            <p class="font-medium">Error Loading Live Preview</p>
            <p class="mt-1 text-sm">{error}</p>
          </div>
        </div>
      {:else if !liveContent}
        <div class="flex h-48 items-center justify-center">
          <div class="text-center text-gray-500">
            <p class="font-medium">📖 Live Preview (Decoded)</p>
            <p class="mt-1 text-sm">Upload SVG to see live decoded preview</p>
          </div>
        </div>
      {:else}
        {@html liveContent}
      {/if}
    </div>
  </div>
</div>
