<script lang="ts">
  import type { Font } from "$lib/types";

  let { svgFileId, fonts, refreshTrigger } = $props<{
    svgFileId: number | null;
    fonts: Font[];
    refreshTrigger: number;
  }>();
</script>

<div class="p-8 text-center">
  <h3 class="text-lg font-semibold mb-2">Live Preview</h3>
  <p class="text-muted-foreground">
    Component will be implemented in next phase
  </p>
</div>
