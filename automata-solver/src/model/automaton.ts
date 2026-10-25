export type AutomatonKind = 'DFA' | 'NFA' | 'NFA-EPSILON';

export interface Transition { from: string; symbol: string; to: string; }
export interface EpsilonTransition { from: string; to: string; }

export interface Automaton {
  id: string;
  name: string;
  kind: AutomatonKind;
  states: string[];
  alphabet: string[];
  initialState: string;
  finalStates: string[];
  transitions: Transition[];
  epsilon: EpsilonTransition[];
  /** Optional Cytoscape coordinates, keyed by state name. */
  positions?: Record<string, { x: number; y: number }>;
}

let counter = 0;
export function newId(prefix = 'a'): string {
  counter += 1;
  return `${prefix}_${counter}_${Date.now().toString(36)}`;
}

export function createAutomaton(name = 'A'): Automaton {
  return { id: newId('auto'), name, kind: 'DFA', states: [], alphabet: [], initialState: '', finalStates: [], transitions: [], epsilon: [] };
}

export function copyAutomaton(a: Automaton, id?: string): Automaton {
  return {
    ...a,
    id: id ?? a.id,
    states: [...a.states], alphabet: [...a.alphabet], finalStates: [...a.finalStates],
    transitions: a.transitions.map(t => ({ ...t })), epsilon: a.epsilon.map(e => ({ ...e })),
    ...(a.positions ? { positions: Object.fromEntries(Object.entries(a.positions).map(([state, p]) => [state, { x: p.x, y: p.y }])) } : {}),
  };
}

export function getTargets(a: Automaton, from: string, symbol: string): string[] {
  return a.transitions.filter(t => t.from === from && t.symbol === symbol).map(t => t.to);
}

export function move(a: Automaton, states: string[], symbol: string): string[] {
  const out = new Set<string>();
  for (const s of states) for (const t of getTargets(a, s, symbol)) out.add(t);
  return [...out];
}

export function epsilonClosure(a: Automaton, states: string[]): string[] {
  const seen = new Set(states);
  const stack = [...states];
  while (stack.length) {
    const s = stack.pop()!;
    for (const e of a.epsilon) if (e.from === s && !seen.has(e.to)) { seen.add(e.to); stack.push(e.to); }
  }
  return [...seen].sort((x, y) => a.states.indexOf(x) - a.states.indexOf(y));
}

export function reachableStates(a: Automaton): Set<string> {
  if (!a.initialState || !a.states.includes(a.initialState)) return new Set();
  const seen = new Set<string>([a.initialState]);
  const queue = [a.initialState];
  let head = 0;
  while (head < queue.length) {
    const s = queue[head++];
    for (const t of a.transitions) if (t.from === s && !seen.has(t.to)) { seen.add(t.to); queue.push(t.to); }
    for (const e of a.epsilon) if (e.from === s && !seen.has(e.to)) { seen.add(e.to); queue.push(e.to); }
  }
  return seen;
}

export function isDFA(a: Automaton): boolean {
  if (a.epsilon.length > 0) return false;
  const seen = new Set<string>();
  for (const t of a.transitions) {
    const k = `${t.from}\u0001${t.symbol}`;
    if (seen.has(k)) return false;
    seen.add(k);
  }
  return a.transitions.every(t => a.states.includes(t.from) && a.states.includes(t.to) && a.alphabet.includes(t.symbol));
}

export function isComplete(a: Automaton): boolean {
  return isDFA(a) && a.states.every(s => a.alphabet.every(c => getTargets(a, s, c).length === 1));
}

