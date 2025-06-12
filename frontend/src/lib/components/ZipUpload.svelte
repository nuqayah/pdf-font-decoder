<script lang="ts">
  import {
    Package,
    UploadCloud,
    CheckCircle,
    AlertCircle,
    FileArchive,
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
  import { apiClient } from "$lib/api";
  import type { ZipUploadResponse, UploadProgress } from "$lib/types";

  let { onZipProcessed } = $props<{
    onZipProcessed: (data: ZipUploadResponse) => void;
  }>();

  let fileInput = $state<HTMLInputElement>();
  let dragOver = $state(false);
  let isUploading = $state(false);
  let uploadedFile = $state<File | null>(null);
  let error = $state<string | null>(null);
  let uploadResult = $state<ZipUploadResponse | null>(null);
  let uploadProgress = $state<UploadProgress | null>(null);
  let progressInterval = $state<NodeJS.Timeout | null>(null);

  function handleFileSelect(event: Event) {
    const target = event.target as HTMLInputElement;
    const file = target.files?.[0];
    if (file && file.name.endsWith(".zip")) {
      processZipFile(file);
    } else if (file) {
      error = "Please select a ZIP file";
    }
  }

  function handleDrop(event: DragEvent) {
    event.preventDefault();
    dragOver = false;

    const file = event.dataTransfer?.files[0];
    if (file && file.name.endsWith(".zip")) {
      processZipFile(file);
    } else if (file) {
      error = "Please drop a ZIP file";
    }
  }

  function handleDragOver(event: DragEvent) {
    event.preventDefault();
    dragOver = true;
  }

  function handleDragLeave() {
    dragOver = false;
  }

  function handleKeydown(event: KeyboardEvent, action: () => void) {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      action();
    }
  }

  async function processZipFile(file: File) {
    uploadedFile = file;
    error = null;
    isUploading = true;
    uploadProgress = {
      current: 0,
      total: 10,
      percentage: 0,
      message: "Starting upload...",
      completed: false,
    };

    try {
      const result = await apiClient.uploadZip(file);

      if (result.task_id) {
        uploadProgress = {
          current: 1,
          total: 10,
          percentage: 10,
          message: "Upload complete, processing...",
          completed: false,
        };
        startProgressPolling(result.task_id);
      } else {
        uploadProgress = {
          current: 10,
          total: 10,
          percentage: 100,
          message: "Upload completed!",
          completed: true,
        };
        isUploading = false;
        if (result.processed_svgs) {
          uploadResult = result;
          onZipProcessed(result);
        }
      }
    } catch (err) {
      error = `Failed to process ZIP file: ${err instanceof Error ? err.message : "Unknown error"}`;
      isUploading = false;
      uploadProgress = null;
    }
  }

  function startProgressPolling(taskId: string) {
    progressInterval = setInterval(async () => {
      try {
        const progress = await apiClient.getUploadProgress(taskId);
        uploadProgress = progress;

        if (progress.completed) {
          stopProgressPolling();
          isUploading = false;

          if (progress.error) {
            error = progress.error;
          } else if (progress.result) {
            uploadResult = {
              message: "ZIP processing completed",
              task_id: taskId,
              status: "completed",
              processed_svgs: progress.result.processed_svgs,
              unmatched_fonts: progress.result.unmatched_fonts,
            };
            onZipProcessed(uploadResult);
          }
        }
      } catch (err) {
        console.error("Error polling progress:", err);
        stopProgressPolling();
        isUploading = false;
        error = `Failed to get progress: ${err instanceof Error ? err.message : "Unknown error"}`;
      }
    }, 1000);
  }

  function stopProgressPolling() {
    if (progressInterval) {
      clearInterval(progressInterval);
      progressInterval = null;
    }
  }

  function resetUpload() {
    uploadedFile = null;
    uploadResult = null;
    uploadProgress = null;
    error = null;
    isUploading = false;
    stopProgressPolling();
  }

  $effect(() => {
    return () => {
      stopProgressPolling();
    };
  });
</script>

