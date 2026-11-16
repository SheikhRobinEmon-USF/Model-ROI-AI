<script lang="ts">
  import { FlaskConical, History as HistoryIcon, MessagesSquare, Moon, PanelLeft, Plus, Search, Sun, TriangleAlert, Trophy, X } from '@lucide/svelte'
  import { onMount } from 'svelte'
  import { fade, fly, slide } from 'svelte/transition'
  import { PAGES, studio, type Page } from './lib/studio.svelte'
  import { quick, rise } from './lib/motion'
  import Benchmark from './components/Benchmark.svelte'
  import ChatList from './components/ChatList.svelte'
  import CommandPalette from './components/CommandPalette.svelte'
  import DeployDialog from './components/DeployDialog.svelte'
  import History from './components/History.svelte'
  import PromptLab from './components/PromptLab.svelte'
  import Results from './components/Results.svelte'
  import RunProgress from './components/RunProgress.svelte'

  const icons = { 'Prompt lab': MessagesSquare, Benchmark: FlaskConical, Results: Trophy, History: HistoryIcon }
  const titles: Record<Page, [string, string]> = {
    'Prompt lab': ['Compare answers', ''],
    Benchmark: ['Benchmark models', 'Run identical cases through every model and rank them on measured evidence.'],
    Results: ['Evaluation results', 'Quality, speed and reliability for the run you have open.'],
    History: ['Run history', 'Every comparison and benchmark saved on this machine.'],
  }
  const mac = /Mac|iPhone|iPad/.test(navigator.platform)

  onMount(studio.start)

  function shortcuts(e: KeyboardEvent) {
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') { e.preventDefault(); studio.paletteOpen = !studio.paletteOpen }
    else if (e.key === 'Escape' && studio.chatMenu) studio.chatMenu = false
  }
</script>

<svelte:window onkeydown={shortcuts} />

