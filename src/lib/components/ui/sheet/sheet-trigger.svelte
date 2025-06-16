<SheetPrimitive.Trigger bind:ref data-slot="sheet-trigger" {...restProps} />

<script lang="ts">
import {Dialog as SheetPrimitive} from 'bits-ui'

let {ref = $bindable(null), ...restProps}: SheetPrimitive.TriggerProps = $props()
</script>
