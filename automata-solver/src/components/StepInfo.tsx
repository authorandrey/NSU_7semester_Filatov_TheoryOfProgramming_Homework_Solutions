import React from 'react';
import type { Step } from '../trace/types';
export function StepInfo({ step }: { step: Step | null }) {
  if (!step) return <div className="step-info empty">Алгоритм не запущен. Выберите алгоритм и нажмите «Запустить».</div>;
  return <div className="step-info">
    <div className="step-title"><span className="badge">{step.operationType}</span>{step.title}</div>
    <p>{step.explanation}</p>
    {step.currentSymbol !== undefined && <p className="mono">Символ: «{step.currentSymbol}»</p>}
    {step.currentWordPosition !== undefined && <p className="mono">Позиция во входном слове: {step.currentWordPosition}</p>}
    {!!step.highlightStates?.length && <p className="mono">Затронуты: {step.highlightStates.join(', ')}</p>}
    {!!step.conflictStates?.length && <p className="mono danger">Конфликт / разделитель: {step.conflictStates.join(', ')}</p>}
    {!!step.newStates?.length && <p className="mono success">Новые: {step.newStates.join(', ')}</p>}
    {!!step.partitions && <div className="partition-list"><strong>{step.partitions.label}:</strong>{step.partitions.blocks.map(b => <div key={b.name}><span className="partition-name">{b.name}</span> = {'{'}{b.states.join(', ')}{'}'}</div>)}</div>}
  </div>;
}
