<script lang="ts">
  import {
    UploadCloud,
    FileText,
    CheckCircle,
    AlertCircle,
    X,
  } from "@lucide/svelte";
  import { Button } from "$lib/components/ui/button";
  import {
    Card,
    CardContent,
    CardHeader,
    CardTitle,
  } from "$lib/components/ui/card";
  import { Badge } from "$lib/components/ui/badge";
  import { Progress } from "$lib/components/ui/progress";
  import { Separator } from "$lib/components/ui/separator";

  let {
    uploadedFile = $bindable(),
    requiredFonts = $bindable(),
    uploadedFonts = $bindable(),
    onFileProcessed,
    onAllFontsUploaded,
  } = $props<{
    uploadedFile: File | null;
    requiredFonts: string[];
    uploadedFonts: Record<string, File>;
    onFileProcessed: (data: { file: File; fonts: string[] }) => void;
    onAllFontsUploaded: () => void;
  }>();

  let fileInput = $state<HTMLInputElement>();
  let fontFileInput = $state<HTMLInputElement>();
  let dragOver = $state(false);
  let dragOverType = $state<"svg" | "fonts" | null>(null);

  let uploadProgress = $derived(
    requiredFonts.length > 0
      ? (Object.keys(uploadedFonts).length / requiredFonts.length) * 100
      : 0
  );

  // Drag and drop handling
  function handleSvgSelect(event: Event) {
    const target = event.target as HTMLInputElement;
    const file = target.files?.[0];
    if (file && file.type === "image/svg+xml") {
      processFile(file);
    }
  }

  function handleFontSelect(event: Event) {
    const target = event.target as HTMLInputElement;
    const files = Array.from(target.files || []);
    processFontFiles(files);
  }

  function handleDrop(event: DragEvent) {
    event.preventDefault();
    dragOver = false;
    dragOverType = null;

    const files = Array.from(event.dataTransfer?.files || []);
    const svgFile = files.find((file) => file.type === "image/svg+xml");
    const fontFiles = files.filter(
      (file) => file.name.endsWith(".woff") || file.name.endsWith(".woff2")
    );

    if (svgFile && !uploadedFile) {
      processFile(svgFile);
    }

    if (fontFiles.length > 0 && uploadedFile) {
      processFontFiles(fontFiles);
    }
  }

  function handleDragOver(event: DragEvent) {
    event.preventDefault();
    dragOver = true;

    const files = Array.from(event.dataTransfer?.items || []);
    const hasSvg = files.some((item) => item.type === "image/svg+xml");
    const hasFonts = files.some(
      (item) =>
        item.type.includes("font") ||
        item.type.includes("woff") ||
        (item.kind === "file" &&
          (item.getAsFile()?.name.endsWith(".woff") ||
            item.getAsFile()?.name.endsWith(".woff2")))
    );

    if (hasSvg && !uploadedFile) {
      dragOverType = "svg";
    } else if (hasFonts && uploadedFile) {
      dragOverType = "fonts";
    }
  }

  function handleDragLeave() {
    dragOver = false;
    dragOverType = null;
  }

  function handleKeydown(event: KeyboardEvent, action: () => void) {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      action();
    }
  }

  // File processing with validation
  async function processFile(file: File) {
    uploadedFile = file;
    requiredFonts = [];
    onFileProcessed({ file, fonts: [] });
  }

  function processFontFiles(files: File[]) {
    files.forEach((file) => {
      if (file.name.endsWith(".woff") || file.name.endsWith(".woff2")) {
        const fontName = file.name.replace(/\.(woff2?|ttf|otf)$/i, "");
        const matchedFont = requiredFonts.find(
          (required: string) =>
            required.toLowerCase().includes(fontName.toLowerCase()) ||
            fontName.toLowerCase().includes(required.toLowerCase())
        );

        if (matchedFont) {
          uploadedFonts[matchedFont] = file;
        } else {
          const availableFont = requiredFonts.find(
            (font: string) => !uploadedFonts[font]
          );
          if (availableFont) {
            uploadedFonts[availableFont] = file;
          }
        }
      }
    });
    uploadedFonts = { ...uploadedFonts };
  }

  function removeFontFile(fontName: string) {
    delete uploadedFonts[fontName];
    uploadedFonts = { ...uploadedFonts };
  }

  function removeUploadedFile() {
    uploadedFile = null;
    requiredFonts = [];
    uploadedFonts = {};
  }

  // Progress tracking and user feedback
  $effect(() => {
    if (uploadProgress === 100 && requiredFonts.length > 0) {
      setTimeout(() => {
        onAllFontsUploaded();
      }, 500);
    }
  });
