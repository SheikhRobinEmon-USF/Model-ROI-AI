<script lang="ts">
  import { scoreTone, words } from '../lib/format'
  let { judge }: { judge: any } = $props()
</script>

{#if judge?.dimensions}
  <div class="mt-3 rounded-xl border border-line bg-sunken/60 p-3">
    <div class="mb-2 flex flex-wrap items-baseline justify-between gap-x-3">
      <span class="eyebrow">Quality breakdown</span>
      <span class="text-xs text-faint">{judge.model} · {judge.rubric_version} · equal-weight mean</span>
    </div>
    <dl class="grid gap-1.5">
      {#each Object.entries(judge.dimensions) as [key, value]}
        <div class="grid grid-cols-[minmax(0,7.5rem)_1fr_auto] items-center gap-3 text-[13px]">
          <dt class="truncate capitalize text-muted">{words(key)}</dt>
          <dd class="h-1.5 overflow-hidden rounded-full bg-sunken {value == null ? '' : 'tone-' + scoreTone(value as number)}" aria-hidden="true">
            {#if value != null}<div class="h-full rounded-full bg-(--tone)" style:width="{(value as number) * 10}%"></div>{/if}
          </dd>
          <dd class="num min-w-16 whitespace-nowrap text-right font-medium">{value == null ? 'N/A' : value + ' / 10'}</dd>
        </div>
      {/each}
    </dl>
  </div>
{/if}
