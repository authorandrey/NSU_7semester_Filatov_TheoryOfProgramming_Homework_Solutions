import type { Automaton } from '../model/automaton';
import { copyAutomaton, epsilonClosure, getTargets, newId } from '../model/automaton';
import type { Step, Trace } from '../trace/types';

export function determinize(input: Automaton): Trace {
  const steps: Step[] = [];
  const alphabet = [...input.alphabet];
  const canonical = (s: string[]) => [...new Set(s)].sort((a, b) => input.states.indexOf(a) - input.states.indexOf(b));
  const displayName = (s: string[]) => s.length ? `{${s.join(', ')}}` : '∅';
  const keyOf = (s: string[]) => JSON.stringify(canonical(s));
  const start = canonical(epsilonClosure(input, [input.initialState]));
  const startName = displayName(start);
  const dfa: Automaton = { id: newId('dfa'), name: `${input.name}-DFA`, kind: 'DFA', states: [], alphabet, initialState: startName, finalStates: [], transitions: [], epsilon: [] };
  const snapshot = () => copyAutomaton(dfa, dfa.id);
  const subsets = new Map<string, string[]>();
  const queue: string[][] = [];
  const addState = (subset: string[]) => {
    const normalized = canonical(subset); const key = keyOf(normalized); const name = displayName(normalized);
    if (subsets.has(key)) return { name, isNew: false };
    subsets.set(key, normalized); dfa.states.push(name); if (normalized.some(s => input.finalStates.includes(s))) dfa.finalStates.push(name); queue.push(normalized);
    return { name, isNew: true };
  };
  addState(start);
  steps.push({ index: 0, title: 'Начальное подмножество', explanation: `S₀ = ε-closure({${input.initialState}}) = ${startName}.`, operationType: 'init', automaton: snapshot(), highlightStates: [startName], keyStep: true });
  let head = 0;
  while (head < queue.length) {
    const subset = queue[head++]; const from = displayName(subset);
    steps.push({ index: steps.length, title: `Обработка подмножества ${from}`, explanation: `Рассматриваем переходы из каждого состояния множества ${from}.`, operationType: 'subset', automaton: snapshot(), highlightStates: [from] });
    for (const symbol of alphabet) {
      const raw = new Set<string>(); const used: { from: string; symbol: string; to: string }[] = [];
      for (const s of subset) for (const target of getTargets(input, s, symbol)) { raw.add(target); used.push({ from: s, symbol, to: target }); }
      const next = canonical(epsilonClosure(input, [...raw]));
      const added = addState(next); const to = added.name;
      dfa.transitions.push({ from, symbol, to });
      steps.push({ index: steps.length, title: `δ'(${from}, «${symbol}») = ${to}`, explanation: `Переходы по «${symbol}» из ${from} дают {${[...raw].join(', ') || '∅'}}; ε-замыкание даёт ${to}. ${added.isNew ? 'Получено новое подмножество.' : 'Это подмножество уже создано.'}`, operationType: added.isNew ? 'new' : 'transition', currentSymbol: symbol, automaton: snapshot(), highlightStates: [to], newStates: added.isNew ? [to] : [], highlightTransitions: [{ from, symbol, to }], keyStep: added.isNew });
    }
  }
  steps.push({ index: steps.length, title: 'Готовый ДКА', explanation: `Построено ${dfa.states.length} подмножеств. Заключительны все подмножества, содержащие хотя бы одно заключительное состояние исходного автомата. Пустое подмножество, если оно достижимо, образует сток.`, operationType: 'result', automaton: snapshot(), keyStep: true });
  return { algorithm: 'determinize', title: 'Детерминизация (построение подмножеств)', baseAutomaton: copyAutomaton(input), steps, result: { success: true, message: `Построен полный ДКА с ${dfa.states.length} состояниями.`, automaton: snapshot() } };
}
