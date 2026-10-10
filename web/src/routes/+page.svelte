<script lang="ts">
  import { onMount } from 'svelte';
  import Editor from '$lib/Editor.svelte';
  import { ApiError, request, type Machine } from '$lib/api';
  import { examples, instructions, registerHelp, hex, signed } from '$lib/programs';
  import '../app.css';

  let source = $state(examples[0].source);
  let machine = $state<Machine | null>(null);
  let connection = $state<'loading' | 'connected' | 'disconnected' | 'expired'>('loading');
  let busy = $state(false);
  let message = $state('');
  let assemblyLine = $state<number | null>(null);
  let storageWarning = $state('');
  let tab = $state<'workspace' | 'examples' | 'guide'>('workspace');
  let mobileMenu = $state(false);
  let theme = $state('dark');
  let speed = $state(20);
  let inputText = $state('');
  let inputBase = $state('dec');
  let memoryPage = $state(0);
  let addressText = $state('');
  let selectedAddress = $state<number | null>(null);
  let memoryTab = $state<'memory' | 'listing'>('memory');
  let saveLabel = $state('Saved on this device');
  let pollTimer: ReturnType<typeof setTimeout>;
  let stopped = false;
  let generation = 0;
  const dirty = $derived(!!machine && source !== machine.source);
  const active = $derived(machine?.status === 'running');
  const usable = $derived(connection === 'connected' && !busy);
  const canExecute = $derived(usable && !dirty && !!machine && ['ready', 'paused'].includes(machine.status));
  const currentLine = $derived(dirty ? null : machine?.status === 'halted' || machine?.status === 'failed' ? machine?.listing.find(row => row.address === machine?.last_address)?.line ?? null : machine?.current_line ?? null);
  const statusLabels = { ready: 'Ready', running: 'Running', paused: 'Paused', waiting_for_input: 'Waiting for input', halted: 'Halted', failed: 'Execution failed' };
  const status = $derived(connection === 'loading' ? 'Connecting' : connection === 'disconnected' ? 'Disconnected' : connection === 'expired' ? 'Session expired' : machine ? statusLabels[machine.status] : 'Not assembled');
  const currentRow = $derived(machine?.listing.find(row => row.address === machine?.current_address));

  function persist(text: string) {
    source = text; assemblyLine = null;
    try { localStorage.setItem('marie.source', text); saveLabel = 'Saved on this device'; }
    catch { storageWarning = 'Browser storage is unavailable. Copy your source before closing this tab.'; saveLabel = 'Not saved'; }
  }
  function rememberSession(id: string | null) {
    try { id ? sessionStorage.setItem('marie.session', id) : sessionStorage.removeItem('marie.session'); }
    catch { storageWarning = 'Session recovery is unavailable in this browser.'; }
  }
  function accept(next: Machine) { machine = next; speed = next.speed; connection = 'connected'; }
  function report(error: unknown) {
    if (error instanceof ApiError) {
      message = error.message;
      if (error.kind === 'assembly') assemblyLine = error.line ?? null;
      else if (error.status === 404) { connection = 'expired'; machine = null; rememberSession(null); }
      else if (error.status === 401) connection = 'disconnected';
    } else {
      connection = 'disconnected';
      message = 'Cannot reach the simulator. Your source is saved here; reconnect to check the execution state.';
    }
  }
  async function poll() {
    if (stopped) return;
    if (machine && !busy && connection !== 'expired') {
      const epoch = generation;
      try {
        const next = await request<Machine>(`/sessions/${machine.id}`);
        if (epoch === generation && !stopped) { accept(next); if (message.startsWith('Cannot reach')) message = ''; }
      } catch (error) { if (epoch === generation && !stopped) report(error); }
    }
    if (!stopped) pollTimer = setTimeout(poll, machine?.status === 'running' ? 200 : 1200);
  }
  async function reconnect() {
    if (busy) return;
    busy = true; message = ''; generation++;
    try {
      await request('/bootstrap');
      if (machine && connection !== 'expired') accept(await request<Machine>(`/sessions/${machine.id}`));
      else connection = 'connected';
    } catch (error) { report(error); } finally { busy = false; }
  }
  async function assemble() {
    if (!usable || active) return;
    busy = true; message = ''; assemblyLine = null; generation++;
    try {
      const next = await request<Machine>('/sessions', { source, replace: connection === 'expired' ? null : machine?.id ?? null });
      accept(next); rememberSession(next.id); memoryPage = Math.floor(next.current_address / 64); selectedAddress = null;
    } catch (error) { report(error); } finally { busy = false; }
  }
  async function command(action: string, extras: Record<string, number> = {}) {
    if (!usable || !machine) return;
    busy = true; message = ''; generation++;
    try {
      accept(await request<Machine>(`/sessions/${machine.id}/commands`, { action, revision: machine.revision, ...extras }));
      if (action === 'reset') { inputText = ''; memoryPage = Math.floor(machine.current_address / 64); }
    } catch (error) {
      report(error);
      if (error instanceof ApiError && error.status === 409) {
        try { accept(await request<Machine>(`/sessions/${machine.id}`)); } catch (err) { report(err); }
      }
    } finally { busy = false; }
  }
  function supplyInput() {
    const text = inputText.trim();
    const valid = inputBase === 'dec' ? /^-?\d+$/.test(text) : /^(?:0x)?[0-9a-f]{1,4}$/i.test(text);
    const value = Number.parseInt(text, inputBase === 'dec' ? 10 : 16);
    if (!valid || !Number.isInteger(value) || value < -32768 || value > (inputBase === 'dec' ? 32767 : 65535)) { message = 'Enter a signed decimal word (−32768 to 32767) or hexadecimal word (0000 to FFFF).'; return; }
    void command('input', { value }).then(() => { if (machine?.status !== 'waiting_for_input') inputText = ''; });
  }
  function changeTheme() {
    theme = theme === 'light' ? 'dark' : 'light'; document.documentElement.dataset.theme = theme;
    try { localStorage.setItem('marie.theme', theme); } catch { /* theme still works */ }
  }
  function loadExample(index: number) {
    if (active || busy) return;
    persist(examples[index].source); message = ''; tab = 'workspace';
  }
  function jumpMemory() {
    if (!/^(?:0x)?[0-9a-f]{1,3}$/i.test(addressText.trim())) { message = 'Memory address must be hexadecimal, 000 through FFF.'; return; }
    const address = parseInt(addressText, 16); memoryPage = Math.floor(address / 64); selectedAddress = address;
  }
  function shortcuts(event: KeyboardEvent) {
    if ((event.metaKey || event.ctrlKey) && event.key === 'Enter') { event.preventDefault(); void assemble(); }
    if (event.key === 'F10') { event.preventDefault(); if (canExecute) void command('step'); }
  }
  onMount(() => {
    theme = document.documentElement.dataset.theme || 'dark';
    try { const saved = localStorage.getItem('marie.source'); if (saved !== null) source = saved; } catch { storageWarning = 'Local storage is unavailable; source cannot be saved.'; }
    void (async () => {
      try {
        await request('/bootstrap'); connection = 'connected';
        let saved: string | null = null;
        try { saved = sessionStorage.getItem('marie.session'); } catch { /* no recovery */ }
        if (saved) { accept(await request<Machine>(`/sessions/${saved}`)); memoryPage = Math.floor(machine!.current_address / 64); }
      } catch (error) { report(error); }
      if (!stopped) void poll();
    })();
    return () => { stopped = true; clearTimeout(pollTimer); generation++; };
  });
