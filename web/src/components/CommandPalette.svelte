<script lang="ts">
  import { ChartColumn, Cloud, CornerDownLeft, Cpu, FlaskConical, History, MessageSquare, MessagesSquare, Moon, Plus, RefreshCw, Rocket, Search, Sun, Trophy } from '@lucide/svelte'
  import { fade, scale } from 'svelte/transition'
  import { studio, type Page } from '../lib/studio.svelte'
  import { pop, quick } from '../lib/motion'

  type Command = { id: string; label: string; group: string; icon: any; hint?: string; run: () => void }
  let query = $state(''), index = $state(0), list = $state<HTMLElement>()

  const go = (page: Page) => () => studio.nav(page)
  const commands = $derived<Command[]>([
    { id: 'new', label: 'New chat', group: 'Actions', icon: Plus, run: studio.newChat },
    { id: 'lab', label: 'Go to Prompt lab', group: 'Navigate', icon: MessagesSquare, run: go('Prompt lab') },
    { id: 'bench', label: 'Go to Benchmark', group: 'Navigate', icon: FlaskConical, run: go('Benchmark') },
    { id: 'results', label: 'Go to Results', group: 'Navigate', icon: Trophy, run: go('Results') },
    { id: 'history', label: 'Go to History', group: 'Navigate', icon: History, run: go('History') },
    { id: 'mode', label: studio.mode === 'local' ? 'Switch to hosted models' : 'Switch to local models', group: 'Actions', icon: studio.mode === 'local' ? Cloud : Cpu, run: () => studio.switchMode(studio.mode === 'local' ? 'hosted' : 'local') },
    { id: 'theme', label: studio.theme === 'dark' ? 'Use light theme' : 'Use dark theme', group: 'Actions', icon: studio.theme === 'dark' ? Sun : Moon, run: () => studio.setTheme(studio.theme === 'dark' ? 'light' : 'dark') },
    { id: 'deploy', label: 'Deploy a model to Ollama', group: 'Actions', icon: Rocket, run: studio.openDeployment },
    { id: 'refresh', label: 'Refresh model status', group: 'Actions', icon: RefreshCw, run: () => void studio.refresh() },
    { id: 'trends', label: 'Analyze saved benchmarks', group: 'Actions', icon: ChartColumn, run: async () => { await studio.nav('History'); await studio.loadAnalytics() } },
    ...studio.chats.map((chat) => ({ id: chat.run_id, label: chat.title, group: 'Chats', icon: MessageSquare, run: () => void studio.openChat(chat.run_id) })),
  ])
  const matches = $derived.by(() => {
    const terms = query.toLowerCase().split(/\s+/).filter(Boolean)
    return commands.filter((c) => terms.every((t) => (c.label + ' ' + c.group).toLowerCase().includes(t))).slice(0, 40)
  })
  $effect(() => { void query; index = 0 })
  $effect(() => { if (studio.paletteOpen) query = '' })

  function choose(command?: Command) {
    if (!command) return
    studio.paletteOpen = false
    command.run()
  }
  function keys(e: KeyboardEvent) {
    if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
      e.preventDefault()
      index = (index + (e.key === 'ArrowDown' ? 1 : -1) + matches.length) % Math.max(1, matches.length)
      list?.querySelector(`[data-index="${index}"]`)?.scrollIntoView({ block: 'nearest' })
    } else if (e.key === 'Enter') { e.preventDefault(); choose(matches[index]) }
    else if (e.key === 'Escape') studio.paletteOpen = false
  }
  function focus(node: HTMLInputElement) { node.focus() }
</script>

{#if studio.paletteOpen}
  <!-- svelte-ignore a11y_click_events_have_key_events, a11y_no_static_element_interactions -->
  <div class="fixed inset-0 z-50 grid place-items-start justify-items-center bg-black/55 px-3 pt-[12vh] backdrop-blur-sm" transition:fade={quick} onclick={(e) => { if (e.target === e.currentTarget) studio.paletteOpen = false }}>
    <div class="glass w-full max-w-xl overflow-hidden rounded-2xl shadow-2xl" role="dialog" aria-modal="true" aria-label="Command palette" in:scale={pop}>
      <div class="flex items-center gap-3 border-b border-line px-4">
        <Search size={17} class="shrink-0 text-faint" aria-hidden="true" />
        <input use:focus class="h-13 min-w-0 flex-1 bg-transparent text-[15px] outline-none placeholder:text-faint" placeholder="Search commands and chats…" aria-label="Search commands and chats"
          role="combobox" aria-expanded="true" aria-controls="palette-list" aria-activedescendant={matches[index] ? 'cmd-' + matches[index].id : undefined} bind:value={query} onkeydown={keys} />
        <kbd class="num rounded-md border border-line px-1.5 py-0.5 text-[10.5px] text-faint">esc</kbd>
      </div>
      <ul id="palette-list" role="listbox" aria-label="Commands" class="max-h-[min(24rem,55vh)] overflow-y-auto p-1.5" bind:this={list}>
        {#each matches as command, i (command.id)}
          {#if i === 0 || matches[i - 1].group !== command.group}<li class="eyebrow px-2.5 pb-1 pt-2.5" role="presentation">{command.group}</li>{/if}
          <!-- svelte-ignore a11y_click_events_have_key_events -->
          <li id={'cmd-' + command.id} data-index={i} role="option" aria-selected={i === index}
            class="flex cursor-pointer items-center gap-3 rounded-lg px-2.5 py-2 text-sm text-muted aria-selected:bg-accent-soft aria-selected:text-text"
            onclick={() => choose(command)} onpointermove={() => (index = i)}>
            <command.icon size={15} class="shrink-0" aria-hidden="true" />
            <span class="min-w-0 flex-1 truncate">{command.label}</span>
            {#if i === index}<CornerDownLeft size={13} class="shrink-0 text-faint" aria-hidden="true" />{/if}
          </li>
        {:else}
          <li class="px-3 py-8 text-center text-sm text-faint" role="presentation">Nothing matches “{query}”.</li>
        {/each}
      </ul>
    </div>
  </div>
{/if}
