<script lang="ts">
  import { apiClient } from '$lib/api';
  import { Badge } from '$lib/components/ui/badge';
  import { Button } from '$lib/components/ui/button';
  import { Input } from '$lib/components/ui/input';
  import type { Font, Glyph } from '$lib/types';

  let {
    fonts,
    svgFileId,
    onMappingChanged,
    mappingProgress = $bindable(),
  } = $props<{
    fonts: Font[];
    mappingProgress: number;
    svgFileId: number | null;
    onMappingChanged: () => void;
  }>();

  let bulkMappingMode = $state(false);
  let bulkMappingValues = $state<Record<number, string>>({});

  $effect(() => {
    calculateProgress();
  });

  function calculateProgress() {
    let totalGlyphs = 0;
    let mappedGlyphs = 0;

    fonts.forEach((font: Font) => {
      font.glyphs.forEach((glyph: Glyph) => {
        totalGlyphs++;
        if (glyph.mapping && glyph.mapping.trim()) mappedGlyphs++;
      });
    });

    mappingProgress = totalGlyphs > 0 ? Math.round((mappedGlyphs / totalGlyphs) * 100) : 0;
  }

  async function updateMapping(glyph: Glyph, mapping: string) {
    if (!svgFileId) return;

    try {
      await apiClient.updateGlyphMapping(glyph.glyph_id, mapping);
      glyph.mapping = mapping;
      glyph.is_mapped = !!mapping.trim();
      calculateProgress();
      onMappingChanged?.();
    } catch (error) {
      console.error('Failed to update glyph mapping:', error);
    }
  }

  async function applyBulkMapping(font: Font) {
    const value = bulkMappingValues[font.font_id];
    if (!value || !value.trim()) return;

    const unmappedGlyphs = font.glyphs.filter((g) => !g.is_mapped);
    const promises = unmappedGlyphs.map((glyph) => updateMapping(glyph, value.trim()));

    await Promise.all(promises);
  }

  async function applyAllBulkMappings() {
    const promises = fonts.map((font: Font) => applyBulkMapping(font));
    await Promise.all(promises);

    bulkMappingValues = {};
    bulkMappingMode = false;
  }

  function closeBulkMode() {
    bulkMappingMode = false;
    bulkMappingValues = {};
  }

  function handleKeydown(event: KeyboardEvent, currentIndex: number, fontGlyphs: Glyph[]) {
    if (event.key === 'ArrowDown' || event.key === 'Enter') {
      event.preventDefault();
      const nextIndex = currentIndex + 1;
      if (nextIndex < fontGlyphs.length) {
        const nextInput = document.querySelector(
          `[data-glyph-input="${fontGlyphs[nextIndex].glyph_id}"]`
        ) as HTMLInputElement;
        nextInput?.focus();
      }
    } else if (event.key === 'ArrowUp') {
      event.preventDefault();
      const prevIndex = currentIndex - 1;
      if (prevIndex >= 0) {
        const prevInput = document.querySelector(
          `[data-glyph-input="${fontGlyphs[prevIndex].glyph_id}"]`
        ) as HTMLInputElement;
        prevInput?.focus();
      }
    }
  }

  function getTotalGlyphsCount() {
    return fonts.reduce((total: number, font: Font) => total + font.glyphs.length, 0);
  }

  function getMappedGlyphsCount() {
    return fonts.reduce(
      (total: number, font: Font) => total + font.glyphs.filter((g: Glyph) => g.is_mapped).length,
      0
    );
  }

  function getUnmappedGlyphsForFont(font: Font) {
    return font.glyphs.filter((g) => !g.is_mapped).length;
  }
</script>

