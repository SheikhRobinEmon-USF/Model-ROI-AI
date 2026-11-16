<script lang="ts">
  import { ArrowRight, Gauge, Layers, RefreshCw, SlidersHorizontal } from '@lucide/svelte'
  import { fly } from 'svelte/transition'
  import { MAX_MODELS, studio } from '../lib/studio.svelte'
  import { words } from '../lib/format'
  import { rise } from '../lib/motion'
  import ModeSwitch from './ModeSwitch.svelte'
  import RoutingNote from './RoutingNote.svelte'

  const categories = $derived(studio.suite === 'analytical' ? ['math', 'coding', 'case_study'] : ['structured_extraction', 'hospital_finance_qa', 'instruction_following_classification'])
  const total = $derived(studio.countValid ? studio.count * studio.selected.length : 0)
</script>

<div class="grid items-start gap-5 lg:grid-cols-[minmax(0,1.5fr)_minmax(19rem,1fr)]">
  <fieldset class="grid min-w-0 gap-5" disabled={!!studio.busy}>
    <section class="card p-5 sm:p-6" in:fly={rise()}>
      <h2 class="mb-4 flex items-center gap-2 text-lg font-semibold"><Layers size={17} class="text-accent-text" aria-hidden="true" />Workload</h2>
      <div class="grid gap-4 sm:grid-cols-2">
        <div><label class="label" for="suite">Evaluation set</label>
          <select id="suite" class="field" bind:value={studio.suite} onchange={() => { studio.count = 5; studio.category = 'all' }}>
            <option value="analytical">Analytical challenges</option><option value="standard">Built-in graded cases</option></select></div>
        <div><label class="label" for="category">Task category</label>
          <select id="category" class="field" bind:value={studio.category}>
            <option value="all">All categories</option>{#each categories as c}<option value={c}>{words(c).replace(/^./, (l) => l.toUpperCase())}</option>{/each}</select></div>
        <div class="sm:col-span-2">
          <div class="flex items-baseline justify-between"><label class="label" for="cases">Cases per model</label><span class="text-xs text-faint">1 – {studio.maxCases}</span></div>
          <div class="flex items-center gap-3">
            <input class="h-1.5 min-w-0 flex-1 accent-(--accent-text)" type="range" min="1" max={studio.maxCases} bind:value={studio.count} aria-label="Cases per model slider" />
            <input id="cases" class="field num !w-20 text-center" type="number" min="1" max={studio.maxCases} bind:value={studio.count} aria-invalid={!studio.countValid} />
          </div>
        </div>
      </div>
      <p class="mt-4 flex gap-2 text-[13px] text-muted"><Gauge size={15} class="mt-0.5 shrink-0 text-faint" aria-hidden="true" />Each model receives identical cases. Outputs are checked against the same expected answers.</p>
    </section>

    <section class="card p-5 sm:p-6" in:fly={rise(60)}>
      <h2 class="flex items-center gap-2 text-lg font-semibold"><SlidersHorizontal size={17} class="text-accent-text" aria-hidden="true" />Ranking thresholds</h2>
      <p class="mb-4 mt-1 text-[13px] text-muted">A model must clear every threshold before it is ranked.</p>
      <div class="grid items-end gap-4 sm:grid-cols-3">
        <label><span class="label">Minimum task success (%)</span><input class="field num" type="number" min="0" max="100" bind:value={studio.minSuccess} /></label>
        <label><span class="label">Minimum schema compliance (%)</span><input class="field num" type="number" min="0" max="100" bind:value={studio.minSchema} /></label>
        <label><span class="label">Maximum p95 time (s, optional)</span><input class="field num" type="number" min="0.01" step="any" placeholder="No limit" bind:value={studio.maxLatency} /></label>
      </div>
    </section>
  </fieldset>

  <aside class="card p-5 sm:p-6 lg:sticky lg:top-0" in:fly={rise(120)}>
    <div class="mb-3 flex items-baseline justify-between"><h2 class="text-lg font-semibold">Models</h2><span class="num text-xs text-faint">{studio.selected.length}/{MAX_MODELS}</span></div>
    <div class="mb-3 flex flex-wrap items-center gap-2"><ModeSwitch /></div>
    <RoutingNote />
    <div class="mt-3 grid gap-2">
      {#each studio.visibleModels as m (m.id)}
        {@const on = studio.selected.includes(m.id)}
        <label class="model hue-{studio.hue(m.id)} flex items-center gap-3 rounded-xl border px-3 py-2.5 transition-colors has-disabled:opacity-55 {on ? 'border-(--hue) bg-accent-soft' : 'border-line hover:border-line-strong'}">
          <i class="dot" aria-hidden="true"></i>
          <span class="min-w-0 flex-1"><span class="block truncate text-sm font-medium">{m.label ?? m.name}</span>
            <code class="num block truncate text-[11.5px] text-faint">{m.installed ? m.id.replace(/^ollama\//, '') : m.provider ? 'Configure ' + m.provider + ' credentials' : 'ollama pull ' + m.id}</code></span>
          <input class="check" type="checkbox" value={m.id} bind:group={studio.selected} disabled={!!studio.busy || !m.installed || (studio.selected.length >= MAX_MODELS && !on)} />
        </label>
      {:else}
        <p class="rounded-xl border border-dashed border-line-strong px-3 py-4 text-[13px] text-muted">{studio.loaded ? (studio.mode === 'local' ? 'No local models found. Open Ollama, then refresh.' : 'No hosted providers are configured.') : 'Checking models…'}</p>
      {/each}
    </div>
    <button class="btn btn-ghost btn-sm mt-2" disabled={!!studio.busy} onclick={studio.refresh}><RefreshCw size={13} aria-hidden="true" />Refresh model status</button>
    <div class="mt-4 border-t border-line pt-4">
      <button class="btn btn-primary h-12 w-full text-[15px]" disabled={!!studio.busy || !studio.selected.length || !studio.countValid} onclick={studio.execute}>Run benchmark<ArrowRight size={16} aria-hidden="true" /></button>
      <p class="mt-2.5 text-center text-xs text-faint">{#if total}<span class="num">{studio.count} × {studio.selected.length} = {total}</span> generations · {/if}Runs sequentially · {studio.mode === 'local' ? 'Ollama' : 'provider APIs'}</p>
    </div>
  </aside>
</div>
