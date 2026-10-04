<script lang="ts">
  import { onMount } from 'svelte';
  import { EditorState, StateEffect, StateField, Compartment } from '@codemirror/state';
  import { EditorView, lineNumbers, highlightActiveLine, keymap, Decoration, type DecorationSet } from '@codemirror/view';
  import { history, historyKeymap, defaultKeymap, indentWithTab } from '@codemirror/commands';
  import { StreamLanguage, syntaxHighlighting, HighlightStyle } from '@codemirror/language';
  import { tags } from '@lezer/highlight';
  let { value, onchange, line = null, errorLine = null, readonly = false }: { value: string; onchange: (v: string) => void; line?: number | null; errorLine?: number | null; readonly?: boolean } = $props();
  let container: HTMLDivElement;
  let view: EditorView | undefined;
  const editable = new Compartment();
  const mark = StateEffect.define<{ line: number | null; error: boolean }>();
  const executionLine = StateField.define<DecorationSet>({
    create: () => Decoration.none,
    update(decorations, tr) {
      decorations = decorations.map(tr.changes);
      for (const effect of tr.effects) if (effect.is(mark)) {
        const n = effect.value.line;
        decorations = n && n <= tr.state.doc.lines ? Decoration.set([Decoration.line({ class: effect.value.error ? 'assembly-error-line' : 'execution-line' }).range(tr.state.doc.line(n).from)]) : Decoration.none;
      }
      return decorations;
    },
    provide: field => EditorView.decorations.from(field)
  });
  const language = StreamLanguage.define({
    token(stream) {
      if (stream.eatSpace()) return null;
      if (stream.match(/[/;].*/)) return 'comment';
      if (stream.match(/\b(?:LoadI|StoreI|JumpI|AddI|Skipcond|Load|Store|Subt|Input|Output|Halt|Jump|Clear|Add|JnS)\b/i)) return 'keyword';
      if (stream.match(/\b(?:HEX|DEC|ORG)\b/i)) return 'type';
      if (stream.match(/[A-Za-z_]\w*(?=,)/)) return 'definition';
      if (stream.match(/-?[0-9][0-9A-Fa-f]*\b/)) return 'number';
      stream.next(); return null;
    }
  });
  onMount(() => {
    view = new EditorView({ parent: container, state: EditorState.create({ doc: value, extensions: [
      lineNumbers(), history(), highlightActiveLine(), executionLine, language,
      syntaxHighlighting(HighlightStyle.define([
        { tag: tags.keyword, color: 'var(--syntax-keyword)' }, { tag: tags.comment, color: 'var(--muted)', fontStyle: 'italic' },
        { tag: tags.number, color: 'var(--syntax-number)' }, { tag: tags.typeName, color: 'var(--syntax-number)' }, { tag: tags.definition(tags.variableName), color: 'var(--ink)' }
      ])),
      keymap.of([...defaultKeymap, ...historyKeymap, indentWithTab]),
      EditorView.contentAttributes.of({ 'aria-label': 'MARIE assembly source', spellcheck: 'false' }),
      editable.of(EditorState.readOnly.of(readonly)),
      EditorView.updateListener.of(update => { if (update.docChanged) onchange(update.state.doc.toString()); }),
      EditorView.theme({ '&': { height: '100%', fontSize: '14px' }, '.cm-scroller': { fontFamily: 'var(--mono)', overflow: 'auto', lineHeight: '1.9' }, '.cm-content': { padding: '18px 0', caretColor: 'var(--ink)' }, '.cm-gutters': { backgroundColor: 'var(--panel)', color: 'var(--muted)', border: 'none', padding: '0 8px 0 10px' }, '.cm-activeLine': { backgroundColor: 'var(--subtle)' }, '.cm-cursor': { borderLeftColor: 'var(--ink)' }, '&.cm-focused .cm-selectionBackground, .cm-selectionBackground': { backgroundColor: 'var(--selection)' }, '&.cm-focused': { outline: 'none' }, '.execution-line': { backgroundColor: 'var(--orange-soft)', borderLeft: '3px solid var(--accent)' }, '.assembly-error-line': { backgroundColor: 'var(--error-soft)', borderLeft: '3px solid var(--error)' } })
    ] }) });
    return () => view?.destroy();
  });
  $effect(() => { const text = value; if (view && view.state.doc.toString() !== text) view.dispatch({ changes: { from: 0, to: view.state.doc.length, insert: text } }); });
  $effect(() => { const current = errorLine ?? line; if (view) view.dispatch({ effects: mark.of({ line: current, error: !!errorLine }) }); });
  $effect(() => { const locked = readonly; if (view) view.dispatch({ effects: editable.reconfigure(EditorState.readOnly.of(locked)) }); });
</script>
<div class="editor-host" bind:this={container}></div>
<style>.editor-host { height: 430px; min-width: 0; } @media(max-width: 700px) { .editor-host { height: 340px; } }</style>