<div class="h-full overflow-auto">
  {#if fonts.length === 0}
    <div class="text-muted-foreground flex h-64 items-center justify-center">
      <div class="text-center">
        <div class="mb-2 text-lg font-medium">No fonts loaded</div>
        <div class="text-sm">Upload fonts to start mapping glyphs</div>
      </div>
    </div>
  {:else}
    <div class="bg-background/95 border-border/50 sticky top-0 mb-4 border-b p-3 backdrop-blur-sm">
      <div class="flex items-center justify-between">
        <div class="text-muted-foreground text-sm">
          {getMappedGlyphsCount()} of {getTotalGlyphsCount()} glyphs mapped across
          {fonts.length} fonts
        </div>
        <div class="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            class="h-7 text-xs"
            onclick={() => (bulkMappingMode = true)}
          >
            Bulk Fill
          </Button>
        </div>
      </div>
    </div>

    <div class="space-y-6 px-1">
      {#each fonts as font}
        <div class="space-y-1">
          <div class="border-border/50 flex items-center justify-between border-b px-1 py-2">
            <div class="flex items-center gap-2">
              <div class="text-foreground text-sm font-semibold">
                {font.font_name}
              </div>
              <div class="text-muted-foreground text-xs">{font.filename}</div>
            </div>
            <Badge variant="outline" class="h-5 text-xs">
              {font.glyphs.filter((glyph: Glyph) => glyph.is_mapped).length} / {font.glyphs.length}
            </Badge>
          </div>

          <div class="space-y-0.5">
            {#each font.glyphs as glyph, index}
              <div
                class="hover:bg-muted/30 group flex items-center gap-2 rounded-sm px-1 py-1.5 transition-colors"
              >
                <div class="size-10 shrink-0">
                  {#if glyph.preview_image}
                    <img
                      src={glyph.preview_image}
                      alt={glyph.codepoint}
                      class="h-full w-full rounded-sm object-contain"
                      onerror={(e) => {
                        const img = e.target as HTMLImageElement;
                        img.style.display = 'none';
                        const fallback = img.nextElementSibling as HTMLElement;
                        if (fallback) fallback.style.display = 'flex';
                      }}
                    />
                    <div
                      class="bg-muted/50 text-muted-foreground flex h-full w-full items-center justify-center rounded-sm font-mono text-[8px]"
                      style="display:none"
                    >
                      ?
                    </div>
                  {:else}
                    <div
                      class="bg-muted/50 text-muted-foreground flex h-full w-full items-center justify-center rounded-sm font-mono text-[8px]"
                    >
                      ?
                    </div>
                  {/if}
                </div>

                <div class="w-16 shrink-0">
                  <div class="text-foreground truncate font-mono text-xs" title={glyph.codepoint}>
                    {glyph.codepoint.length > 8
                      ? glyph.codepoint.substring(0, 7) + '…'
                      : glyph.codepoint}
                  </div>
                </div>

                <div class="min-w-0 flex-1">
                  <Input
                    type="text"
                    placeholder="Map to character"
                    value={glyph.mapping}
                    data-glyph-input={glyph.glyph_id}
                    class="group-hover:border-border group-hover:bg-background focus:border-ring focus:bg-background h-7 border-transparent bg-transparent text-xs transition-colors"
                    oninput={(e) => {
                      const target = e.target as HTMLInputElement;
                      updateMapping(glyph, target.value);
                    }}
                    onkeydown={(e) => handleKeydown(e, index, font.glyphs)}
                  />
                </div>

                <div class="shrink-0">
                  {#if glyph.is_mapped}
                    <Badge
                      variant="default"
                      class="h-5 bg-green-500 px-1.5 text-[10px] hover:bg-green-500"
                    >
                      ✓
                    </Badge>
                  {:else}
                    <Badge variant="secondary" class="h-5 px-1.5 text-[10px] opacity-40">−</Badge>
                  {/if}
                </div>
              </div>
            {/each}
          </div>
        </div>
      {/each}
    </div>

    {#if bulkMappingMode}
      <div
        class="bg-background/80 fixed inset-0 z-50 flex items-center justify-center backdrop-blur-sm"
      >
        <div
          class="bg-background border-border max-h-[80vh] max-w-lg min-w-96 overflow-auto rounded-lg border p-6"
        >
          <div class="mb-4 flex items-center justify-between">
            <div class="text-lg font-semibold">Bulk Fill Unmapped Glyphs</div>
            <Button variant="ghost" size="sm" onclick={closeBulkMode}>✕</Button>
          </div>

          <div class="text-muted-foreground mb-6 text-sm">
            Set a value for all unmapped glyphs in each font. Only empty/unmapped glyphs will be
            filled.
          </div>

          <div class="space-y-4">
            {#each fonts as font}
              {@const unmappedCount = getUnmappedGlyphsForFont(font)}
              <div class="border-border rounded-lg border p-3">
                <div class="mb-2 flex items-center justify-between">
                  <div>
                    <div class="text-sm font-medium">{font.font_name}</div>
                    <div class="text-muted-foreground text-xs">
                      {unmappedCount} unmapped glyphs
                    </div>
                  </div>
                  <Badge variant="outline" class="text-xs">
                    {font.glyphs.filter((g: Glyph) => g.is_mapped).length} /
                    {font.glyphs.length}
                  </Badge>
                </div>

                {#if unmappedCount > 0}
                  <div class="flex items-center gap-2">
                    <Input
                      type="text"
                      placeholder="Value to fill (e.g., 'A', ' ', '?')"
                      bind:value={bulkMappingValues[font.font_id]}
                      class="flex-1 text-sm"
                    />
                    <Button
                      variant="default"
                      size="sm"
                      onclick={() => applyBulkMapping(font)}
                      disabled={!bulkMappingValues[font.font_id]?.trim()}
                      class="whitespace-nowrap"
                    >
                      Fill {unmappedCount}
                    </Button>
                  </div>
                {:else}
                  <div class="rounded bg-green-50 p-2 text-xs text-green-600 dark:bg-green-950/20">
                    ✓ All glyphs in this font are already mapped
                  </div>
                {/if}
              </div>
            {/each}
          </div>

          <div class="border-border mt-6 flex items-center justify-between border-t pt-4">
            <Button variant="outline" onclick={closeBulkMode}>Cancel</Button>
            <Button
              variant="default"
              onclick={applyAllBulkMappings}
              disabled={!Object.values(bulkMappingValues).some((val) => val?.trim())}
            >
              Apply All
            </Button>
          </div>
        </div>
      </div>
    {/if}
  {/if}
</div>
