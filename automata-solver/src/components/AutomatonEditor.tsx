import React, { useEffect, useState } from 'react';
import type { Automaton } from '../model/automaton';
import { getTargets, validateAutomaton } from '../model/automaton';
import { parseAutomaton, serializeAutomaton } from '../model/parse';

export interface AutomatonEditorProps { automaton: Automaton; onChange: (a: Automaton) => void; }
export function AutomatonEditor({ automaton, onChange }: AutomatonEditorProps) {
  const [tab, setTab] = useState<'table' | 'text' | 'json'>('table');
  const [textDraft, setTextDraft] = useState(() => serializeAutomaton(automaton));
  const [jsonDraft, setJsonDraft] = useState(() => JSON.stringify(automaton, null, 2));
  const [alphabetDraft, setAlphabetDraft] = useState(() => automaton.alphabet.join(' '));
  const [errors, setErrors] = useState<string[]>([]);
  useEffect(() => { setTextDraft(serializeAutomaton(automaton)); setJsonDraft(JSON.stringify(automaton, null, 2)); setAlphabetDraft(automaton.alphabet.join(' ')); }, [automaton]);
  const change = (next: Automaton) => { onChange(next); setErrors([]); };

  const setCell = (state: string, symbol: string, raw: string) => {
    const targets = raw.split(',').map(s => s.trim()).filter(Boolean);
    const states = [...automaton.states];
    for (const target of targets) if (!states.includes(target)) states.push(target);
    const transitions = automaton.transitions.filter(t => !(t.from === state && t.symbol === symbol));
    transitions.push(...targets.map(to => ({ from: state, symbol, to })));
    const isNondeterministic = transitions.some((t, i) => transitions.some((u, j) => j !== i && u.from === t.from && u.symbol === t.symbol));
    change({ ...automaton, states, transitions, kind: automaton.epsilon.length ? 'NFA-EPSILON' : isNondeterministic ? 'NFA' : 'DFA' });
  };
  const addState = () => {
    let i = automaton.states.length; let name = `q${i}`;
    while (automaton.states.includes(name)) name = `q${++i}`;
    change({ ...automaton, states: [...automaton.states, name], initialState: automaton.initialState || name });
  };
  const removeState = (s: string) => change({ ...automaton, states: automaton.states.filter(x => x !== s), finalStates: automaton.finalStates.filter(x => x !== s), initialState: automaton.initialState === s ? (automaton.states.find(x => x !== s) ?? '') : automaton.initialState, transitions: automaton.transitions.filter(t => t.from !== s && t.to !== s), epsilon: automaton.epsilon.filter(e => e.from !== s && e.to !== s) });
  const setAlphabet = (raw: string) => {
    const alphabet = raw.split(/[\s,]+/).filter(Boolean);
    change({ ...automaton, alphabet, transitions: automaton.transitions.filter(t => alphabet.includes(t.symbol)) });
  };
  const applyText = () => { const r = parseAutomaton(textDraft, automaton.name); if (r.errors.length) { setErrors(r.errors); return; } change({ ...r.automaton!, id: automaton.id }); };
  const applyJson = () => {
    try {
      const value = JSON.parse(jsonDraft) as Automaton;
      const normalized = { ...value, id: automaton.id };
      const e = validateAutomaton(normalized);
      if (e.length) { setErrors(e); return; }
      change(normalized);
    } catch (error) { setErrors([`JSON: ${error instanceof Error ? error.message : String(error)}`]); }
  };

  return <div className="editor">
    <div className="tabs"><button className={tab === 'table' ? 'active' : ''} onClick={() => setTab('table')}>Таблица</button><button className={tab === 'text' ? 'active' : ''} onClick={() => setTab('text')}>Текст</button><button className={tab === 'json' ? 'active' : ''} onClick={() => setTab('json')}>JSON</button></div>
    {tab === 'table' && <>
      <div className="row alphabet-row"><label>Алфавит:</label><input value={alphabetDraft} onChange={e => setAlphabetDraft(e.target.value)} /><button onClick={() => setAlphabet(alphabetDraft)} title="Применить новый алфавит">OK</button></div>
      <div className="row"><label>Имя:</label><input value={automaton.name} onChange={e => change({ ...automaton, name: e.target.value })} /></div>
      <div className="row"><button onClick={addState}>+ состояние</button><span className="muted">Для НКА несколько целей через запятую.</span></div>
      <div className="table-scroll"><table className="automaton-table"><thead><tr><th>Состояние</th><th>q₀</th><th>F</th>{automaton.alphabet.map(c => <th key={c}>{c}</th>)}<th></th></tr></thead><tbody>
        {automaton.states.map(s => <tr key={s}><td>{s}</td><td><input aria-label={`Начальное ${s}`} type="radio" checked={automaton.initialState === s} onChange={() => change({ ...automaton, initialState: s })} /></td><td><input aria-label={`Заключительное ${s}`} type="checkbox" checked={automaton.finalStates.includes(s)} onChange={e => change({ ...automaton, finalStates: e.target.checked ? [...automaton.finalStates, s] : automaton.finalStates.filter(x => x !== s) })} /></td>{automaton.alphabet.map(c => <td key={c}><input aria-label={`${s}, ${c}`} value={getTargets(automaton, s, c).join(',')} onChange={e => setCell(s, c, e.target.value)} /></td>)}<td><button title={`Удалить ${s}`} onClick={() => removeState(s)}>×</button></td></tr>)}
      </tbody></table></div>
    </>}
    {tab === 'text' && <><textarea className="mono big" value={textDraft} onChange={e => setTextDraft(e.target.value)} /><div className="row"><button onClick={applyText}>Применить текст</button></div></>}
    {tab === 'json' && <><textarea className="mono big" value={jsonDraft} onChange={e => setJsonDraft(e.target.value)} /><div className="row"><button onClick={applyJson}>Применить JSON</button></div></>}
    {errors.length > 0 && <ul className="errors">{errors.map((e, i) => <li key={i}>{e}</li>)}</ul>}
  </div>;
}
