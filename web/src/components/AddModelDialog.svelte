<script lang="ts">
  import { Check, CircleAlert, Download, FileBox, PackagePlus, SlidersHorizontal, Trash2, Upload, X } from '@lucide/svelte'
  import { studio, type AddTab } from '../lib/studio.svelte'
  import { bytes, percent } from '../lib/format'

  const tabs: [AddTab, string, any][] = [['upload', 'Upload a file', Upload], ['pull', 'Download by name', Download], ['customize', 'Customize installed', SlidersHorizontal]]
  const uploadSteps = ['Upload', 'Verify and copy into Ollama', 'Register']
  const NAME = /^[a-z0-9][a-z0-9_-]{0,62}$/

  let dialog = $state<HTMLDialogElement>()
  let file = $state<File | null>(null), fileError = $state(''), name = $state(''), instructions = $state(''), dragging = $state(false)
  let reference = $state(''), removing = $state('')
  const job = $derived(studio.job)
  const bases = $derived(studio.models.filter((m) => !m.provider && m.installed))
  const taken = (value: string) => studio.models.some((m) => m.name === 'modelroi/' + value + ':latest')

  $effect(() => {
    if (studio.addOpen && !dialog?.open) dialog?.showModal()
    if (!studio.addOpen && dialog?.open) dialog.close()
  })
  // A finished import closes the dialog; start the next one from a clean form.
  $effect(() => { if (!studio.addOpen) { file = null; fileError = ''; name = ''; instructions = ''; reference = ''; removing = '' } })

  const close = () => { if (!job) studio.addOpen = false }

  async function choose(picked: File | undefined | null) {
    if (!picked) return
    file = null; fileError = ''
    if (!picked.name.toLowerCase().endsWith('.gguf') || (await picked.slice(0, 4).text()) !== 'GGUF') {
      fileError = picked.name + ' is not a GGUF model file.'
      return
    }
    file = picked
    if (!name) name = picked.name.toLowerCase().replace(/\.gguf$/, '').replace(/[^a-z0-9_-]+/g, '-').replace(/^[^a-z0-9]+|-+$/g, '').slice(0, 63)
  }
  function drop(e: DragEvent) {
    e.preventDefault(); dragging = false
    if (!job) choose(e.dataTransfer?.files?.[0])
  }
  const details = (m: (typeof studio.models)[number]) => [m.parameters && m.parameters + ' parameters', m.quantization, bytes(m.size)].filter(Boolean).join(' · ')
</script>

