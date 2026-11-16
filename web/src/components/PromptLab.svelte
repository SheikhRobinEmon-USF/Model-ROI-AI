<script lang="ts">
  import { ArrowUp, Check, ChevronDown, Copy, FileText, Paperclip, Plus, RefreshCw, Target, Trophy, X, Zap } from '@lucide/svelte'
  import { fly } from 'svelte/transition'
  import { MAX_MODELS, studio } from '../lib/studio.svelte'
  import { scoreTone, seconds } from '../lib/format'
  import { rise } from '../lib/motion'
  import ModeSwitch from './ModeSwitch.svelte'
  import RoutingNote from './RoutingNote.svelte'
  import Rubric from './Rubric.svelte'
  import ScoreRing from './ScoreRing.svelte'
  import SplitRating from './SplitRating.svelte'

  const starters = [
    ['Reasoning', "A clinic's revenue grew 12% to $4.2M while costs rose 9% to $3.1M. What happened to its operating margin?"],
    ['Extraction', 'Return the payer, service date and total as JSON from: "Claim for Dana Ortiz, Aetna, 3 March 2026, total $1,284.50".'],
    ['Coding', 'Write a Python function that merges overlapping intervals, then explain its time complexity.'],
    ['Judgement', 'When is a 4B local model good enough for support triage, and when is a large hosted model worth paying for?'],
  ]

  let picker = $state<HTMLDetailsElement>()
  const canSend = $derived(!studio.busy && !!studio.selected.length && !!studio.prompt.trim())

  function focusedId(turn: any, index: number) {
    return turn.answers.some((a: any) => a.requested_model === studio.focused[index]) ? studio.focused[index] : turn.answers[0]?.requested_model
  }
  /** Highlights are only meaningful when at least two answers can be compared. */
  function leaders(turn: any) {
    const judged = turn.answers.filter((a: any) => a.judge), timed = turn.answers.filter((a: any) => a.output && a.latency_ms != null)
    const top = judged.length > 1 ? Math.max(...judged.map((a: any) => a.judge.score)) : null
    const fast = timed.length > 1 ? Math.min(...timed.map((a: any) => a.latency_ms)) : null
    return {
      best: top != null && judged.filter((a: any) => a.judge.score === top).length === 1 ? judged.find((a: any) => a.judge.score === top).requested_model : null,
      fastest: fast != null && timed.filter((a: any) => a.latency_ms === fast).length === 1 ? timed.find((a: any) => a.latency_ms === fast).requested_model : null,
    }
  }
  function keydown(e: KeyboardEvent) {
    if (e.key === 'Enter' && !e.shiftKey && !e.isComposing) {
      e.preventDefault()
      if (canSend) studio.execute()
    }
  }
  function pick(e: Event) {
    const input = e.currentTarget as HTMLInputElement, file = input.files?.[0]
    if (file) studio.attach(file)
    input.value = ''
  }
</script>

<svelte:document onclick={(e) => { if (picker?.open && !picker.contains(e.target as Node)) picker.open = false }} />

