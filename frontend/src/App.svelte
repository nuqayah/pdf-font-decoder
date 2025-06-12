<script lang="ts">
  import { apiClient } from "$lib/api";
  import type { Font, ZipUploadResponse } from "$lib/types";
  import { Badge } from "$lib/components/ui/badge";
  import { Button } from "$lib/components/ui/button";
  import { Progress } from "$lib/components/ui/progress";
  import FileUpload from "$lib/components/FileUpload.svelte";
  import ZipUpload from "$lib/components/ZipUpload.svelte";
  import SVGSelector from "$lib/components/SVGSelector.svelte";
  import { Card, CardContent } from "$lib/components/ui/card";
  import {
    Tabs,
    TabsContent,
    TabsList,
    TabsTrigger,
  } from "$lib/components/ui/tabs";
  import GlyphEditor from "$lib/components/GlyphEditor.svelte";
  import LivePreview from "$lib/components/LivePreview.svelte";
  import SourceOfTruth from "$lib/components/SourceOfTruth.svelte";

  let mappingProgress = $state(0);
  let livePreviewRefresh = $state(0);
  let requiredFonts = $state<string[]>([]);
  let uploadedSvg = $state<File | null>(null);
  let uploadedFonts = $state<Record<string, File>>({});
  let currentStep = $state<"upload" | "svg-selection" | "mapping">("upload");
  let uploadMode = $state<"individual" | "zip">("individual");

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
      error = `Failed to upload SVG: ${err instanceof Error ? err.message : "Unknown error"}`;
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
        error = "No fonts to upload";
        return;
      }

      if (fontFiles.length > 0) {
        await apiClient.uploadFonts(svgFileId, fontFiles);
      }
      const fontsResponse = await apiClient.getFonts(svgFileId);
      serverFonts = fontsResponse.fonts;
      currentStep = "mapping";
    } catch (err) {
      error = `Failed to process fonts: ${err instanceof Error ? err.message : "Unknown error"}`;
    } finally {
      isLoading = false;
    }
  }

  function handleZipProcessed(data: ZipUploadResponse) {
    zipUploadResult = data;
    if (data.processed_svgs?.length === 1) {
      const svg = data.processed_svgs[0];
      handleSvgSelected(svg.svg_file_id, svg.filename);
    } else {
      currentStep = "svg-selection";
    }
  }

  async function handleSvgSelected(
    selectedSvgFileId: number,
    filename: string
  ) {
    svgFileId = selectedSvgFileId;
    currentSvgFilename = filename;

    isLoading = true;
    error = null;

    try {
      const fontsResponse = await apiClient.getFonts(svgFileId);
      serverFonts = fontsResponse.fonts;
      currentStep = "mapping";
    } catch (err) {
      error = `Failed to load fonts for SVG: ${err instanceof Error ? err.message : "Unknown error"}`;
    } finally {
      isLoading = false;
    }
  }

  function resetToUpload() {
    currentStep = "upload";
    uploadMode = "individual";
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

<div class="h-full flex flex-col bg-background">
  <header class="border-b border-border p-4">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-xl font-semibold text-foreground">SVG Font Analyzer</h1>
        <p class="text-sm text-muted-foreground">
          Upload SVG files, analyze font requirements, and map glyphs to
          characters
        </p>
      </div>
      <div class="flex items-center gap-2">
        <Badge variant={currentStep === "upload" ? "default" : "secondary"}>
          1. Upload Files
        </Badge>
        {#if uploadMode === "zip"}
          <Badge
            variant={currentStep === "svg-selection" ? "default" : "secondary"}
          >
            2. Select SVG
          </Badge>
          <Badge variant={currentStep === "mapping" ? "default" : "secondary"}>
            3. Glyph Mapping
          </Badge>
        {:else}
          <Badge variant={currentStep === "mapping" ? "default" : "secondary"}>
            2. Glyph Mapping
          </Badge>
        {/if}
      </div>
    </div>
  </header>

  <div class="flex-1 overflow-hidden">
    {#if currentStep === "upload"}
      <div class="h-full overflow-y-auto p-8">
        <div class="max-w-4xl mx-auto">
          <Tabs
            value={uploadMode}
            onValueChange={(value) =>
              (uploadMode = value as "individual" | "zip")}
          >
            <TabsList class="grid w-full grid-cols-2 mb-6">
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
              <CardContent class="text-center py-8">
                <div class="inline-flex items-center gap-2 text-primary">
                  <div
                    class="w-4 h-4 border-2 border-primary border-t-transparent rounded-full animate-spin"
                  ></div>
                  <span class="text-sm font-medium">
                    {uploadMode === "zip"
                      ? "Processing ZIP file..."
                      : uploadedSvg && !requiredFonts.length
                        ? "Processing SVG file..."
                        : "Processing fonts..."}
                  </span>
                </div>
              </CardContent>
            </Card>
          {/if}

          {#if error}
            <Card
              class="mt-6 border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-950/20"
            >
              <CardContent class="py-4">
                <div
                  class="flex items-center gap-2 text-red-700 dark:text-red-300"
                >
                  <div
                    class="w-4 h-4 rounded-full bg-red-600 flex items-center justify-center"
                  >
                    <span class="text-white text-xs">!</span>
                  </div>
                  <span class="text-sm font-medium">{error}</span>
                </div>
              </CardContent>
            </Card>
          {/if}
        </div>
      </div>
    {:else if currentStep === "svg-selection"}
      <div class="h-full overflow-y-auto p-8">
        <div class="max-w-4xl mx-auto">
          <SVGSelector onSvgSelected={handleSvgSelected} />
        </div>
      </div>
    {:else if currentStep === "mapping"}
      <div class="h-full flex">
        <div class="w-1/3 border-r border-border">
          <div class="h-full flex flex-col">
            <div class="p-4 border-b border-border">
              <h3 class="font-semibold text-foreground">
                🔍 Source of Truth (Raw Symbols)
              </h3>
              <p class="text-xs text-muted-foreground">
                Shows raw obfuscated symbols without any font styling
              </p>
              {#if currentSvgFilename}
                <p class="text-xs text-primary mt-1">📄 {currentSvgFilename}</p>
              {/if}
            </div>
            <div class="flex-1 overflow-auto">
              <SourceOfTruth {svgFileId} />
            </div>
          </div>
        </div>

        <div class="w-1/3 border-r border-border">
          <div class="h-full flex flex-col">
            <div class="p-4 border-b border-border">
              <h3 class="font-semibold text-foreground">
                📖 Live Preview (Decoded)
              </h3>
              <p class="text-xs text-muted-foreground">
                Updates in real-time as you map glyphs to show decoded text
              </p>
            </div>
            <div class="flex-1 overflow-auto">
              <LivePreview
                {svgFileId}
                fonts={serverFonts}
                refreshTrigger={livePreviewRefresh}
              />
            </div>
          </div>
        </div>

        <div class="w-1/3">
          <div class="h-full flex flex-col">
            <div class="p-4 border-b border-border">
              <div class="flex items-center justify-between">
                <div>
                  <h3 class="font-semibold text-foreground">Glyph Editor</h3>
                  <p class="text-xs text-muted-foreground">
                    Map glyphs to characters
                  </p>
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

  <footer class="border-t border-border p-4">
    <div
      class="flex items-center justify-between text-sm text-muted-foreground"
    >
      <div>SVG Font Analyzer v1.0.0</div>
      <div class="flex items-center gap-4">
        {#if currentStep !== "upload"}
          <Button
            variant="outline"
            size="sm"
            onclick={() => {
              if (currentStep === "mapping") {
                currentStep = uploadMode === "zip" ? "svg-selection" : "upload";
              } else if (currentStep === "svg-selection") {
                currentStep = "upload";
              }
            }}
          >
            ← Back
          </Button>
        {/if}
        {#if currentStep === "upload" && uploadMode === "zip"}
          <Button variant="ghost" size="sm" onclick={resetToUpload}
            >Reset</Button
          >
        {/if}
        <div>Ready to analyze your fonts</div>
      </div>
    </div>
  </footer>
</div>
