import type { Automaton } from '../model/automaton';
import { completeOverAlphabet, copyAutomaton, getTargets, isDFA, newId, unionAlphabet } from '../model/automaton';
import type { Step, Trace } from '../trace/types';

const pairName = (p: [string, string]) => JSON.stringify(p);

export function checkEquivalenceProduct(inputA: Automaton, inputB: Automaton): Trace {
  const steps: Step[] = [];
  const alphabet = unionAlphabet(inputA, inputB);
  const fail = (message: string): Trace => ({ algorithm: 'equivalence-product', title: 'Проверка эквивалентности', baseAutomaton: copyAutomaton(inputA), steps, result: { success: false, message } });
  if (!isDFA(inputA) || !isDFA(inputB)) {
    steps.push({ index: 0, title: 'Ожидались два ДКА', explanation: 'Для проверки эквивалентности через произведение сначала детерминируйте входы и обработайте ε-переходы.', operationType: 'error', automaton: copyAutomaton(inputA) });
    return fail('Проверка поддерживает два ДКА без ε-переходов.');
  }
  const ca = completeOverAlphabet(inputA, alphabet); const cb = completeOverAlphabet(inputB, alphabet);
  const a = ca.aut, b = cb.aut;
  const product: Automaton = { id: newId('eqprod'), name: 'A △ B', kind: 'DFA', states: [], alphabet, initialState: pairName([a.initialState, b.initialState]), finalStates: [], transitions: [], epsilon: [] };
  const snap = () => copyAutomaton(product, product.id);
  const mismatched = (p: [string, string]) => a.finalStates.includes(p[0]) !== b.finalStates.includes(p[1]);
  const previous = new Map<string, { pair: [string, string]; previous: string | null; symbol: string | null }>();
  const start: [string, string] = [a.initialState, b.initialState]; const startName = pairName(start);
  previous.set(startName, { pair: start, previous: null, symbol: null });
  const addState = (p: [string, string]) => {
    const name = pairName(p); if (product.states.includes(name)) return;
    product.states.push(name); if (mismatched(p)) product.finalStates.push(name);
  };
  addState(start);
  steps.push({ index: 0, title: 'Начальная пара', explanation: `Начинаем с (${a.initialState}, ${b.initialState}). Проверяется симметрическая разность языков: заключительна пара, если ровно один компонент заключительный.${ca.sink || cb.sink ? ` Добавленные стоки: A — ${ca.sink ?? 'нет'}, B — ${cb.sink ?? 'нет'}.` : ''}`, operationType: 'init', automaton: snap(), highlightStates: [startName], sideGraphs: [{ title: `A: ${a.name}`, automaton: a, highlightStates: [a.initialState] }, { title: `B: ${b.name}`, automaton: b, highlightStates: [b.initialState] }], keyStep: true });
  const queue: Array<[string, string]> = [start]; let head = 0; let found: [string, string] | null = null;
  while (head < queue.length) {
    const p = queue[head++]; const from = pairName(p);
    steps.push({ index: steps.length, title: `Проверка пары ${from}`, explanation: `A-состояние ${p[0]} ${a.finalStates.includes(p[0]) ? 'заключительное' : 'незаключительное'}; B-состояние ${p[1]} ${b.finalStates.includes(p[1]) ? 'заключительное' : 'незаключительное'}.`, operationType: 'check-pair', automaton: snap(), highlightStates: [from], sideGraphs: [{ title: `A: ${a.name}`, automaton: a, highlightStates: [p[0]] }, { title: `B: ${b.name}`, automaton: b, highlightStates: [p[1]] }] });
    if (mismatched(p)) { found = p; steps.push({ index: steps.length, title: `Найдено различие в ${from}`, explanation: 'Одна компонента заключительная, а другая нет. Восстановим слово, по которому эта пара достижима.', operationType: 'conflict', automaton: snap(), conflictStates: [from], keyStep: true }); break; }
    for (const c of alphabet) {
      const ta = getTargets(a, p[0], c)[0]; const tb = getTargets(b, p[1], c)[0];
      if (!ta || !tb) throw new Error('Внутренняя ошибка: входы не были корректно дополнены.');
      const target: [string, string] = [ta, tb]; const to = pairName(target);
      // Always add the edge, even when this target pair was seen before.
      product.transitions.push({ from, symbol: c, to });
      if (!previous.has(to)) {
        previous.set(to, { pair: target, previous: from, symbol: c }); addState(target); queue.push(target);
        steps.push({ index: steps.length, title: `Открыта пара ${to}`, explanation: `По символу «${c}» из ${from} достижима новая пара ${to}; она добавлена в очередь BFS.`, operationType: 'discover', currentSymbol: c, automaton: snap(), highlightStates: [to], newStates: [to], highlightTransitions: [{ from, symbol: c, to }], sideGraphs: [{ title: `A: ${a.name}`, automaton: a, highlightStates: [ta] }, { title: `B: ${b.name}`, automaton: b, highlightStates: [tb] }] });
      } else {
        steps.push({ index: steps.length, title: `Переход в уже известную пару ${to}`, explanation: `По «${c}» получаем ${to}; пара уже встречалась, поэтому повторно в очередь не добавляется. Ребро сохраняется в произведении.`, operationType: 'transition', currentSymbol: c, automaton: snap(), highlightStates: [to], highlightTransitions: [{ from, symbol: c, to }] });
      }
    }
  }
  if (!found) {
    steps.push({ index: steps.length, title: 'Автоматы эквивалентны', explanation: `Проверены все ${product.states.length} достижимых пар. Ни одна пара не различается по заключительности, следовательно, L(A) = L(B).`, operationType: 'result', automaton: snap(), keyStep: true });
    return { algorithm: 'equivalence-product', title: 'Проверка эквивалентности (через произведение)', baseAutomaton: copyAutomaton(inputA), steps, result: { success: true, message: 'Автоматы эквивалентны.', automaton: snap() } };
  }
  const chars: string[] = []; let cur: string | null = pairName(found);
  while (cur) { const info: { pair: [string, string]; previous: string | null; symbol: string | null } = previous.get(cur)!; if (info.symbol !== null) chars.unshift(info.symbol); cur = info.previous; }
  const word = chars.join('');
  steps.push({ index: steps.length, title: 'Кратчайшее различающее слово', explanation: `Кратчайшее различающее слово: «${word}» (длина ${[...word].length}). При его чтении один автомат принимает слово, а второй отвергает.`, operationType: 'result', automaton: snap(), highlightStates: [pairName(found)], keyStep: true });
  return { algorithm: 'equivalence-product', title: 'Проверка эквивалентности (через произведение)', baseAutomaton: copyAutomaton(inputA), steps, result: { success: false, message: `Автоматы не эквивалентны. Различающее слово: «${word}».`, automaton: snap(), distinguishingWord: word } };
}