<Card class="relative">
  <CardHeader>
    <CardTitle class="flex items-center gap-2">
      <Package class="w-5 h-5" />
      Bulk Upload: ZIP File with SVGs & Fonts
    </CardTitle>
  </CardHeader>
  <CardContent>
    {#if !uploadedFile}
      <div
        class="border-2 border-dashed transition-all duration-200 cursor-pointer rounded-lg {dragOver
          ? 'border-primary bg-primary/5 scale-[1.02]'
          : 'border-border hover:border-primary/50'}"
        role="button"
        tabindex="0"
        aria-label="Upload ZIP file by clicking or dropping"
        ondragover={handleDragOver}
        ondragleave={handleDragLeave}
        ondrop={handleDrop}
        onclick={() => fileInput?.click()}
        onkeydown={(e) => handleKeydown(e, () => fileInput?.click())}
      >
        <div class="flex flex-col items-center justify-center p-8 text-center">
          <FileArchive class="w-12 h-12 mb-4 text-muted-foreground" />
          <h3 class="text-lg font-semibold text-foreground mb-2">
            Drop your ZIP file here
          </h3>
          <p class="text-sm text-muted-foreground mb-4">
            ZIP should contain SVG files and their corresponding font files
          </p>
          <Button variant="outline" size="sm">Choose ZIP File</Button>
        </div>
      </div>

      <input
        bind:this={fileInput}
        type="file"
        accept=".zip"
        class="hidden"
        onchange={handleFileSelect}
      />

      <div class="mt-4 p-4 bg-muted/50 rounded-lg">
        <h4 class="text-sm font-medium text-foreground mb-2">
          📁 Expected ZIP Structure:
        </h4>
        <div class="text-xs text-muted-foreground space-y-1">
          <div>• SVG files (*.svg)</div>
          <div>• Font files (*.woff, *.woff2, *.ttf, *.otf)</div>
          <div>• All files can be in root or organized in folders</div>
        </div>
      </div>
    {:else}
      <div class="space-y-4">
        <div
          class="flex items-center justify-between p-4 bg-muted/50 rounded-lg"
        >
          <div class="flex items-center gap-3">
            <FileArchive class="w-8 h-8 text-primary" />
            <div>
              <p class="font-medium text-foreground">{uploadedFile.name}</p>
              <p class="text-sm text-muted-foreground">
                {(uploadedFile.size / 1024 / 1024).toFixed(2)} MB
              </p>
            </div>
          </div>
          <div class="flex items-center gap-2">
            {#if isUploading}
              <div
                class="w-4 h-4 border-2 border-primary border-t-transparent rounded-full animate-spin"
              ></div>
              <span class="text-sm text-primary">Processing...</span>
            {:else if uploadResult}
              <CheckCircle class="w-4 h-4 text-green-600" />
              <span class="text-sm text-green-600">Processed</span>
            {:else if error}
              <AlertCircle class="w-4 h-4 text-red-600" />
              <span class="text-sm text-red-600">Error</span>
            {/if}
          </div>
        </div>

        {#if uploadProgress && isUploading}
          <div class="space-y-2">
            <div class="flex justify-between text-sm">
              <span class="text-muted-foreground">{uploadProgress.message}</span
              >
              <span class="text-primary font-medium"
                >{uploadProgress.percentage}%</span
              >
            </div>
            <Progress value={uploadProgress.percentage} class="h-2" />
            <div class="text-xs text-muted-foreground">
              Step {uploadProgress.current} of {uploadProgress.total}
            </div>
          </div>
        {/if}

        {#if uploadResult && !isUploading}
          <div class="space-y-4">
            <Separator />

            {#if uploadResult.processed_svgs && uploadResult.processed_svgs.length > 0}
              <div>
                <h4 class="text-sm font-semibold text-foreground mb-3">
                  📄 Processed SVG Files ({uploadResult.processed_svgs.length})
                </h4>
                <div class="space-y-2">
                  {#each uploadResult.processed_svgs as svg}
                    <div
                      class="flex items-center justify-between p-3 bg-green-50 dark:bg-green-950/20 rounded-md border border-green-200 dark:border-green-800"
                    >
                      <div class="flex items-center gap-2">
                        <CheckCircle class="w-4 h-4 text-green-600" />
                        <span class="text-sm font-medium">{svg.filename}</span>
                      </div>
                      <div class="flex gap-1">
                        <Badge variant="secondary" class="text-xs">
                          {svg.required_fonts.length} fonts required
                        </Badge>
                        <Badge variant="outline" class="text-xs">
                          {svg.matched_fonts.length} matched
                        </Badge>
                      </div>
                    </div>
                  {/each}
                </div>
              </div>
            {/if}

            {#if uploadResult.unmatched_fonts && uploadResult.unmatched_fonts.length > 0}
              <div>
                <h4 class="text-sm font-semibold text-foreground mb-3">
                  ⚠️ Unmatched Fonts ({uploadResult.unmatched_fonts.length})
                </h4>
                <div class="space-y-1">
                  {#each uploadResult.unmatched_fonts as font}
                    <div
                      class="p-2 bg-yellow-50 dark:bg-yellow-950/20 rounded-md border border-yellow-200 dark:border-yellow-800"
                    >
                      <span class="text-sm text-yellow-700 dark:text-yellow-300"
                        >{font}</span
                      >
                    </div>
                  {/each}
                </div>
                <p class="text-xs text-muted-foreground mt-2">
                  These fonts couldn't be automatically matched to any SVG
                  requirements. You can still map glyphs manually.
                </p>
              </div>
            {/if}

            {#if !uploadResult.processed_svgs || uploadResult.processed_svgs.length === 0}
              <div
                class="p-4 bg-yellow-50 dark:bg-yellow-950/20 rounded-lg border border-yellow-200 dark:border-yellow-800"
              >
                <div
                  class="flex items-center gap-2 text-yellow-700 dark:text-yellow-300"
                >
                  <AlertCircle class="w-4 h-4" />
                  <span class="text-sm font-medium"
                    >No SVG files were processed successfully</span
                  >
                </div>
              </div>
            {/if}
          </div>
        {/if}

        {#if error}
          <div
            class="p-4 bg-red-50 dark:bg-red-950/20 rounded-lg border border-red-200 dark:border-red-800"
          >
            <div class="flex items-center gap-2 text-red-700 dark:text-red-300">
              <AlertCircle class="w-4 h-4" />
              <span class="text-sm font-medium">{error}</span>
            </div>
          </div>
        {/if}

        <div class="flex justify-between">
          <Button
            variant="outline"
            onclick={resetUpload}
            disabled={isUploading}
          >
            Upload Different ZIP
          </Button>
          {#if uploadResult && !isUploading}
            <Button onclick={() => onZipProcessed(uploadResult)}>
              Continue to SVG Selection
            </Button>
          {/if}
        </div>
      </div>
    {/if}
  </CardContent>
</Card>
