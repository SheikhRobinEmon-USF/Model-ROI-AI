<script lang="ts">
  import { scoreTone } from '../lib/format'
  let { split }: { split: any } = $props()
</script>

<div class="tone-{scoreTone(split.mean)}">
  <p class="mb-1.5 text-sm"><strong class="num text-base">{split.mean} / 10</strong> <span class="text-muted">· Judge average</span></p>
  <meter min="0" max="10" value={split.mean} aria-label="Average of the two judge ratings"></meter>
  <p class="mt-2 text-[13px] text-muted">The judges gave different ratings after peer review. Final grade pending agreement.</p>
  {#each split.reviews as review}
    <p class="mt-2 text-sm"><strong>{review.model} · {review.score}/10</strong><br /><span class="text-muted">{review.reason}</span></p>
  {/each}
</div>
