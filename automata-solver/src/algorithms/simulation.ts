import type { Automaton } from '../model/automaton';
import { copyAutomaton, epsilonClosure, getTargets } from '../model/automaton';
import type { Step, Trace } from '../trace/types';

export function simulate(aut: Automaton, word: string): Trace {
  const steps: Step[] = [];
  const nfa = aut.kind !== 'DFA';
  const symbols = [...word];
  let current = new Set<string>(nfa ? epsilonClosure(aut, [aut.initialState]) : [aut.initialState]);
  let failure: string | null = null;

  steps.push({
    index: 0, title: 'Начальная конфигурация',
    explanation: nfa ? `Начальное множество — ε-замыкание {${aut.initialState}} = {${[...current].join(', ')}}.` : `Начинаем в начальном состоянии ${aut.initialState}.`,
    operationType: 'init', automaton: copyAutomaton(aut), highlightStates: [...current], currentWordPosition: 0,
  });

  for (let pos = 0; pos < symbols.length; pos++) {
    const symbol = symbols[pos];
    if (!aut.alphabet.includes(symbol)) {
      failure = `Символ «${symbol}» не принадлежит алфавиту.`;
      steps.push({
        index: steps.length, title: `Символ «${symbol}» вне алфавита`, explanation: `${failure} Σ = {${aut.alphabet.join(', ')}}.`,
        operationType: 'error', automaton: copyAutomaton(aut), highlightStates: [...current], currentWordPosition: pos + 1, currentSymbol: symbol, result: 'reject', keyStep: true,
      });
      break;
    }
    const raw = new Set<string>();
    const used: { from: string; symbol: string; to: string }[] = [];
    for (const s of current) for (const target of getTargets(aut, s, symbol)) {
      raw.add(target); used.push({ from: s, symbol, to: target });
    }
    const next = new Set<string>(nfa ? epsilonClosure(aut, [...raw]) : [...raw]);
    steps.push({
      index: steps.length, title: `Чтение символа ${pos + 1}: «${symbol}»`,
      explanation: nfa
        ? `Сначала π({${[...current].join(', ') || '∅'}}, «${symbol}») = {${[...raw].join(', ') || '∅'}}, затем ε-замыкание даёт {${[...next].join(', ') || '∅'}}.`
        : `δ(${[...current].join(', ') || '∅'}, «${symbol}») = ${[...next].join(', ') || '∅'}.`,
      operationType: 'read', automaton: copyAutomaton(aut), highlightStates: [...next], highlightTransitions: used,
      currentSymbol: symbol, currentWordPosition: pos + 1,
    });
    current = next;
    if (current.size === 0) {
      failure = 'Множество активных состояний стало пустым.';
      steps.push({ index: steps.length, title: 'Нет активных состояний', explanation: `${failure} Оставшаяся часть слова не может быть принята.`, operationType: 'dead', automaton: copyAutomaton(aut), currentWordPosition: pos + 1, result: 'reject', keyStep: true });
      break;
    }
  }

  const accepted = !failure && [...current].some(s => aut.finalStates.includes(s));
  const accepting = [...current].filter(s => aut.finalStates.includes(s));
  steps.push({
    index: steps.length, title: accepted ? 'Слово допускается' : 'Слово не допускается',
    explanation: failure ?? (accepted
      ? `После чтения всего слова достигнуты {${[...current].join(', ')}}. Заключительные среди них: {${accepting.join(', ')}}. Слово принадлежит языку.`
      : `После чтения всего слова достигнуты {${[...current].join(', ') || '∅'}}. Заключительных состояний среди них нет. Слово не принадлежит языку.`),
    operationType: 'result', automaton: copyAutomaton(aut), highlightStates: accepted ? accepting : [...current], conflictStates: accepted ? [] : [...current],
    currentWordPosition: symbols.length, result: accepted ? 'accept' : 'reject', keyStep: true,
  });
  return { algorithm: 'simulate', title: `Симуляция слова «${word}»`, baseAutomaton: copyAutomaton(aut), steps, result: { success: accepted, message: accepted ? 'Слово допускается' : 'Слово не допускается' } };
}
