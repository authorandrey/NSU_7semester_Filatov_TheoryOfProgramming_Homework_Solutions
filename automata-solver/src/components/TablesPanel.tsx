import React from 'react';
import type { Step } from '../trace/types';
export function TablesPanel({ step }: { step: Step | null }) {
  if (!step || !step.tables?.length) return <div className="empty tables-empty">Для этого шага таблиц нет.</div>;
  return <div className="tables">{step.tables.map((table, i) => <div key={`${table.title}-${i}`} className="table-block"><h4>{table.title}</h4><div className="table-scroll"><table><thead><tr>{table.headers.map((h, j) => <th key={j}>{h}</th>)}</tr></thead><tbody>{table.rows.map((row, ri) => <tr key={ri}>{row.map((cell, ci) => <td key={ci} className={table.highlighted?.some(([r, c]) => r === ri && c === ci) ? 'cell-hl' : ''}>{cell}</td>)}</tr>)}</tbody></table></div></div>)}</div>;
}
