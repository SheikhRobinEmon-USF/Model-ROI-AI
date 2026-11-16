<script lang="ts">
  import { Cloud, Cpu, PackagePlus } from '@lucide/svelte'
  import { studio } from '../lib/studio.svelte'
  let { compact = false }: { compact?: boolean } = $props()
</script>

<div class="inline-flex rounded-xl border border-line bg-sunken p-0.5" role="group" aria-label="Inference location">
  {#each ['local', 'hosted'] as const as value}
    <button
      class="inline-flex h-8 items-center gap-1.5 rounded-[0.6rem] px-3 text-[13px] font-medium text-muted transition-colors aria-pressed:bg-raised aria-pressed:text-text aria-pressed:shadow-card disabled:opacity-50"
      disabled={!!studio.busy} aria-pressed={studio.mode === value} onclick={() => studio.switchMode(value)}>
      {#if value === 'local'}<Cpu size={14} aria-hidden="true" />Local{:else}<Cloud size={14} aria-hidden="true" />Hosted{/if}
    </button>
  {/each}
</div>
<button class="btn btn-sm {compact ? 'max-sm:w-8 max-sm:px-0' : ''}" disabled={!!studio.busy} onclick={() => studio.openAddModel()} aria-label="Add model">
  <PackagePlus size={14} aria-hidden="true" /><span class={compact ? 'max-sm:hidden' : ''}>Add model</span>
</button>
