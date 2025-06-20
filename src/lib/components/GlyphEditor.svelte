<TooltipProvider>
    <div class="h-full overflow-auto">
        {#if fonts.length === 0}
            <div class="text-muted-foreground flex h-64 items-center justify-center text-center">
                <p class="mb-2 text-lg font-medium">No fonts loaded</p>
                <p class="text-sm">Upload fonts to start mapping glyphs</p>
            </div>
        {:else}
            <div
                class="bg-background/95 border-border/50 sticky top-0 mb-4 flex items-center justify-between border-b p-3 backdrop-blur-sm"
            >
                <div class="text-muted-foreground text-sm">
                    {getMappedGlyphsCount()} of {getTotalGlyphsCount()} glyphs mapped across
                    {fonts.length} fonts
                </div>
                <Button
                    variant="outline"
                    size="sm"
                    class="h-7 text-xs"
                    onclick={() => (bulkMappingMode = true)}
                >
                    Bulk Fill
                </Button>
            </div>

            <div class="space-y-6 px-1">
                {#each fonts as font}
                    {@const unmappedCount = getUnmappedGlyphsForFont(font)}
                    <div class="space-y-1">
                        <div
                            class="border-border/50 flex items-center justify-between border-b px-1 py-2"
                        >
                            <div class="flex items-center gap-2">
                                <p class="text-foreground text-sm font-semibold">
                                    {font.font_name}
                                </p>
                                <p class="text-muted-foreground text-xs">{font.filename}</p>
                            </div>
                            <div class="flex items-center gap-2">
                                <div class="flex items-center gap-1">
                                    <Tooltip>
                                        <TooltipTrigger>
                                            <Button
                                                variant="outline"
                                                size="sm"
                                                class="h-7 w-7 p-0"
                                                onclick={() => generatePngPreviews(font)}
                                                disabled={pngGenerationState[font.font_id]?.loading}
                                            >
                                                {#if pngGenerationState[font.font_id]?.loading}
                                                    <Loader2 class="h-4 w-4 animate-spin" />
                                                {:else}
                                                    <Image class="h-4 w-4" />
                                                {/if}
                                            </Button>
                                        </TooltipTrigger>
                                        <TooltipContent>
                                            <p>Generate PNG previews for all glyphs in this font</p>
                                        </TooltipContent>
                                    </Tooltip>

                                    {#if unmappedCount > 0}
                                        <Tooltip>
                                            <TooltipTrigger>
                                                <Button
                                                    variant="outline"
                                                    size="sm"
                                                    class="h-7 w-7 p-0"
                                                    onclick={() => generateSuggestions(font)}
                                                    disabled={aiGenerationState[font.font_id]
                                                        ?.loading}
                                                >
                                                    {#if aiGenerationState[font.font_id]?.loading}
                                                        <Loader2 class="h-4 w-4 animate-spin" />
                                                    {:else}
                                                        <Sparkles class="h-4 w-4" />
                                                    {/if}
                                                </Button>
                                            </TooltipTrigger>
                                            <TooltipContent>
                                                <p>Generate AI suggestions for unmapped glyphs</p>
                                            </TooltipContent>
                                        </Tooltip>
                                    {/if}
                                </div>

                                <div class="flex flex-col items-end gap-1">
                                    {#if pngGenerationState[font.font_id]?.error}
                                        <p class="text-destructive text-right text-xs">
                                            {pngGenerationState[font.font_id].error}
                                        </p>
                                    {/if}
                                    {#if aiGenerationState[font.font_id]?.error}
                                        <p class="text-destructive text-right text-xs">
                                            {aiGenerationState[font.font_id].error}
                                        </p>
                                    {/if}
                                    <Badge variant="outline" class="h-5 text-xs">
                                        {font.glyphs.filter((glyph: Glyph) => glyph.is_mapped)
                                            .length} /
                                        {font.glyphs.length}
                                    </Badge>
                                </div>
                            </div>
                        </div>

                        <div class="space-y-0.5">
                            {#each font.glyphs as glyph, index}
                                <div
                                    class="hover:bg-muted/30 group flex items-center gap-2 rounded-sm px-1 py-1.5 transition-colors"
                                >
                                    <div class="flex w-20 flex-shrink-0 gap-1">
                                        <div class="size-10 flex-shrink-0">
                                            {#if glyph.preview_image}
                                                <img
                                                    src={glyph.preview_image}
                                                    alt={glyph.codepoint}
                                                    class="h-full w-full rounded-sm object-contain"
                                                    onerror={e => {
                                                        const img = e.target as HTMLImageElement
                                                        img.style.display = 'none'
                                                        const fallback =
                                                            img.nextElementSibling as HTMLElement
                                                        if (fallback)
                                                            fallback.style.display = 'flex'
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
                                        <div class="size-10 flex-shrink-0">
                                            {#if glyph.rendered_preview}
                                                <img
                                                    src={glyph.rendered_preview}
                                                    alt={`${glyph.codepoint} rendered`}
                                                    class="bg-background h-full w-full rounded-sm object-contain"
                                                />
                                            {:else}
                                                <div
                                                    class="bg-muted/50 text-muted-foreground flex h-full w-full items-center justify-center rounded-sm font-mono text-[8px]"
                                                >
                                                    -
                                                </div>
                                            {/if}
                                        </div>
                                    </div>

                                    <div class="w-16 flex-shrink-0">
                                        <div
                                            class="text-foreground truncate font-mono text-xs"
                                            title={glyph.codepoint}
                                        >
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
                                            oninput={e => {
                                                const target = e.target as HTMLInputElement
                                                updateMapping(glyph, target.value)
                                            }}
                                            onkeydown={e => handleKeydown(e, index, font.glyphs)}
                                        />
                                    </div>

                                    <div class="flex-shrink-0">
                                        {#if glyph.is_mapped}
                                            <Badge
                                                variant="default"
                                                class="h-5 bg-green-500 px-1.5 text-[10px] hover:bg-green-500"
                                            >
                                                ✓
                                            </Badge>
                                        {:else}
                                            <Badge
                                                variant="secondary"
                                                class="h-5 px-1.5 text-[10px] opacity-40">−</Badge
                                            >
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
                    onclick={handleBackdropClick}
                    onkeydown={handleBackdropKeydown}
                    role="presentation"
                >
                    <div
                        class="bg-background border-border max-h-[80vh] max-w-lg min-w-96 overflow-auto rounded-lg border p-6"
                        role="dialog"
                        aria-modal="true"
                        aria-labelledby="bulk-fill-title"
                    >
                        <div class="mb-4 flex items-center justify-between">
                            <div class="text-lg font-semibold" id="bulk-fill-title">
                                Bulk Fill Unmapped Glyphs
                            </div>
                            <Button variant="ghost" size="sm" onclick={closeBulkMode}>✕</Button>
                        </div>

                        <div class="text-muted-foreground mb-6 text-sm">
                            Set a value for all unmapped glyphs in each font. Only empty/unmapped
                            glyphs will be filled.
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
                                        <div
                                            class="rounded bg-green-50 p-2 text-xs text-green-600 dark:bg-green-950/20"
                                        >
                                            ✓ All glyphs in this font are already mapped
                                        </div>
                                    {/if}
                                </div>
                            {/each}
                        </div>

                        <div
                            class="border-border mt-6 flex items-center justify-between border-t pt-4"
                        >
                            <Button variant="outline" onclick={closeBulkMode}>Cancel</Button>
                            {#if fonts.length > 1}
                                <Button
                                    variant="default"
                                    onclick={applyAllBulkMappings}
                                    disabled={!Object.values(bulkMappingValues).some(val =>
                                        val?.trim(),
                                    )}
                                >
                                    Apply All
                                </Button>
                            {/if}
                        </div>
                    </div>
                </div>
            {/if}
        {/if}
    </div>
</TooltipProvider>

<script lang="ts">
import {apiClient} from '$lib/api'
import type {Font, Glyph} from '$lib/types'
import {Badge} from '$lib/components/ui/badge'
import {Input} from '$lib/components/ui/input'
import {Button} from '$lib/components/ui/button'
import {Tooltip, TooltipContent, TooltipTrigger, TooltipProvider} from '$lib/components/ui/tooltip'
import {Image, Sparkles, Loader2} from '@lucide/svelte'

let {
    fonts,
    svgFileId,
    onMappingChanged,
    mappingProgress = $bindable(),
} = $props<{
    fonts: Font[]
    mappingProgress: number
    svgFileId: number | null
    onMappingChanged: () => void
}>()

let bulkMappingMode = $state(false)
let bulkMappingValues = $state<Record<number, string>>({})
let aiGenerationState = $state<Record<number, {loading: boolean; error: string | null}>>({})
let pngGenerationState = $state<Record<number, {loading: boolean; error: string | null}>>({})

$effect(() => {
    const handleWindowKeyDown = (e: KeyboardEvent) => {
        if (bulkMappingMode && e.key === 'Escape') {
            closeBulkMode()
        }
    }

    window.addEventListener('keydown', handleWindowKeyDown)

    return () => {
        window.removeEventListener('keydown', handleWindowKeyDown)
    }
})

$effect(() => {
    calculateProgress()
})

function calculateProgress() {
    let totalGlyphs = 0
    let mappedGlyphs = 0

    fonts.forEach((font: Font) => {
        font.glyphs.forEach((glyph: Glyph) => {
            totalGlyphs++
            if (glyph.mapping && glyph.mapping.trim()) mappedGlyphs++
        })
    })

    mappingProgress = totalGlyphs > 0 ? Math.round((mappedGlyphs / totalGlyphs) * 100) : 0
}

async function updateMapping(glyph: Glyph, mapping: string) {
    if (!svgFileId) return

    try {
        await apiClient.updateGlyphMapping(glyph.glyph_id, mapping)
        glyph.mapping = mapping
        glyph.is_mapped = !!mapping.trim()
        calculateProgress()
        onMappingChanged?.()
    } catch (error) {
        console.error('Failed to update glyph mapping:', error)
    }
}

async function applyBulkMapping(font: Font) {
    const value = bulkMappingValues[font.font_id]
    if (!value || !value.trim()) return

    const unmappedGlyphs = font.glyphs.filter(g => !g.is_mapped)
    const promises = unmappedGlyphs.map(glyph => updateMapping(glyph, value.trim()))

    await Promise.all(promises)
}

async function applyAllBulkMappings() {
    const promises = fonts.map((font: Font) => applyBulkMapping(font))
    await Promise.all(promises)

    bulkMappingValues = {}
    bulkMappingMode = false
}

function closeBulkMode() {
    bulkMappingMode = false
    bulkMappingValues = {}
}

function handleBackdropClick(event: MouseEvent) {
    if (event.target === event.currentTarget) closeBulkMode()
}

function handleBackdropKeydown(event: KeyboardEvent) {
    if (event.key === 'Escape') closeBulkMode()
}

function handleKeydown(event: KeyboardEvent, currentIndex: number, fontGlyphs: Glyph[]) {
    if (event.key === 'ArrowDown' || event.key === 'Enter') {
        event.preventDefault()
        const nextIndex = currentIndex + 1
        if (nextIndex < fontGlyphs.length) {
            const nextInput = document.querySelector(
                `[data-glyph-input="${fontGlyphs[nextIndex].glyph_id}"]`,
            ) as HTMLInputElement
            nextInput?.focus()
        }
    } else if (event.key === 'ArrowUp') {
        event.preventDefault()
        const prevIndex = currentIndex - 1
        if (prevIndex >= 0) {
            const prevInput = document.querySelector(
                `[data-glyph-input="${fontGlyphs[prevIndex].glyph_id}"]`,
            ) as HTMLInputElement
            prevInput?.focus()
        }
    }
}

function getTotalGlyphsCount() {
    return fonts.reduce((total: number, font: Font) => total + font.glyphs.length, 0)
}

function getMappedGlyphsCount() {
    return fonts.reduce((total: number, font: Font) => {
        return total + font.glyphs.filter((glyph: Glyph) => glyph.is_mapped).length
    }, 0)
}

function getUnmappedGlyphsForFont(font: Font) {
    return font.glyphs.filter((g: Glyph) => !g.is_mapped).length
}

async function generateSuggestions(font: Font) {
    aiGenerationState[font.font_id] = {loading: true, error: null}

    try {
        const result = await apiClient.generateAISuggestions(font.font_id)
        console.log(`AI suggestions generated for font ${font.font_name}:`, result)

        if (svgFileId) {
            const response = await apiClient.getFonts(svgFileId)
            const updatedFont = response.fonts.find((f: Font) => f.font_id === font.font_id)
            if (updatedFont) {
                Object.assign(font, updatedFont)
                calculateProgress()
            }
        }

        onMappingChanged()
        aiGenerationState[font.font_id] = {loading: false, error: null}
    } catch (err) {
        console.error(`Error generating AI suggestions for font ${font.font_name}:`, err)
        aiGenerationState[font.font_id] = {loading: false, error: 'Failed to generate suggestions.'}
    }
}

async function generatePngPreviews(font: Font) {
    pngGenerationState[font.font_id] = {loading: true, error: null}

    try {
        const result = await apiClient.generatePngPreviews(font.font_id)
        console.log(`PNG previews generated for font ${font.font_name}:`, result)

        // Refresh font data to get the new PNG previews
        if (svgFileId) {
            const response = await apiClient.getFonts(svgFileId)
            const updatedFont = response.fonts.find((f: Font) => f.font_id === font.font_id)
            if (updatedFont) {
                Object.assign(font, updatedFont)
            }
        }

        pngGenerationState[font.font_id] = {loading: false, error: null}
    } catch (err) {
        console.error(`Error generating PNG previews for font ${font.font_name}:`, err)
        pngGenerationState[font.font_id] = {
            loading: false,
            error: 'Failed to generate PNG previews.',
        }
    }
}
</script>
