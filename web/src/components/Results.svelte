<script lang="ts">
  import { ChevronDown, ChevronLeft, ChevronRight, CircleCheck, CircleX, Download, MessageSquare, RefreshCw, Sparkles, Trophy } from '@lucide/svelte'
  import { fly } from 'svelte/transition'
  import { studio } from '../lib/studio.svelte'
  import { percent, scoreTone, seconds } from '../lib/format'
  import { rise } from '../lib/motion'
  import Rubric from './Rubric.svelte'
  import ScoreRing from './ScoreRing.svelte'
  import SplitRating from './SplitRating.svelte'

  const report = $derived(studio.report)
  const runs = $derived(studio.runs)
  const name = studio.name

  let requested = ''
  $effect(() => {
    const id = report?.run_id
    if (!id) { requested = ''; return }
    if (!report.comparison_summary && requested !== id) { requested = id; void studio.readSummary(report) }
  })

  const slowest = $derived(Math.max(1, ...(report?.answers ?? []).map((a: any) => a.latency_ms ?? 0)))
  const cases = $derived(runs[0]?.results ?? [])
  const current = $derived(cases[studio.caseIndex])
  const stats = (r: any) => [
    ['Median attempt', seconds(r.p50_ms)],
    ['p95 attempt', seconds(r.p95_ms)],
    ...(r.metrics ? [
      ...(['correctness', 'faithfulness'] as const).map((key) => ['Judged ' + key, r.quality_dimensions?.[key] ? r.quality_dimensions[key].mean.toFixed(1) + ' / 10' : 'N/A']),
      ['Schema compliance', percent(r.metrics.schema_rate, 1)],
      ['Request errors', percent(r.metrics.error_rate, 1)],
      ['Fees per success', r.metrics.provider_cost_per_success == null ? 'Unavailable' : '$' + r.metrics.provider_cost_per_success],
      ...(r.metrics.field_micro_f1 != null ? [['Extraction field F1', r.metrics.field_micro_f1.toFixed(3)]] : []),
    ] : []),
  ]
</script>

