<script lang="ts">
  import { apiClient } from '$lib/api';
  import { Badge } from '$lib/components/ui/badge';
  import { Button } from '$lib/components/ui/button';
  import { Progress } from '$lib/components/ui/progress';
  import ZipUpload from '$lib/components/ZipUpload.svelte';
  import type { Font, ZipUploadResponse } from '$lib/types';
  import FileUpload from '$lib/components/FileUpload.svelte';
  import { Card, CardContent } from '$lib/components/ui/card';
  import SVGSelector from '$lib/components/SVGSelector.svelte';

  import { Tabs, TabsList, TabsContent, TabsTrigger } from '$lib/components/ui/tabs';

  import GlyphEditor from '$lib/components/GlyphEditor.svelte';
  import LivePreview from '$lib/components/LivePreview.svelte';
  import SourceOfTruth from '$lib/components/SourceOfTruth.svelte';

  let mappingProgress = $state(0);
  let livePreviewRefresh = $state(0);
  let requiredFonts = $state<string[]>([]);
  let uploadedSvg = $state<File | null>(null);
  let uploadedFonts = $state<Record<string, File>>({});
  let uploadMode = $state<'individual' | 'zip'>('individual');
  let currentStep = $state<'upload' | 'svg-selection' | 'mapping'>('upload');

  let isLoading = $state(false);
  let serverFonts = $state<Font[]>([]);
  let error = $state<string | null>(null);
  let svgFileId = $state<number | null>(null);
  let currentSvgFilename = $state<string | null>(null);
  let zipUploadResult = $state<ZipUploadResponse | null>(null);

  async function handleFileProcessed(data: { file: File; fonts: string[] }) {
    isLoading = true;
    error = null;

    try {
      const response = await apiClient.uploadSvg(data.file);
      svgFileId = response.file_id;
      requiredFonts = response.required_fonts;
    } catch (err) {
      error = `Failed to upload SVG: ${err instanceof Error ? err.message : 'Unknown error'}`;
    } finally {
      isLoading = false;
    }
  }

  async function handleAllFontsUploaded() {
    if (!svgFileId) return;

    isLoading = true;
    error = null;

    try {
      const fontFiles = Object.values(uploadedFonts);
      if (fontFiles.length === 0 && requiredFonts.length > 0) {
        error = 'No fonts to upload';
        return;
      }

      if (fontFiles.length > 0) await apiClient.uploadFonts(svgFileId, fontFiles);

      const fontsResponse = await apiClient.getFonts(svgFileId);
      serverFonts = fontsResponse.fonts;
      currentStep = 'mapping';
    } catch (err) {
      error = `Failed to process fonts: ${err instanceof Error ? err.message : 'Unknown error'}`;
    } finally {
      isLoading = false;
    }
  }

  function handleZipProcessed(data: ZipUploadResponse) {
    zipUploadResult = data;
    if (data.processed_svgs?.length === 1) {
      const svg = data.processed_svgs[0];
      handleSvgSelected(svg.svg_file_id, svg.filename);
    } else currentStep = 'svg-selection';
  }

  async function handleSvgSelected(selectedSvgFileId: number, filename: string) {
    svgFileId = selectedSvgFileId;
    currentSvgFilename = filename;

    isLoading = true;
    error = null;

    try {
      const fontsResponse = await apiClient.getFonts(svgFileId);
      serverFonts = fontsResponse.fonts;
      currentStep = 'mapping';
    } catch (err) {
      error = `Failed to load fonts for SVG: ${err instanceof Error ? err.message : 'Unknown error'}`;
    } finally {
      isLoading = false;
    }
  }

  function resetToUpload() {
    currentStep = 'upload';
    uploadMode = 'individual';
    uploadedSvg = null;
    uploadedFonts = {};
    requiredFonts = [];
    svgFileId = null;
    currentSvgFilename = null;
    serverFonts = [];
    zipUploadResult = null;
    error = null;
    mappingProgress = 0;
  }
</script>

