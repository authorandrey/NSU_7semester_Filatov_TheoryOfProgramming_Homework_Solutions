import type { Automaton } from '../model/automaton';
import { completeWithSink, copyAutomaton, getTargets, isComplete, isDFA, reachableStates, removeStates } from '../model/automaton';
import type { Step, TableData, Trace } from '../trace/types';
import { buildQuotient } from './minimization';

const pairKey = (p: string, q: string) => [p, q].sort().join('\u0001');
function buildTable(states: string[], marked: Map<string, unknown>, highlight?: string): TableData {
  const headers = ['', ...states];
  const rows = states.map((r, i) => [r, ...states.map((c, j) => i === j ? '—' : marked.has(pairKey(r, c)) ? '×' : '·')]);
  const highlighted: Array<[number, number]> = [];
  if (highlight) {
    const [a, b] = highlight.split('\u0001'); const ia = states.indexOf(a), ib = states.indexOf(b);
    if (ia >= 0 && ib >= 0) { highlighted.push([ia, ib + 1], [ib, ia + 1]); }
  }
  return { title: 'Таблица различимости', headers, rows, highlighted };
}
export interface TableOptions { complete?: boolean; removeUnreachable?: boolean; detail?: 'marks' | 'all'; }

export function minimizeTableFilling(input: Automaton, options: TableOptions = {}): Trace {
  const steps: Step[] = [];
  let aut = copyAutomaton(input);
  const push = (s: Omit<Step, 'index' | 'automaton'> & { automaton?: Automaton }) => {
    steps.push({ ...s, index: steps.length, automaton: copyAutomaton(s.automaton ?? aut) } as Step);
  };
  const fail = (message: string): Trace => ({ algorithm: 'minimize-table', title: 'Минимизация (табличный метод)', baseAutomaton: copyAutomaton(input), steps, result: { success: false, message } });
  push({ title: 'Исходный автомат', explanation: `Q = {${aut.states.join(', ')}}, Σ = {${aut.alphabet.join(', ')}}.`, operationType: 'init' });
  if (!isDFA(aut)) {
    push({ title: 'Ожидался ДКА', explanation: 'Табличный метод применяется к ДКА без ε-переходов и недетерминированных переходов.', operationType: 'error' });
    return fail('Входной автомат не является корректным ДКА.');
  }
  if (options.complete === false && !isComplete(aut)) {
    push({ title: 'Требуется дополнение', explanation: 'Для корректного табличного метода неполный ДКА нужно дополнить стоковым состоянием. Включите соответствующую опцию.', operationType: 'error' });
    return fail('Для неполного ДКА требуется дополнение стоковым состоянием.');
  }
  if (options.complete !== false && !isComplete(aut)) {
    const completed = completeWithSink(aut); aut = completed.aut;
    push({ title: 'Дополнение стоковым состоянием', explanation: `Добавлено незаключительное состояние ${completed.sink}.`, operationType: 'complete', newStates: completed.sink ? [completed.sink] : [], keyStep: true });
  }
  if (options.removeUnreachable !== false) {
    const reach = reachableStates(aut); const unreachable = aut.states.filter(s => !reach.has(s));
    push({ title: 'Проверка достижимости', explanation: `Достижимы {${[...reach].join(', ')}}.${unreachable.length ? ` Недостижимы {${unreachable.join(', ')}}.` : ' Все состояния достижимы.'}`, operationType: 'reach', highlightStates: [...reach], conflictStates: unreachable });
    if (unreachable.length) { aut = removeStates(aut, unreachable); push({ title: 'Удаление недостижимых состояний', explanation: `Удалены {${unreachable.join(', ')}}.`, operationType: 'remove', keyStep: true }); }
  }
  const states = [...aut.states];
  const isFinal = (s: string) => aut.finalStates.includes(s);
  const pairs: Array<[string, string]> = [];
  for (let i = 0; i < states.length; i++) for (let j = i + 1; j < states.length; j++) pairs.push([states[i], states[j]]);
  const marked = new Map<string, { reason: string; symbol?: string; via?: [string, string] }>();
  push({ title: `Создание таблицы (${pairs.length} пар)`, explanation: 'Каждая неупорядоченная пара разных состояний занимает одну клетку выше или ниже диагонали.', operationType: 'init-table', tables: [buildTable(states, marked)], keyStep: true });

  for (const [p, q] of pairs) if (isFinal(p) !== isFinal(q)) {
    const key = pairKey(p, q);
    marked.set(key, { reason: 'Различие по заключительности.' });
    push({ title: `Первичная отметка (${p}, ${q})`, explanation: `${p} ${isFinal(p) ? 'заключительное' : 'незаключительное'}, а ${q} ${isFinal(q) ? 'заключительное' : 'незаключительное'}. Поэтому пара различима пустым суффиксом.`, operationType: 'mark', highlightStates: [p, q], tables: [buildTable(states, marked, key)], keyStep: true });
  }

  let changed = true; let pass = 0;
  while (changed) {
    changed = false; pass++;
    for (const [p, q] of pairs) {
      const key = pairKey(p, q); if (marked.has(key)) continue;
      for (const c of aut.alphabet) {
        const tp = getTargets(aut, p, c)[0]; const tq = getTargets(aut, q, c)[0];
        if (!tp || !tq) continue;
        const targetKey = pairKey(tp, tq);
        if (marked.has(targetKey)) {
          marked.set(key, { reason: `По символу ${c} переходит в уже различимую пару (${tp}, ${tq}).`, symbol: c, via: [tp, tq] });
          changed = true;
          push({ title: `Отметка (${p}, ${q}) по «${c}»`, explanation: `δ(${p}, «${c}») = ${tp}, δ(${q}, «${c}») = ${tq}. Пара (${tp}, ${tq}) уже отмечена, следовательно, (${p}, ${q}) тоже различима.`, operationType: 'mark', currentSymbol: c, highlightStates: [p, q], conflictStates: [tp, tq], tables: [buildTable(states, marked, key)], keyStep: true });
          break;
        } else if (options.detail === 'all') {
          push({ title: `Проверка (${p}, ${q}) по «${c}»`, explanation: `Переходы ведут в (${tp}, ${tq}); эта пара пока не отмечена. Продолжаем проверку других символов и последующих итераций.`, operationType: 'scan', currentSymbol: c, highlightStates: [p, q], conflictStates: [tp, tq], tables: [buildTable(states, marked, key)] });
        }
      }
    }
  }

  // Equivalence classes are the connected components of the relation of unmarked pairs.
  const parent = new Map(states.map(s => [s, s]));
  const find = (x: string): string => { let p = parent.get(x)!; while (p !== parent.get(p)!) p = parent.get(p)!; let cur = x; while (parent.get(cur)! !== p) { const n = parent.get(cur)!; parent.set(cur, p); cur = n; } return p; };
  const union = (a: string, b: string) => { const x = find(a), y = find(b); if (x !== y) parent.set(y, x); };
  for (const [p, q] of pairs) if (!marked.has(pairKey(p, q))) union(p, q);
  const groups = new Map<string, string[]>();
  for (const s of states) { const r = find(s); if (!groups.has(r)) groups.set(r, []); groups.get(r)!.push(s); }
  const blocks = [...groups.values()];
  push({ title: 'Итоговые классы', explanation: `Непомеченные пары задают классы неразличимости: ${blocks.map(b => `{${b.join(', ')}}`).join(', ')}.`, operationType: 'final-partition', partitions: { label: 'P*', blocks: blocks.map((b, i) => ({ name: `P${i}`, states: b })) }, tables: [buildTable(states, marked)], keyStep: true });
  const minimized = buildQuotient(aut, blocks);
  push({ title: 'Минимальный автомат', explanation: `Построен фактор-автомат с ${blocks.length} состояниями.`, operationType: 'build', automaton: minimized, keyStep: true });
  return { algorithm: 'minimize-table', title: 'Минимизация ДКА (табличный метод)', baseAutomaton: copyAutomaton(input), steps, result: { success: true, message: `Минимальный ДКА содержит ${blocks.length} состояний.`, automaton: minimized } };
}
