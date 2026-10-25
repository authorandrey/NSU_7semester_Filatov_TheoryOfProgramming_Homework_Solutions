import type { Automaton } from '../model/automaton';
import { completeOverAlphabet, copyAutomaton, getTargets, isDFA, newId, unionAlphabet } from '../model/automaton';
import type { Step, Trace } from '../trace/types';

export type ProductMode = 'intersection' | 'symmetric-difference' | 'union';
export function productModeLabel(m: ProductMode): string {
  if (m === 'intersection') return 'пересечение (оба заключительных)';
  if (m === 'symmetric-difference') return 'симметрическая разность (ровно один заключительный)';
  return 'объединение (хотя бы один заключительный)';
}
function finalOf(mode: ProductMode, fa: boolean, fb: boolean): boolean {
  if (mode === 'intersection') return fa && fb;
  if (mode === 'union') return fa || fb;
  return fa !== fb;
}
function pairName(p: [string, string]): string { return JSON.stringify(p); }

export function buildProduct(inputA: Automaton, inputB: Automaton, mode: ProductMode): Trace {
  const steps: Step[] = [];
  const alphabet = unionAlphabet(inputA, inputB);
  const error = (message: string): Trace => ({ algorithm: 'product', title: 'Произведение автоматов', baseAutomaton: copyAutomaton(inputA), steps, result: { success: false, message } });
  steps.push({ index: 0, title: 'Проверка входных автоматов', explanation: `Строим режим «${productModeLabel(mode)}». Для корректного произведения оба входа должны быть ДКА. Общий алфавит Σ = {${alphabet.join(', ')}}.`, operationType: 'init', automaton: copyAutomaton(inputA), sideGraphs: [{ title: `A: ${inputA.name}`, automaton: copyAutomaton(inputA), highlightStates: [inputA.initialState] }, { title: `B: ${inputB.name}`, automaton: copyAutomaton(inputB), highlightStates: [inputB.initialState] }], keyStep: true });
  if (!isDFA(inputA) || !isDFA(inputB)) {
    steps.push({ index: steps.length, title: 'Ожидались два ДКА', explanation: 'Перед построением произведения детерминируйте НКА и удалите ε-переходы, если они есть.', operationType: 'error', automaton: copyAutomaton(inputA) });
    return error('Произведение в этом инструменте строится для двух ДКА.');
  }
  const ca = completeOverAlphabet(inputA, alphabet);
  const cb = completeOverAlphabet(inputB, alphabet);
  const a = ca.aut, b = cb.aut;
  if (ca.sink || cb.sink) steps.push({ index: steps.length, title: 'Согласование алфавитов и дополнение', explanation: `Автоматы дополнены над общим алфавитом. Стоковые состояния: A — ${ca.sink ?? 'не требуется'}, B — ${cb.sink ?? 'не требуется'}. Отсутствовавшие переходы теперь ведут в незаключительные стоки.`, operationType: 'complete', automaton: copyAutomaton(inputA), sideGraphs: [{ title: `A после нормализации`, automaton: a, highlightStates: ca.sink ? [ca.sink] : [] }, { title: `B после нормализации`, automaton: b, highlightStates: cb.sink ? [cb.sink] : [] }], keyStep: true });

  const product: Automaton = { id: newId('prod'), name: 'A×B', kind: 'DFA', states: [], alphabet, initialState: pairName([a.initialState, b.initialState]), finalStates: [], transitions: [], epsilon: [] };
  const snapshot = () => copyAutomaton(product, product.id);
  const queue: Array<[string, string]> = [[a.initialState, b.initialState]];
  const seen = new Set<string>();
  const addState = (p: [string, string]) => {
    const name = pairName(p);
    if (seen.has(name)) return false;
    seen.add(name); product.states.push(name);
    if (finalOf(mode, a.finalStates.includes(p[0]), b.finalStates.includes(p[1]))) product.finalStates.push(name);
    return true;
  };
  addState(queue[0]);
  product.initialState = pairName(queue[0]);
  steps.push({ index: steps.length, title: 'Начальное состояние произведения', explanation: `q₀' = (${a.initialState}, ${b.initialState}). Заключительность каждой пары определяется режимом «${productModeLabel(mode)}».`, operationType: 'start-pair', automaton: snapshot(), highlightStates: [product.initialState], sideGraphs: [{ title: `A: ${a.name}`, automaton: a, highlightStates: [a.initialState] }, { title: `B: ${b.name}`, automaton: b, highlightStates: [b.initialState] }], keyStep: true });

  let head = 0;
  while (head < queue.length) {
    const p = queue[head++]; const from = pairName(p);
    steps.push({ index: steps.length, title: `Обработка пары ${from}`, explanation: `Из пары (${p[0]}, ${p[1]}) вычисляем переход по каждому символу общего алфавита.`, operationType: 'pair', automaton: snapshot(), highlightStates: [from], sideGraphs: [{ title: `A: ${a.name}`, automaton: a, highlightStates: [p[0]] }, { title: `B: ${b.name}`, automaton: b, highlightStates: [p[1]] }] });
    for (const c of alphabet) {
      const ta = getTargets(a, p[0], c)[0]; const tb = getTargets(b, p[1], c)[0];
      if (!ta || !tb) throw new Error('Внутренняя ошибка: нормализованный ДКА содержит отсутствующий переход.');
      const target: [string, string] = [ta, tb]; const to = pairName(target); const isNew = addState(target);
      product.transitions.push({ from, symbol: c, to });
      if (isNew) queue.push(target);
      steps.push({ index: steps.length, title: `δ(${from}, «${c}») = ${to}`, explanation: `δ_A(${p[0]}, «${c}») = ${ta}; δ_B(${p[1]}, «${c}») = ${tb}. В произведении получаем ${to}. ${isNew ? 'Пара новая и добавлена в очередь.' : 'Пара уже была создана.'}`, operationType: isNew ? 'new-pair' : 'transition', automaton: snapshot(), highlightStates: [to], newStates: isNew ? [to] : [], highlightTransitions: [{ from, symbol: c, to }], currentSymbol: c, sideGraphs: [{ title: `A: ${a.name}`, automaton: a, highlightStates: [ta] }, { title: `B: ${b.name}`, automaton: b, highlightStates: [tb] }] });
    }
  }
  steps.push({ index: steps.length, title: 'Итоговое произведение', explanation: `Построено ${product.states.length} достижимых пар; заключительных состояний — ${product.finalStates.length}. Это произведение по достижимым состояниям, а не обязательно полное Q_A × Q_B.`, operationType: 'result', automaton: snapshot(), tables: [{ title: 'Состояния произведения', headers: ['Пара', 'Статус'], rows: product.states.map(s => [s, product.finalStates.includes(s) ? 'заключительное' : 'незаключительное']) }], keyStep: true });
  return { algorithm: 'product', title: `Произведение автоматов (${productModeLabel(mode)})`, baseAutomaton: copyAutomaton(inputA), steps, result: { success: true, message: `Построено произведение: ${product.states.length} достижимых состояний.`, automaton: snapshot() } };
}
