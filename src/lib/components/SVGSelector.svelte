<script lang="ts">
  import { Clock, FileText, Database, ChevronLeft, ChevronRight } from '@lucide/svelte';

  import { Card, CardTitle, CardHeader, CardContent } from '$lib/components/ui/card';

  import { onMount } from 'svelte';
  import { apiClient } from '$lib/api';
  import { Badge } from '$lib/components/ui/badge';
  import { Button } from '$lib/components/ui/button';
  import { Separator } from '$lib/components/ui/separator';
  import type { SVGListItem, SVGListResponse } from '$lib/types';

  let { onSvgSelected } = $props<{
    onSvgSelected: (svgId: number, filename: string) => void;
  }>();

  let loading = $state(true);
  let currentPage = $state(1);
  let loadingPage = $state(false);
  let svgs = $state<SVGListItem[]>([]);
  let error = $state<string | null>(null);
  let pagination = $state<SVGListResponse['pagination'] | null>(null);

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
      error = `Failed to load SVG files: ${err instanceof Error ? err.message : 'Unknown error'}`;
      svgs = [];
      pagination = null;
    } finally {
      loading = false;
      loadingPage = false;
    }
  }

  async function goToPage(page: number) {
    if (page >= 1 && pagination && page <= pagination.total_pages) await loadSvgs(page);
  }

  function formatDate(dateString: string): string {
    return new Date(dateString).toLocaleString();
  }

  onMount(() => loadSvgs(1));
</script>

<Card>
  <CardHeader>
    <CardTitle class="flex items-center gap-2">
      <Database class="h-5 w-5" />
      Select SVG File to Work With
    </CardTitle>
  </CardHeader>
  <CardContent>
    {#if loading}
      <div class="flex flex-col items-center justify-center py-12">
        <div
          class="border-primary mb-4 h-8 w-8 animate-spin rounded-full border-2 border-t-transparent"
        ></div>
        <p class="text-muted-foreground">Loading SVG files...</p>
        <p class="text-muted-foreground mt-1 text-xs">
          This may take a moment for large collections
        </p>
      </div>
    {:else if error}
      <div class="py-8 text-center">
        <div class="mb-2 text-red-600">{error}</div>
        <Button variant="outline" onclick={() => loadSvgs(currentPage)}>Retry</Button>
      </div>
    {:else if svgs.length === 0}
      <div class="py-8 text-center">
        <FileText class="text-muted-foreground mx-auto mb-4 h-12 w-12" />
        <h3 class="text-foreground mb-2 text-lg font-semibold">No SVG Files Found</h3>
        <p class="text-muted-foreground">Upload some SVG files to get started.</p>
      </div>
    {:else}
      <div class="space-y-4">
        {#if pagination}
          <div class="text-muted-foreground flex items-center justify-between text-sm">
            <div>
              Showing {(currentPage - 1) * pagination.items_per_page + 1}-{Math.min(
                currentPage * pagination.items_per_page,
                pagination.total_items
              )} of {pagination.total_items} SVG files
            </div>
            <div>
              Page {pagination.current_page} of {pagination.total_pages}
            </div>
          </div>
        {/if}

        <div class="relative space-y-2">
          {#if loadingPage}
            <div
              class="bg-background/80 absolute inset-0 z-10 flex items-center justify-center rounded-lg backdrop-blur-sm"
            >
              <div class="flex items-center gap-2">
                <div
                  class="border-primary h-4 w-4 animate-spin rounded-full border-2 border-t-transparent"
                ></div>
                <span class="text-muted-foreground text-sm">Loading page...</span>
              </div>
            </div>
          {/if}

          {#each svgs as svg}
            <div
              class="border-border hover:border-primary bg-card cursor-pointer rounded-lg border p-4 transition-all duration-200 hover:shadow-md"
              role="button"
              tabindex="0"
              onclick={() => onSvgSelected(svg.svg_file_id, svg.filename)}
              onkeydown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  onSvgSelected(svg.svg_file_id, svg.filename);
                }
              }}
            >
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-3">
                  <FileText class="text-primary h-5 w-5" />
                  <div>
                    <p class="text-foreground font-medium">{svg.filename}</p>
                    <div class="text-muted-foreground flex items-center gap-2 text-xs">
                      <Clock class="h-3 w-3" />
                      <span>Uploaded: {formatDate(svg.upload_date)}</span>
                    </div>
                  </div>
                </div>
                <div class="flex items-center gap-2">
                  <Badge variant="outline">Ready to map</Badge>
                  <ChevronRight class="text-muted-foreground h-4 w-4" />
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
              <ChevronLeft class="mr-1 h-4 w-4" />
              Previous
            </Button>

            <div class="flex items-center gap-2">
              {#if pagination.total_pages <= 7}
                {#each Array.from({ length: pagination?.total_pages || 0 }, (_, i) => i + 1) as page}
                  <Button
                    variant={page === currentPage ? 'default' : 'outline'}
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
                    variant={page === currentPage ? 'default' : 'outline'}
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
                    variant={page === currentPage ? 'default' : 'outline'}
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
                    variant={page === currentPage ? 'default' : 'outline'}
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
              <ChevronRight class="ml-1 h-4 w-4" />
            </Button>
          </div>
        {/if}
      </div>
    {/if}
  </CardContent>
</Card>