</script>

<div class="space-y-6">
  <!-- SVG Upload Section -->
  <Card class="relative">
    <CardHeader>
      <CardTitle class="flex items-center gap-2">
        <FileText class="w-5 h-5" />
        Step 1: Upload SVG File
      </CardTitle>
    </CardHeader>
    <CardContent>
      {#if !uploadedFile}
        <div
          class="border-2 border-dashed transition-all duration-200 cursor-pointer rounded-lg {dragOver &&
          dragOverType === 'svg'
            ? 'border-primary bg-primary/5 scale-[1.02]'
            : 'border-border hover:border-primary/50'}"
          role="button"
          tabindex="0"
          aria-label="Upload SVG file by clicking or dropping"
          ondragover={handleDragOver}
          ondragleave={handleDragLeave}
          ondrop={handleDrop}
          onclick={() => fileInput?.click()}
          onkeydown={(e) => handleKeydown(e, () => fileInput?.click())}
        >
          <div
            class="flex flex-col items-center justify-center p-8 text-center"
          >
            <UploadCloud class="w-12 h-12 mb-4 text-muted-foreground" />
            <h3 class="text-lg font-semibold text-foreground mb-2">
              Drop your SVG file here
            </h3>
            <p class="text-sm text-muted-foreground mb-4">or click to browse</p>
            <Button variant="outline" size="sm">Choose SVG File</Button>
          </div>
        </div>
      {:else}
        <div
          class="flex items-center justify-between p-4 bg-green-50 dark:bg-green-950/20 border border-green-200 dark:border-green-800 rounded-lg"
        >
          <div class="flex items-center gap-3">
            <CheckCircle class="w-5 h-5 text-green-600" />
            <div>
              <p class="font-medium text-green-800 dark:text-green-200">
                {uploadedFile.name}
              </p>
              <p class="text-sm text-green-600 dark:text-green-400">
                {(uploadedFile.size / 1024).toFixed(1)} KB • {requiredFonts.length}
                font{requiredFonts.length !== 1 ? "s" : ""} detected
              </p>
            </div>
          </div>
          <Button variant="ghost" size="icon" onclick={removeUploadedFile}>
            <X class="w-4 h-4" />
          </Button>
        </div>
      {/if}

      <input
        bind:this={fileInput}
        type="file"
        accept=".svg,image/svg+xml"
        class="hidden"
        oninput={handleSvgSelect}
      />
    </CardContent>
  </Card>

  {#if uploadedFile && requiredFonts.length > 0}
    <Separator />

    <!-- Font Upload Section -->
    <Card class="relative">
      <CardHeader>
        <div class="flex items-center justify-between">
          <CardTitle class="flex items-center gap-2">
            <UploadCloud class="w-5 h-5" />
            Step 2: Upload Font Files
          </CardTitle>
          <Badge variant={uploadProgress === 100 ? "default" : "secondary"}>
            {uploadProgress.toFixed(0)}% Complete
          </Badge>
        </div>
        <p class="text-sm text-muted-foreground">
          Upload all required font files at once. You can drag multiple files or
          select them all together.
        </p>
      </CardHeader>
      <CardContent class="space-y-4">
        <!-- Progress -->
        <div class="space-y-2">
          <div class="flex items-center justify-between text-sm">
            <span class="font-medium">
              {Object.keys(uploadedFonts).length} of {requiredFonts.length} fonts
              uploaded
            </span>
            {#if uploadProgress === 100}
              <span class="text-green-600 font-medium">✓ All fonts ready!</span>
            {/if}
          </div>
          <Progress value={uploadProgress} />
        </div>

        <!-- Bulk Upload Area -->
        {#if uploadProgress < 100}
          <div
            class="border-2 border-dashed transition-all duration-200 cursor-pointer rounded-lg {dragOver &&
            dragOverType === 'fonts'
              ? 'border-primary bg-primary/5 scale-[1.02]'
              : 'border-border hover:border-primary/50'}"
            role="button"
            tabindex="0"
            aria-label="Upload font files by clicking or dropping"
            ondragover={handleDragOver}
            ondragleave={handleDragLeave}
            ondrop={handleDrop}
            onclick={() => fontFileInput?.click()}
            onkeydown={(e) => handleKeydown(e, () => fontFileInput?.click())}
          >
            <div
              class="flex flex-col items-center justify-center p-6 text-center"
            >
              <UploadCloud class="w-8 h-8 mb-3 text-muted-foreground" />
              <h4 class="font-medium text-foreground mb-1">
                Drop font files here or click to select
              </h4>
              <p class="text-sm text-muted-foreground">
                Select multiple .woff or .woff2 files at once
              </p>
            </div>
          </div>
        {/if}

        <!-- Required Fonts List -->
        <div class="space-y-3">
          <h4 class="text-sm font-medium text-foreground">Required Fonts:</h4>
          <div class="grid gap-2">
            {#each requiredFonts as fontName}
              <div
                class="flex items-center justify-between p-3 border rounded-lg"
              >
                <div class="flex items-center gap-2">
                  <div class="font-mono text-sm font-medium">{fontName}</div>
                  {#if uploadedFonts[fontName]}
                    <Badge variant="default" class="text-xs bg-green-500">
                      ✓ {uploadedFonts[fontName].name}
                    </Badge>
                  {:else}
                    <Badge variant="outline" class="text-xs">Required</Badge>
                  {/if}
                </div>
                {#if uploadedFonts[fontName]}
                  <div class="flex items-center gap-2">
                    <span class="text-xs text-muted-foreground">
                      {(uploadedFonts[fontName].size / 1024).toFixed(1)} KB
                    </span>
                    <Button
                      variant="ghost"
                      size="icon"
                      onclick={() => removeFontFile(fontName)}
                    >
                      <X class="w-3 h-3" />
                    </Button>
                  </div>
                {/if}
              </div>
            {/each}
          </div>
        </div>

        <input
          bind:this={fontFileInput}
          type="file"
          accept=".woff,.woff2"
          multiple
          class="hidden"
          oninput={handleFontSelect}
        />

        <!-- Instructions -->
        <div
          class="p-4 bg-blue-50 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-800 rounded-lg"
        >
          <div class="flex items-start gap-3">
            <AlertCircle class="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" />
            <div class="text-sm">
              <p class="font-medium text-blue-800 dark:text-blue-200 mb-1">
                Upload Tips:
              </p>
              <ul class="text-blue-700 dark:text-blue-300 space-y-1">
                <li>
                  • You can upload more font files than required - extras will
                  be ignored
                </li>
                <li>
                  • Drag and drop multiple files at once for faster upload
                </li>
                <li>• Supported formats: .woff, .woff2</li>
                <li>
                  • Font files will be automatically matched to requirements
                </li>
              </ul>
            </div>
          </div>
        </div>

        {#if uploadProgress === 100}
          <div class="text-center p-4">
            <div
              class="inline-flex items-center gap-2 text-green-600 font-medium mb-3"
            >
              <CheckCircle class="w-5 h-5" />
              All required fonts uploaded successfully!
            </div>
            <p class="text-sm text-muted-foreground">
              Proceeding to glyph mapping automatically...
            </p>
          </div>
        {/if}
      </CardContent>
    </Card>
  {/if}

  {#if uploadedFile && requiredFonts.length === 0}
    <!-- No fonts required -->
    <Card>
      <CardContent class="text-center py-8">
        <CheckCircle class="w-12 h-12 mx-auto mb-4 text-green-500" />
        <h3 class="text-lg font-semibold text-foreground mb-2">
          No Font Files Required
        </h3>
        <p class="text-muted-foreground mb-4">
          Your SVG file doesn't require any external font files.
        </p>
        <Button onclick={() => onAllFontsUploaded()}>
          Continue to Processing →
        </Button>
      </CardContent>
    </Card>
  {/if}
</div>
