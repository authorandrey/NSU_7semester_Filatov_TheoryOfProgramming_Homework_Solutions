import React, { useEffect, useRef, useState } from 'react';
import type { Core } from 'cytoscape';
import type { Automaton } from './model/automaton';
import { copyAutomaton, createAutomaton, validateAutomaton } from './model/automaton';
import { examples } from './model/examples';
import type { Trace } from './trace/types';
import { GraphView } from './components/GraphView';
import { AutomatonEditor } from './components/AutomatonEditor';
import { AlgorithmPanel, type AlgorithmOptions, type Mode } from './components/AlgorithmPanel';
import { StepControls } from './components/StepControls';
import { StepInfo } from './components/StepInfo';
import { TablesPanel } from './components/TablesPanel';
import { Legend } from './components/Legend';
import { simulate } from './algorithms/simulation';
import { minimizeHopcroft } from './algorithms/minimization';
import { minimizeTableFilling } from './algorithms/tableFilling';
import { buildProduct } from './algorithms/product';
import { checkEquivalenceProduct } from './algorithms/equivalence';
import { checkEquivalenceUnionFind } from './algorithms/unionFindEquivalence';
import { determinize } from './algorithms/determinize';
import { automatonToSvg } from './export/svgExport';
import { buildSolutionPdf, loadImageSize, type RenderedImage } from './export/pdfExport';
import { download, exportProjectJson, type ProjectSnapshot } from './export/jsonExport';

const STORAGE_KEY = 'automata-solver-project-v1';
interface Project { A: Automaton; B: Automaton; }
function defaultProject(): Project { const e = examples[0].build(); return { A: e.A, B: e.B ?? createAutomaton('B') }; }
function loadProject(): Project | null {
  try { const raw = localStorage.getItem(STORAGE_KEY); if (!raw) return null; const value = JSON.parse(raw); if (value?.A && value?.B) return value as Project; }
  catch { /* Ignore inaccessible or outdated browser storage. */ }
  return null;
}
function isAutomaton(value: unknown): value is Automaton {
  if (!value || typeof value !== 'object') return false;
  const a = value as Partial<Automaton>;
  return typeof a.id === 'string' && typeof a.name === 'string'
    && (a.kind === 'DFA' || a.kind === 'NFA' || a.kind === 'NFA-EPSILON')
    && Array.isArray(a.states) && a.states.every(s => typeof s === 'string')
    && Array.isArray(a.alphabet) && a.alphabet.every(s => typeof s === 'string')
    && typeof a.initialState === 'string' && Array.isArray(a.finalStates) && a.finalStates.every(s => typeof s === 'string')
    && Array.isArray(a.transitions) && a.transitions.every(t => !!t && typeof t.from === 'string' && typeof t.symbol === 'string' && typeof t.to === 'string')
    && Array.isArray(a.epsilon) && a.epsilon.every(t => !!t && typeof t.from === 'string' && typeof t.to === 'string');
}

