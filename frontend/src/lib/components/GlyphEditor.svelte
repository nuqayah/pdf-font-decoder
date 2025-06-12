<script lang="ts">
  import type { Font } from "$lib/types";

  let {
    fonts,
    svgFileId,
    mappingProgress = $bindable(),
    onMappingChanged,
  } = $props<{
    fonts: Font[];
    svgFileId: number | null;
    mappingProgress: number;
    onMappingChanged: () => void;
  }>();
</script>

<div class="p-8 text-center">
  <h3 class="text-lg font-semibold mb-2">Glyph Editor</h3>
  <p class="text-muted-foreground">
    Component will be implemented in next phase
  </p>
</div>