<div class="bg-background flex h-full flex-col">
  <header class="border-border border-b p-4">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-foreground text-xl font-semibold">SVG Font Analyzer</h1>
        <p class="text-muted-foreground text-sm">
          Upload SVG files, analyze font requirements, and map glyphs to characters
        </p>
      </div>
      <div class="flex items-center gap-2">
        <Badge variant={currentStep === 'upload' ? 'default' : 'secondary'}>1. Upload Files</Badge>
        {#if uploadMode === 'zip'}
          <Badge variant={currentStep === 'svg-selection' ? 'default' : 'secondary'}>
            2. Select SVG
          </Badge>
          <Badge variant={currentStep === 'mapping' ? 'default' : 'secondary'}>
            3. Glyph Mapping
          </Badge>
        {:else}
          <Badge variant={currentStep === 'mapping' ? 'default' : 'secondary'}>
            2. Glyph Mapping
          </Badge>
        {/if}
      </div>
    </div>
  </header>

  <div class="flex-1 overflow-hidden">
    {#if currentStep === 'upload'}
      <div class="h-full overflow-y-auto p-8">
        <div class="mx-auto max-w-4xl">
          <Tabs
            value={uploadMode}
            onValueChange={(value) => (uploadMode = value as 'individual' | 'zip')}
          >
            <TabsList class="mb-6 grid w-full grid-cols-2">
              <TabsTrigger value="individual">Individual Files</TabsTrigger>
              <TabsTrigger value="zip">ZIP Upload (Bulk)</TabsTrigger>
            </TabsList>

            <TabsContent value="individual">
              <FileUpload
                bind:uploadedFile={uploadedSvg}
                bind:requiredFonts
                bind:uploadedFonts
                onFileProcessed={handleFileProcessed}
                onAllFontsUploaded={handleAllFontsUploaded}
              />
            </TabsContent>

            <TabsContent value="zip">
              <ZipUpload onZipProcessed={handleZipProcessed} />
            </TabsContent>
          </Tabs>

          {#if isLoading}
            <Card class="mt-6">
              <CardContent class="py-8 text-center">
                <div class="text-primary inline-flex items-center gap-2">
                  <div
                    class="border-primary h-4 w-4 animate-spin rounded-full border-2 border-t-transparent"
                  ></div>
                  <span class="text-sm font-medium">
                    {uploadMode === 'zip'
                      ? 'Processing ZIP file...'
                      : uploadedSvg && !requiredFonts.length
                        ? 'Processing SVG file...'
                        : 'Processing fonts...'}
                  </span>
                </div>
              </CardContent>
            </Card>
          {/if}

          {#if error}
            <Card class="mt-6 border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-950/20">
              <CardContent class="py-4">
                <div class="flex items-center gap-2 text-red-700 dark:text-red-300">
                  <div class="flex h-4 w-4 items-center justify-center rounded-full bg-red-600">
                    <span class="text-xs text-white">!</span>
                  </div>
                  <span class="text-sm font-medium">{error}</span>
                </div>
              </CardContent>
            </Card>
          {/if}
        </div>
      </div>
    {:else if currentStep === 'svg-selection'}
      <div class="h-full overflow-y-auto p-8">
        <div class="mx-auto max-w-4xl">
          <SVGSelector onSvgSelected={handleSvgSelected} />

          {#if isLoading}
            <Card class="mt-6">
              <CardContent class="py-8 text-center">
                <div class="text-primary inline-flex items-center gap-2">
                  <div
                    class="border-primary h-4 w-4 animate-spin rounded-full border-2 border-t-transparent"
                  ></div>
                  <span class="text-sm font-medium">Loading fonts...</span>
                </div>
              </CardContent>
            </Card>
          {/if}

          {#if error}
            <Card class="mt-6 border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-950/20">
              <CardContent class="py-4">
                <div class="flex items-center gap-2 text-red-700 dark:text-red-300">
                  <div class="flex h-4 w-4 items-center justify-center rounded-full bg-red-600">
                    <span class="text-xs text-white">!</span>
                  </div>
                  <span class="text-sm font-medium">{error}</span>
                </div>
              </CardContent>
            </Card>
          {/if}
        </div>
      </div>
    {:else if currentStep === 'mapping'}
      <div class="flex h-full">
        <div class="border-border w-1/3 border-r">
          <div class="flex h-full flex-col">
            <div class="border-border border-b p-4">
              <h3 class="text-foreground font-semibold">🔍 Source of Truth (Raw Symbols)</h3>
              <p class="text-muted-foreground text-xs">
                Shows raw obfuscated symbols without any font styling
              </p>
              {#if currentSvgFilename}
                <p class="text-primary mt-1 text-xs">📄 {currentSvgFilename}</p>
              {/if}
            </div>
            <div class="flex-1 overflow-auto">
              <SourceOfTruth {svgFileId} />
            </div>
          </div>
        </div>

        <div class="border-border w-1/3 border-r">
          <div class="flex h-full flex-col">
            <div class="border-border border-b p-4">
              <h3 class="text-foreground font-semibold">📖 Live Preview (Decoded)</h3>
              <p class="text-muted-foreground text-xs">
                Updates in real-time as you map glyphs to show decoded text
              </p>
            </div>
            <div class="flex-1 overflow-auto">
              <LivePreview {svgFileId} fonts={serverFonts} refreshTrigger={livePreviewRefresh} />
            </div>
          </div>
        </div>

        <div class="w-1/3">
          <div class="flex h-full flex-col">
            <div class="border-border border-b p-4">
              <div class="flex items-center justify-between">
                <div>
                  <h3 class="text-foreground font-semibold">Glyph Editor</h3>
                  <p class="text-muted-foreground text-xs">Map glyphs to characters</p>
                </div>
                <Badge variant="outline">{mappingProgress}% Complete</Badge>
              </div>
              <Progress value={mappingProgress} class="mt-2" />
            </div>
            <div class="flex-1 overflow-auto">
              <GlyphEditor
                fonts={serverFonts}
                {svgFileId}
                bind:mappingProgress
                onMappingChanged={() => livePreviewRefresh++}
              />
            </div>
          </div>
        </div>
      </div>
    {/if}
  </div>

  <footer class="border-border border-t p-4">
    <div class="text-muted-foreground flex items-center justify-between text-sm">
      <div>SVG Font Analyzer v1.0.0</div>
      <div class="flex items-center gap-4">
        {#if currentStep !== 'upload'}
          <Button
            variant="outline"
            size="sm"
            onclick={() => {
              if (currentStep === 'mapping') {
                currentStep = uploadMode === 'zip' ? 'svg-selection' : 'upload';
              } else if (currentStep === 'svg-selection') {
                currentStep = 'upload';
              }
            }}
          >
            ← Back
          </Button>
        {/if}
        {#if currentStep === 'upload' && uploadMode === 'zip'}
          <Button variant="ghost" size="sm" onclick={resetToUpload}>Reset</Button>
        {/if}
        <div>Ready to analyze your fonts</div>
      </div>
    </div>
  </footer>
</div>
