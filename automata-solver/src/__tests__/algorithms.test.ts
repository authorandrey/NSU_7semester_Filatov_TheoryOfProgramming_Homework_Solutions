import { describe, expect, it } from 'vitest';
import type { Automaton } from '../model/automaton';
import { accepts, isComplete, validateAutomaton } from '../model/automaton';
import { parseAutomaton, serializeAutomaton } from '../model/parse';
import { simulate } from '../algorithms/simulation';
import { minimizeHopcroft } from '../algorithms/minimization';
import { minimizeTableFilling } from '../algorithms/tableFilling';
import { buildProduct } from '../algorithms/product';
import { checkEquivalenceProduct } from '../algorithms/equivalence';
import { checkEquivalenceUnionFind } from '../algorithms/unionFindEquivalence';
import { determinize } from '../algorithms/determinize';

function mk(states: string[], alphabet: string[], initial: string, final: string[], transitions: Array<[string, string, string]>, kind: Automaton['kind'] = 'DFA', epsilon: Array<[string, string]> = []): Automaton {
  return { id: `test_${states.join('_')}`, name: 'T', states, alphabet, initialState: initial, finalStates: final, kind, transitions: transitions.map(([from,symbol,to]) => ({from,symbol,to})), epsilon: epsilon.map(([from,to]) => ({from,to})) };
}
function words(alphabet: string[], maxLen: number): string[] {
  const out = ['']; let frontier = [''];
  for (let n=1;n<=maxLen;n++) { frontier = frontier.flatMap(w => alphabet.map(c => w+c)); out.push(...frontier); }
  return out;
}
const A0 = mk(['q0','q1','q2'], ['a','b'], 'q0', ['q0'], [['q0','a','q1'],['q0','b','q2'],['q1','a','q2'],['q1','b','q0'],['q2','a','q2'],['q2','b','q2']]);
const Mini = mk(['s0','s1','s2','s3','s4'], ['0','1'], 's0', ['s2','s4'], [['s0','0','s1'],['s0','1','s2'],['s1','0','s0'],['s1','1','s2'],['s2','0','s3'],['s2','1','s4'],['s3','0','s4'],['s3','1','s3'],['s4','0','s3'],['s4','1','s4']]);
const EqA = mk(['A0','A1','A2'], ['a','b'], 'A0', ['A2'], [['A0','a','A1'],['A0','b','A0'],['A1','a','A2'],['A1','b','A1'],['A2','a','A2'],['A2','b','A2']]);
const EqB = mk(['B0','B1','B2'], ['a','b'], 'B0', ['B2'], [['B0','a','B1'],['B0','b','B0'],['B1','a','B2'],['B1','b','B1'],['B2','a','B2'],['B2','b','B2']]);

 describe('model / text parser', () => {
  it('round trips a simple automaton', () => {
    const text = serializeAutomaton(A0); const parsed = parseAutomaton(text);
    expect(parsed.errors).toEqual([]); expect(parsed.automaton?.states).toEqual(A0.states); expect(parsed.automaton?.transitions).toHaveLength(A0.transitions.length);
  });
  it('detects invalid transitions', () => {
    const bad = { ...A0, transitions: [...A0.transitions, { from:'q0', symbol:'x', to:'missing' }] };
    expect(validateAutomaton(bad).length).toBeGreaterThan(0);
  });
});

describe('simulation', () => {
  it('accepts empty word when q0 is final', () => expect(simulate(A0, '').result.success).toBe(true));
  it('accepts abab and rejects aaa', () => { expect(simulate(A0, 'abab').result.success).toBe(true); expect(simulate(A0, 'aaa').result.success).toBe(false); });
  it('rejects symbols outside the alphabet', () => expect(simulate(A0, 'ax').result.success).toBe(false));
  it('simulates epsilon-NFA closure', () => {
    const nfa = mk(['q0','q1','q2'], ['a'], 'q0', ['q2'], [['q1','a','q2']], 'NFA-EPSILON', [['q0','q1']]);
    expect(simulate(nfa, 'a').result.success).toBe(true);
  });
});

