import type { Automaton, Transition } from '../model/automaton';
import { completeWithSink, copyAutomaton, getTargets, isComplete, isDFA, newId, reachableStates, removeStates } from '../model/automaton';
import type { PartitionView, Step, Trace } from '../trace/types';

const blockKey = (block: string[]) => [...block].sort().join('\u0001');
const partitionView = (blocks: string[][], label = 'P'): PartitionView => ({ label, blocks: blocks.map((states, i) => ({ name: `P${i}`, states: [...states] })) });

export function buildQuotient(aut: Automaton, blocks: string[][]): Automaton {
  const blockOf = new Map<string, number>();
  blocks.forEach((block, i) => block.forEach(s => blockOf.set(s, i)));
  const states = blocks.map((_, i) => `C${i}`);
  const initialIdx = blockOf.get(aut.initialState);
  if (initialIdx === undefined) throw new Error('Начальное состояние отсутствует в разбиении.');
  const finalStates = blocks.map((b, i) => b.some(s => aut.finalStates.includes(s)) ? `C${i}` : null).filter((s): s is string => s !== null);
  const transitions: Transition[] = [];
  for (let i = 0; i < blocks.length; i++) {
    const representative = blocks[i][0];
    if (!representative) continue;
    for (const symbol of aut.alphabet) {
      const target = getTargets(aut, representative, symbol)[0];
      if (!target) continue;
      const j = blockOf.get(target);
      if (j === undefined) throw new Error(`Целевое состояние ${target} отсутствует в разбиении.`);
      transitions.push({ from: `C${i}`, symbol, to: `C${j}` });
    }
  }
  return { id: newId('min'), name: `${aut.name}-min`, kind: 'DFA', states, alphabet: [...aut.alphabet], initialState: `C${initialIdx}`, finalStates, transitions, epsilon: [] };
}

export interface MinimizeOptions { complete?: boolean; removeUnreachable?: boolean; }
type StepDraft = Omit<Step, 'index' | 'automaton'> & { automaton?: Automaton };

