import React from 'react';
import type { ProductMode } from '../algorithms/product';
export type Mode = 'simulate' | 'minimize-hopcroft' | 'minimize-table' | 'product' | 'equivalence-product' | 'equivalence-unionfind' | 'determinize';
export interface AlgorithmOptions { word: string; productMode: ProductMode; complete: boolean; removeUnreachable: boolean; detail: 'marks' | 'all'; }
export interface AlgorithmPanelProps { mode: Mode; options: AlgorithmOptions; onChangeMode: (mode: Mode) => void; onChangeOptions: (options: AlgorithmOptions) => void; onRun: () => void; canRun: boolean; }
export function AlgorithmPanel(p: AlgorithmPanelProps) {
  const { mode, options } = p;
  return <div className="algo-panel">
    <h3>Алгоритм</h3>
    <select aria-label="Алгоритм" value={mode} onChange={e => p.onChangeMode(e.target.value as Mode)}>
      <option value="simulate">Симуляция слова</option><option value="minimize-hopcroft">Минимизация (Хопкрофт)</option><option value="minimize-table">Минимизация (табличный метод, дополнительный)</option><option value="product">Произведение A × B</option><option value="equivalence-product">Эквивалентность (через произведение)</option><option value="equivalence-unionfind">Эквивалентность (Union-Find)</option><option value="determinize">Детерминизация (НКА → ДКА)</option>
    </select>
    {mode === 'simulate' && <div className="row"><label>Слово:</label><input value={options.word} onChange={e => p.onChangeOptions({ ...options, word: e.target.value })} /></div>}
    {(mode === 'minimize-hopcroft' || mode === 'minimize-table') && <>
      <label className="check"><input type="checkbox" checked={options.complete} onChange={e => p.onChangeOptions({ ...options, complete: e.target.checked })} /> Дополнять неполный ДКА стоком</label>
      <label className="check"><input type="checkbox" checked={options.removeUnreachable} onChange={e => p.onChangeOptions({ ...options, removeUnreachable: e.target.checked })} /> Удалять недостижимые состояния</label>
      {mode === 'minimize-table' && <label className="check"><input type="checkbox" checked={options.detail === 'all'} onChange={e => p.onChangeOptions({ ...options, detail: e.target.checked ? 'all' : 'marks' })} /> Показывать все проверки пар</label>}
      {!options.complete && <p className="warning">Если автомат неполный, отключение стока приведёт к диагностике ошибки: алгоритм требует обработки отсутствующих переходов.</p>}
    </>}
    {mode === 'product' && <div className="row"><label>Режим:</label><select value={options.productMode} onChange={e => p.onChangeOptions({ ...options, productMode: e.target.value as ProductMode })}><option value="intersection">Пересечение</option><option value="symmetric-difference">Симметрическая разность</option><option value="union">Объединение</option></select></div>}
    {(mode === 'product' || mode === 'equivalence-product' || mode === 'equivalence-unionfind') && <p className="muted">Для этих режимов используются автоматы A и B. При разных алфавитах они приводятся к общему алфавиту с добавлением стоковых состояний.</p>}
    <button className="primary" onClick={p.onRun} disabled={!p.canRun}>Запустить</button>
  </div>;
}