describe('Hopcroft minimization', () => {
  it('preserves language and minimizes the sample to three states', () => {
    const trace = minimizeHopcroft(Mini); const min = trace.result.automaton!;
    expect(trace.result.success).toBe(true); expect(min.states).toHaveLength(3); expect(isComplete(min)).toBe(true);
    for (const word of words(Mini.alphabet, 5)) expect(accepts(min, word)).toBe(accepts(Mini, word));
  });
  it('does not silently mishandle an incomplete DFA when completion is disabled', () => {
    const partial = mk(['s','f'], ['0','1'], 's', ['f'], [['s','0','f'],['f','0','f']]);
    const trace = minimizeHopcroft(partial, { complete: false });
    expect(trace.result.success).toBe(false);
  });
  it('removes unreachable states and preserves language', () => {
    const a = mk(['q0','q1','orphan'], ['a'], 'q0', ['q1'], [['q0','a','q1'],['q1','a','q1'],['orphan','a','orphan']]);
    const trace = minimizeHopcroft(a); expect(trace.result.automaton?.states).not.toContain('orphan');
    for (const w of words(['a'], 4)) expect(accepts(trace.result.automaton!, w)).toBe(accepts(a,w));
  });
});

describe('table-filling minimization', () => {
  it('agrees with Hopcroft on minimal state count and language', () => {
    const h = minimizeHopcroft(Mini).result.automaton!; const t = minimizeTableFilling(Mini).result.automaton!;
    expect(t.states).toHaveLength(h.states.length);
    for (const w of words(Mini.alphabet, 5)) expect(accepts(t,w)).toBe(accepts(Mini,w));
  });
});

describe('product', () => {
  const X = mk(['p0','p1'], ['a','b'], 'p0', ['p1'], [['p0','a','p1'],['p0','b','p0'],['p1','a','p1'],['p1','b','p1']]);
  const Y = mk(['r0','r1'], ['a','b'], 'r0', ['r1'], [['r0','a','r0'],['r0','b','r1'],['r1','a','r1'],['r1','b','r1']]);
  it('recognizes intersection and symmetric difference', () => {
    const inter = buildProduct(X,Y,'intersection').result.automaton!; const diff = buildProduct(X,Y,'symmetric-difference').result.automaton!;
    for (const w of words(['a','b'],5)) { expect(accepts(inter,w)).toBe(accepts(X,w)&&accepts(Y,w)); expect(accepts(diff,w)).toBe(accepts(X,w)!==accepts(Y,w)); }
  });
  it('normalizes differing alphabets and missing transitions', () => {
    const a = mk(['s','f'], ['a'], 's', ['f'], [['s','a','f'],['f','a','f']]);
    const b = mk(['t'], ['b'], 't', [], [['t','b','t']]);
    const p = buildProduct(a,b,'union').result.automaton!;
    expect(p.alphabet.sort()).toEqual(['a','b']);
    for (const w of words(['a','b'],4)) expect(accepts(p,w)).toBe(accepts(a,w)||accepts(b,w));
  });
});

describe('equivalence', () => {
  it('finds equivalent machines with different state names', () => expect(checkEquivalenceProduct(EqA,EqB).result.success).toBe(true));
  it('returns a real distinguishing word for inequivalent machines', () => {
    const A = mk(['x0','x1'],['a','b'],'x0',['x1'],[['x0','a','x1'],['x0','b','x0'],['x1','a','x1'],['x1','b','x1']]);
    const B = mk(['y0','y1'],['a','b'],'y0',['y0'],[['y0','a','y1'],['y0','b','y0'],['y1','a','y0'],['y1','b','y1']]);
    const trace = checkEquivalenceProduct(A,B); const word = trace.result.distinguishingWord;
    expect(trace.result.success).toBe(false); expect(word).toBeDefined(); expect(accepts(A,word!)).not.toBe(accepts(B,word!));
  });
  it('adds edges into already visited product pairs', () => {
    const trace = checkEquivalenceProduct(EqA, EqB); const last = trace.steps.find(s => s.operationType === 'result');
    expect(last?.automaton.transitions.length).toBeGreaterThanOrEqual(last?.automaton.states.length ?? 0);
  });
  it('Union-Find agrees with product and handles different alphabets', () => {
    expect(checkEquivalenceUnionFind(EqA,EqB).result.success).toBe(true);
    const a = mk(['s','f'], ['a'], 's', ['f'], [['s','a','f'],['f','a','f']]);
    const b = mk(['t'], ['b'], 't', [], [['t','b','t']]);
    expect(checkEquivalenceUnionFind(a,b).result.success).toBe(checkEquivalenceProduct(a,b).result.success);
  });
});

describe('determinization', () => {
  it('preserves language of an NFA and makes a complete DFA', () => {
    const nfa = mk(['n0','n1'], ['a','b'], 'n0', ['n1'], [['n0','a','n0'],['n0','a','n1'],['n0','b','n0'],['n1','a','n1'],['n1','b','n1']], 'NFA');
    const dfa = determinize(nfa).result.automaton!; expect(dfa.kind).toBe('DFA'); expect(isComplete(dfa)).toBe(true);
    for (const w of words(nfa.alphabet,5)) expect(accepts(dfa,w)).toBe(accepts(nfa,w));
  });
});