export function validateAutomaton(a: Automaton): string[] {
  const errors: string[] = [];
  if (!a || typeof a !== 'object') return ['Автомат должен быть объектом.'];
  if (!['DFA', 'NFA', 'NFA-EPSILON'].includes(a.kind)) errors.push('Неизвестный тип автомата.');
  if (typeof a.name !== 'string' || !a.name.trim()) errors.push('У автомата должно быть имя.');
  if (!Array.isArray(a.states) || a.states.some(s => typeof s !== 'string')) return [...errors, 'Множество состояний должно быть списком строк.'];
  if (!Array.isArray(a.alphabet) || a.alphabet.some(c => typeof c !== 'string')) return [...errors, 'Алфавит должен быть списком строк.'];
  if (!Array.isArray(a.finalStates) || a.finalStates.some(s => typeof s !== 'string')) return [...errors, 'Заключительные состояния должны быть списком строк.'];
  if (!Array.isArray(a.transitions) || a.transitions.some(t => !t || typeof t.from !== 'string' || typeof t.to !== 'string' || typeof t.symbol !== 'string')) return [...errors, 'Каждый переход должен содержать строки from, symbol и to.'];
  if (!Array.isArray(a.epsilon) || a.epsilon.some(e => !e || typeof e.from !== 'string' || typeof e.to !== 'string')) return [...errors, 'Каждый ε-переход должен содержать строки from и to.'];
  if (!a.states.length) errors.push('Нужно задать хотя бы одно состояние.');
  if (new Set(a.states).size !== a.states.length) errors.push('Имена состояний должны быть уникальны.');
  if (a.states.some(s => !s.trim())) errors.push('Имя состояния не может быть пустым.');
  if (a.states.some(s => s === '__start' || s.startsWith('__g_'))) errors.push('Имя состояния конфликтует со служебным идентификатором визуализатора.');
  if (new Set(a.alphabet).size !== a.alphabet.length) errors.push('Символы алфавита должны быть уникальными.');
  if (a.alphabet.some(c => [...c].length !== 1 || c === 'ε' || c.trim() === '')) errors.push('Алфавит должен состоять из уникальных одиночных символов; ε задаётся отдельно.');
  if (!a.states.includes(a.initialState)) errors.push('Начальное состояние должно входить в Q.');
  if (a.finalStates.some(s => !a.states.includes(s))) errors.push('Все заключительные состояния должны входить в Q.');
  for (const t of a.transitions) {
    if (!a.states.includes(t.from)) errors.push(`Переход начинается из неизвестного состояния «${t.from}».`);
    if (!a.states.includes(t.to)) errors.push(`Переход ведёт в неизвестное состояние «${t.to}».`);
    if (!a.alphabet.includes(t.symbol)) errors.push(`Символ перехода «${t.symbol}» отсутствует в алфавите.`);
  }
  for (const e of a.epsilon) if (!a.states.includes(e.from) || !a.states.includes(e.to)) errors.push('ε-переход ссылается на неизвестное состояние.');
  if (a.kind === 'DFA' && !isDFA(a)) errors.push('Автомат помечен как ДКА, но имеет ε-переходы, повторные переходы или некорректные ссылки.');
  if (a.kind === 'DFA' && a.transitions.some(t => a.transitions.some(u => u !== t && u.from === t.from && u.symbol === t.symbol))) errors.push('У ДКА не может быть нескольких переходов из состояния по одному символу.');
  return [...new Set(errors)];
}

export function removeStates(aut: Automaton, toRemove: string[]): Automaton {
  const rm = new Set(toRemove);
  const states = aut.states.filter(s => !rm.has(s));
  return {
    ...aut, states,
    initialState: rm.has(aut.initialState) ? '' : aut.initialState,
    finalStates: aut.finalStates.filter(s => !rm.has(s)),
    transitions: aut.transitions.filter(t => !rm.has(t.from) && !rm.has(t.to)),
    epsilon: aut.epsilon.filter(e => !rm.has(e.from) && !rm.has(e.to)),
  };
}

/** Complete a deterministic automaton over an explicitly supplied alphabet.
 * Missing transitions reject by routing to a fresh non-final sink state. */
export function completeOverAlphabet(input: Automaton, alphabet: string[]): { aut: Automaton; sink: string | null } {
  const aut = copyAutomaton(input);
  const sigma = [...new Set(alphabet)];
  aut.alphabet = sigma;
  const missing: Array<{ from: string; symbol: string }> = [];
  for (const s of aut.states) for (const c of sigma) if (getTargets(aut, s, c).length === 0) missing.push({ from: s, symbol: c });
  if (!missing.length) return { aut, sink: null };
  let sink = '⊥';
  let k = 0;
  while (aut.states.includes(sink)) sink = `⊥${++k}`;
  aut.states.push(sink);
  for (const m of missing) aut.transitions.push({ from: m.from, symbol: m.symbol, to: sink });
  for (const c of sigma) aut.transitions.push({ from: sink, symbol: c, to: sink });
  return { aut, sink };
}

export function completeWithSink(aut: Automaton): { aut: Automaton; sink: string | null } {
  return completeOverAlphabet(aut, aut.alphabet);
}

export function unionAlphabet(a: Automaton, b: Automaton): string[] {
  return [...new Set([...a.alphabet, ...b.alphabet])].sort();
}

export function accepts(a: Automaton, word: string): boolean {
  const symbols = [...word];
  if (symbols.some(c => !a.alphabet.includes(c))) return false;
  let cur = new Set<string>(a.kind === 'DFA' ? [a.initialState] : epsilonClosure(a, [a.initialState]));
  for (const ch of symbols) {
    const next = new Set<string>();
    for (const s of cur) for (const t of getTargets(a, s, ch)) next.add(t);
    cur = a.kind === 'DFA' ? next : new Set(epsilonClosure(a, [...next]));
    if (!cur.size) return false;
  }
  return [...cur].some(s => a.finalStates.includes(s));
}
