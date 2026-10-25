import React from 'react';
export interface StepControlsProps {
  index: number; total: number; playing: boolean; busy?: boolean;
  onChange: (index: number) => void; onPlayToggle: () => void; onReset: () => void;
  onExportPdf: () => void; onExportPdfFull: () => void; onExportJson: () => void; onExportAutomatonJson: () => void; onExportSvg: () => void; onExportPng: () => void;
}
export function StepControls(p: StepControlsProps) {
  const max = Math.max(0, p.total - 1); const disabled = !p.total || !!p.busy;
  return <div className="step-controls">
    <button title="К началу" onClick={() => p.onChange(0)} disabled={disabled}>⏮</button>
    <button title="Предыдущий шаг" onClick={() => p.onChange(Math.max(0, p.index - 1))} disabled={disabled || p.index === 0}>◀</button>
    <button title="Автовоспроизведение / пауза" onClick={p.onPlayToggle} disabled={disabled}>{p.playing ? '⏸' : '▶'}</button>
    <button title="Следующий шаг" onClick={() => p.onChange(Math.min(max, p.index + 1))} disabled={disabled || p.index >= max}>▶</button>
    <button title="К концу" onClick={() => p.onChange(max)} disabled={disabled}>⏭</button>
    <span className="step-counter">Шаг {p.total ? p.index + 1 : 0} / {p.total}</span><span className="spacer" />
    <button onClick={p.onReset} disabled={p.busy}>Сброс</button><button onClick={p.onExportPdf} disabled={disabled}>PDF кратко</button><button onClick={p.onExportPdfFull} disabled={disabled}>PDF все шаги</button><button onClick={p.onExportSvg} disabled={disabled}>SVG</button><button onClick={p.onExportPng} disabled={disabled}>PNG</button><button onClick={p.onExportJson}>JSON проекта</button><button onClick={p.onExportAutomatonJson}>JSON автомата</button>
  </div>;
}
