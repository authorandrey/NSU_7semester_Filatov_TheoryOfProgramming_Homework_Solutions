import React, { useEffect, useRef } from 'react';
import cytoscape, { type Core, type ElementDefinition } from 'cytoscape';
import type { Automaton } from '../model/automaton';
import type { PartitionView, TransitionRef } from '../trace/types';

const positionCache = new Map<string, Map<string, { x: number; y: number }>>();
const getPositionMap = (id: string) => { if (!positionCache.has(id)) positionCache.set(id, new Map()); return positionCache.get(id)!; };
export interface GraphViewProps {
  automaton: Automaton;
  highlightStates?: string[];
  highlightTransitions?: TransitionRef[];
  conflictStates?: string[];
  newStates?: string[];
  partitions?: PartitionView;
  editable?: boolean;
  compact?: boolean;
  onChangeAutomaton?: (a: Automaton) => void;
  onReady?: (cy: Core) => void;
}

const style: any[] = [
  { selector: 'node.state', style: { 'background-color': '#fff', 'border-color': '#334155', 'border-width': 2, label: 'data(label)', width: 48, height: 48, 'font-size': 12, 'text-valign': 'center', 'text-halign': 'center', color: '#0f172a', 'text-wrap': 'wrap', 'text-max-width': '70px' } },
  { selector: 'node.final', style: { 'border-style': 'double', 'border-width': 5 } },
  { selector: 'node.initial', style: { 'border-color': '#2563eb' } },
  { selector: 'node.hl', style: { 'background-color': '#fde68a', 'border-color': '#d97706', 'border-width': 4 } },
  { selector: 'node.cf', style: { 'background-color': '#fecaca', 'border-color': '#dc2626', 'border-width': 4 } },
  { selector: 'node.nw', style: { 'background-color': '#bbf7d0', 'border-color': '#16a34a', 'border-width': 4 } },
  { selector: 'node.group', style: { 'background-color': '#e0e7ff', 'background-opacity': 0.36, 'border-color': '#6366f1', 'border-width': 2, 'border-style': 'dashed', label: 'data(label)', 'text-valign': 'top', 'text-halign': 'center', 'font-size': 12, color: '#4338ca', padding: 18, 'compound-sizing-wrt-labels': 'include' } },
  { selector: 'edge.edge', style: { width: 1.8, 'line-color': '#64748b', 'target-arrow-color': '#64748b', 'target-arrow-shape': 'triangle', 'curve-style': 'bezier', label: 'data(label)', 'font-size': 11, color: '#0f172a', 'text-background-color': '#fff', 'text-background-opacity': 0.92, 'text-background-padding': '2px', 'text-rotation': 'autorotate' } },
  { selector: 'edge.hl', style: { 'line-color': '#d97706', 'target-arrow-color': '#d97706', width: 3.2 } },
  { selector: 'node.start-marker', style: { width: 1, height: 1, 'background-opacity': 0, 'border-width': 0, label: '' } },
  { selector: 'edge.start-edge', style: { width: 1.8, 'line-color': '#2563eb', 'target-arrow-color': '#2563eb', 'target-arrow-shape': 'triangle', 'curve-style': 'straight' } },
];