</script>

<svelte:head><title>MARIE — Assembly Simulator</title><meta name="description" content="Write and run MARIE assembly, inspect registers, and explore memory." /></svelte:head>
<svelte:window onkeydown={shortcuts} />

<a class="skip-link" href="#main-content">Skip to simulator</a>
<div class="family-backdrop" aria-hidden="true"></div>
<header class="site-header">
  <a class="brand" href="/" aria-label="MARIE home"><img src="/ad-logo.png" alt="AD" width="34" height="34" /><span>marie<span class="orange">.</span></span></a>
  <nav class:open={mobileMenu} aria-label="Main navigation">
    <button class:chosen={tab === 'workspace'} onclick={() => { tab = 'workspace'; mobileMenu = false; }}>Workspace</button>
    <button class:chosen={tab === 'examples'} onclick={() => { tab = 'examples'; mobileMenu = false; }}>Examples</button>
    <button class:chosen={tab === 'guide'} onclick={() => { tab = 'guide'; mobileMenu = false; }}>Instruction guide</button>
  </nav>
  <button class="icon-button theme-button" onclick={changeTheme} aria-label={`Switch to ${theme === 'light' ? 'dark' : 'light'} theme`} title="Change theme">{theme === 'light' ? '☾' : '☀'}</button>
  <button class="icon-button mobile-menu" onclick={() => mobileMenu = !mobileMenu} aria-label="Toggle navigation" aria-expanded={mobileMenu}>☰</button>
