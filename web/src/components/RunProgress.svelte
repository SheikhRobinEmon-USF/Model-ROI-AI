<script lang="ts">
  import { Check } from '@lucide/svelte'
  import { slide } from 'svelte/transition'
  import { STAGES, studio } from '../lib/studio.svelte'
  import { quick } from '../lib/motion'
  const clock = $derived(Math.floor(studio.elapsed / 60) + ':' + String(studio.elapsed % 60).padStart(2, '0'))
</script>

{#if studio.busy}
  <section class="processing mx-auto w-full max-w-[1100px] px-4 pt-3 md:px-8" transition:slide={quick}>
    <div class="glass rounded-2xl px-4 py-2.5 shadow-card">
      <div class="flex items-center gap-3 text-[13.5px]">
        <i class="spinner" aria-hidden="true"></i>
        <div role="status" class="min-w-0 flex-1 truncate font-medium">{studio.busy}…</div>
        {#if studio.elapsed >= 2}<span class="num text-xs text-faint" aria-hidden="true">{clock}</span>{/if}
      </div>
      {#if studio.phase}
        <ol class="mt-2.5 grid grid-cols-4 gap-1.5" aria-label="Evaluation stages">
          {#each STAGES as [key, label]}
            {@const current = studio.phase === key}
            {@const done = !current && studio.visited.includes(key)}
            <li class="relative pt-2.5 text-[11.5px] {current ? 'font-semibold text-accent-text' : done ? 'text-muted' : 'text-faint'}" aria-current={current ? 'step' : undefined}>
              <span class="absolute inset-x-0 top-0 h-1 rounded-full {current ? 'animate-pulse bg-accent-text' : done ? 'bg-accent-text/55' : 'bg-line-strong'}"></span>
              <span class="inline-flex items-center gap-1">{#if done}<Check size={11} aria-hidden="true" />{/if}{label}</span>
            </li>
          {/each}
        </ol>
      {/if}
    </div>
  </section>
{/if}
