<script lang="ts">
  import { Ellipsis, Pencil, Pin, PinOff, Search, Trash2 } from '@lucide/svelte'
  import { slide } from 'svelte/transition'
  import { studio } from '../lib/studio.svelte'
  import { ago } from '../lib/format'
  import { quick } from '../lib/motion'

  let menu = $state(''), editMode = $state<'' | 'rename' | 'delete'>(''), newTitle = $state(''), filter = $state('')
  const shown = $derived(studio.chats.filter((c) => c.title.toLowerCase().includes(filter.trim().toLowerCase())))
  const close = () => { menu = ''; editMode = '' }
  async function manage(chat: any, operation: 'rename' | 'pin' | 'unpin' | 'delete') {
    await studio.manageChat(chat, operation, newTitle)
    if (!studio.error) close()
  }
</script>

<div class="flex min-h-0 flex-1 flex-col">
  <div class="flex items-center justify-between px-3 pb-1.5">
    <h2 class="eyebrow">Chats</h2>
    {#if studio.chats.length}<span class="num text-[11px] text-faint">{studio.chats.length}</span>{/if}
  </div>
  {#if studio.chats.length > 6}
    <label class="relative mx-2 mb-2 block">
      <Search size={14} class="pointer-events-none absolute left-2.5 top-1/2 -translate-y-1/2 text-faint" aria-hidden="true" />
      <input class="field !min-h-8 !py-1 !pl-8 text-[13px]" type="search" placeholder="Filter chats" aria-label="Filter chats" bind:value={filter} />
    </label>
  {/if}
  <div class="min-h-0 flex-1 overflow-y-auto px-2 pb-2">
    {#each shown as chat (chat.run_id)}
      {@const active = studio.activeChat === chat.run_id}
      <div class="group relative">
        <div class="flex items-center rounded-lg transition-colors hover:bg-accent-soft {active ? 'bg-accent-soft' : ''}">
          <button class="flex min-w-0 flex-1 items-center gap-2 py-2 pl-2.5 pr-1 text-left text-[13.5px] disabled:opacity-60 {active ? 'font-medium text-text' : 'text-muted group-hover:text-text'}"
            disabled={!!studio.busy} title={chat.title} aria-current={active ? 'true' : undefined} onclick={() => studio.openChat(chat.run_id)}>
            {#if chat.pinned}<Pin size={12} class="shrink-0 text-accent-text" aria-hidden="true" />{/if}
            <span class="truncate">{chat.title}</span>
          </button>
          <button class="btn btn-ghost btn-sm btn-icon mr-0.5 opacity-60 group-hover:opacity-100 focus-visible:opacity-100 aria-expanded:opacity-100 md:opacity-0" disabled={!!studio.busy}
            aria-label={'Actions for ' + chat.title} aria-expanded={menu === chat.run_id} onclick={() => { menu = menu === chat.run_id ? '' : chat.run_id; editMode = '' }}>
            <Ellipsis size={15} aria-hidden="true" />
          </button>
        </div>
        {#if menu === chat.run_id}
          <div class="mx-1 mb-1.5 mt-1 rounded-xl border border-line-strong bg-raised p-1.5 shadow-card" transition:slide={quick}>
            {#if editMode === 'rename'}
              <form class="grid gap-1.5" onsubmit={(e) => { e.preventDefault(); manage(chat, 'rename') }}>
                <!-- svelte-ignore a11y_autofocus -->
                <input class="field !min-h-8 !py-1 text-[13px]" aria-label="Chat name" bind:value={newTitle} maxlength="100" autofocus />
                <div class="flex gap-1.5"><button class="btn btn-primary btn-sm flex-1" disabled={!!studio.busy || !newTitle.trim()}>Save name</button><button type="button" class="btn btn-sm" onclick={close}>Cancel</button></div>
              </form>
            {:else if editMode === 'delete'}
              <p class="px-1.5 pb-1.5 pt-1 text-[12.5px] text-muted">Delete this conversation and its saved results?</p>
              <div class="flex gap-1.5"><button class="btn btn-sm flex-1 !border-bad/40 !text-bad" disabled={!!studio.busy} onclick={() => manage(chat, 'delete')}>Confirm deletion</button><button class="btn btn-sm" onclick={close}>Cancel</button></div>
            {:else}
              <div class="grid text-[13px]">
                <button class="btn btn-ghost btn-sm !justify-start" onclick={() => { editMode = 'rename'; newTitle = chat.title }}><Pencil size={13} aria-hidden="true" />Rename</button>
                <button class="btn btn-ghost btn-sm !justify-start" onclick={() => manage(chat, chat.pinned ? 'unpin' : 'pin')}>{#if chat.pinned}<PinOff size={13} aria-hidden="true" />Unpin{:else}<Pin size={13} aria-hidden="true" />Pin{/if}</button>
                <button class="btn btn-ghost btn-sm !justify-start hover:!text-bad" onclick={() => (editMode = 'delete')}><Trash2 size={13} aria-hidden="true" />Delete</button>
              </div>
              <p class="border-t border-line px-2 pt-1.5 text-[11px] text-faint">{chat.depth} {chat.depth === 1 ? 'turn' : 'turns'} · {ago(chat.started_at)}</p>
            {/if}
          </div>
        {/if}
      </div>
    {:else}
      <p class="px-2.5 py-2 text-[13px] leading-snug text-faint">{studio.chats.length ? 'No chats match that filter.' : 'Your conversations will appear here.'}</p>
    {/each}
  </div>
</div>
