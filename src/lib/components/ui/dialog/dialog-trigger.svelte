<DialogPrimitive.Trigger bind:ref data-slot="dialog-trigger" {...restProps} />

<script lang="ts">
import {Dialog as DialogPrimitive} from 'bits-ui'

let {ref = $bindable(null), ...restProps}: DialogPrimitive.TriggerProps = $props()
</script>