</header>

<main id="main-content">
  <h1 class="sr-only">MARIE Assembly Simulator</h1>

  {#if tab === 'workspace'}
    <div class="toolbar" aria-label="Execution controls">
      <div class="controls">
        <button class="primary" disabled={!usable || active || !source.trim()} onclick={assemble}><span aria-hidden="true">⌘</span> {busy && !machine ? 'Assembling…' : 'Assemble'}</button>
        <div class="control-divider"></div>
        <button class="run-button" disabled={!canExecute} onclick={() => command('run')}><span aria-hidden="true">▶</span> Run</button>
        <button disabled={!usable || !active} onclick={() => command('pause')}><span aria-hidden="true">Ⅱ</span> Pause</button>
        <button disabled={!canExecute} onclick={() => command('step')} title="Step (F10)"><span aria-hidden="true">↦</span> Step</button>
        <button disabled={!usable || !machine} onclick={() => command('reset')}><span aria-hidden="true">↺</span> Reset</button>
      </div>
      <label class="speed">Speed <select aria-label="Execution speed" bind:value={speed} disabled={!usable || !machine} onchange={() => command('speed', { speed })}>{#each [1, 5, 20, 100, 1000, 5000] as rate}<option value={rate}>{rate.toLocaleString()} / sec</option>{/each}</select></label>
    </div>
    <div class="state-strip"><span class="status" class:running={active} class:failed={machine?.status === 'failed' || connection === 'disconnected'}><span class="status-dot"></span><span aria-live="polite">{status}</span></span><span class="state-note">{busy ? 'Sending command…' : dirty ? 'Source changed · assemble to apply edits' : machine?.status === 'waiting_for_input' ? 'Supply a number below, then Run or Step to continue.' : machine?.status === 'halted' ? 'Program complete · reset to explore it again' : machine ? `${machine.steps.toLocaleString()} instructions executed` : 'Start with Assemble, then explore one step at a time.'}</span>{#if connection === 'disconnected' || connection === 'expired'}<button class="text-button" disabled={busy} onclick={reconnect}>{connection === 'expired' ? 'Start a new session' : 'Reconnect'}</button>{/if}</div>
    {#if message}<div class="alert" role="alert"><strong>{assemblyLine ? `Assembly error · line ${assemblyLine}` : 'Simulator notice'}</strong><span>{message}</span></div>{/if}
    {#if machine?.error}<div class="alert" role="alert"><strong>Execution error</strong><span>{machine.error}</span></div>{/if}
    {#if storageWarning}<div class="alert warning" role="status">{storageWarning}</div>{/if}

    <div class="workspace-grid">
      <section class="panel source-panel" aria-label="Source editor">
        <div class="panel-heading"><div><span class="panel-number">01</span><h2>Source code</h2></div><label class="example-select"><span class="sr-only">Load example (replaces current source)</span><select disabled={active || busy} value="" onchange={(e) => { if (e.currentTarget.value !== '') loadExample(Number(e.currentTarget.value)); e.currentTarget.value = ''; }}><option value="" disabled>Load an example</option>{#each examples as example, index}<option value={index}>{example.name}</option>{/each}</select></label></div>
        <div class="file-bar"><span><span class="orange">▤</span> program.mas</span><span>MARIE Assembly</span></div>
        <Editor value={source} onchange={persist} line={currentLine} errorLine={assemblyLine} readonly={active || busy} />
        <div class="editor-footer"><span class="save-indicator"></span><span>{saveLabel}</span><span class="shortcut">⌘ / Ctrl + Enter to assemble</span></div>
      </section>
      <div class="machine-column">
        <section class="panel register-panel" aria-label="Registers">
          <div class="panel-heading"><div><span class="panel-number">02</span><h2>Registers</h2></div><span class="mini-label">LIVE MACHINE STATE</span></div>
          <div class="registers">
            {#each ['AC','PC','MAR','MBR','IR','InReg','OutReg'] as name}
              <div class="register" class:accumulator={name === 'AC'}><div><abbr title={registerHelp[name]}>{name === 'InReg' ? 'IN' : name === 'OutReg' ? 'OUT' : name}</abbr><span class="register-caption">{registerHelp[name].split(' · ')[0]}</span></div><div class="register-value"><code>{hex(machine?.registers[name] ?? 0, ['PC','MAR'].includes(name) ? 3 : 4)}</code><span>{['PC','MAR'].includes(name) ? machine?.registers[name] ?? 0 : signed(machine?.registers[name] ?? 0)} <small>dec</small></span></div></div>
            {/each}
          </div>
          <div class="next-instruction"><span class="mini-label">{machine?.status === 'halted' ? 'PROGRAM COMPLETE' : 'NEXT INSTRUCTION'}</span><code>{machine?.status === 'halted' ? 'Halt reached' : machine ? `${hex(machine.current_address, 3)}  ${currentRow?.source.trim() ?? 'Unmapped memory'}` : '— Assemble to begin'}</code></div>
        </section>
        <section class="panel io-panel" aria-label="Input and output">
          <div class="panel-heading"><div><span class="panel-number">03</span><h2>Input / Output</h2></div><span class="mini-label">NUMERIC WORDS</span></div>
          <form class="input-form" onsubmit={(e) => { e.preventDefault(); supplyInput(); }}><label for="machine-input">{machine?.status === 'waiting_for_input' ? 'Your program is waiting for a number' : 'Input · available when requested'}</label><div><input id="machine-input" placeholder={inputBase === 'dec' ? 'e.g. 42 or −7' : 'e.g. 002A'} bind:value={inputText} disabled={!usable || machine?.status !== 'waiting_for_input'} maxlength="12" autocomplete="off" /><select aria-label="Input number format" bind:value={inputBase}><option value="dec">DEC</option><option value="hex">HEX</option></select><button class="input-submit" disabled={!usable || machine?.status !== 'waiting_for_input' || !inputText.trim()} type="submit" aria-label="Supply input">↵</button></div></form>
          <div class="output-heading"><span>Output</span><span class="mini-label">DECIMAL / HEX</span></div>
          <!-- svelte-ignore a11y_no_noninteractive_tabindex (Keyboard users need to scroll the output log.) -->
          <div class="output-log" tabindex="0" role="region" aria-label="Program output">{#if machine?.output.length}{#each machine.output as value, index}<div><span class="output-index">{String(index + 1).padStart(2, '0')}</span><code>{signed(value)}</code><code class="muted">0x{hex(value)}</code></div>{/each}{:else}<p><span aria-hidden="true">↳</span> Your program’s output will appear here.</p>{/if}</div>
        </section>
      </div>
    </div>
    <section class="panel memory-panel" aria-label="Memory inspector">
      <div class="panel-heading"><div><span class="panel-number">04</span><h2>Inside the memory</h2></div><div class="segmented"><button class:chosen={memoryTab === 'memory'} onclick={() => memoryTab = 'memory'}>Memory</button><button class:chosen={memoryTab === 'listing'} onclick={() => memoryTab = 'listing'}>Program listing</button></div></div>
      {#if memoryTab === 'memory'}
        <div class="memory-tools"><p>4,096 words <span class="dot-separator">·</span> Hex values <span class="dot-separator">·</span> Select a cell for decimal</p><form onsubmit={(e) => { e.preventDefault(); jumpMemory(); }}><label class="sr-only" for="memory-address">Jump to hexadecimal address</label><input id="memory-address" placeholder="Address (hex)" bind:value={addressText} maxlength="5" /><button type="submit">Go</button><button type="button" disabled={!machine} onclick={() => { memoryPage = Math.floor((machine?.current_address ?? 0) / 64); selectedAddress = machine?.current_address ?? null; }}>Follow PC</button></form></div>
        <div class="memory-scroll"><table class="memory-table"><caption class="sr-only">Memory words {hex(memoryPage * 64, 3)} through {hex(memoryPage * 64 + 63, 3)}</caption><thead><tr><th scope="col">ADDR</th>{#each Array(8) as _, column}<th scope="col">+{column}</th>{/each}</tr></thead><tbody>{#each Array(8) as _, row}<tr><th scope="row">{hex(memoryPage * 64 + row * 8, 3)}</th>{#each Array(8) as _, col}{@const address = memoryPage * 64 + row * 8 + col}<td><button class:pc={!!machine && machine.current_address === address} class:nonzero={(machine?.memory[address] ?? 0) !== 0} class:selected={selectedAddress === address} onclick={() => selectedAddress = address} title={`Address ${hex(address, 3)}: ${signed(machine?.memory[address] ?? 0)} decimal`} aria-label={`Address ${hex(address, 3)}, hex ${hex(machine?.memory[address] ?? 0)}, decimal ${signed(machine?.memory[address] ?? 0)}`}>{hex(machine?.memory[address] ?? 0)}</button></td>{/each}</tr>{/each}</tbody></table></div>
        <div class="memory-footer"><span>{#if selectedAddress !== null}<code>{hex(selectedAddress, 3)}</code> → <strong>{signed(machine?.memory[selectedAddress] ?? 0)}</strong> decimal / <code>0x{hex(machine?.memory[selectedAddress] ?? 0)}</code>{:else}<span class="pc-key"></span> Program counter <span class="muted">· 12-bit addresses</span>{/if}</span><div><button class="icon-button" disabled={memoryPage === 0} onclick={() => memoryPage--} aria-label="Previous memory page">←</button><span>{memoryPage + 1} / 64</span><button class="icon-button" disabled={memoryPage === 63} onclick={() => memoryPage++} aria-label="Next memory page">→</button></div></div>
      {:else}
        <div class="listing-scroll"><table class="listing-table"><thead><tr><th>Address</th><th>Line</th><th>Word</th><th>Source</th></tr></thead><tbody>{#each machine?.listing ?? [] as row}<tr class:current={row.address === machine?.current_address}><td><code>{hex(row.address, 3)}</code></td><td>{row.line}</td><td><code>{hex(machine?.memory[row.address] ?? row.word)}</code></td><td><code>{row.source}</code></td></tr>{:else}<tr><td colspan="4" class="empty-listing">Assemble your source to see the address and encoding of each line.</td></tr>{/each}</tbody></table></div>
      {/if}
    </section>

  {:else if tab === 'examples'}
    <section class="library"><p class="eyebrow">LEARN BY DOING</p><h2>Small programs. Big ideas.</h2><p>Choose a starting point. Loading an example replaces the source in your editor.</p><div class="example-grid">{#each examples as example, index}<article class="panel example-card"><span class="panel-number">0{index + 1}</span><h3>{example.name}</h3><p>{example.description}</p><pre>{example.source.split('\n').filter(l => !l.startsWith('/')).slice(0, 5).join('\n').trim()}</pre><button disabled={active || busy} onclick={() => loadExample(index)}>Open in workspace <span>↗</span></button></article>{/each}</div>{#if active}<p class="alert">Pause your running program before loading an example.</p>{/if}</section>
  {:else}
    <section class="guide"><p class="eyebrow">THE FIELD GUIDE</p><h2>Meet your little machine.</h2><p>MARIE is a teaching architecture with 16-bit words, 12-bit addresses, and one accumulator. Every instruction makes a small, visible change.</p><div class="guide-steps"><article class="panel"><span class="panel-number">01</span><h3>Write & assemble</h3><p>Use labels like <code>Value, DEC 42</code>. Addresses and <code>HEX</code> values use hexadecimal; <code>DEC</code> uses signed decimal. Comments begin with <code>/</code> or <code>;</code>.</p></article><article class="panel"><span class="panel-number">02</span><h3>Follow each step</h3><p>Assemble, then Step (F10). The highlighted line is the next instruction. PC points to it; IR holds the last fetched instruction. Run follows the selected speed.</p></article><article class="panel"><span class="panel-number">03</span><h3>Inspect & experiment</h3><p>Hex shows raw bits; decimal shows signed words. Input pauses until you supply a value, then leaves execution paused. Reset restores all memory and registers.</p></article></div><div class="panel instruction-panel"><div class="panel-heading"><h3>Instruction reference</h3><span class="mini-label">X = HEX ADDRESS OR LABEL</span></div><dl>{#each instructions as [name, description]}<div><dt><code>{name}</code></dt><dd>{description}</dd></div>{/each}</dl></div><div class="guide-detail"><p><strong>Words & overflow.</strong> Values wrap modulo 65,536. Signed decimal ranges from −32,768 to 32,767; FFFF represents −1. Indirect pointers and PC use the low 12 bits. JnS also changes AC to X + 1.</p><p><strong>Temporary sessions.</strong> Refresh reconnects in this tab. Sessions expire after 30 minutes without requests or disappear on server restart. During a disconnect, execution continues within its limits. Your saved source is independent of the session.</p><p><strong>Fair execution.</strong> Each reset permits up to 100,000 instructions, 1,024 outputs, 60 seconds running, and 2 seconds of engine CPU time. Reset or reassemble after a limit is reached.</p></div></section>
  {/if}
  <footer><span>Made by <a href="https://apps.aaryandehade.com">Aaryan<span class="orange">.</span></a></span><span>Machine Architecture that is Really Intuitive and Easy</span><a href="https://github.com/dehadeaaryan/marie-simulator" target="_blank" rel="noreferrer">Source code ↗</a></footer>
</main>
