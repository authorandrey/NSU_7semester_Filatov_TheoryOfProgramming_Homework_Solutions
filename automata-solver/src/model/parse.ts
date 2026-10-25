import type { Automaton } from './automaton';
import { newId } from './automaton';

export function parseAutomaton(text: string, name = 'A'): { automaton?: Automaton; errors: string[] } {
  const errors: string[] = [];
  const states: string[] = [];
  const alphabet: string[] = [];
  let initialState = '';
  const finalStates: string[] = [];
  const transitions: { from: string; symbol: string; to: string }[] = [];
  const epsilon: { from: string; to: string }[] = [];
  const lines = text.split(/\r?\n/).map(l => l.trim()).filter(l => l && !l.startsWith('//'));
  let mode: 'header' | 'transitions' = 'header';

  for (const line of lines) {
    if (/^transitions\s*:/i.test(line)) { mode = 'transitions'; continue; }
    if (mode === 'header') {
      const m = /^(\w+)\s*:\s*(.*)$/.exec(line);
      if (!m) { errors.push(`Не понята строка: «${line}»`); continue; }
      const [, key, raw] = m;
      const vals = raw.split(/[\s,]+/).filter(Boolean);
      switch (key.toLowerCase()) {
        case 'states': states.push(...vals); break;
        case 'alphabet': case 'sigma': alphabet.push(...vals); break;
        case 'initial': case 'start': initialState = vals[0] ?? ''; break;
        case 'final': finalStates.push(...vals); break;
        default: errors.push(`Неизвестный заголовок: ${key}`);
      }
    } else {
      const parts = line.split(/[\s,]+/).filter(Boolean);
      if (parts.length !== 3) { errors.push(`Ожидалось «q a p»: «${line}»`); continue; }
      const [from, sym, to] = parts;
      if (sym === 'eps' || sym === 'ε' || sym === 'epsilon') epsilon.push({ from, to });
      else transitions.push({ from, symbol: sym, to });
    }
  }

  for (const t of transitions) {
    if (!states.includes(t.from)) states.push(t.from);
    if (!states.includes(t.to)) states.push(t.to);
    if (!alphabet.includes(t.symbol)) alphabet.push(t.symbol);
  }
  for (const e of epsilon) {
    if (!states.includes(e.from)) states.push(e.from);
    if (!states.includes(e.to)) states.push(e.to);
  }
  if (new Set(states).size !== states.length) errors.push('Список состояний содержит повторы.');
  if (new Set(alphabet).size !== alphabet.length) errors.push('Список алфавита содержит повторы.');
  if (!states.length) errors.push('Не задано ни одного состояния.');
  if (!initialState) errors.push('Не задано начальное состояние.');
  else if (!states.includes(initialState)) errors.push(`Начальное состояние «${initialState}» отсутствует в списке состояний.`);
  for (const f of finalStates) if (!states.includes(f)) errors.push(`Заключительное состояние «${f}» отсутствует в списке состояний.`);
  if (errors.length) return { errors };

  const kind = epsilon.length ? 'NFA-EPSILON'
    : transitions.some((t, i) => transitions.findIndex(u => u.from === t.from && u.symbol === t.symbol) !== i) ? 'NFA'
    : 'DFA';
  return {
    automaton: {
      id: newId('parsed'), name, kind, states, alphabet, initialState,
      finalStates: [...new Set(finalStates)], transitions, epsilon,
    }, errors: [],
  };
}

export function serializeAutomaton(a: Automaton): string {
  const lines = [
    `states: ${a.states.join(' ')}`,
    `alphabet: ${a.alphabet.join(' ')}`,
    `initial: ${a.initialState}`,
    `final: ${a.finalStates.join(' ')}`,
    'transitions:',
    ...a.transitions.map(t => `${t.from} ${t.symbol} ${t.to}`),
    ...a.epsilon.map(e => `${e.from} eps ${e.to}`),
  ];
  return lines.join('\n');
}
