<script lang="ts">
  import { ChartColumn, ChevronRight, FlaskConical, MessageSquare, Search } from '@lucide/svelte'
  import { fly } from 'svelte/transition'
  import { studio } from '../lib/studio.svelte'
  import { clock, dayLabel, percent, scoreTone, seconds } from '../lib/format'
  import { rise } from '../lib/motion'

  const kinds = ['All', 'Chats', 'Benchmarks'] as const
  let kind = $state<(typeof kinds)[number]>('All'), query = $state('')
  const shown = $derived(studio.history.filter((h) =>
    (kind === 'All' || (kind === 'Chats') === !!h.title) && ((h.chat_name ?? h.title ?? '') + ' ' + h.model_id).toLowerCase().includes(query.trim().toLowerCase())))
  const groups = $derived.by(() => {
    const out: { day: string; rows: any[] }[] = []
    for (const row of shown) {
      const day = dayLabel(row.started_at)
      if (out.at(-1)?.day === day) out.at(-1)!.rows.push(row); else out.push({ day, rows: [row] })
    }
    return out
  })
  const slowest = $derived(Math.max(1, ...(studio.analytics ?? []).map((a) => a.median_ms ?? 0)))
</script>

<section class="card mb-6 p-5 sm:p-6" in:fly={rise()}>
  <div class="flex flex-wrap items-center gap-3">
    <div class="min-w-0 flex-1 basis-72"><h2 class="flex items-center gap-2 text-lg font-semibold"><ChartColumn size={17} class="text-accent-text" aria-hidden="true" />Benchmark trends</h2>
      <p class="mt-0.5 text-[13px] text-muted">All saved benchmark attempts, pooled across workloads. Median time uses completed responses.</p></div>
    <button class="btn" disabled={!!studio.busy} onclick={studio.loadAnalytics}>{studio.analytics ? 'Refresh benchmark statistics' : 'Analyze saved benchmarks'}</button>
  </div>
  {#if studio.analytics}
    {#if studio.analytics.length}
      <div class="mt-4 overflow-x-auto">
        <table class="w-full min-w-[34rem] text-left text-sm">
          <thead><tr class="eyebrow border-b border-line [&>th]:px-2 [&>th]:pb-2 [&>th]:font-medium"><th>Model</th><th>Pass rate</th><th>Average grade</th><th>Median time</th><th class="text-right">Runs</th></tr></thead>
          <tbody>
            {#each studio.analytics as item, i}
              {@const rate = item.attempts ? item.passed / item.attempts : 0}
              <tr class="hue-{studio.hue(item.model, i)} border-b border-line last:border-0 [&>td]:px-2 [&>td]:py-3">
                <td><span class="flex items-center gap-2 font-medium"><i class="dot" aria-hidden="true"></i>{studio.name(item.model)}</span></td>
                <td><div class="flex items-center gap-2.5"><div class="h-1.5 w-20 overflow-hidden rounded-full bg-sunken" aria-hidden="true"><div class="h-full rounded-full bg-(--hue)" style:width={percent(rate)}></div></div><span class="num">{percent(rate)}</span><span class="num text-xs text-faint">{item.passed}/{item.attempts}</span></div></td>
                <td>{#if item.mean_grade != null}<span class="num tone-{scoreTone(item.mean_grade)} font-medium text-(--tone)">{item.mean_grade.toFixed(1)}</span><span class="text-xs text-faint"> / 10 · {item.graded} graded</span>{:else}<span class="text-faint">—</span>{/if}</td>
                <td><div class="flex items-center gap-2.5"><div class="h-1.5 w-16 overflow-hidden rounded-full bg-sunken" aria-hidden="true"><div class="h-full rounded-full bg-muted" style:width={percent((item.median_ms ?? 0) / slowest)}></div></div><span class="num">{seconds(item.median_ms)}</span></div></td>
                <td class="num text-right text-muted">{item.runs}</td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    {:else}<p class="mt-4 text-sm text-muted">Run a benchmark to see historical statistics.</p>{/if}
  {/if}
</section>

<div class="mb-3 flex flex-wrap items-center gap-2.5">
  <div class="inline-flex rounded-xl border border-line bg-sunken p-0.5" role="tablist" aria-label="Filter runs">
    {#each kinds as k}<button role="tab" aria-selected={kind === k} class="h-8 rounded-[0.6rem] px-3 text-[13px] font-medium text-muted transition-colors aria-selected:bg-raised aria-selected:text-text aria-selected:shadow-card" onclick={() => (kind = k)}>{k}</button>{/each}
  </div>
  <label class="relative min-w-40 flex-1 sm:max-w-xs">
    <Search size={14} class="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-faint" aria-hidden="true" />
    <input class="field !min-h-9 !py-1 !pl-9 text-[13.5px]" type="search" placeholder="Search runs" aria-label="Search runs" bind:value={query} />
  </label>
  <span class="num ml-auto text-xs text-faint">{shown.length} {shown.length === 1 ? 'run' : 'runs'}</span>
</div>

{#each groups as group (group.day)}
  <h3 class="eyebrow mb-1.5 mt-5 px-1">{group.day}</h3>
  <div class="card divide-y divide-line overflow-hidden">
    {#each group.rows as h (h.run_id)}
      <button class="history group flex w-full items-center gap-3 px-4 py-3 text-left transition-colors hover:bg-accent-soft disabled:opacity-60" disabled={!!studio.busy} onclick={() => studio.openRun(h.run_id)}>
        <span class="grid size-9 shrink-0 place-items-center rounded-xl {h.title ? 'bg-accent-soft text-accent-text' : 'bg-sunken text-muted'}">{#if h.title}<MessageSquare size={15} aria-hidden="true" />{:else}<FlaskConical size={15} aria-hidden="true" />{/if}</span>
        <span class="min-w-0 flex-1">
          <strong class="block truncate text-sm font-medium">{h.title ? (h.chat_name ?? h.title) : h.model_id}</strong>
          <span class="block truncate text-xs text-faint">{h.title ? 'Chat · ' + h.model_id : 'Matched benchmark'}</span>
        </span>
        <span class="num shrink-0 text-xs text-faint">{clock(h.started_at)}</span>
        <ChevronRight size={15} class="shrink-0 text-faint transition-transform group-hover:translate-x-0.5" aria-hidden="true" />
      </button>
    {/each}
  </div>
{:else}
  <p class="card px-5 py-10 text-center text-sm text-muted">{studio.history.length ? 'No runs match that filter.' : 'Your saved comparisons will appear here after your first run.'}</p>
{/each}