{#snippet nameField(value: string, set: (v: string) => void, id: string)}
  <div><label class="label" for={id}>Model name</label>
    <input {id} class="field num" {value} oninput={(e) => set(e.currentTarget.value)} required maxlength="63" placeholder="support-analyst-v1" disabled={!!job} aria-invalid={!!value && (!NAME.test(value) || taken(value))} />
    <p class="mt-1 text-xs {value && (!NAME.test(value) || taken(value)) ? 'text-bad' : 'text-faint'}">
      {#if value && !NAME.test(value)}Use lowercase letters, digits, hyphens and underscores, starting with a letter or digit.
      {:else if value && taken(value)}That name is already used. Add a version, for example {value}-v2.
      {:else}Saved in Ollama as <span class="num">modelroi/{value || 'name'}</span>.{/if}</p></div>
{/snippet}

{#snippet bar(loaded: number, total: number)}
  <div class="h-2 overflow-hidden rounded-full bg-line-strong" role="progressbar" aria-valuemin="0" aria-valuemax="100" aria-valuenow={total ? Math.round((100 * loaded) / total) : undefined} aria-label={job?.label}>
    {#if total}<div class="h-full rounded-full bg-accent-text transition-[width] duration-300" style:width={percent(loaded / total, 1)}></div>
    {:else}<div class="skeleton h-full w-full !rounded-full"></div>{/if}
  </div>
{/snippet}

<dialog bind:this={dialog} aria-label="Add a model" onclose={() => (studio.addOpen = false)} oncancel={(e) => { if (job) e.preventDefault() }}
  onclick={(e) => { if (e.target === dialog) close() }}
  class="add-model m-auto max-h-[calc(100dvh-1.5rem)] w-[min(38rem,calc(100vw-1.5rem))] overflow-y-auto rounded-3xl border border-line-strong bg-surface p-0 text-text shadow-2xl backdrop:bg-black/60 backdrop:backdrop-blur-sm">
  <div class="grid gap-4 p-5 sm:p-7">
    <div class="flex items-start gap-3">
      <span class="grid size-10 shrink-0 place-items-center rounded-xl bg-accent text-accent-ink"><PackagePlus size={19} aria-hidden="true" /></span>
      <div class="min-w-0 flex-1">
        <h2 class="text-lg font-semibold">Add a model</h2>
        <p class="mt-0.5 text-[13.5px] text-muted">Bring your own model into the comparison. Files and weights stay on this computer, inside Ollama.</p>
      </div>
      <button type="button" class="btn btn-ghost btn-sm btn-icon" aria-label="Close" disabled={!!job} onclick={close}><X size={16} aria-hidden="true" /></button>
    </div>

    <div class="grid grid-cols-3 gap-1 rounded-xl border border-line bg-sunken p-1" role="tablist" aria-label="How to add a model">
      {#each tabs as [key, label, Icon]}
        <button type="button" role="tab" id={'tab-' + key} aria-selected={studio.addTab === key} aria-controls="add-panel" disabled={!!job}
          class="flex min-h-10 items-center justify-center gap-1.5 rounded-lg px-2 text-[13px] font-medium leading-tight text-muted transition-colors aria-selected:bg-raised aria-selected:text-text aria-selected:shadow-card disabled:opacity-60 max-sm:flex-col max-sm:py-1.5 max-sm:text-[11.5px]"
          onclick={() => { studio.addTab = key; studio.error = '' }}><Icon size={14} aria-hidden="true" />{label}</button>
      {/each}
    </div>

    {#if studio.error}
      <p role="alert" class="flex gap-2 rounded-xl bg-bad-soft px-3 py-2.5 text-[13px] text-bad"><CircleAlert size={15} class="mt-0.5 shrink-0" aria-hidden="true" /><span class="min-w-0 break-words">{studio.error}</span></p>
    {/if}

    <div id="add-panel" role="tabpanel" aria-labelledby={'tab-' + studio.addTab}>
      {#if studio.addTab === 'upload'}
        <form class="grid gap-4" onsubmit={(e) => { e.preventDefault(); if (file) studio.importFile(file, name, instructions) }}>
          <!-- svelte-ignore a11y_no_static_element_interactions -->
          <div ondragover={(e) => { e.preventDefault(); dragging = true }} ondragleave={() => (dragging = false)} ondrop={drop}>
            <label class="flex min-h-28 flex-col items-center justify-center gap-1.5 rounded-2xl border-2 border-dashed px-4 py-5 text-center transition-colors focus-within:border-accent-text has-disabled:opacity-60
              {dragging ? 'border-accent-text bg-accent-soft' : file ? 'border-accent-text/50 bg-accent-soft' : 'border-line-strong hover:border-accent-text'}">
              <input class="sr-only" type="file" accept=".gguf" aria-label="Model file" disabled={!!job} onchange={(e) => { choose(e.currentTarget.files?.[0]); e.currentTarget.value = '' }} />
              {#if file}
                <FileBox size={22} class="text-accent-text" aria-hidden="true" />
                <span class="max-w-full truncate text-sm font-medium">{file.name}</span>
                <span class="text-xs text-muted"><span class="num">{bytes(file.size)}</span>{#if !job} · choose a different file{/if}</span>
              {:else}
                <Upload size={22} class="text-faint" aria-hidden="true" />
                <span class="text-sm font-medium">Drop a <span class="num">.gguf</span> file here, or browse</span>
                <span class="text-xs text-muted">Your fine-tuned or downloaded weights in GGUF format</span>
              {/if}
            </label>
          </div>
          {#if fileError}
            <p class="-mt-2 text-[13px] text-bad">{fileError} Convert your weights to GGUF first; the <a class="underline" href="https://docs.ollama.com/import" target="_blank" rel="noreferrer">Ollama import guide</a> shows how.</p>
          {/if}

          {#if job?.kind === 'upload'}
            <ol class="grid gap-2.5 rounded-2xl border border-line bg-sunken/60 p-4" aria-label="Import progress">
              {#each uploadSteps as step, i}
                {@const state = job.step > i ? 'done' : job.step === i ? 'now' : 'next'}
                <li aria-current={state === 'now' ? 'step' : undefined}>
                  <div class="flex items-center gap-2.5 text-[13.5px] {state === 'next' ? 'text-faint' : ''}">
                    <span class="num grid size-5 shrink-0 place-items-center rounded-full text-[11px] font-semibold {state === 'done' ? 'bg-accent text-accent-ink' : state === 'now' ? 'bg-accent-soft text-accent-text ring-1 ring-accent-text' : 'bg-sunken text-faint ring-1 ring-line-strong'}">
                      {#if state === 'done'}<Check size={11} strokeWidth={3} aria-hidden="true" />{:else}{i + 1}{/if}</span>
                    <span class="{state === 'now' ? 'font-medium' : ''}">{step}</span>
                    {#if state === 'now' && i === 0 && job.total}<span class="num ml-auto text-xs text-muted">{bytes(job.loaded)} of {bytes(job.total)} · {percent(job.loaded / job.total)}</span>{/if}
                  </div>
                  {#if state === 'now'}<div class="ml-[1.875rem] mt-2">{@render bar(i === 0 ? job.loaded : 0, i === 0 ? job.total : 0)}</div>{/if}
                </li>
              {/each}
            </ol>
          {:else}
            {@render nameField(name, (v) => (name = v), 'upload-name')}
            <details class="group/i rounded-xl border border-line px-3">
              <summary class="flex min-h-10 items-center justify-between text-[13px] font-medium text-muted hover:text-text">System instructions<span class="text-xs font-normal text-faint group-open/i:hidden">Optional</span></summary>
              <textarea class="field mb-3 min-h-20 resize-y" aria-label="System instructions" bind:value={instructions} maxlength="8000" placeholder="How should this model answer? Leave empty to use the model as it is."></textarea>
            </details>
            <p class="text-xs leading-relaxed text-faint">Importing needs free disk space of about twice the file size, until Ollama has copied the file. Models trained with PyTorch, MLX or Transformers must be converted to GGUF first.</p>
          {/if}

          <div class="flex flex-wrap justify-end gap-2">
            {#if job?.kind === 'upload'}
              <button type="button" class="btn" disabled={job.step > 0} onclick={studio.cancelJob}>{job.step > 0 ? 'Finishing…' : 'Cancel upload'}</button>
            {:else}
              <button type="button" class="btn" onclick={close}>Cancel</button>
              <button type="submit" class="btn btn-primary" disabled={!!studio.busy || !file || !NAME.test(name) || taken(name)}><Upload size={15} aria-hidden="true" />Import model</button>
            {/if}
          </div>
        </form>

      {:else if studio.addTab === 'pull'}
        <form class="grid gap-4" onsubmit={(e) => { e.preventDefault(); studio.pullModel(reference.trim()) }}>
          <div><label class="label" for="pull-ref">Model reference</label>
            <input id="pull-ref" class="field num" bind:value={reference} required maxlength="260" spellcheck="false" autocapitalize="off" placeholder="hf.co/your-name/your-model-GGUF:Q4_K_M" disabled={!!job} />
            <p class="mt-1.5 text-xs leading-relaxed text-faint">A tag from the Ollama library, such as <span class="num">llama3.2:1b</span>, or a GGUF repository on Hugging Face written as <span class="num">hf.co/user/repo:quantization</span>. Ollama downloads it; large models can take several minutes and several GB.</p></div>
          {#if job?.kind === 'pull'}
            <div class="grid gap-2 rounded-2xl border border-line bg-sunken/60 p-4">
              <div class="flex items-baseline justify-between gap-3 text-[13.5px]"><span class="min-w-0 truncate font-medium" role="status">{job.label}</span>
                {#if job.total}<span class="num shrink-0 text-xs text-muted">{bytes(job.loaded)} of {bytes(job.total)} · {percent(job.loaded / job.total)}</span>{/if}</div>
              {@render bar(job.loaded, job.total)}
              <p class="text-xs text-faint">If you cancel, Ollama keeps what it has and resumes next time.</p>
            </div>
          {/if}
          <div class="flex flex-wrap justify-end gap-2">
            {#if job?.kind === 'pull'}
              <button type="button" class="btn" onclick={studio.cancelJob}>Cancel download</button>
            {:else}
              <button type="button" class="btn" onclick={close}>Cancel</button>
              <button type="submit" class="btn btn-primary" disabled={!!studio.busy || !reference.trim()}><Download size={15} aria-hidden="true" />Download model</button>
            {/if}
          </div>
        </form>

      {:else}
        <form class="grid gap-4" onsubmit={(e) => { e.preventDefault(); studio.deploy() }}>
          <p class="text-[13.5px] text-muted">Give an installed model its own instructions and compare it as a separate candidate. This changes behaviour, not weights.</p>
          <label><span class="label">Installed base model</span>
            <select class="field" bind:value={studio.deployBase} disabled={!!job}>{#each bases as m}<option value={m.id}>{m.name}</option>{:else}<option value="">No local model installed</option>{/each}</select></label>
          {@render nameField(studio.deployName, (v) => (studio.deployName = v), 'custom-name')}
          <label><span class="label">Model instructions</span>
            <textarea class="field min-h-28 resize-y" bind:value={studio.instructions} required maxlength="8000" placeholder="How should this model answer?" disabled={!!job}></textarea></label>
          <div class="flex flex-wrap justify-end gap-2">
            <button type="button" class="btn" disabled={!!job} onclick={close}>Cancel</button>
            <button type="submit" class="btn btn-primary" disabled={!!studio.busy || !studio.deployBase || !studio.instructions.trim() || !NAME.test(studio.deployName) || taken(studio.deployName)}>
              {#if job}<i class="spinner" aria-hidden="true"></i>{/if}Create model</button>
          </div>
        </form>
      {/if}
    </div>

    {#if studio.ownModels.length && !job}
      <section class="border-t border-line pt-4" aria-label="Your models">
        <h3 class="eyebrow mb-2">Your models · {studio.ownModels.length}</h3>
        <ul class="grid gap-1.5">
          {#each studio.ownModels as m (m.id)}
            <li class="hue-{studio.hue(m.id)} rounded-xl border border-line px-3 py-2">
              <div class="flex items-center gap-2.5">
                <i class="dot" aria-hidden="true"></i>
                <span class="min-w-0 flex-1"><span class="block truncate text-[13.5px] font-medium">{m.label ?? m.name}</span>
                  {#if details(m)}<span class="num block truncate text-[11.5px] text-faint">{details(m)}</span>{/if}</span>
                {#if removing !== m.id}<button type="button" class="btn btn-ghost btn-sm btn-icon hover:!text-bad" aria-label={'Remove ' + (m.label ?? m.name)} disabled={!!studio.busy} onclick={() => (removing = m.id)}><Trash2 size={14} aria-hidden="true" /></button>{/if}
              </div>
              {#if removing === m.id}
                <div class="mt-2 flex flex-wrap items-center gap-2 border-t border-line pt-2">
                  <p class="min-w-0 flex-1 basis-48 text-[12.5px] text-muted">Delete this model from Ollama? Saved results that used it are kept.</p>
                  <button type="button" class="btn btn-sm !border-bad/40 !text-bad" disabled={!!studio.busy} onclick={async () => { await studio.removeModel(m); removing = '' }}>Delete model</button>
                  <button type="button" class="btn btn-sm" onclick={() => (removing = '')}>Keep</button>
                </div>
              {/if}
            </li>
          {/each}
        </ul>
      </section>
    {/if}
  </div>
</dialog>
