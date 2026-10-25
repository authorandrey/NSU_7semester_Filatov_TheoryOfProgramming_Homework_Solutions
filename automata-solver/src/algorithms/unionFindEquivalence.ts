import type { Automaton } from '../model/automaton';
import { completeOverAlphabet, copyAutomaton, getTargets, isDFA, newId, unionAlphabet } from '../model/automaton';
import type { PartitionView, Step, Trace } from '../trace/types';

class UnionFind {
  private parent = new Map<string, string>();
  private size = new Map<string, number>();
  constructor(items: string[]) { for (const x of items) { this.parent.set(x, x); this.size.set(x, 1); } }
  find(x: string): string {
    let root = x;
    while (this.parent.get(root)! !== root) root = this.parent.get(root)!;
    let current = x;
    while (this.parent.get(current)! !== root) { const next = this.parent.get(current)!; this.parent.set(current, root); current = next; }
    return root;
  }
  union(a: string, b: string): string {
    let ra = this.find(a), rb = this.find(b);
    if (ra === rb) return ra;
    if (this.size.get(ra)! < this.size.get(rb)!) [ra, rb] = [rb, ra];
    this.parent.set(rb, ra); this.size.set(ra, this.size.get(ra)! + this.size.get(rb)!); return ra;
  }
  classOf(x: string): string[] { const root = this.find(x); return [...this.parent.keys()].filter(s => this.find(s) === root); }
  classes(): string[][] {
    const map = new Map<string, string[]>();
    for (const s of this.parent.keys()) { const root = this.find(s); if (!map.has(root)) map.set(root, []); map.get(root)!.push(s); }
    return [...map.values()];
  }
}
const partitionView = (blocks: string[][], label: string): PartitionView => ({ label, blocks: blocks.map((states, i) => ({ name: `K${i}`, states: [...states] })) });