export function GraphView(props: GraphViewProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<Core | null>(null);
  const propsRef = useRef(props);
  propsRef.current = props;

  useEffect(() => {
    if (!containerRef.current) return;
    const cy = cytoscape({ container: containerRef.current, style, wheelSensitivity: 0.2, boxSelectionEnabled: false, userPanningEnabled: true, userZoomingEnabled: true });
    cyRef.current = cy;
    cy.on('dragfree', 'node', event => {
      const node = event.target;
      const current = propsRef.current;
      if (node.id() === '__start' || node.hasClass('group')) return;
      const position = { x: node.position('x'), y: node.position('y') };
      getPositionMap(current.automaton.id).set(node.id(), position);
      current.onChangeAutomaton?.({ ...current.automaton, positions: { ...(current.automaton.positions ?? {}), [node.id()]: position } });
      const initial = current.automaton.initialState;
      if (node.id() === initial) {
        const marker = cy.getElementById('__start');
        if (marker.length) marker.position({ x: node.position('x') - 80, y: node.position('y') });
      }
    });
    cy.on('dbltap', 'node', event => {
      const current = propsRef.current;
      if (!current.editable) return;
      const node = event.target;
      if (node.id() === '__start' || node.hasClass('group')) return;
      current.onChangeAutomaton?.(toggleFinal(current.automaton, node.id()));
    });
    cy.on('dbltap', event => {
      const current = propsRef.current;
      if (!current.editable || event.target !== cy) return;
      const name = window.prompt('Имя нового состояния:', `q${current.automaton.states.length}`);
      if (!name?.trim()) return;
      if (current.automaton.states.includes(name.trim())) { window.alert('Такое состояние уже существует.'); return; }
      const stateName = name.trim();
      getPositionMap(current.automaton.id).set(stateName, event.position);
      current.onChangeAutomaton?.({ ...current.automaton, states: [...current.automaton.states, stateName], initialState: current.automaton.initialState || stateName });
    });
    propsRef.current.onReady?.(cy);
    return () => { cy.destroy(); cyRef.current = null; };
  }, []);

  useEffect(() => {
    const cy = cyRef.current; if (!cy) return;
    const aut = props.automaton; const positions = getPositionMap(aut.id);
    for (const [state, position] of Object.entries(aut.positions ?? {})) positions.set(state, position);
    const parentOf = new Map<string, string>(); const groupNodes: ElementDefinition[] = [];
    props.partitions?.blocks.forEach((block, i) => {
      const id = `__g_${i}`; groupNodes.push({ data: { id, label: `${props.partitions?.label ?? 'P'}: ${block.name}` }, classes: 'group' });
      block.states.forEach(s => { if (aut.states.includes(s)) parentOf.set(s, id); });
    });
    const nodes: ElementDefinition[] = aut.states.map(s => {
      const classes = ['state'];
      if (s === aut.initialState) classes.push('initial');
      if (aut.finalStates.includes(s)) classes.push('final');
      if (props.highlightStates?.includes(s)) classes.push('hl');
      if (props.conflictStates?.includes(s)) classes.push('cf');
      if (props.newStates?.includes(s)) classes.push('nw');
      const data: Record<string, unknown> = { id: s, label: s };
      if (parentOf.has(s)) data.parent = parentOf.get(s);
      return { data, classes: classes.join(' '), ...(positions.has(s) ? { position: positions.get(s)! } : {}) };
    });
    nodes.push({ data: { id: '__start', label: '' }, classes: 'start-marker' });
    const merged = new Map<string, string[]>();
    for (const t of aut.transitions) {
      const key = `${t.from}\u0001${t.to}`;
      if (!merged.has(key)) merged.set(key, []);
      merged.get(key)!.push(t.symbol);
    }
    const edges: ElementDefinition[] = []; let i = 0;
    for (const [key, symbols] of merged) {
      const [from, to] = key.split('\u0001');
      const highlighted = (props.highlightTransitions ?? []).some(t => t.from === from && t.to === to && symbols.includes(t.symbol));
      edges.push({ data: { id: `edge_${i++}`, source: from, target: to, label: [...new Set(symbols)].join(', ') }, classes: highlighted ? 'edge hl' : 'edge' });
    }
    if (aut.initialState && aut.states.includes(aut.initialState)) edges.push({ data: { id: '__start_edge', source: '__start', target: aut.initialState, label: '' }, classes: 'start-edge' });
    cy.elements().remove();
    cy.add([...groupNodes, ...nodes, ...edges]);
    if (aut.states.length) {
      const missing = aut.states.some(s => !positions.has(s));
      if (missing) {
        cy.layout({ name: 'cose', animate: false, fit: true, padding: 42, nodeRepulsion: () => 14000, idealEdgeLength: () => 120, randomize: true } as any).run();
        for (const s of aut.states) { const node = cy.getElementById(s); if (node.length) positions.set(s, node.position()); }
      } else {
        cy.layout({ name: 'preset', fit: true, padding: 42 }).run();
      }
      const initial = cy.getElementById(aut.initialState);
      if (initial.length) cy.getElementById('__start').position({ x: initial.position('x') - 80, y: initial.position('y') });
      cy.fit(undefined, 42);
    }
  }, [props.automaton, props.highlightStates, props.highlightTransitions, props.conflictStates, props.newStates, props.partitions]);

  return <div ref={containerRef} className={`graph-view${props.compact ? ' compact' : ''}`} />;
}

function toggleFinal(a: Automaton, s: string): Automaton {
  const finalStates = a.finalStates.includes(s) ? a.finalStates.filter(x => x !== s) : [...a.finalStates, s];
  return { ...a, finalStates };
}