export default function App() {
  const [project, setProject] = useState<Project>(() => loadProject() ?? defaultProject());
  const [active, setActive] = useState<'A' | 'B'>('A');
  const [mode, setMode] = useState<Mode>('simulate');
  const [options, setOptions] = useState<AlgorithmOptions>({ word: 'abab', productMode: 'intersection', complete: true, removeUnreachable: true, detail: 'marks' });
  const [trace, setTrace] = useState<Trace | null>(null);
  const [stepIdx, setStepIdx] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [exampleIdx, setExampleIdx] = useState(0);
  const [leftOpen, setLeftOpen] = useState(true);
  const [rightOpen, setRightOpen] = useState(true);
  const [busy, setBusy] = useState(false);
  const [uiError, setUiError] = useState('');
  const cyRef = useRef<Core | null>(null);
  const importRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(project)); } catch { /* Storage may be disabled or full. */ }
  }, [project]);

  useEffect(() => {
    if (!playing || !trace) return;
    if (stepIdx >= trace.steps.length - 1) { setPlaying(false); return; }
    const timer = window.setTimeout(() => setStepIdx(i => Math.min(i + 1, trace.steps.length - 1)), 850);
    return () => window.clearTimeout(timer);
  }, [playing, trace, stepIdx]);

  const currentStep = trace?.steps[Math.min(stepIdx, (trace?.steps.length ?? 1) - 1)] ?? null;
  const displayAut = currentStep?.automaton ?? project[active];
  const canRun = mode === 'simulate' || mode === 'minimize-hopcroft' || mode === 'minimize-table' || mode === 'determinize'
    ? project.A.states.length > 0
    : project.A.states.length > 0 && project.B.states.length > 0;

  const run = () => {
    setUiError(''); setPlaying(false);
    const inputs = mode === 'product' || mode === 'equivalence-product' || mode === 'equivalence-unionfind' ? [project.A, project.B] : [project.A];
    const errors = inputs.flatMap((a, i) => validateAutomaton(a).map(e => `${inputs.length > 1 ? (i === 0 ? 'A: ' : 'B: ') : ''}${e}`));
    if (errors.length) { setUiError(errors.join('\n')); return; }
    try {
      let next: Trace;
      switch (mode) {
        case 'simulate': next = simulate(project.A, options.word); break;
        case 'minimize-hopcroft': next = minimizeHopcroft(project.A, { complete: options.complete, removeUnreachable: options.removeUnreachable }); break;
        case 'minimize-table': next = minimizeTableFilling(project.A, { complete: options.complete, removeUnreachable: options.removeUnreachable, detail: options.detail }); break;
        case 'product': next = buildProduct(project.A, project.B, options.productMode); break;
        case 'equivalence-product': next = checkEquivalenceProduct(project.A, project.B); break;
        case 'equivalence-unionfind': next = checkEquivalenceUnionFind(project.A, project.B); break;
        case 'determinize': next = determinize(project.A); break;
      }
      setTrace(next); setStepIdx(0);
      if (!next.result.success) setUiError(next.result.message);
    } catch (error) {
      setUiError(error instanceof Error ? error.message : String(error));
    }
  };

  const resetTrace = () => { setStepIdx(0); setPlaying(false); setTrace(null); setUiError(''); };
  const updateActive = (next: Automaton) => { setProject(p => ({ ...p, [active]: next })); resetTrace(); };
  const runExample = (i: number) => {
    const e = examples[i].build(); setProject({ A: e.A, B: e.B ?? createAutomaton('B') }); setActive('A'); setExampleIdx(i); resetTrace();
  };

  const exportPng = () => {
    const cy = cyRef.current; if (!cy) { setUiError('Граф ещё не готов для экспорта.'); return; }
    const anchor = document.createElement('a'); anchor.href = cy.png({ full: true, scale: 2, bg: '#ffffff' }); anchor.download = 'automaton-step.png'; anchor.click();
  };
  const exportSvg = () => {
    const cy = cyRef.current; if (!cy) { setUiError('Граф ещё не готов для экспорта.'); return; }
    const pos = new Map<string, { x: number; y: number }>();
    for (const s of displayAut.states) { const node = cy.getElementById(s); if (node.length) pos.set(s, node.position()); }
    const svg = automatonToSvg(displayAut, pos, {
      highlightStates: currentStep?.highlightStates, conflictStates: currentStep?.conflictStates, newStates: currentStep?.newStates,
      highlightTransitions: currentStep?.highlightTransitions, partitions: currentStep?.partitions,
    });
    download('automaton-step.svg', svg, 'image/svg+xml;charset=utf-8');
  };
  const exportPdf = async (full: boolean) => {
    if (!trace) return;
    const cy = cyRef.current; if (!cy) { setUiError('Граф ещё не готов для экспорта.'); return; }
    setBusy(true); setPlaying(false); setUiError('');
    const oldIdx = stepIdx; const images: Record<number, RenderedImage> = {};
    const chosenSteps = full ? trace.steps : (trace.steps.filter(s => s.keyStep).length >= 2 ? trace.steps.filter(s => s.keyStep) : trace.steps);
    try {
      for (const step of chosenSteps) {
        setStepIdx(step.index);
        await new Promise<void>(resolve => window.setTimeout(resolve, 160));
        const data = cy.png({ full: true, scale: 2, bg: '#ffffff' });
        const dimensions = await loadImageSize(data);
        images[step.index] = { data, ...dimensions };
      }
      const pdf = await buildSolutionPdf(trace, chosenSteps, images);
      pdf.save(`automata_${trace.algorithm}_${full ? 'full' : 'brief'}.pdf`);
    } catch (error) {
      setUiError(`Не удалось создать PDF: ${error instanceof Error ? error.message : String(error)}`);
    } finally { setStepIdx(oldIdx); setBusy(false); }
  };
  const exportJson = () => {
    const snapshot: ProjectSnapshot = { version: 1, automata: { A: project.A, B: project.B }, trace, stepIndex: stepIdx };
    download('automata_project.json', exportProjectJson(snapshot));
  };
  const exportAutomatonJson = () => {
    const cy = cyRef.current;
    const positions: NonNullable<Automaton['positions']> = { ...(displayAut.positions ?? {}) };
    if (cy) for (const state of displayAut.states) {
      const node = cy.getElementById(state);
      if (node.length) positions[state] = { x: node.position('x'), y: node.position('y') };
    }
    download(`${displayAut.name.replace(/[^a-z0-9_-]+/gi, '_') || 'automaton'}.json`, JSON.stringify({ ...displayAut, positions }, null, 2));
  };
  const importJson = async (file?: File) => {
    if (!file) return;
    setUiError('');
    try {
      const parsed: unknown = JSON.parse(await file.text());
      const value = parsed as { automata?: { A?: unknown; B?: unknown }; automaton?: unknown; A?: unknown; B?: unknown; trace?: unknown; stepIndex?: unknown };
      // Accept either a full project snapshot or a standalone automaton JSON.
      const standalone = value.automaton ?? (isAutomaton(parsed) ? parsed : undefined);
      const a = standalone ?? value.automata?.A ?? value.A;
      const b = value.automata?.B ?? value.B;
      if (!isAutomaton(a)) throw new Error('JSON не содержит автомат в ожидаемом формате. Ожидаются поля name, kind, states, alphabet, initialState, finalStates, transitions и epsilon.');
      const nextA = a as Automaton;
      if (standalone || !b) {
        const errors = validateAutomaton(nextA);
        if (errors.length) throw new Error(errors.join('\n'));
        setProject(p => ({ ...p, A: copyAutomaton(nextA) })); setActive('A');
        setTrace(null); setStepIdx(0); setPlaying(false);
        return;
      }
      if (!isAutomaton(b)) throw new Error('JSON содержит автомат A, но автомат B имеет неверный формат.');
      const nextB = b as Automaton;
      const errors = [...validateAutomaton(nextA).map(e => `A: ${e}`), ...validateAutomaton(nextB).map(e => `B: ${e}`)];
      if (errors.length) throw new Error(errors.join('\n'));
      setProject({ A: copyAutomaton(nextA), B: copyAutomaton(nextB) }); setActive('A');
      const importedTrace = value.trace as Trace | null | undefined;
      if (importedTrace && Array.isArray(importedTrace.steps) && importedTrace.steps.length) {
        setTrace(importedTrace); const max = importedTrace.steps.length - 1;
        setStepIdx(typeof value.stepIndex === 'number' ? Math.max(0, Math.min(max, value.stepIndex)) : 0);
      } else { setTrace(null); setStepIdx(0); }
      setPlaying(false);
    } catch (error) { setUiError(`Импорт не выполнен: ${error instanceof Error ? error.message : String(error)}`); }
    finally { if (importRef.current) importRef.current.value = ''; }
  };

  const useResultAsCurrent = () => {
    const result = trace?.result.automaton;
    if (!result) return;
    setProject(p => ({ ...p, [active]: copyAutomaton(result) }));
    setTrace(null); setStepIdx(0); setPlaying(false); setUiError('');
  };

  const sideA = currentStep?.sideGraphs?.[0]; const sideB = currentStep?.sideGraphs?.[1];
  return <div className="app">
    <header>
      <div className="brand"><strong>Решатель по конечным автоматам</strong><span className="subtitle">Теория программирования</span></div>
      <span className="spacer" />
      <select aria-label="Демонстрационный пример" value={exampleIdx} onChange={e => runExample(Number(e.target.value))}>{examples.map((ex, i) => <option key={i} value={i}>{ex.label}</option>)}</select>
      <button onClick={() => runExample(exampleIdx)}>Загрузить пример</button>
      <button onClick={() => importRef.current?.click()}>Импорт JSON</button>
      <input ref={importRef} type="file" accept="application/json,.json" hidden onChange={e => void importJson(e.target.files?.[0])} />
      <button onClick={() => setLeftOpen(v => !v)}>{leftOpen ? 'Скрыть редактор' : 'Показать редактор'}</button>
      <button onClick={() => setRightOpen(v => !v)}>{rightOpen ? 'Скрыть панель' : 'Показать панель'}</button>
    </header>
    <div className={`main ${leftOpen ? '' : 'no-left'} ${rightOpen ? '' : 'no-right'}`}>
      {leftOpen && <aside className="left">
        <div className="row"><button className={active === 'A' ? 'active' : ''} onClick={() => { setActive('A'); resetTrace(); }}>Автомат A</button><button className={active === 'B' ? 'active' : ''} onClick={() => { setActive('B'); resetTrace(); }}>Автомат B</button></div>
        <AutomatonEditor automaton={project[active]} onChange={updateActive} />
      </aside>}
      <main className="center">
        <div className="graphs"><GraphView automaton={displayAut} highlightStates={currentStep?.highlightStates} highlightTransitions={currentStep?.highlightTransitions} conflictStates={currentStep?.conflictStates} newStates={currentStep?.newStates} partitions={currentStep?.partitions} editable={!trace} onChangeAutomaton={updateActive} onReady={cy => { cyRef.current = cy; }} />
          {(sideA || sideB) && <div className="side-graphs">{sideA && <div className="side-graph"><div className="side-title">{sideA.title}</div><GraphView automaton={sideA.automaton} highlightStates={sideA.highlightStates} compact /></div>}{sideB && <div className="side-graph"><div className="side-title">{sideB.title}</div><GraphView automaton={sideB.automaton} highlightStates={sideB.highlightStates} compact /></div>}</div>}
        </div>
        <Legend />
        <StepControls index={stepIdx} total={trace?.steps.length ?? 0} playing={playing} busy={busy}
          onChange={i => { setPlaying(false); setStepIdx(i); }} onPlayToggle={() => setPlaying(v => !v)} onReset={resetTrace}
          onExportPdf={() => void exportPdf(false)} onExportPdfFull={() => void exportPdf(true)} onExportJson={exportJson} onExportAutomatonJson={exportAutomatonJson} onExportSvg={exportSvg} onExportPng={exportPng} />
        {trace && <div className="trace-summary"><strong>{trace.title}</strong><span>{trace.steps.length} шагов</span><span className={trace.result.success ? 'success' : 'danger'}>{trace.result.message}</span>{trace.result.automaton && <button onClick={useResultAsCurrent}>Взять результат за текущий автомат</button>}</div>}
      </main>
      {rightOpen && <aside className="right"><AlgorithmPanel mode={mode} options={options} onChangeMode={m => { setMode(m); resetTrace(); }} onChangeOptions={setOptions} onRun={run} canRun={canRun} />
        {uiError && <pre className="errors-panel">{uiError}</pre>}
        {trace && <div className={`result ${trace.result.success ? 'result-ok' : 'result-error'}`}><strong>Результат:</strong> {trace.result.message}</div>}
        <StepInfo step={currentStep} /><TablesPanel step={currentStep} />
        {trace && <div className="pdf-options"><button onClick={() => void exportPdf(false)} disabled={busy}>Экспорт PDF — кратко</button><button onClick={() => void exportPdf(true)} disabled={busy}>Экспорт PDF — все шаги</button></div>}
        {busy && <div className="overlay">Формируем PDF…</div>}
      </aside>}
    </div>
  </div>;
}
