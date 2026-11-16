<script lang="ts">
  import { scoreTone } from '../lib/format'
  let { score, size = 44, max = 10 }: { score: number; size?: number; max?: number } = $props()
  const stroke = $derived(size >= 64 ? 6 : 4)
  const radius = $derived((size - stroke) / 2)
  const length = $derived(2 * Math.PI * radius)
</script>

<div class="relative grid shrink-0 place-items-center tone-{scoreTone((score / max) * 10)}" style:width="{size}px" style:height="{size}px" role="img" aria-label="Quality {score.toFixed(1)} out of {max}">
  <svg width={size} height={size} class="-rotate-90" aria-hidden="true">
    <circle cx={size / 2} cy={size / 2} r={radius} fill="none" stroke="var(--sunken)" stroke-width={stroke} />
    <circle cx={size / 2} cy={size / 2} r={radius} fill="none" stroke="var(--tone)" stroke-width={stroke} stroke-linecap="round"
      stroke-dasharray={length} stroke-dashoffset={length * (1 - Math.max(0, Math.min(1, score / max)))} style="transition: stroke-dashoffset .7s var(--ease-out)" />
  </svg>
  <span class="num absolute font-semibold" style:font-size="{size >= 64 ? 20 : 12.5}px" aria-hidden="true">{score.toFixed(1)}</span>
</div>
