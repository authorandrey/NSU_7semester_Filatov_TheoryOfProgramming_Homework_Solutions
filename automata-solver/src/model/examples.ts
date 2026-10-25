import type { Automaton } from './automaton';

function mk(
  name: string, states: string[], alphabet: string[], initial: string,
  final: string[], transitions: Array<[string, string, string]>,
  kind: Automaton['kind'] = 'DFA', epsilon: Array<[string, string]> = [],
): Automaton {
  return {
    id: `ex_${name}`, name, kind, states, alphabet, initialState: initial, finalStates: final,
    transitions: transitions.map(([from, symbol, to]) => ({ from, symbol, to })),
    epsilon: epsilon.map(([from, to]) => ({ from, to })),
  };
}

export const examples: { label: string; build: () => { A: Automaton; B?: Automaton } }[] = [
  { label: 'A0: пример автомата из лекции', build: () => ({
    A: mk('A0', ['q0', 'q1', 'q2'], ['a', 'b'], 'q0', ['q0'], [
      ['q0', 'a', 'q1'], ['q0', 'b', 'q2'], ['q1', 'a', 'q2'], ['q1', 'b', 'q0'], ['q2', 'a', 'q2'], ['q2', 'b', 'q2'],
    ]),
  }) },
  { label: 'ε-НКА: демонстрация ε-замыкания', build: () => ({
    A: mk('NFAε', ['q0', 'q1', 'q2'], ['a', 'b', 'c'], 'q0', ['q2'], [
      ['q0', 'a', 'q0'], ['q0', 'b', 'q0'], ['q1', 'a', 'q1'], ['q1', 'c', 'q1'], ['q1', 'a', 'q2'],
    ], 'NFA-EPSILON', [['q0', 'q1']]),
  }) },
  { label: 'Минимизация: 5 состояний, 3 класса (пример)', build: () => ({
    A: mk('Mini', ['s0', 's1', 's2', 's3', 's4'], ['0', '1'], 's0', ['s2', 's4'], [
      ['s0', '0', 's1'], ['s0', '1', 's2'], ['s1', '0', 's0'], ['s1', '1', 's2'],
      ['s2', '0', 's3'], ['s2', '1', 's4'], ['s3', '0', 's4'], ['s3', '1', 's3'], ['s4', '0', 's3'], ['s4', '1', 's4'],
    ]),
  }) },
  { label: 'Недостижимое состояние (пример)', build: () => ({
    A: mk('Unreach', ['p0', 'p1', 'p2', 'orphan'], ['x', 'y'], 'p0', ['p2'], [
      ['p0', 'x', 'p1'], ['p0', 'y', 'p0'], ['p1', 'x', 'p2'], ['p1', 'y', 'p1'],
      ['p2', 'x', 'p2'], ['p2', 'y', 'p2'], ['orphan', 'x', 'orphan'], ['orphan', 'y', 'orphan'],
    ]),
  }) },
  { label: 'Эквивалентные автоматы (пример)', build: () => ({
    A: mk('Eq1', ['A0', 'A1', 'A2'], ['a', 'b'], 'A0', ['A2'], [
      ['A0', 'a', 'A1'], ['A0', 'b', 'A0'], ['A1', 'a', 'A2'], ['A1', 'b', 'A1'], ['A2', 'a', 'A2'], ['A2', 'b', 'A2'],
    ]),
    B: mk('Eq2', ['B0', 'B1', 'B2'], ['a', 'b'], 'B0', ['B2'], [
      ['B0', 'a', 'B1'], ['B0', 'b', 'B0'], ['B1', 'a', 'B2'], ['B1', 'b', 'B1'], ['B2', 'a', 'B2'], ['B2', 'b', 'B2'],
    ]),
  }) },
  { label: 'Неэквивалентные автоматы (пример)', build: () => ({
    A: mk('Neq1', ['X0', 'X1'], ['a', 'b'], 'X0', ['X1'], [
      ['X0', 'a', 'X1'], ['X0', 'b', 'X0'], ['X1', 'a', 'X1'], ['X1', 'b', 'X1'],
    ]),
    B: mk('Neq2', ['Y0', 'Y1'], ['a', 'b'], 'Y0', ['Y0'], [
      ['Y0', 'a', 'Y1'], ['Y0', 'b', 'Y0'], ['Y1', 'a', 'Y0'], ['Y1', 'b', 'Y1'],
    ]),
  }) },
];