{#snippet brand()}
  <span class="grid size-8 shrink-0 place-items-center rounded-[0.6rem] bg-accent text-accent-ink shadow-[0_0_24px_-4px_var(--accent)]" aria-hidden="true">
    <svg viewBox="0 0 32 32" width="20" height="20" fill="none" stroke="currentColor" stroke-width="3.2" stroke-linecap="round"><path d="M6 12q5-5 10 0t10 0M6 20q5-5 10 0t10 0" /></svg>
  </span>
  <span class="text-[17px] font-semibold tracking-[-0.03em]">ModelROI</span>
{/snippet}

{#snippet themeToggle()}
  <button class="btn btn-ghost btn-sm btn-icon" aria-label={studio.theme === 'dark' ? 'Switch to light theme' : 'Switch to dark theme'} onclick={() => studio.setTheme(studio.theme === 'dark' ? 'light' : 'dark')}>
    {#if studio.theme === 'dark'}<Sun size={16} aria-hidden="true" />{:else}<Moon size={16} aria-hidden="true" />{/if}
  </button>
{/snippet}

<div class="aurora" aria-hidden="true"></div>

<div class="flex h-dvh">
  <aside class="hidden w-[17rem] shrink-0 flex-col border-r border-line bg-glass backdrop-blur-xl md:flex">
    <div class="flex items-center gap-2.5 px-4 pb-4 pt-5">{@render brand()}<span class="eyebrow ml-auto">Studio</span></div>
    <div class="grid gap-2 px-3">
      <button class="btn btn-primary w-full" disabled={!!studio.busy} onclick={studio.newChat}><Plus size={16} strokeWidth={2.5} aria-hidden="true" />New chat</button>
      <button class="btn w-full !justify-start !font-normal text-muted" aria-label="Search commands" aria-keyshortcuts="Control+K Meta+K" onclick={() => (studio.paletteOpen = true)}>
        <Search size={14} aria-hidden="true" />Search<kbd class="num ml-auto rounded-md border border-line px-1.5 py-px text-[10.5px] text-faint">{mac ? '⌘' : 'Ctrl '}K</kbd></button>
    </div>
    <nav class="grid gap-0.5 px-3 py-4" aria-label="Workspace">
      {#each PAGES as p}
        {@const Icon = icons[p]}
        <button class="relative flex h-9 items-center gap-2.5 rounded-lg px-2.5 text-sm transition-colors disabled:opacity-50 {p === studio.page ? 'bg-accent-soft font-medium text-text' : 'text-muted hover:bg-accent-soft hover:text-text'}"
          disabled={!!studio.busy} aria-current={p === studio.page ? 'page' : undefined} onclick={() => studio.nav(p)}>
          {#if p === studio.page}<span class="absolute -left-3 top-2 h-5 w-[3px] rounded-r-full bg-accent-text" aria-hidden="true"></span>{/if}
          <Icon size={16} class={p === studio.page ? 'text-accent-text' : ''} aria-hidden="true" />{p}
          {#if p === 'Results' && studio.report}<span class="ml-auto size-1.5 rounded-full bg-accent-text" aria-hidden="true"></span>{/if}
        </button>
      {/each}
    </nav>
    <ChatList />
    <div class="flex items-center gap-2.5 border-t border-line px-4 py-3">
      <span class="live-dot shrink-0" style:--good={studio.readyCount ? null : 'var(--warn)'} aria-hidden="true"></span>
      <span class="min-w-0 flex-1 text-xs leading-tight"><span class="block truncate font-medium">{studio.mode === 'local' ? 'Local workspace' : 'Hosted providers'}</span>
        <span class="block truncate text-faint">{studio.loaded ? studio.readyCount + (studio.readyCount === 1 ? ' model ready' : ' models ready') : 'Checking models…'}</span></span>
      {@render themeToggle()}
    </div>
  </aside>

  <div class="flex min-w-0 flex-1 flex-col">
    <header class="flex items-center gap-2 border-b border-line bg-glass px-3 py-2 backdrop-blur-xl md:hidden">
      {@render brand()}
      <span class="ml-auto flex items-center gap-1">
        {#if studio.page === 'Prompt lab'}<button class="mobile-chats btn btn-sm" aria-expanded={studio.chatMenu} onclick={() => (studio.chatMenu = !studio.chatMenu)}><PanelLeft size={14} aria-hidden="true" />Chat history</button>{/if}
        {@render themeToggle()}
      </span>
    </header>

    <RunProgress />
    {#if studio.error && !studio.deployOpen}
      <div class="mx-auto w-full max-w-[1100px] px-4 pt-3 md:px-8" transition:slide={quick}>
        <div class="flex items-start gap-2.5 rounded-2xl border border-bad/30 bg-bad-soft px-4 py-2.5 text-sm text-bad">
          <TriangleAlert size={16} class="mt-0.5 shrink-0" aria-hidden="true" /><p role="alert" class="alert min-w-0 flex-1">{studio.error}</p>
          <button class="btn btn-ghost btn-sm btn-icon -my-1 !text-bad" aria-label="Dismiss" onclick={() => (studio.error = '')}><X size={14} aria-hidden="true" /></button>
        </div>
      </div>
    {/if}

    <main class="min-h-0 flex-1 {studio.page === 'Prompt lab' ? '' : 'overflow-y-auto'}" aria-busy={!!studio.busy}>
      {#key studio.page}
        {#if studio.page === 'Prompt lab'}
          <h1 class="sr-only">{titles[studio.page][0]}</h1>
          <PromptLab />
        {:else}
          <div class="mx-auto w-full max-w-[1100px] px-4 pb-16 pt-7 md:px-8 md:pt-10">
            <div class="heading mb-7" in:fly={rise()}>
              <small class="eyebrow">Workspace / {studio.page}</small>
              <h1 class="mt-1.5 text-[clamp(1.9rem,4.5vw,2.9rem)] font-semibold leading-[1.08] tracking-[-0.04em]">{titles[studio.page][0]}</h1>
              <p class="mt-2 max-w-xl text-[15px] text-muted">{titles[studio.page][1]}</p>
            </div>
            {#if studio.page === 'Benchmark'}<Benchmark />{:else if studio.page === 'Results'}<Results />{:else}<History />{/if}
          </div>
        {/if}
      {/key}
    </main>

    <nav class="grid grid-cols-4 border-t border-line bg-glass pb-[env(safe-area-inset-bottom)] backdrop-blur-xl md:hidden" aria-label="Workspace">
      {#each PAGES as p}
        {@const Icon = icons[p]}
        <button class="relative flex h-14 flex-col items-center justify-center gap-0.5 text-[11px] transition-colors disabled:opacity-50 {p === studio.page ? 'font-semibold text-accent-text' : 'text-muted'}"
          disabled={!!studio.busy} aria-current={p === studio.page ? 'page' : undefined} onclick={() => studio.nav(p)}>
          {#if p === studio.page}<span class="absolute top-0 h-[3px] w-8 rounded-b-full bg-accent-text" aria-hidden="true"></span>{/if}
          <Icon size={18} aria-hidden="true" />{p}
        </button>
      {/each}
    </nav>
  </div>
</div>

{#if studio.chatMenu && studio.page === 'Prompt lab'}
  <!-- svelte-ignore a11y_click_events_have_key_events, a11y_no_static_element_interactions -->
  <div class="fixed inset-0 z-40 bg-black/55 backdrop-blur-sm md:hidden" transition:fade={quick} onclick={(e) => { if (e.target === e.currentTarget) studio.chatMenu = false }}>
    <aside class="chat-history flex h-full w-[min(20rem,86vw)] flex-col border-r border-line-strong bg-surface pt-3 shadow-2xl" aria-label="Chat history" transition:fly={{ x: -24, duration: quick.duration }}>
      <div class="flex justify-end px-2"><button class="btn btn-ghost btn-sm btn-icon" aria-label="Close chat list" onclick={() => (studio.chatMenu = false)}><X size={16} aria-hidden="true" /></button></div>
      <ChatList />
    </aside>
  </div>
{/if}

<CommandPalette />
<DeployDialog />