<section class="chat-space mx-auto flex h-full min-h-0 w-full max-w-[1100px] flex-col px-3 sm:px-4 md:px-8">
  <div class="chat-tools relative z-10 flex flex-wrap items-center gap-2 py-3">
    <ModeSwitch compact />
    <details bind:this={picker}>
      <summary class="btn btn-sm">
        <span class="flex -space-x-1" aria-hidden="true">{#each studio.selected.slice(0, 5) as id}<i class="dot hue-{studio.hue(id)} !shadow-none ring-2 ring-raised"></i>{/each}</span>
        Models · {studio.selected.length}<ChevronDown size={14} class="text-faint" aria-hidden="true" />
      </summary>
      <div class="model-menu absolute border border-line-strong bg-raised left-0 top-full z-20 mt-1 max-h-[min(26rem,60dvh)] w-[min(100%,23rem)] overflow-y-auto rounded-2xl p-2 shadow-2xl">
        <p class="flex items-center justify-between px-2 pb-1.5 pt-1 text-xs text-faint"><span>Compare up to {MAX_MODELS} responders</span><span class="num">{studio.selected.length}/{MAX_MODELS}</span></p>
        {#each studio.visibleModels as m (m.id)}
          <label class="flex items-center gap-3 rounded-xl px-2 py-2 transition-colors hover:bg-accent-soft has-disabled:opacity-55">
            <input class="check" type="checkbox" value={m.id} bind:group={studio.selected} disabled={!!studio.busy || !m.installed || (studio.selected.length >= MAX_MODELS && !studio.selected.includes(m.id))} />
            <span class="min-w-0 flex-1">
              <span class="flex items-center gap-2 text-sm font-medium"><i class="dot hue-{studio.hue(m.id)}" aria-hidden="true"></i><span class="truncate">{m.label ?? m.name}</span></span>
              <small class="mt-0.5 block truncate text-xs text-faint">{m.custom ? 'Your model · Ollama' : (m.provider ?? 'Ollama')} · {m.installed ? 'Ready' : m.provider ? 'Setup needed' : 'ollama pull ' + m.id}</small>
            </span>
          </label>
        {:else}
          <p class="px-2 py-3 text-[13px] text-muted">{studio.loaded ? (studio.mode === 'local' ? 'No local models found. Open Ollama, then refresh.' : 'No hosted providers are configured.') : 'Checking models…'}</p>
        {/each}
        <button class="btn btn-ghost btn-sm mt-1 w-full" disabled={!!studio.busy} onclick={studio.refresh}><RefreshCw size={13} aria-hidden="true" />Refresh model status</button>
      </div>
    </details>
    <button class="btn btn-sm btn-icon ml-auto md:hidden" disabled={!!studio.busy} onclick={studio.newChat} aria-label="New chat"><Plus size={16} aria-hidden="true" /></button>
  </div>

  {#if studio.mode === 'hosted'}
    <div class="grid gap-2 pb-2">
      <RoutingNote />
      <label class="context-option flex w-fit items-center gap-2 text-[13px] text-muted"><input class="check" type="checkbox" bind:checked={studio.longContext} disabled={!!studio.busy} /> Longer chat history · up to 32 turns</label>
    </div>
  {/if}

  <div class="chat-feed -mx-1 min-h-0 flex-1 overflow-y-auto scroll-smooth px-1 pb-4" bind:this={studio.feed}>
    {#each studio.turns as turn, index}
      {@const lead = leaders(turn)}
      {@const live = !turn.run_id && index === studio.turns.length - 1}
      <section class="chat-turn mb-8">
        <div class="group/msg mt-4 flex flex-col items-end" in:fly={rise()}>
          <div class="message max-w-[min(85%,44rem)] whitespace-pre-wrap break-words rounded-3xl rounded-br-lg bg-accent px-4 py-2.5 text-[15px] text-accent-ink shadow-card">{turn.prompt}</div>
          <div class="message-actions mt-1">
            <button class="btn btn-ghost btn-sm !min-h-7 !px-2 text-xs" aria-label="Copy prompt" onclick={() => studio.copyPrompt(turn.prompt, index)}>
              {#if studio.copied === index}<Check size={12} aria-hidden="true" />Copied{:else}<Copy size={12} aria-hidden="true" />Copy{/if}
            </button>
          </div>
        </div>

        {#if turn.answers.length > 2}
          <div class="answer-picker mb-3 mt-2 flex gap-2 overflow-x-auto pb-1" role="group" aria-label="Choose an answer">
            {#each turn.answers as answer}
              {@const on = focusedId(turn, index) === answer.requested_model}
              <button class="hue-{studio.hue(answer.requested_model)} min-w-0 shrink-0 rounded-xl border px-3 py-2 text-left transition-colors {on ? 'border-(--hue) bg-accent-soft' : 'border-line bg-surface hover:border-line-strong'}"
                aria-pressed={on} onclick={() => (studio.focused[index] = answer.requested_model)}>
                <span class="flex items-center gap-2 text-[13.5px] font-medium"><i class="dot" aria-hidden="true"></i>{studio.name(answer.requested_model)}{#if lead.best === answer.requested_model}<Trophy size={12} class="text-accent-text" aria-hidden="true" />{/if}</span>
                <small class="num mt-0.5 block text-[11.5px] text-faint">{answer.judge ? answer.judge.score + '/10' : answer.status} · {seconds(answer.latency_ms)}</small>
              </button>
            {/each}
          </div>
        {/if}

        <div class="cards mt-3 grid items-start gap-3 {turn.answers.length + (live ? studio.pending.length : 0) === 2 ? 'lg:grid-cols-2' : ''}">
          {#each turn.answers.filter((a: any) => turn.answers.length <= 2 || a.requested_model === focusedId(turn, index)) as row (row.requested_model)}
            <article class="response card hue-{studio.hue(row.requested_model)} relative flex flex-col overflow-hidden" in:fly={rise()}>
              <span class="absolute inset-x-0 top-0 h-px bg-linear-to-r from-transparent via-(--hue) to-transparent opacity-70" aria-hidden="true"></span>
              <header class="flex items-center gap-2.5 px-4 pt-3.5">
                <i class="dot" aria-hidden="true"></i>
                <strong class="min-w-0 truncate text-[14.5px] font-semibold">{studio.name(row.requested_model)}</strong>
                {#if lead.best === row.requested_model}<span class="chip chip-accent"><Trophy size={11} aria-hidden="true" />Top score</span>{/if}
                {#if lead.fastest === row.requested_model}<span class="chip max-sm:hidden"><Zap size={11} aria-hidden="true" />Fastest</span>{/if}
                <span class="ml-auto flex shrink-0 items-center gap-2.5">
                  {#if row.latency_ms != null}<span class="num text-xs text-faint">{seconds(row.latency_ms)}</span>{/if}
                  {#if row.judge}<ScoreRing score={row.judge.score} size={38} />{/if}
                </span>
              </header>
              <pre class="flex-1 px-4 pb-4 pt-2.5 text-[14.5px] leading-relaxed {row.output ? '' : 'text-bad'}">{row.output ?? row.error}</pre>
              <details class="answer-metrics group/metrics border-t border-line">
                <summary class="flex min-h-11 items-center gap-2 px-4 text-[13px] font-medium text-muted transition-colors hover:text-text">
                  <ChevronDown size={14} class="transition-transform group-open/metrics:rotate-180" aria-hidden="true" />
                  Metrics{#if row.judge} · <span class="num">{row.judge.score.toFixed(1)} / 10</span>{/if}
                </summary>
                <div class="px-4 pb-4">
                  <dl class="mb-3 grid grid-cols-2 gap-2 sm:grid-cols-3">
                    <div class="rounded-xl bg-sunken/70 px-3 py-2"><dt class="text-[11.5px] text-faint">Response time</dt><dd class="num text-sm font-medium">{seconds(row.latency_ms)}</dd></div>
                    <div class="rounded-xl bg-sunken/70 px-3 py-2"><dt class="text-[11.5px] text-faint">Tokens in / out</dt><dd class="num text-sm font-medium">{row.input_tokens ?? '—'} / {row.output_tokens ?? '—'}</dd></div>
                    {#if row.decode_tokens_per_second != null}<div class="rounded-xl bg-sunken/70 px-3 py-2"><dt class="text-[11.5px] text-faint">Decode speed</dt><dd class="num text-sm font-medium">{row.decode_tokens_per_second.toFixed(1)} tok/s</dd></div>{/if}
                  </dl>
                  {#if row.judge}
                    <div class="tone-{scoreTone(row.judge.score)}">
                      <p class="mb-1.5 flex items-baseline gap-2 text-sm"><strong class="num text-base">{row.judge.score.toFixed(1)} / 10</strong><span class="text-faint">{row.judge.scope ?? 'Answer quality'}</span></p>
                      <meter min="0" max="10" value={row.judge.score} aria-label={studio.name(row.requested_model) + ' quality'}></meter>
                    </div>
                    <p class="mt-2.5 text-sm leading-relaxed text-muted">{row.judge.reason}</p>
                    <Rubric judge={row.judge} />
                  {:else if row.judge_split}
                    <SplitRating split={row.judge_split} />
                    {#if row.judge_error}<p class="mt-2 text-sm text-warn">{row.judge_error}</p>{/if}
                  {:else}
                    <p class="text-sm text-muted">{row.judge_error ?? row.error ?? 'Awaiting grading'}</p>
                  {/if}
                  {#if turn.reference_answer}
                    <div class="mt-3 rounded-xl border border-dashed border-line-strong p-3"><p class="eyebrow mb-1 flex items-center gap-1.5"><Target size={11} aria-hidden="true" />Grading reference</p><p class="whitespace-pre-wrap text-[13px] text-muted">{turn.reference_answer}</p></div>
                  {/if}
                  {#if turn.run_id && !row.judge && row.output}
                    <button class="btn btn-sm mt-3" disabled={!!studio.busy} onclick={() => studio.regrade(turn.run_id, index)}><RefreshCw size={13} aria-hidden="true" />Retry ungraded answers</button>
                  {/if}
                </div>
              </details>
            </article>
          {/each}
          {#if live}
            {#each turn.answers.length > 2 ? [] : studio.pending as id, n (id)}
              <div class="card hue-{studio.hue(id)} p-4" aria-hidden="true">
                <div class="flex items-center gap-2.5"><i class="dot"></i><span class="text-[14.5px] font-semibold">{studio.name(id)}</span><span class="ml-auto text-xs text-faint">{n === 0 ? 'Generating…' : 'Queued'}</span></div>
                <div class="mt-4 grid gap-2.5 {n === 0 ? '' : 'opacity-40'}"><div class="skeleton h-3 w-11/12"></div><div class="skeleton h-3 w-full"></div><div class="skeleton h-3 w-8/12"></div></div>
              </div>
            {/each}
          {/if}
        </div>
      </section>
    {:else}
      <div class="mx-auto flex min-h-full max-w-3xl flex-col justify-center py-6" in:fly={rise()}>
        <p class="eyebrow mb-3 flex items-center gap-2"><span class="live-dot"></span>{studio.mode === 'local' ? 'Local' : 'Hosted'} · {studio.selected.length} {studio.selected.length === 1 ? 'model' : 'models'} selected</p>
        <h2 class="chat-empty gradient-text text-[clamp(2rem,6vw,3.6rem)] font-semibold leading-[1.05] tracking-[-0.045em]">What would you like to compare?</h2>
        <p class="mt-4 max-w-xl text-[15px] text-muted">Ask once. Every selected model answers the same prompt, an independent judge grades each answer, and you see quality next to speed.</p>
        {#if studio.selected.length}
          <ul class="mt-4 flex flex-wrap gap-1.5" aria-label="Selected models">{#each studio.selected as id}<li class="chip hue-{studio.hue(id)}"><i class="dot !size-1.5 !shadow-none" aria-hidden="true"></i>{studio.name(id)}</li>{/each}</ul>
        {/if}
        <div class="mt-7 grid gap-2.5 sm:grid-cols-2">
          {#each starters as [kind, text], i}
            <button class="card group/s flex flex-col items-start p-3.5 text-left transition-[border-color,transform] duration-200 hover:-translate-y-0.5 hover:border-accent-text disabled:opacity-50 {i > 1 ? 'max-sm:hidden' : ''}" disabled={!!studio.busy}
              in:fly={rise(80 + i * 50)} onclick={() => { studio.prompt = text; studio.editor?.focus() }}>
              <span class="eyebrow !text-accent-text">{kind}</span>
              <span class="mt-1 line-clamp-2 block text-[13.5px] leading-snug text-muted group-hover/s:text-text">{text}</span>
            </button>
          {/each}
        </div>
      </div>
    {/each}
  </div>

  <div class="composer glass mb-3 rounded-3xl p-2 shadow-card transition-shadow focus-within:border-accent-text focus-within:shadow-[0_0_0_4px_var(--accent-soft)] max-md:mb-2">
    {#if studio.fileName}
      <details class="mx-1 mb-1 rounded-xl border border-line bg-sunken/70">
        <summary class="flex items-center gap-2 px-3 py-2 text-[13px]"><FileText size={14} class="text-accent-text" aria-hidden="true" /><span class="min-w-0 flex-1 truncate font-medium">{studio.fileName}</span><span class="text-xs text-faint">Edit excerpt</span></summary>
        <div class="grid gap-2 px-3 pb-3"><textarea class="field min-h-24 resize-y text-[13px]" aria-label="File excerpt" bind:value={studio.excerpt}></textarea>
          <button class="btn btn-sm w-fit" onclick={() => { studio.fileName = ''; studio.excerpt = '' }}><X size={13} aria-hidden="true" />Remove attachment</button></div>
      </details>
    {/if}
    <textarea id="question" class="block max-h-[28dvh] min-h-12 w-full resize-none bg-transparent px-3 py-2.5 text-[15px] outline-none [field-sizing:content] placeholder:text-faint disabled:opacity-60"
      aria-label="What should the models solve?" bind:this={studio.editor} bind:value={studio.prompt} maxlength="8000" rows="1"
      placeholder={studio.turns.length ? 'Ask a follow-up…' : 'Message the models…'} disabled={!!studio.busy} onkeydown={keydown}></textarea>
    {#if studio.referenceOpen}
      <div class="mx-1 mb-1.5 rounded-xl border border-dashed border-line-strong p-2.5">
        <label class="label" for="reference">Ideal answer for the judge</label>
        <textarea id="reference" class="field min-h-16 resize-y text-[13.5px]" disabled={!!studio.busy} bind:value={studio.reference} maxlength="4000" placeholder="What should a good answer include?"></textarea>
      </div>
    {/if}
    <div class="composer-actions flex items-center gap-1">
      <label class="btn btn-ghost btn-sm relative focus-within:outline-2 focus-within:outline-accent-text has-disabled:opacity-45"><Paperclip size={14} aria-hidden="true" />Attach<input class="sr-only" disabled={!!studio.busy} type="file" onchange={pick} /></label>
      <button class="btn btn-ghost btn-sm {studio.reference ? '!text-accent-text' : ''}" disabled={!!studio.busy} aria-expanded={studio.referenceOpen} onclick={() => (studio.referenceOpen = !studio.referenceOpen)}>
        <Target size={14} aria-hidden="true" /><span class="max-[380px]:sr-only">{studio.reference ? 'Edit reference' : 'Reference answer'}</span></button>
      <span class="ml-auto pr-1 text-[11.5px] text-faint max-md:hidden">{#if !studio.selected.length}Select a model to begin{:else}<kbd class="num">Enter</kbd> to send · <kbd class="num">Shift Enter</kbd> for a new line{/if}</span>
      <button class="send btn btn-primary max-md:ml-auto !rounded-2xl" disabled={!canSend} onclick={studio.execute}>Send<ArrowUp size={15} strokeWidth={2.5} aria-hidden="true" /></button>
    </div>
  </div>
</section>
