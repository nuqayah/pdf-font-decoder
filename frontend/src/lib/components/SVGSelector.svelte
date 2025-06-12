<script lang="ts">
  import {
    Clock,
    FileText,
    Database,
    ChevronLeft,
    ChevronRight,
  } from "@lucide/svelte";

  import {
    Card,
    CardTitle,
    CardHeader,
    CardContent,
  } from "$lib/components/ui/card";

  import { onMount } from "svelte";
  import { apiClient } from "$lib/api";
  import { Badge } from "$lib/components/ui/badge";
  import { Button } from "$lib/components/ui/button";
  import { Separator } from "$lib/components/ui/separator";
  import type { SVGListItem, SVGListResponse } from "$lib/types";

  let { onSvgSelected } = $props<{
    onSvgSelected: (svgId: number, filename: string) => void;
  }>();

  let loading = $state(true);
  let currentPage = $state(1);
  let loadingPage = $state(false);
  let svgs = $state<SVGListItem[]>([]);
  let error = $state<string | null>(null);
  let pagination = $state<SVGListResponse["pagination"] | null>(null);

  async function loadSvgs(page: number = 1) {
    if (page !== currentPage) loadingPage = true;
    else loading = true;

    error = null;

    try {
      const response = await apiClient.getSvgs(page, 20);
      svgs = response.svgs;
      pagination = response.pagination;
      currentPage = page;
    } catch (err) {
      error = `Failed to load SVG files: ${err instanceof Error ? err.message : "Unknown error"}`;
      svgs = [];
      pagination = null;
    } finally {
      loading = false;
      loadingPage = false;
    }
  }

  async function goToPage(page: number) {
    if (page >= 1 && pagination && page <= pagination.total_pages)
      await loadSvgs(page);
  }

  function formatDate(dateString: string): string {
    return new Date(dateString).toLocaleString();
  }

  onMount(() => loadSvgs(1));
</script>

