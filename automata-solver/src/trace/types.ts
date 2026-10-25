import type { Automaton } from '../model/automaton';

export interface TransitionRef { from: string; symbol: string; to: string; }
export interface TableData { title: string; headers: string[]; rows: string[][]; highlighted?: Array<[number, number]>; }
export interface PartitionBlockView { name: string; states: string[]; }
export interface PartitionView { label: string; blocks: PartitionBlockView[]; }
export interface SideGraphSpec { title: string; automaton: Automaton; highlightStates: string[]; }

export interface Step {
  index: number;
  title: string;
  explanation: string;
  operationType: string;
  automaton: Automaton;
  highlightStates?: string[];
  highlightTransitions?: TransitionRef[];
  conflictStates?: string[];
  newStates?: string[];
  partitions?: PartitionView;
  currentSymbol?: string;
  currentWordPosition?: number;
  tables?: TableData[];
  sideGraphs?: SideGraphSpec[];
  result?: string;
  keyStep?: boolean;
}

export interface TraceResult { success: boolean; message: string; automaton?: Automaton; distinguishingWord?: string; }
export interface Trace { algorithm: string; title: string; baseAutomaton: Automaton; steps: Step[]; result: TraceResult; }
