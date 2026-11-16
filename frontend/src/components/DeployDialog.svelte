<script lang="ts">
  import { Rocket, X } from '@lucide/svelte'
  import { studio } from '../lib/studio.svelte'

  let dialog = $state<HTMLDialogElement>()
  $effect(() => {
    if (studio.deployOpen && !dialog?.open) dialog?.showModal()
    if (!studio.deployOpen && dialog?.open) dialog.close()
  })
  const bases = $derived(studio.models.filter((m) => !m.provider && m.installed))
</script>

<dialog bind:this={dialog} aria-label="Deploy a model" onclose={() => (studio.deployOpen = false)}
  onclick={(e) => { if (e.target === dialog) studio.deployOpen = false }}
  class="deploy-form m-auto w-[min(34rem,calc(100vw-1.5rem))] rounded-3xl border border-line-strong bg-surface p-0 text-text shadow-2xl backdrop:bg-black/60 backdrop:backdrop-blur-sm">
  <form class="grid gap-4 p-5 sm:p-7" onsubmit={(e) => { e.preventDefault(); studio.deploy() }}>
    <div class="flex items-start gap-3">
      <span class="grid size-10 shrink-0 place-items-center rounded-xl bg-accent text-accent-ink"><Rocket size={18} aria-hidden="true" /></span>
      <div class="min-w-0 flex-1">
        <h2 class="text-lg font-semibold">Deploy your model</h2>
        <p class="mt-0.5 text-[13.5px] text-muted">Create a local Ollama responder with its own instructions. If you already imported your own weights into Ollama, refresh the model list to select them.</p>
      </div>
      <button type="button" class="btn btn-ghost btn-sm btn-icon" aria-label="Close" onclick={() => (studio.deployOpen = false)}><X size={16} aria-hidden="true" /></button>
    </div>
    {#if studio.error}<p class="rounded-xl bg-bad-soft px-3 py-2 text-[13px] text-bad">{studio.error}</p>{/if}
    <label><span class="label">Model name</span>
      <input class="field num" bind:value={studio.deployName} required maxlength="63" pattern="[a-z0-9][a-z0-9_\-]*" placeholder="support-analyst-v1" />
      <span class="mt-1 block text-xs text-faint">Lowercase letters, digits, hyphens and underscores.</span></label>
    <label><span class="label">Installed base model</span>
      <select class="field" bind:value={studio.deployBase}>{#each bases as m}<option value={m.id}>{m.name}</option>{:else}<option value="">No local model installed</option>{/each}</select></label>
    <label><span class="label">Model instructions</span>
      <textarea class="field min-h-28 resize-y" bind:value={studio.instructions} required maxlength="8000" placeholder="How should this model answer?"></textarea></label>
    <div class="flex flex-wrap justify-end gap-2 pt-1">
      <button type="button" class="btn" disabled={!!studio.busy} onclick={() => (studio.deployOpen = false)}>Cancel</button>
      <button type="submit" class="btn btn-primary" disabled={!!studio.busy || !studio.deployBase || !studio.instructions.trim() || !studio.deployName.trim()}>
        {#if studio.busy}<i class="spinner" aria-hidden="true"></i>{/if}Deploy to Ollama</button>
    </div>
  </form>
</dialog>
