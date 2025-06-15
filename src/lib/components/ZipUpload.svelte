<script lang="ts">
  import { Package, CheckCircle, AlertCircle, FileArchive } from '@lucide/svelte';

  import { Card, CardTitle, CardHeader, CardContent } from '$lib/components/ui/card';

  import { apiClient } from '$lib/api';
  import { Badge } from '$lib/components/ui/badge';
  import { Button } from '$lib/components/ui/button';
  import { Progress } from '$lib/components/ui/progress';
  import { Separator } from '$lib/components/ui/separator';
  import type { ZipUploadResponse, UploadProgress } from '$lib/types';

  let { onZipProcessed } = $props<{
    onZipProcessed: (data: ZipUploadResponse) => void;
  }>();

  let dragOver = $state(false);
  let isUploading = $state(false);
  let error = $state<string | null>(null);
  let fileInput = $state<HTMLInputElement>();
  let uploadedFile = $state<File | null>(null);
  let uploadProgress = $state<UploadProgress | null>(null);
  let uploadResult = $state<ZipUploadResponse | null>(null);
  let progressInterval = $state<NodeJS.Timeout | null>(null);

  function handleFileSelect(event: Event) {
    const target = event.target as HTMLInputElement;
    const file = target.files?.[0];
    if (file && file.name.endsWith('.zip')) processZipFile(file);
    else if (file) error = 'Please select a ZIP file';
  }

  function handleDrop(event: DragEvent) {
    event.preventDefault();
    dragOver = false;

    const file = event.dataTransfer?.files[0];
    if (file && file.name.endsWith('.zip')) processZipFile(file);
    else if (file) error = 'Please drop a ZIP file';
  }

  function handleDragOver(event: DragEvent) {
    event.preventDefault();
    dragOver = true;
  }

  function handleDragLeave() {
    dragOver = false;
  }

  function handleKeydown(event: KeyboardEvent, action: () => void) {
    if (event.key === 'Enter' || event.key === ' ') {
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
      message: 'Starting upload...',
      completed: false,
    };

    try {
      const result = await apiClient.uploadZip(file);

      if (result.task_id) {
        uploadProgress = {
          current: 1,
          total: 10,
          percentage: 10,
          message: 'Upload complete, processing...',
          completed: false,
        };
        startProgressPolling(result.task_id);
      } else {
        uploadProgress = {
          current: 10,
          total: 10,
          percentage: 100,
          message: 'Upload completed!',
          completed: true,
        };
        isUploading = false;
        if (result.processed_svgs) {
          uploadResult = result;
          onZipProcessed(result);
        }
      }
    } catch (err) {
      error = `Failed to process ZIP file: ${err instanceof Error ? err.message : 'Unknown error'}`;
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

          if (progress.error) error = progress.error;
          else if (progress.result) {
            uploadResult = {
              message: 'ZIP processing completed',
              task_id: taskId,
              status: 'completed',
              processed_svgs: progress.result.processed_svgs,
              unmatched_fonts: progress.result.unmatched_fonts,
            };
            onZipProcessed(uploadResult);
          }
        }
      } catch (err) {
        console.error('Error polling progress:', err);
        stopProgressPolling();
        isUploading = false;
        error = `Failed to get progress: ${err instanceof Error ? err.message : 'Unknown error'}`;
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
      <Package class="h-5 w-5" />
      Bulk Upload: ZIP File with SVGs & Fonts
    </CardTitle>
  </CardHeader>
  <CardContent>
    {#if !uploadedFile}
      <div
        class="cursor-pointer rounded-lg border-2 border-dashed transition-all duration-200 {dragOver
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
          <FileArchive class="text-muted-foreground mb-4 h-12 w-12" />
          <h3 class="text-foreground mb-2 text-lg font-semibold">Drop your ZIP file here</h3>
          <p class="text-muted-foreground mb-4 text-sm">
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

      <div class="bg-muted/50 mt-4 rounded-lg p-4">
        <h4 class="text-foreground mb-2 text-sm font-medium">📁 Expected ZIP Structure:</h4>
        <div class="text-muted-foreground space-y-1 text-xs">
          <div>• SVG files (*.svg)</div>
          <div>• Font files (*.woff, *.woff2, *.ttf, *.otf)</div>
          <div>• All files can be in root or organized in folders</div>
        </div>
      </div>
    {:else}
      <div class="space-y-4">
        <div class="bg-muted/50 flex items-center justify-between rounded-lg p-4">
          <div class="flex items-center gap-3">
            <FileArchive class="text-primary h-8 w-8" />
            <div>
              <p class="text-foreground font-medium">{uploadedFile.name}</p>
              <p class="text-muted-foreground text-sm">
                {(uploadedFile.size / 1024 / 1024).toFixed(2)} MB
              </p>
            </div>
          </div>
          <div class="flex items-center gap-2">
            {#if isUploading}
              <div
                class="border-primary h-4 w-4 animate-spin rounded-full border-2 border-t-transparent"
              ></div>
              <span class="text-primary text-sm">Processing...</span>
            {:else if uploadResult}
              <CheckCircle class="h-4 w-4 text-green-600" />
              <span class="text-sm text-green-600">Processed</span>
            {:else if error}
              <AlertCircle class="h-4 w-4 text-red-600" />
              <span class="text-sm text-red-600">Error</span>
            {/if}
          </div>
        </div>

        {#if uploadProgress && isUploading}
          <div class="space-y-2">
            <div class="flex justify-between text-sm">
              <span class="text-muted-foreground">{uploadProgress.message}</span>
              <span class="text-primary font-medium">{uploadProgress.percentage}%</span>
            </div>
            <Progress value={uploadProgress.percentage} class="h-2" />
            <div class="text-muted-foreground text-xs">
              Step {uploadProgress.current} of {uploadProgress.total}
            </div>
          </div>
        {/if}

        {#if uploadResult && !isUploading}
          <div class="space-y-4">
            <Separator />

            {#if uploadResult.processed_svgs && uploadResult.processed_svgs.length > 0}
              <div>
                <h4 class="text-foreground mb-3 text-sm font-semibold">
                  📄 Processed SVG Files ({uploadResult.processed_svgs.length})
                </h4>
                <div class="space-y-2">
                  {#each uploadResult.processed_svgs as svg}
                    <div
                      class="flex items-center justify-between rounded-md border border-green-200 bg-green-50 p-3 dark:border-green-800 dark:bg-green-950/20"
                    >
                      <div class="flex items-center gap-2">
                        <CheckCircle class="h-4 w-4 text-green-600" />
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
                <h4 class="text-foreground mb-3 text-sm font-semibold">
                  ⚠️ Unmatched Fonts ({uploadResult.unmatched_fonts.length})
                </h4>
                <div class="space-y-1">
                  {#each uploadResult.unmatched_fonts as font}
                    <div
                      class="rounded-md border border-yellow-200 bg-yellow-50 p-2 dark:border-yellow-800 dark:bg-yellow-950/20"
                    >
                      <span class="text-sm text-yellow-700 dark:text-yellow-300">{font}</span>
                    </div>
                  {/each}
                </div>
                <p class="text-muted-foreground mt-2 text-xs">
                  These fonts couldn't be automatically matched to any SVG requirements. You can
                  still map glyphs manually.
                </p>
              </div>
            {/if}

            {#if !uploadResult.processed_svgs || uploadResult.processed_svgs.length === 0}
              <div
                class="rounded-lg border border-yellow-200 bg-yellow-50 p-4 dark:border-yellow-800 dark:bg-yellow-950/20"
              >
                <div class="flex items-center gap-2 text-yellow-700 dark:text-yellow-300">
                  <AlertCircle class="h-4 w-4" />
                  <span class="text-sm font-medium">No SVG files were processed successfully</span>
                </div>
              </div>
            {/if}
          </div>
        {/if}

        <!-- Error Display -->
        {#if error}
          <div
            class="rounded-lg border border-red-200 bg-red-50 p-4 dark:border-red-800 dark:bg-red-950/20"
          >
            <div class="flex items-center gap-2 text-red-700 dark:text-red-300">
              <AlertCircle class="h-4 w-4" />
              <span class="text-sm font-medium">{error}</span>
            </div>
          </div>
        {/if}

        <!-- Actions -->
        <div class="flex justify-between">
          <Button variant="outline" onclick={resetUpload} disabled={isUploading}>
            Upload Different ZIP
          </Button>
          {#if uploadResult && !isUploading}
            <Button onclick={() => onZipProcessed(uploadResult)}>Continue to SVG Selection</Button>
          {/if}
        </div>
      </div>
    {/if}
  </CardContent>
</Card>
