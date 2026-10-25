import jsPDF from 'jspdf';
import type { Step, Trace } from '../trace/types';
export interface RenderedImage { data: string; w: number; h: number; }

function wrapText(ctx: CanvasRenderingContext2D, text: string, maxWidth: number): string[] {
  const words = text.split(/\s+/); const lines: string[] = []; let line = '';
  for (const word of words) {
    const test = line ? `${line} ${word}` : word;
    if (line && ctx.measureText(test).width > maxWidth) { lines.push(line); line = word; } else line = test;
  }
  if (line) lines.push(line); return lines;
}
function drawWrapped(ctx: CanvasRenderingContext2D, text: string, x: number, y: number, width: number, lineHeight: number): number {
  let nextY = y;
  for (const paragraph of text.split('\n')) {
    for (const line of wrapText(ctx, paragraph, width)) { ctx.fillText(line, x, nextY); nextY += lineHeight; }
    nextY += lineHeight * 0.25;
  }
  return nextY;
}
function drawStepCanvas(trace: Trace, step: Step, image?: RenderedImage, pageNo = 1): HTMLCanvasElement[] {
  // Page content is rasterised by the browser canvas so Cyrillic does not depend on jsPDF's built-in fonts.
  const width = 1485; const height = 1050; const margin = 70; const pages: HTMLCanvasElement[] = [];
  let canvas = document.createElement('canvas'); canvas.width = width; canvas.height = height;
  let ctx = canvas.getContext('2d'); if (!ctx) throw new Error('Не удалось создать canvas для PDF.');
  const fresh = (title: string) => {
    ctx!.fillStyle = '#ffffff'; ctx!.fillRect(0,0,width,height);
    ctx!.fillStyle = '#0f172a'; ctx!.font = 'bold 34px Arial, sans-serif';
    const lines = wrapText(ctx!, title, width - 2*margin); let y = 62;
    for (const line of lines) { ctx!.fillText(line, margin, y); y += 42; }
    ctx!.strokeStyle = '#cbd5e1'; ctx!.lineWidth = 2; ctx!.beginPath(); ctx!.moveTo(margin, y+6); ctx!.lineTo(width-margin, y+6); ctx!.stroke();
    ctx!.font = '18px Arial, sans-serif'; return y+35;
  };
  let y = fresh(`${trace.title} — шаг ${step.index + 1}: ${step.title}`);
  if (image && image.data) {
    // buildSolutionPdf preloads this image before rendering the page.
    const loaded = (image as RenderedImage & { loadedImage?: HTMLImageElement }).loadedImage;
    if (loaded) {
      const maxW = width - 2*margin; const maxH = 450; const scale = Math.min(maxW / loaded.naturalWidth, maxH / loaded.naturalHeight);
      const dw = loaded.naturalWidth*scale; const dh = loaded.naturalHeight*scale;
      ctx.drawImage(loaded, margin+(maxW-dw)/2, y, dw, dh); y += dh+22;
    }
  }
  ctx.fillStyle = '#0f172a'; ctx.font = '20px Arial, sans-serif';
  y = drawWrapped(ctx, step.explanation, margin, y, width-2*margin, 27) + 8;
  const tables = step.tables ?? [];
  for (const table of tables) {
    if (y > height-170) { ctx.fillStyle='#64748b'; ctx.font='16px Arial,sans-serif'; ctx.fillText(`Страница ${pageNo+pages.length}`, margin, height-25); pages.push(canvas); canvas=document.createElement('canvas');canvas.width=width;canvas.height=height;ctx=canvas.getContext('2d')!;y=fresh(`${trace.title} — продолжение шага ${step.index+1}`); }
    ctx.fillStyle = '#1d4ed8'; ctx.font = 'bold 20px Arial,sans-serif'; ctx.fillText(table.title, margin, y); y += 30;
    const colCount = Math.max(1, table.headers.length); const colWidth = (width-2*margin)/colCount;
    ctx.font='bold 14px Arial,sans-serif'; ctx.fillStyle='#e2e8f0'; ctx.fillRect(margin,y-20,width-2*margin,28); ctx.fillStyle='#0f172a';
    table.headers.forEach((h,i)=>ctx!.fillText(truncate(ctx!,h,colWidth-10),margin+i*colWidth+5,y)); y += 23;
    ctx.font='14px Arial,sans-serif';
    for (const row of table.rows) {
      if (y > height-80) { ctx.fillStyle='#64748b'; ctx.fillText(`Страница ${pageNo+pages.length}`, margin, height-25); pages.push(canvas); canvas=document.createElement('canvas');canvas.width=width;canvas.height=height;ctx=canvas.getContext('2d')!;y=fresh(`${trace.title} — таблица «${table.title}»`); }
      row.forEach((cell,i)=>{ ctx!.strokeStyle='#cbd5e1';ctx!.strokeRect(margin+i*colWidth,y-18,colWidth,25);ctx!.fillStyle='#0f172a';ctx!.fillText(truncate(ctx!,cell,colWidth-10),margin+i*colWidth+5,y); }); y+=25;
    }
    y+=18;
  }
  ctx.fillStyle='#64748b';ctx.font='14px Arial,sans-serif';ctx.fillText(`Алгоритм: ${trace.algorithm} · Страница ${pageNo+pages.length}`,margin,height-25);
  pages.push(canvas); return pages;
}
function truncate(ctx: CanvasRenderingContext2D, text: string, maxWidth: number): string {
  if (ctx.measureText(text).width <= maxWidth) return text;
  let value = text; while (value.length > 1 && ctx.measureText(value+'…').width > maxWidth) value = value.slice(0,-1); return value+'…';
}

export async function buildSolutionPdf(trace: Trace, steps: Step[], images: Record<number, RenderedImage>): Promise<jsPDF> {
  const doc = new jsPDF({ orientation: 'landscape', unit: 'mm', format: 'a4', compress: true });
  const pageCanvases: HTMLCanvasElement[] = [];
  // Preload all graph snapshots; canvas text uses a browser font to retain Russian labels.
  for (const step of steps) {
    const image = images[step.index];
    if (image?.data) {
      const img = new Image();
      await new Promise<void>((resolve) => { img.onload = () => resolve(); img.onerror = () => resolve(); img.src = image.data; });
      (image as RenderedImage & { loadedImage?: HTMLImageElement }).loadedImage = img;
    }
    pageCanvases.push(...drawStepCanvas(trace, step, image, pageCanvases.length+1));
  }
  pageCanvases.forEach((canvas, index) => {
    if (index > 0) doc.addPage('a4', 'landscape');
    doc.addImage(canvas.toDataURL('image/png'), 'PNG', 0, 0, 297, 210, undefined, 'FAST');
  });
  return doc;
}

export function loadImageSize(dataUrl: string): Promise<{ w: number; h: number }> {
  return new Promise(resolve => {
    const img = new Image();
    img.onload = () => resolve({ w: img.naturalWidth, h: img.naturalHeight });
    img.onerror = () => resolve({ w: 1200, h: 700 });
    img.src = dataUrl;
  });
}
