<script lang="ts">
  import { apiClient } from "$lib/api";
  import type { Font, Glyph } from "$lib/types";
  import { Input } from "$lib/components/ui/input";
  import { Badge } from "$lib/components/ui/badge";
  import { Button } from "$lib/components/ui/button";

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

    mappingProgress =
      totalGlyphs > 0 ? Math.round((mappedGlyphs / totalGlyphs) * 100) : 0;
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
      console.error("Failed to update glyph mapping:", error);
    }
  }

  async function applyBulkMapping(font: Font) {
    const value = bulkMappingValues[font.font_id];
    if (!value || !value.trim()) return;

    const unmappedGlyphs = font.glyphs.filter((g) => !g.is_mapped);
    const promises = unmappedGlyphs.map((glyph) =>
      updateMapping(glyph, value.trim())
    );

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

  function handleKeydown(
    event: KeyboardEvent,
    currentIndex: number,
    fontGlyphs: Glyph[]
  ) {
    if (event.key === "ArrowDown" || event.key === "Enter") {
      event.preventDefault();
      const nextIndex = currentIndex + 1;
      if (nextIndex < fontGlyphs.length) {
        const nextInput = document.querySelector(
          `[data-glyph-input="${fontGlyphs[nextIndex].glyph_id}"]`
        ) as HTMLInputElement;
        nextInput?.focus();
      }
    } else if (event.key === "ArrowUp") {
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
    return fonts.reduce(
      (total: number, font: Font) => total + font.glyphs.length,
      0
    );
  }

  function getMappedGlyphsCount() {
    return fonts.reduce(
      (total: number, font: Font) =>
        total + font.glyphs.filter((g: Glyph) => g.is_mapped).length,
      0
    );
  }

  function getUnmappedGlyphsForFont(font: Font) {
    return font.glyphs.filter((g) => !g.is_mapped).length;
  }
</script>

<div class="h-full overflow-auto">
  {#if fonts.length === 0}
    <div class="flex items-center justify-center h-64 text-muted-foreground">
      <div class="text-center">
        <div class="text-lg font-medium mb-2">No fonts loaded</div>
        <div class="text-sm">Upload fonts to start mapping glyphs</div>
      </div>
    </div>
  {:else}
    <div
      class="sticky top-0 bg-background/95 backdrop-blur-sm border-b border-border/50 p-3 mb-4"
    >
      <div class="flex items-center justify-between">
        <div class="text-sm text-muted-foreground">
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
          <div
            class="flex items-center justify-between py-2 px-1 border-b border-border/50"
          >
            <div class="flex items-center gap-2">
              <div class="text-sm font-semibold text-foreground">
                {font.font_name}
              </div>
              <div class="text-xs text-muted-foreground">{font.filename}</div>
            </div>
            <Badge variant="outline" class="text-xs h-5">
              {font.glyphs.filter((glyph: Glyph) => glyph.is_mapped).length} / {font
                .glyphs.length}
            </Badge>
          </div>

          <div class="space-y-0.5">
            {#each font.glyphs as glyph, index}
              <div
                class="flex items-center gap-2 py-1.5 px-1 hover:bg-muted/30 rounded-sm group transition-colors"
              >
                <div class="size-10 flex-shrink-0">
                  {#if glyph.preview_image}
                    <img
                      src={glyph.preview_image}
                      alt={glyph.codepoint}
                      class="w-full h-full object-contain rounded-sm"
                      onerror={(e) => {
                        const img = e.target as HTMLImageElement;
                        img.style.display = "none";
                        const fallback = img.nextElementSibling as HTMLElement;
                        if (fallback) fallback.style.display = "flex";
                      }}
                    />
                    <div
                      class="w-full h-full bg-muted/50 rounded-sm flex items-center justify-center text-[8px] text-muted-foreground font-mono"
                      style="display:none"
                    >
                      ?
                    </div>
                  {:else}
                    <div
                      class="w-full h-full bg-muted/50 rounded-sm flex items-center justify-center text-[8px] text-muted-foreground font-mono"
                    >
                      ?
                    </div>
                  {/if}
                </div>

                <div class="w-16 flex-shrink-0">
                  <div
                    class="text-xs font-mono text-foreground truncate"
                    title={glyph.codepoint}
                  >
                    {glyph.codepoint.length > 8
                      ? glyph.codepoint.substring(0, 7) + "…"
                      : glyph.codepoint}
                  </div>
                </div>

                <div class="flex-1 min-w-0">
                  <Input
                    type="text"
                    placeholder="Map to character"
                    value={glyph.mapping}
                    data-glyph-input={glyph.glyph_id}
                    class="h-7 text-xs border-transparent bg-transparent group-hover:border-border group-hover:bg-background focus:border-ring focus:bg-background transition-colors"
                    oninput={(e) => {
                      const target = e.target as HTMLInputElement;
                      updateMapping(glyph, target.value);
                    }}
                    onkeydown={(e) => handleKeydown(e, index, font.glyphs)}
                  />
                </div>

                <div class="flex-shrink-0">
                  {#if glyph.is_mapped}
                    <Badge
                      variant="default"
                      class="h-5 text-[10px] px-1.5 bg-green-500 hover:bg-green-500"
                    >
                      ✓
                    </Badge>
                  {:else}
                    <Badge
                      variant="secondary"
                      class="h-5 text-[10px] px-1.5 opacity-40"
                    >
                      −
                    </Badge>
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
        class="fixed inset-0 bg-background/80 backdrop-blur-sm flex items-center justify-center z-50"
      >
        <div
          class="bg-background border border-border rounded-lg p-6 min-w-96 max-w-lg max-h-[80vh] overflow-auto"
        >
          <div class="flex items-center justify-between mb-4">
            <div class="text-lg font-semibold">Bulk Fill Unmapped Glyphs</div>
            <Button variant="ghost" size="sm" onclick={closeBulkMode}>✕</Button>
          </div>

          <div class="text-sm text-muted-foreground mb-6">
            Set a value for all unmapped glyphs in each font. Only
            empty/unmapped glyphs will be filled.
          </div>

          <div class="space-y-4">
            {#each fonts as font}
              {@const unmappedCount = getUnmappedGlyphsForFont(font)}
              <div class="p-3 border border-border rounded-lg">
                <div class="flex items-center justify-between mb-2">
                  <div>
                    <div class="text-sm font-medium">{font.font_name}</div>
                    <div class="text-xs text-muted-foreground">
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
                  <div
                    class="text-xs text-green-600 bg-green-50 dark:bg-green-950/20 p-2 rounded"
                  >
                    ✓ All glyphs in this font are already mapped
                  </div>
                {/if}
              </div>
            {/each}
          </div>

          <div
            class="flex items-center justify-between mt-6 pt-4 border-t border-border"
          >
            <Button variant="outline" onclick={closeBulkMode}>Cancel</Button>
            <Button
              variant="default"
              onclick={applyAllBulkMappings}
              disabled={!Object.values(bulkMappingValues).some((val) =>
                val?.trim()
              )}
            >
              Apply All
            </Button>
          </div>
        </div>
      </div>
    {/if}
  {/if}
</div>