{#if !report}
  <div class="card mx-auto mt-6 max-w-lg px-6 py-12 text-center" in:fly={rise()}>
    <span class="mx-auto mb-4 grid size-12 place-items-center rounded-2xl bg-accent-soft text-accent-text"><Trophy size={22} aria-hidden="true" /></span>
    <h2 class="text-lg font-semibold">No result open yet</h2>
    <p class="mt-1 text-sm text-muted">Run a comparison or open a saved result from History.</p>
  </div>
{:else}
  <div class="toolbar mb-4 flex flex-wrap items-center gap-2">
    <span class="chip">{report.answers ? 'Prompt comparison' : 'Matched workload'}</span>
    <span class="text-[13px] text-muted">{new Date(report.started_at).toLocaleString()}</span>
    <span class="ml-auto flex flex-wrap gap-2">
      {#if report.answers}<button class="btn btn-sm" disabled={!!studio.busy} onclick={() => studio.action('Opening chat', () => studio.resume(report))}><MessageSquare size={14} aria-hidden="true" />Continue chat</button>{/if}
      <button class="btn btn-sm" disabled={!!studio.busy || !report.run_id} onclick={studio.download}><Download size={14} aria-hidden="true" />Export JSON</button>
    </span>
  </div>

  <section class="relative mb-7 overflow-hidden rounded-[1.1rem] bg-linear-to-br from-accent-text/60 via-line to-[#3ddbb0]/50 p-px shadow-card" aria-label="Comparison summary" in:fly={rise()}>
    <div class="rounded-[calc(1.1rem-1px)] bg-surface p-5 sm:p-6">
      <div class="mb-2 flex flex-wrap items-center gap-x-3 gap-y-1">
        <h2 class="flex items-center gap-2 font-semibold"><Sparkles size={16} class="text-accent-text" aria-hidden="true" />Comparison summary</h2>
        <small class="num text-xs text-faint">OpenAI · {report.comparison_summary?.model ?? report.judge_model ?? 'gpt-oss:20b'}</small>
      </div>
      {#if report.comparison_summary}
        <p class="max-w-[72ch] whitespace-pre-wrap text-[15px] leading-relaxed">{report.comparison_summary.text}</p>
      {:else if studio.summarizing === report.run_id}
        <p role="status" class="flex items-center gap-2.5 text-sm text-muted"><i class="spinner" aria-hidden="true"></i>The judge is writing the comparison…</p>
        <div class="mt-3 grid gap-2" aria-hidden="true"><div class="skeleton h-3 w-11/12"></div><div class="skeleton h-3 w-9/12"></div></div>
      {:else if studio.summaryError}
        <p class="text-sm text-warn">{studio.summaryError}</p>
        <button class="btn btn-sm mt-3" onclick={() => studio.readSummary(report)}><RefreshCw size={13} aria-hidden="true" />Retry summary</button>
      {:else}<p class="text-sm text-faint">A summary will appear once this run is saved.</p>{/if}
    </div>
  </section>

  {#if report.answers}
    <div class="mb-3 flex flex-wrap items-center justify-between gap-2">
      <h2 class="text-lg font-semibold">Answer quality</h2>
      {#if report.run_id && report.answers.some((r: any) => !r.judge && r.output)}<button class="btn btn-sm" disabled={!!studio.busy} onclick={() => studio.regrade(report.run_id)}><RefreshCw size={13} aria-hidden="true" />Grade saved answers</button>{/if}
    </div>
    <div class="mb-8 grid gap-3 sm:grid-cols-[repeat(auto-fit,minmax(17rem,1fr))]">
      {#each report.answers as row, i (row.requested_model)}
        <article class="card hue-{studio.hue(row.requested_model, i)} p-5" in:fly={rise(i * 50)}>
          <div class="flex items-center gap-3">
            {#if row.judge}<ScoreRing score={row.judge.score} size={68} />{/if}
            <div class="min-w-0"><p class="flex items-center gap-2 text-sm font-semibold"><i class="dot" aria-hidden="true"></i><span class="truncate">{name(row.requested_model)}</span></p>
              <p class="mt-0.5 text-xs text-faint">{row.judge ? (row.judge.scope ?? 'Answer quality') : row.status}{#if row.latency_ms != null} · <span class="num">{seconds(row.latency_ms)}</span>{/if}</p></div>
          </div>
          {#if row.judge}
            <meter class="tone-{scoreTone(row.judge.score)} mt-4" min="0" max="10" value={row.judge.score} aria-label={name(row.requested_model) + ' quality'}></meter>
            <p class="mt-3 text-sm leading-relaxed text-muted">{row.judge.reason ?? row.judge.scope}</p>
            <Rubric judge={row.judge} />
            <details class="group/d mt-3 border-t border-line pt-1">
              <summary class="flex min-h-9 items-center gap-1.5 text-[13px] font-medium text-muted hover:text-text"><ChevronDown size={14} class="transition-transform group-open/d:rotate-180" aria-hidden="true" />Grading details</summary>
              <div class="grid gap-2 pb-1 text-[13px] text-muted">
                <p class="num text-xs text-faint">{row.judge.model}{#if row.judge.ollama_duration_ns != null} · judge call {(row.judge.ollama_duration_ns / 1e9).toFixed(2)} s{#if row.judge.ollama_load_ns != null} · model load {(row.judge.ollama_load_ns / 1e9).toFixed(2)} s{/if}{/if}</p>
                {#each row.judge.transcript ?? [] as round}
                  <details class="rounded-lg bg-sunken/70 px-3"><summary class="py-2 font-medium text-text">Review round {round.round}</summary>
                    {#each round.reviews as review}<p class="pb-2"><strong class="text-text">{review.model} · {review.score}/5</strong><br />{review.reason}</p>{/each}</details>
                {/each}
                {#each Object.entries(row.judge.criteria ?? {}) as [criterion, item]}<p><strong class="text-text">{criterion} · {(item as any).rating}/5</strong><br />{(item as any).reason}</p>{/each}
              </div>
            </details>
          {:else if row.judge_split}
            <div class="mt-4"><SplitRating split={row.judge_split} /></div>
            {#if row.judge_error}<p class="mt-2 text-sm text-warn">{row.judge_error}</p>{/if}
          {:else}
            <p class="mt-3 text-sm {row.status === 'Error' ? 'text-bad' : 'text-muted'}">{row.judge_error ?? (row.status === 'Error' ? row.error : 'Awaiting grading')}</p>
          {/if}
        </article>
      {/each}
    </div>

    <h2 class="mb-3 text-lg font-semibold">Response time</h2>
    <div class="card mb-8 grid gap-3 p-5">
      {#each report.answers.filter((r: any) => r.latency_ms != null) as r, i}
        <div class="barrow hue-{studio.hue(r.requested_model, i)} grid grid-cols-[minmax(0,9rem)_1fr_auto] items-center gap-3 text-sm max-sm:grid-cols-[minmax(0,1fr)_auto]">
          <span class="truncate font-medium">{name(r.requested_model)}</span>
          <div class="h-2.5 overflow-hidden rounded-full bg-sunken max-sm:order-last max-sm:col-span-2" role="img" aria-label="{name(r.requested_model)} responded in {seconds(r.latency_ms)}">
            <div class="h-full rounded-full bg-(--hue) transition-[width] duration-700 ease-out" style:width={percent(r.latency_ms / slowest)}></div></div>
          <span class="num text-muted">{seconds(r.latency_ms)}</span>
        </div>
      {:else}<p class="text-sm text-muted">No completed responses to time.</p>{/each}
    </div>

    <h2 class="mb-3 text-lg font-semibold">Answers</h2>
    <details class="card group/p mb-3 px-5"><summary class="flex min-h-11 items-center gap-2 text-sm font-medium text-muted hover:text-text"><ChevronDown size={14} class="transition-transform group-open/p:rotate-180" aria-hidden="true" />View original prompt</summary><pre class="pb-4 text-sm text-muted">{report.prompt}</pre></details>
    <div class="grid gap-3 lg:grid-cols-2">
      {#each report.answers as r, i}
        <article class="card hue-{studio.hue(r.requested_model, i)} p-5"><p class="mb-2 flex items-center gap-2 text-sm font-semibold"><i class="dot" aria-hidden="true"></i>{name(r.requested_model)}<span class="chip ml-auto font-normal">{r.status}</span></p>
          <pre class="text-[14.5px] leading-relaxed {r.output ? '' : 'text-bad'}">{r.output ?? r.error}</pre></article>
      {/each}
    </div>
  {:else}
    {#if report.ranking}
      {@const gates = report.ranking.gates}
      <section class="card mb-8 p-5 sm:p-6" in:fly={rise(60)}>
        <div class="mb-1 flex flex-wrap items-center gap-2"><h2 class="flex items-center gap-2 text-lg font-semibold"><Trophy size={17} class="text-accent-text" aria-hidden="true" />Provisional ranking</h2></div>
        <p class="mb-4 flex flex-wrap gap-1.5 text-xs"><span class="chip">Success ≥ {gates.min_success}%</span><span class="chip">Schema ≥ {gates.min_schema}%</span>{#if gates.max_p95_seconds}<span class="chip">p95 ≤ {gates.max_p95_seconds}s</span>{/if}</p>
        <ol class="grid gap-2">
          {#each report.ranking.entries as entry, i}
            <li class="hue-{studio.hue(entry.model, i)} flex flex-wrap items-center gap-x-4 gap-y-2 rounded-xl border px-4 py-3 {entry.score != null && i === 0 ? 'border-accent-text/50 bg-accent-soft' : 'border-line'}">
              <span class="num grid size-7 shrink-0 place-items-center rounded-full text-xs font-semibold {entry.score == null ? 'bg-sunken text-faint' : i === 0 ? 'bg-accent text-accent-ink' : 'bg-sunken text-text'}">{entry.score == null ? '–' : i + 1}</span>
              <strong class="flex min-w-0 items-center gap-2 text-sm font-semibold"><i class="dot" aria-hidden="true"></i><span class="truncate">{name(entry.model)}</span></strong>
              {#if entry.score == null}
                <span class="ml-auto flex flex-wrap justify-end gap-1.5">{#each entry.reasons as reason}<span class="chip !whitespace-normal !border-bad/30 !bg-bad-soft text-left !text-bad">{reason}</span>{/each}</span>
              {:else}
                <span class="ml-auto flex min-w-36 flex-1 items-center gap-3 sm:max-w-xs"><span class="h-2 flex-1 overflow-hidden rounded-full bg-sunken" aria-hidden="true"><span class="block h-full rounded-full bg-(--hue)" style:width="{entry.score}%"></span></span><span class="num text-base font-semibold">{entry.score}<span class="text-xs font-normal text-faint"> / 100</span></span></span>
              {/if}
            </li>
          {/each}
        </ol>
        <small class="mt-4 block text-xs leading-relaxed text-faint">Relative weights: {Object.entries(report.ranking.weights).map(([k, v]) => k + ' ' + v).join(' · ')}. Quality uses exact task success. Costs require complete provider-fee data.</small>
      </section>
    {/if}

    <h2 class="mb-3 text-lg font-semibold">Matched workload</h2>
    <div class="mb-8 grid gap-3 sm:grid-cols-[repeat(auto-fit,minmax(18rem,1fr))]">
      {#each runs as r, i}
        <article class="card hue-{studio.hue(r.model_id, i)} p-5" in:fly={rise(i * 50)}>
          <p class="flex items-center gap-2 text-sm font-semibold"><i class="dot" aria-hidden="true"></i><span class="truncate">{name(r.model_id)}</span></p>
          <div class="mt-3 flex items-end justify-between gap-3">
            <p><span class="num text-4xl font-semibold tracking-tight">{percent(r.success_rate)}</span><span class="ml-2 text-xs text-faint">cases passed</span></p>
            <p class="num text-sm text-muted">{r.successful_cases} / {r.attempted_cases}</p>
          </div>
          <progress class="mt-2" style="--tone:var(--hue)" max="1" value={r.success_rate} aria-label="{name(r.model_id)} cases passed"></progress>
          <p class="mt-1.5 text-xs text-faint">95% Wilson interval <span class="num">{r.wilson_95.map((v: number) => percent(v)).join(' – ')}</span></p>
          {#if r.judge_mean != null}
            <div class="tone-{scoreTone(r.judge_mean)} mt-4 rounded-xl bg-sunken/70 p-3">
              <p class="mb-1.5 flex items-baseline justify-between text-[13px]"><span class="text-muted">Judge quality</span><span><strong class="num text-sm">{r.judge_mean.toFixed(1)}/10</strong> <span class="text-xs text-faint">({r.judge_count} scored)</span></span></p>
              <meter min="0" max="10" value={r.judge_mean} aria-label="Average judge rating"></meter>
            </div>
          {/if}
          <dl class="mt-4 grid grid-cols-2 gap-x-4 gap-y-2.5 text-[13px]">
            {#each stats(r) as [label, value]}<div><dt class="text-[11.5px] text-faint">{label}</dt><dd class="num font-medium {value === 'N/A' || value === 'Unavailable' ? 'text-faint' : ''}">{value}</dd></div>{/each}
          </dl>
        </article>
      {/each}
    </div>

    {#if report.pairs}
      <details class="card group/pc mb-8 px-5"><summary class="flex min-h-12 items-center gap-2 text-sm font-semibold"><ChevronDown size={14} class="text-faint transition-transform group-open/pc:rotate-180" aria-hidden="true" />Paired comparisons<span class="chip ml-1 font-normal">{report.pairs.length}</span></summary>
        <div class="grid gap-2 pb-5">
          {#each report.pairs as pair}
            {@const found = pair.holm_p < 0.05}
            <div class="rounded-xl border border-line p-3 text-[13.5px]">
              <p class="flex flex-wrap items-center gap-2 font-medium">{name(pair.first)} <span class="text-faint">vs</span> {name(pair.second)}<span class="chip ml-auto {found ? 'chip-accent' : ''}">Adjusted p = <span class="num">{pair.holm_p.toFixed(3)}</span></span></p>
              <p class="mt-1 text-muted">Only the first passed {pair.first_only} cases. Only the second passed {pair.second_only}. {found ? 'A difference was detected on these cases.' : 'Insufficient evidence of a difference.'}</p>
            </div>
          {/each}
        </div>
      </details>
    {/if}

    {#if current}
      <div class="mb-3 flex flex-wrap items-center gap-2">
        <h2 class="mr-auto text-lg font-semibold"><label for="inspect">Inspect a case</label></h2>
        <button class="btn btn-sm btn-icon" aria-label="Previous case" disabled={studio.caseIndex === 0} onclick={() => studio.caseIndex--}><ChevronLeft size={15} aria-hidden="true" /></button>
        <select id="inspect" class="field num !min-h-8 !w-auto max-w-[60vw] !py-1 text-[13px]" bind:value={studio.caseIndex}>{#each cases as row, i}<option value={i}>{i + 1}/{cases.length} · {row.case_id}</option>{/each}</select>
        <button class="btn btn-sm btn-icon" aria-label="Next case" disabled={studio.caseIndex >= cases.length - 1} onclick={() => studio.caseIndex++}><ChevronRight size={15} aria-hidden="true" /></button>
      </div>
      <div class="card mb-3 p-5">
        <p class="eyebrow mb-1.5">Input</p><p class="whitespace-pre-wrap text-[14.5px]">{current.input}</p>
        <p class="eyebrow mb-1.5 mt-4">Expected</p><pre class="num rounded-xl bg-sunken/70 p-3 text-[13px]">Expected: {JSON.stringify(current.expected)}</pre>
      </div>
      <div class="grid gap-3 lg:grid-cols-2">
        {#each runs as r, i}
          {@const row = r.results[studio.caseIndex]}
          <article class="card hue-{studio.hue(r.model_id, i)} p-5">
            <p class="mb-2 flex items-center gap-2 text-sm font-semibold"><i class="dot" aria-hidden="true"></i><span class="truncate">{name(r.model_id)}</span>
              <span class="chip ml-auto {row.passed ? 'chip-accent' : '!border-bad/30 !bg-bad-soft !text-bad'}">{#if row.passed}<CircleCheck size={12} aria-hidden="true" />Pass{:else}<CircleX size={12} aria-hidden="true" />Miss{/if}</span></p>
            <pre class="text-[14.5px] leading-relaxed">{row.output || row.reason}</pre>
            {#if row.judge}
              <div class="mt-3 border-t border-line pt-3"><p class="flex items-center gap-2.5 text-sm"><ScoreRing score={row.judge.score} size={36} /><strong>Judge · <span class="num">{row.judge.score}/10</span></strong></p>
                <p class="mt-2 text-sm text-muted">{row.judge.reason}</p><Rubric judge={row.judge} /></div>
            {:else if row.judge_split}<div class="mt-3 border-t border-line pt-3"><SplitRating split={row.judge_split} /></div>
            {:else if row.judge_error}<p class="mt-3 text-sm text-warn">{row.judge_error}</p>{/if}
          </article>
        {/each}
      </div>
    {/if}
  {/if}
{/if}
