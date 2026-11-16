<script lang="ts">
  import { ShieldCheck } from '@lucide/svelte'
  import { studio } from '../lib/studio.svelte'
</script>

{#if studio.mode === 'hosted'}
  <p class="routing-note flex gap-2 rounded-xl border border-line bg-sunken/60 px-3 py-2 text-[12.5px] leading-snug text-muted">
    <ShieldCheck size={15} class="mt-px shrink-0 text-accent-text" aria-hidden="true" />
    <span>Hosted responders receive your question, excerpts and context. Your Ollama models generate locally. Groq receives grading evidence and reference answers. Judge · GPT-OSS 120B.{#if !studio.visibleModels.some((m) => m.judge_ready)} <strong class="text-warn">Configure GROQ_API_KEY to enable grading.</strong>{/if}</span>
  </p>
{/if}
