import type { Automaton } from '../model/automaton';
import type { PartitionView, TransitionRef } from '../trace/types';

export interface SvgOptions {
  width?: number; height?: number; highlightStates?: string[]; conflictStates?: string[]; newStates?: string[];
  highlightTransitions?: TransitionRef[]; partitions?: PartitionView;
}
const esc = (s: string) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&apos;');

export function automatonToSvg(aut: Automaton, positions: Map<string, { x: number; y: number }>, opts: SvgOptions = {}): string {
  const padding = 75;
  const nodes = aut.states.map(state => ({ state, p: positions.get(state) ?? { x: 100 + aut.states.indexOf(state) * 100, y: 100 } }));
  if (!nodes.length) return '<svg xmlns="http://www.w3.org/2000/svg" width="360" height="140"><text x="20" y="60" font-family="Arial,sans-serif" font-size="16">Пустой автомат</text></svg>';
  const minX = Math.min(...nodes.map(n => n.p.x)) - padding; const maxX = Math.max(...nodes.map(n => n.p.x)) + padding;
  const minY = Math.min(...nodes.map(n => n.p.y)) - padding; const maxY = Math.max(...nodes.map(n => n.p.y)) + padding;
  const w = opts.width ?? Math.max(420, maxX - minX); const h = opts.height ?? Math.max(280, maxY - minY);
  const shift = (p: { x: number; y: number }) => ({ x: p.x - minX, y: p.y - minY });
  const pos = new Map(nodes.map(n => [n.state, shift(n.p)]));
  const stateR = 26;
  const parts = [`<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}" font-family="Arial, sans-serif">`,
    '<defs><marker id="arrow" markerWidth="9" markerHeight="9" refX="8" refY="3" orient="auto"><path d="M0,0 L0,6 L9,3 z" fill="#64748b"/></marker><marker id="startArrow" markerWidth="9" markerHeight="9" refX="8" refY="3" orient="auto"><path d="M0,0 L0,6 L9,3 z" fill="#2563eb"/></marker></defs>',
    '<rect width="100%" height="100%" fill="#ffffff"/>'];

  // Draw equivalence classes as rounded, translucent clouds behind nodes and transitions.
  for (const [i, block] of (opts.partitions?.blocks ?? []).entries()) {
    const pts = block.states.map(s => pos.get(s)).filter((p): p is { x: number; y: number } => !!p);
    if (!pts.length) continue;
    const left = Math.min(...pts.map(p => p.x)) - 44; const right = Math.max(...pts.map(p => p.x)) + 44;
    const top = Math.min(...pts.map(p => p.y)) - 42; const bottom = Math.max(...pts.map(p => p.y)) + 42;
    const colors = ['#6366f1', '#0f766e', '#c2410c', '#7c3aed', '#0369a1', '#be123c'];
    const color = colors[i % colors.length];
    parts.push(`<rect x="${left}" y="${top}" width="${Math.max(88, right-left)}" height="${Math.max(84,bottom-top)}" rx="26" fill="${color}" fill-opacity="0.09" stroke="${color}" stroke-width="2" stroke-dasharray="7 5"/>`);
    parts.push(`<text x="${(left+right)/2}" y="${top+17}" text-anchor="middle" font-size="12" font-weight="600" fill="${color}">${esc(`${opts.partitions?.label ?? 'P'}: ${block.name}`)}</text>`);
  }

  const pairGroups = new Map<string, string[]>();
  for (const t of aut.transitions) {
    const key = `${t.from}\u0001${t.to}`; if (!pairGroups.has(key)) pairGroups.set(key, []); pairGroups.get(key)!.push(t.symbol);
  }
  const hasReverse = (from: string, to: string) => pairGroups.has(`${to}\u0001${from}`);
  for (const [key, symbolList] of pairGroups) {
    const [from, to] = key.split('\u0001'); const p1 = pos.get(from); const p2 = pos.get(to); if (!p1 || !p2) continue;
    const labels = [...new Set(symbolList)].join(', ');
    const highlighted = (opts.highlightTransitions ?? []).some(t => t.from === from && t.to === to && symbolList.includes(t.symbol));
    const color = highlighted ? '#d97706' : '#64748b';
    if (from === to) {
      parts.push(`<path d="M ${p1.x-15} ${p1.y-stateR+2} C ${p1.x-58} ${p1.y-88}, ${p1.x+58} ${p1.y-88}, ${p1.x+15} ${p1.y-stateR+2}" fill="none" stroke="${color}" stroke-width="${highlighted?3:1.8}" marker-end="url(#arrow)"/>`);
      parts.push(`<text x="${p1.x}" y="${p1.y-78}" text-anchor="middle" font-size="12" fill="#0f172a">${esc(labels)}</text>`);
      continue;
    }
    const dx = p2.x-p1.x; const dy = p2.y-p1.y; const len = Math.hypot(dx,dy)||1; const ux=dx/len; const uy=dy/len;
    const sx=p1.x+ux*stateR; const sy=p1.y+uy*stateR; const ex=p2.x-ux*(stateR+7); const ey=p2.y-uy*(stateR+7);
    const bend = hasReverse(from,to) ? (from.localeCompare(to)<0 ? 26 : -26) : 0;
    const cx=(sx+ex)/2 - uy*bend; const cy=(sy+ey)/2 + ux*bend;
    parts.push(`<path d="M ${sx} ${sy} Q ${cx} ${cy} ${ex} ${ey}" fill="none" stroke="${color}" stroke-width="${highlighted?3:1.8}" marker-end="url(#arrow)"/>`);
    const tx=(sx+2*cx+ex)/4 - uy*(bend===0?12:4); const ty=(sy+2*cy+ey)/4 + ux*(bend===0?12:4);
    parts.push(`<text x="${tx}" y="${ty}" text-anchor="middle" font-size="12" fill="#0f172a" stroke="#fff" stroke-width="4" paint-order="stroke">${esc(labels)}</text>`);
  }

  for (const { state, p } of nodes) {
    const isFinal=aut.finalStates.includes(state), isInitial=aut.initialState===state;
    const fill=opts.conflictStates?.includes(state)?'#fecaca':opts.newStates?.includes(state)?'#bbf7d0':opts.highlightStates?.includes(state)?'#fde68a':'#fff';
    const stroke=isInitial?'#2563eb':opts.conflictStates?.includes(state)?'#dc2626':opts.highlightStates?.includes(state)?'#d97706':'#334155';
    parts.push(`<circle cx="${p.x}" cy="${p.y}" r="${stateR}" fill="${fill}" stroke="${stroke}" stroke-width="${opts.highlightStates?.includes(state)||opts.conflictStates?.includes(state)||opts.newStates?.includes(state)?3:2}"/>`);
    if (isFinal) parts.push(`<circle cx="${p.x}" cy="${p.y}" r="${stateR-5}" fill="none" stroke="#334155" stroke-width="1.6"/>`);
    parts.push(`<text x="${p.x}" y="${p.y+4}" text-anchor="middle" font-size="12" fill="#0f172a">${esc(state)}</text>`);
  }
  if (aut.initialState && pos.has(aut.initialState)) { const p=pos.get(aut.initialState)!; parts.push(`<line x1="${p.x-stateR-34}" y1="${p.y}" x2="${p.x-stateR-4}" y2="${p.y}" stroke="#2563eb" stroke-width="2" marker-end="url(#startArrow)"/>`); }
  parts.push('</svg>'); return parts.join('\n');
}