export function minimizeHopcroft(input: Automaton, options: MinimizeOptions = {}): Trace {
  const steps: Step[] = [];
  let aut = copyAutomaton(input);
  const push = (s: StepDraft) => steps.push({ ...s, index: steps.length, automaton: copyAutomaton(s.automaton ?? aut) } as Step);
  const fail = (message: string): Trace => ({ algorithm: 'minimize-hopcroft', title: 'Минимизация ДКА (Хопкрофт)', baseAutomaton: copyAutomaton(input), steps, result: { success: false, message } });

  push({ title: 'Исходный автомат', explanation: `Q = {${aut.states.join(', ')}}, Σ = {${aut.alphabet.join(', ')}}, q₀ = ${aut.initialState}, F = {${aut.finalStates.join(', ') || '∅'}}.`, operationType: 'init' });
  if (!isDFA(aut)) {
    push({ title: 'Ожидался ДКА', explanation: 'Алгоритм Хопкрофта применим к детерминированному автомату без ε-переходов. Исправьте входные данные.', operationType: 'error', result: 'error' });
    return fail('Входной автомат не является корректным ДКА.');
  }
  if (options.complete === false && !isComplete(aut)) {
    push({ title: 'Требуется дополнение', explanation: 'При отключённом дополнении входной автомат неполный. Для корректной минимизации нужно трактовать отсутствующие переходы как переходы в стоковое состояние; включите опцию дополнения.', operationType: 'error', result: 'error' });
    return fail('Для неполного ДКА требуется дополнение стоковым состоянием.');
  }
  if (options.complete !== false && !isComplete(aut)) {
    const { aut: completed, sink } = completeWithSink(aut);
    aut = completed;
    push({ title: 'Дополнение стоковым состоянием', explanation: `Автомат неполон. Добавлено незаключительное состояние ${sink}; все отсутствующие переходы направлены в него, а переходы из него возвращаются в него.`, operationType: 'complete', newStates: sink ? [sink] : [], keyStep: true });
  }

  if (options.removeUnreachable !== false) {
    const reachable = reachableStates(aut);
    const unreachable = aut.states.filter(s => !reachable.has(s));
    push({ title: 'Поиск достижимых состояний', explanation: `Из ${aut.initialState} достижимы {${[...reachable].join(', ')}}.${unreachable.length ? ` Недостижимы {${unreachable.join(', ')}}.` : ' Недостижимых состояний нет.'}`, operationType: 'reach', highlightStates: [...reachable], conflictStates: unreachable, keyStep: true });
    if (unreachable.length) { aut = removeStates(aut, unreachable); push({ title: 'Удаление недостижимых состояний', explanation: `Удалены {${unreachable.join(', ')}}: они не влияют на распознаваемый язык.`, operationType: 'remove', keyStep: true }); }
  }

  const finals = aut.states.filter(s => aut.finalStates.includes(s));
  const nonfinals = aut.states.filter(s => !aut.finalStates.includes(s));
  const P: string[][] = [];
  if (finals.length) P.push(finals);
  if (nonfinals.length) P.push(nonfinals);
  push({ title: 'Начальное разбиение', explanation: `P₀ = {${P.map(b => `{${b.join(', ')}}`).join(', ')}}. Заключительные и незаключительные состояния находятся в разных классах.`, operationType: 'partition', partitions: partitionView(P, 'P₀'), keyStep: true });
  const W: string[][] = P.map(b => [...b]);

  while (W.length) {
    const A = W.shift()!;
    push({ title: `Извлекаем разделитель {${A.join(', ')}}`, explanation: `Текущий рабочий список содержит ${W.length} блок(а) после извлечения. Блок A используется как цель для поиска прообраза.`, operationType: 'pop-splitter', conflictStates: A, partitions: partitionView(P, 'P'), keyStep: true });
    for (const c of aut.alphabet) {
      const X = aut.states.filter(q => getTargets(aut, q, c).some(t => A.includes(t)));
      push({ title: `Прообраз по символу «${c}»`, explanation: `X = {q ∈ Q | δ(q, «${c}») ∈ A} = {${X.join(', ') || '∅'}}.`, operationType: 'preimage', currentSymbol: c, highlightStates: X, conflictStates: A, partitions: partitionView(P, 'P') });
      if (!X.length) continue;
      const toSplit = [...P].filter(Y => { const n = Y.filter(q => X.includes(q)).length; return n > 0 && n < Y.length; });
      for (const Y of toSplit) {
        const left = Y.filter(q => X.includes(q));
        const right = Y.filter(q => !X.includes(q));
        const idx = P.findIndex(b => blockKey(b) === blockKey(Y));
        if (idx < 0) continue;
        P.splice(idx, 1, left, right);
        const wi = W.findIndex(w => blockKey(w) === blockKey(Y));
        let queued: string[][];
        if (wi >= 0) { W.splice(wi, 1, left, right); queued = [left, right]; }
        else { const smaller = left.length <= right.length ? left : right; W.push(smaller); queued = [smaller]; }
        push({
          title: `Разделяем блок {${Y.join(', ')}}`,
          explanation: `По символу «${c}» блок разделяется на {${left.join(', ')}} (переходят в A) и {${right.join(', ')}} (не переходят в A). ${wi >= 0 ? 'Обе части заняли место исходного блока в W.' : `В W добавлена меньшая часть {${queued[0].join(', ')}}.`}`,
          operationType: 'split', currentSymbol: c, highlightStates: left, conflictStates: right, newStates: [...left, ...right], partitions: partitionView(P, 'P'), keyStep: true,
        });
      }
    }
  }

  push({ title: 'Окончательное разбиение', explanation: `P* = {${P.map(b => `{${b.join(', ')}}`).join(', ')}}. Дальнейших разделений нет.`, operationType: 'final-partition', partitions: partitionView(P, 'P*'), keyStep: true });
  const minimized = buildQuotient(aut, P);
  push({ title: 'Построение фактор-автомата', explanation: 'Каждый блок разбиения становится состоянием фактор-автомата. Переход определяется переходом любого представителя блока.', operationType: 'build', automaton: minimized, keyStep: true });
  push({ title: 'Соответствие классов и новых состояний', explanation: 'Каждое Cᵢ соответствует указанному классу эквивалентности.', operationType: 'mapping', automaton: minimized, tables: [{ title: 'Классы эквивалентности', headers: ['Состояние результата', 'Исходный класс'], rows: P.map((b, i) => [`C${i}`, b.join(', ')]) }], keyStep: true });
  return { algorithm: 'minimize-hopcroft', title: 'Минимизация ДКА (алгоритм Хопкрофта)', baseAutomaton: copyAutomaton(input), steps, result: { success: true, message: `Минимальный ДКА содержит ${P.length} состояний (исходный — ${input.states.length}).`, automaton: minimized } };
}