<Card>
  <CardHeader>
    <CardTitle class="flex items-center gap-2">
      <Database class="w-5 h-5" />
      Select SVG File to Work With
    </CardTitle>
  </CardHeader>
  <CardContent>
    {#if loading}
      <div class="flex flex-col items-center justify-center py-12">
        <div
          class="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin mb-4"
        ></div>
        <p class="text-muted-foreground">Loading SVG files...</p>
        <p class="text-xs text-muted-foreground mt-1">
          This may take a moment for large collections
        </p>
      </div>
    {:else if error}
      <div class="text-center py-8">
        <div class="text-red-600 mb-2">{error}</div>
        <Button variant="outline" onclick={() => loadSvgs(currentPage)}>
          Retry
        </Button>
      </div>
    {:else if svgs.length === 0}
      <div class="text-center py-8">
        <FileText class="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
        <h3 class="text-lg font-semibold text-foreground mb-2">
          No SVG Files Found
        </h3>
        <p class="text-muted-foreground">
          Upload some SVG files to get started.
        </p>
      </div>
    {:else}
      <div class="space-y-4">
        {#if pagination}
          <div
            class="flex items-center justify-between text-sm text-muted-foreground"
          >
            <div>
              Showing {(currentPage - 1) * pagination.items_per_page +
                1}-{Math.min(
                currentPage * pagination.items_per_page,
                pagination.total_items
              )} of {pagination.total_items} SVG files
            </div>
            <div>
              Page {pagination.current_page} of {pagination.total_pages}
            </div>
          </div>
        {/if}

        <div class="space-y-2 relative">
          {#if loadingPage}
            <div
              class="absolute inset-0 bg-background/80 backdrop-blur-sm flex items-center justify-center z-10 rounded-lg"
            >
              <div class="flex items-center gap-2">
                <div
                  class="w-4 h-4 border-2 border-primary border-t-transparent rounded-full animate-spin"
                ></div>
                <span class="text-sm text-muted-foreground"
                  >Loading page...</span
                >
              </div>
            </div>
          {/if}

          {#each svgs as svg}
            <div
              class="p-4 rounded-lg border border-border hover:border-primary transition-all duration-200 cursor-pointer bg-card hover:shadow-md"
              role="button"
              tabindex="0"
              onclick={() => onSvgSelected(svg.svg_file_id, svg.filename)}
              onkeydown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                  e.preventDefault();
                  onSvgSelected(svg.svg_file_id, svg.filename);
                }
              }}
            >
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-3">
                  <FileText class="w-5 h-5 text-primary" />
                  <div>
                    <p class="font-medium text-foreground">{svg.filename}</p>
                    <div
                      class="flex items-center gap-2 text-xs text-muted-foreground"
                    >
                      <Clock class="w-3 h-3" />
                      <span>Uploaded: {formatDate(svg.upload_date)}</span>
                    </div>
                  </div>
                </div>
                <div class="flex items-center gap-2">
                  <Badge variant="outline">Ready to map</Badge>
                  <ChevronRight class="w-4 h-4 text-muted-foreground" />
                </div>
              </div>
            </div>
          {/each}
        </div>

        {#if pagination && pagination.total_pages > 1}
          <Separator />
          <div class="flex items-center justify-between">
            <Button
              variant="outline"
              size="sm"
              disabled={!pagination.has_previous || loadingPage}
              onclick={() => goToPage(currentPage - 1)}
            >
              <ChevronLeft class="w-4 h-4 mr-1" />
              Previous
            </Button>

            <div class="flex items-center gap-2">
              {#if pagination.total_pages <= 7}
                {#each Array.from({ length: pagination?.total_pages || 0 }, (_, i) => i + 1) as page}
                  <Button
                    variant={page === currentPage ? "default" : "outline"}
                    size="sm"
                    class="w-10"
                    disabled={loadingPage}
                    onclick={() => goToPage(page)}
                  >
                    {page}
                  </Button>
                {/each}
              {:else if currentPage <= 4}
                {#each [1, 2, 3, 4, 5] as page}
                  <Button
                    variant={page === currentPage ? "default" : "outline"}
                    size="sm"
                    class="w-10"
                    disabled={loadingPage}
                    onclick={() => goToPage(page)}
                  >
                    {page}
                  </Button>
                {/each}
                <span class="text-muted-foreground">...</span>
                <Button
                  size="sm"
                  class="w-10"
                  variant="outline"
                  disabled={loadingPage}
                  onclick={() => pagination && goToPage(pagination.total_pages)}
                >
                  {pagination?.total_pages || 0}
                </Button>
              {:else if currentPage >= pagination.total_pages - 3}
                <Button
                  variant="outline"
                  size="sm"
                  class="w-10"
                  disabled={loadingPage}
                  onclick={() => goToPage(1)}
                >
                  1
                </Button>
                <span class="text-muted-foreground">...</span>
                {#each Array.from({ length: 5 }, (_, i) => (pagination?.total_pages || 0) - 4 + i) as page}
                  <Button
                    variant={page === currentPage ? "default" : "outline"}
                    size="sm"
                    class="w-10"
                    disabled={loadingPage}
                    onclick={() => goToPage(page)}
                  >
                    {page}
                  </Button>
                {/each}
              {:else}
                <Button
                  variant="outline"
                  size="sm"
                  class="w-10"
                  disabled={loadingPage}
                  onclick={() => goToPage(1)}
                >
                  1
                </Button>
                <span class="text-muted-foreground">...</span>
                {#each [currentPage - 1, currentPage, currentPage + 1] as page}
                  <Button
                    variant={page === currentPage ? "default" : "outline"}
                    size="sm"
                    class="w-10"
                    disabled={loadingPage}
                    onclick={() => goToPage(page)}
                  >
                    {page}
                  </Button>
                {/each}
                <span class="text-muted-foreground">...</span>
                <Button
                  variant="outline"
                  size="sm"
                  class="w-10"
                  disabled={loadingPage}
                  onclick={() => pagination && goToPage(pagination.total_pages)}
                >
                  {pagination?.total_pages || 0}
                </Button>
              {/if}
            </div>

            <Button
              variant="outline"
              size="sm"
              disabled={!pagination.has_next || loadingPage}
              onclick={() => goToPage(currentPage + 1)}
            >
              Next
              <ChevronRight class="w-4 h-4 ml-1" />
            </Button>
          </div>
        {/if}
      </div>
    {/if}
  </CardContent>
</Card>