export function checkEquivalenceUnionFind(inputA: Automaton, inputB: Automaton): Trace {
  const steps: Step[] = [];
  const alphabet = unionAlphabet(inputA, inputB);
  const fail = (message: string): Trace => ({ algorithm: 'equivalence-unionfind', title: 'Проверка эквивалентности (Union-Find)', baseAutomaton: copyAutomaton(inputA), steps, result: { success: false, message } });
  if (!isDFA(inputA) || !isDFA(inputB)) {
    steps.push({ index: 0, title: 'Ожидались два ДКА', explanation: 'Алгоритм Union-Find из курса применяется к двум ДКА без ε-переходов.', operationType: 'error', automaton: copyAutomaton(inputA) });
    return fail('Union-Find проверяет эквивалентность двух ДКА.');
  }
  const aa = completeOverAlphabet(inputA, alphabet).aut;
  const bb = completeOverAlphabet(inputB, alphabet).aut;
  const prefixA = 'A:'; const prefixB = 'B:';
  const combined: Automaton = {
    id: newId('combined'), name: 'Объединённое множество состояний', kind: 'DFA',
    states: [...aa.states.map(s => prefixA + s), ...bb.states.map(s => prefixB + s)], alphabet,
    initialState: '', finalStates: [...aa.finalStates.map(s => prefixA + s), ...bb.finalStates.map(s => prefixB + s)],
    transitions: [
      ...aa.transitions.map(t => ({ from: prefixA + t.from, symbol: t.symbol, to: prefixA + t.to })),
      ...bb.transitions.map(t => ({ from: prefixB + t.from, symbol: t.symbol, to: prefixB + t.to })),
    ], epsilon: [],
  };
  const snapshot = () => copyAutomaton(combined, combined.id);
  const isFinal = (state: string) => combined.finalStates.includes(state);
  const uf = new UnionFind(combined.states);
  const startA = prefixA + aa.initialState; const startB = prefixB + bb.initialState;
  const list: Array<[string, string]> = [[startA, startB]];
  const push = (s: Omit<Step, 'index' | 'automaton'>) => steps.push({ ...s, index: steps.length, automaton: snapshot() } as Step);
  push({ title: 'Инициализация', explanation: `СПИСОК = {(${startA}, ${startB})}. Все состояния начинают в отдельных одноэлементных классах. Префиксы A: и B: предотвращают совпадение имён.`, operationType: 'init', partitions: partitionView(uf.classes(), 'K'), keyStep: true });
  let conflict: { members: string[]; finals: string[]; nonfinals: string[] } | null = null;
  let head = 0;
  while (head < list.length) {
    const [s, sp] = list[head++];
    const rootS = uf.find(s); const rootT = uf.find(sp);
    push({ title: `Извлечена пара (${s}, ${sp})`, explanation: `НАЙТИ(${s}) = ${rootS}; НАЙТИ(${sp}) = ${rootT}. ${rootS === rootT ? 'Состояния уже в одном классе, расширять пару не нужно.' : 'Классы различны: применяем ОБЪЕДИНИТЬ.'}`, operationType: 'pair', highlightStates: [s, sp], partitions: partitionView(uf.classes(), 'K') });
    if (rootS === rootT) continue;
    const root = uf.union(rootS, rootT);
    const members = uf.classOf(root);
    const finals = members.filter(isFinal); const nonfinals = members.filter(s0 => !isFinal(s0));
    push({ title: `ОБЪЕДИНИТЬ(${rootS}, ${rootT})`, explanation: `Объединённый класс: {${members.join(', ')}}. Заключительные: {${finals.join(', ') || '∅'}}, незаключительные: {${nonfinals.join(', ') || '∅'}}.`, operationType: 'union', highlightStates: members, conflictStates: finals.length && nonfinals.length ? members : [], partitions: partitionView(uf.classes(), 'K'), keyStep: true });
    if (finals.length && nonfinals.length) {
      conflict = { members, finals, nonfinals };
      push({ title: 'Обнаружено различие', explanation: `В одном классе оказались заключительные состояния (${finals.join(', ')}) и незаключительные (${nonfinals.join(', ')}). Поэтому начальные состояния не эквивалентны.`, operationType: 'conflict', conflictStates: members, partitions: partitionView(uf.classes(), 'K'), keyStep: true });
      break;
    }
    const children: Array<[string, string]> = [];
    for (const symbol of alphabet) {
      const t1 = getTargets(combined, s, symbol)[0]; const t2 = getTargets(combined, sp, symbol)[0];
      if (!t1 || !t2) throw new Error('Внутренняя ошибка: автоматы должны быть полными над общим алфавитом.');
      children.push([t1, t2]);
    }
    list.push(...children);
    push({ title: 'Добавление пар-потомков', explanation: `Для каждого символа общего алфавита добавлены пары (δ(${s}, a), δ(${sp}, a)). В очереди осталось ${list.length - head} пар.`, operationType: 'expand', highlightStates: children.flat(), partitions: partitionView(uf.classes(), 'K') });
  }
  if (!conflict) {
    const blocks = uf.classes();
    push({ title: 'Проверка завершена', explanation: 'Список исчерпан. Ни один класс не содержит одновременно заключительные и незаключительные состояния; значит, начальные состояния эквивалентны.', operationType: 'result', partitions: partitionView(blocks, 'K*'), tables: [{ title: 'Итоговые классы Union-Find', headers: ['Класс', 'Состояния'], rows: blocks.map((b, i) => [`K${i}`, b.join(', ')]) }], keyStep: true });
    return { algorithm: 'equivalence-unionfind', title: 'Проверка эквивалентности (Union-Find)', baseAutomaton: copyAutomaton(inputA), steps, result: { success: true, message: 'Автоматы эквивалентны.' } };
  }
  return { algorithm: 'equivalence-unionfind', title: 'Проверка эквивалентности (Union-Find)', baseAutomaton: copyAutomaton(inputA), steps, result: { success: false, message: 'Автоматы не эквивалентны.' } };
}
