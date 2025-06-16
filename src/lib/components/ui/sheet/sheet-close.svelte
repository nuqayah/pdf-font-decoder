<SheetPrimitive.Close bind:ref data-slot="sheet-close" {...restProps} />

<script lang="ts">
import {Dialog as SheetPrimitive} from 'bits-ui'

let {ref = $bindable(null), ...restProps}: SheetPrimitive.CloseProps = $props()
</script>
