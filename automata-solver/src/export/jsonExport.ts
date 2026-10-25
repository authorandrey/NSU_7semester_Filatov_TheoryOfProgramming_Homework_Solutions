export interface ProjectSnapshot { version: 1; automata: { A: unknown; B: unknown }; trace: unknown; stepIndex: number; }
export function exportProjectJson(project: ProjectSnapshot): string { return JSON.stringify(project, null, 2); }
export function download(filename: string, content: string | Blob, mime = 'application/json'): void {
  const blob = typeof content === 'string' ? new Blob([content], { type: mime }) : content;
  const url = URL.createObjectURL(blob); const anchor = document.createElement('a');
  anchor.href = url; anchor.download = filename; anchor.click();
  window.setTimeout(() => URL.revokeObjectURL(url), 1500);
}
