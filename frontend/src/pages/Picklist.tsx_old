// frontend/src/pages/Picklist.tsx
import React, { useEffect, useState, useCallback } from 'react';
import {
  DragDropContext,
  Droppable,
  Draggable,
  DropResult,
  DroppableProvided,
  DraggableProvided,
} from 'react-beautiful-dnd';

/* ────────────────────────────  TYPES  ──────────────────────────── */
interface Team {
  team_number: number;
  nickname: string;
  score: number;
  reasoning: string;
  stats: Record<string, number | string>;
}
interface PriorityItem {
  id: string;
  label: string;
  category: 'universal' | 'game-specific';
}
interface FieldSelection {
  field_selections: Record<string, string>;
  manual_url: string;
  year: number;
}

/* ────────────────────  CONSTANT (universal) PRIORITIES  ──────────────────── */
const UNIVERSAL_PRIORITIES: PriorityItem[] = [
  { id: 'reliability', label: 'Reliability / Consistency', category: 'universal' },
  { id: 'driver_skill', label: 'Driver Skill',            category: 'universal' },
  { id: 'defense',      label: 'Defensive Capability',    category: 'universal' },
  { id: 'cycle_speed',  label: 'Cycle Speed',             category: 'universal' },
  { id: 'compat',       label: 'Alliance Compatibility',  category: 'universal' },
];

/* ────────────────────────────  COMPONENT  ──────────────────────────── */
const Picklist: React.FC = () => {
  /* --------  local state  -------- */
  const [datasetPath,         setDatasetPath]         = useState('');
  const [isWorlds,            setIsWorlds]            = useState(false);
  const [fieldSel,            setFieldSel]            = useState<FieldSelection | null>(null);
  const [gamePriorities,      setGamePriorities]      = useState<PriorityItem[]>([]);
  const [available,           setAvailable]           = useState<PriorityItem[]>([]);

  const [firstPriorities,  setFirstPriorities]  = useState<string[]>([]);
  const [secondPriorities, setSecondPriorities] = useState<string[]>([]);
  const [thirdPriorities,  setThirdPriorities]  = useState<string[]>([]);

  const [isGenerating,     setIsGenerating]     = useState(false);
  const [error,            setError]            = useState<string|null>(null);
  const [success,          setSuccess]          = useState<string|null>(null);
  const [tab,              setTab]              = useState<'first'|'second'|'third'>('first');

  /* --------  helper look‑ups  -------- */
  const labelOf = (id:string) =>
    (available.find(p => p.id === id)?.label) ?? id;

  const badgeOf = (id:string) => {
    const cat = available.find(p => p.id === id)?.category;
    if (cat === 'universal')      return <span className="ml-2 px-2 py-0.5 text-xs bg-blue-100 text-blue-800 rounded-full">U</span>;
    if (cat === 'game-specific')  return <span className="ml-2 px-2 py-0.5 text-xs bg-green-100 text-green-800 rounded-full">G</span>;
    return null;
  };

  /* --------  fetch field selection & dataset path once  -------- */
  useEffect(() => {
    (async () => {
      try {
        const ds = await fetch('http://localhost:8000/api/unified/status?event_key=2025arc&year=2025')
          .then(r => r.json());
        if (ds.status === 'exists') setDatasetPath(ds.path ?? '');

        const fs = await fetch('http://localhost:8000/api/schema/field-selections/2025')
          .then(r => r.json());
        if (fs.status === 'success') {
          setFieldSel(fs);
          buildGamePriorities(fs.field_selections);
        }

      } catch (e:any) {
        setError(`Failed to load initial data – ${e.message}`);
      }
    })();
  }, []);

  /* --------  derive game‑specific priorities  -------- */
  const buildGamePriorities = (fields: Record<string,string>) => {
    const result: PriorityItem[] = [];
    const pushIf = (match:string[], id:string, label:string) => {
      if (Object.keys(fields).some(f => match.some(k => f.toLowerCase().includes(k))))
        result.push({ id, label, category:'game-specific' });
    };
    pushIf(['auto'],    'auto',    'Autonomous Performance');
    pushIf(['endgame'], 'endgame', 'Endgame Performance');
    pushIf(['climb'],   'climb',   'Climbing / Hanging');
    setGamePriorities(result);
    setAvailable([...UNIVERSAL_PRIORITIES, ...result]);
  };

  /* ────────────────────────  drag‑and‑drop handlers  ──────────────────────── */
  const onDragEnd = useCallback((r:DropResult) => {
    const {source,destination,draggableId:id} = r;
    if (!destination) return;

    const addTo = (list:string[], set:(f:(p:string[])=>string[])) => {
      if (!list.includes(id)) set(p => [...p, id]);
    };
    const reorder = (list:string[], set:(x:string[])=>void) => {
      const copy = [...list];
      const [m]=copy.splice(source.index,1);
      copy.splice(destination.index,0,m);
      set(copy);
    };

    /* from pool to list */
    if (source.droppableId==='avail') {
      if (destination.droppableId==='first')  addTo(firstPriorities,  setFirstPriorities);
      if (destination.droppableId==='second') addTo(secondPriorities, setSecondPriorities);
      if (destination.droppableId==='third')  addTo(thirdPriorities,  setThirdPriorities);
      return;
    }
    /* reorder inside same list */
    if (source.droppableId===destination.droppableId) {
      if (source.droppableId==='first')  reorder(firstPriorities,  setFirstPriorities);
      if (source.droppableId==='second') reorder(secondPriorities, setSecondPriorities);
      if (source.droppableId==='third')  reorder(thirdPriorities,  setThirdPriorities);
    }
  }, [firstPriorities,secondPriorities,thirdPriorities]);

  /* ────────────────────────────────  UI  ──────────────────────────────── */
  const PriorityColumn = ({id,label,list,setList}:{id:string,label:string,list:string[],setList:React.Dispatch<React.SetStateAction<string[]>>}) => (
    <div className="mb-6">
      <h3 className="font-semibold mb-2">{label}</h3>
      <Droppable droppableId={id}>
        {(p:DroppableProvided) => (
          <div ref={p.innerRef} {...p.droppableProps}
               className="min-h-[160px] p-3 border-2 border-dashed rounded-lg space-y-2">
            {list.map((pid,idx) => (
              <Draggable key={pid} draggableId={pid} index={idx}>
                {(dp:DraggableProvided) => (
                  <div ref={dp.innerRef} {...dp.draggableProps} {...dp.dragHandleProps}
                       className="px-3 py-2 bg-white rounded shadow flex items-center justify-between">
                    <span>{idx+1}. {labelOf(pid)} {badgeOf(pid)}</span>
                    <button className="text-red-500"
                            onClick={()=>setList(prev=>prev.filter(p=>p!==pid))}>×</button>
                  </div>
                )}
              </Draggable>
            ))}
            {p.placeholder}
            {list.length===0 && <p className="text-sm text-gray-400 text-center">Drag here</p>}
          </div>
        )}
      </Droppable>
    </div>
  );

  return (
    <div className="max-w-5xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">Picklist Generator</h1>
      {error   && <div className="mb-4 p-3 bg-red-100 text-red-700 rounded">{error}</div>}
      {success && <div className="mb-4 p-3 bg-green-100 text-green-700 rounded">{success}</div>}

      {!datasetPath ? (
        <p className="text-yellow-600 bg-yellow-50 p-4 rounded border">Load or build a dataset first.</p>
      ) : (
        <DragDropContext onDragEnd={onDragEnd}>
          {/* GRID */}
          <div className="grid md:grid-cols-3 gap-6">
            {/* LEFT – available priorities */}
            <Droppable droppableId="avail">
              {(p:DroppableProvided) => (
                <div ref={p.innerRef} {...p.droppableProps} className="md:col-span-1">
                  <h2 className="font-semibold mb-2">Available Priorities</h2>
                  {available.map((prio,idx)=>(
                    <Draggable key={prio.id} draggableId={prio.id} index={idx}>
                      {(dp:DraggableProvided)=>(
                        <div ref={dp.innerRef} {...dp.draggableProps} {...dp.dragHandleProps}
                             className="px-3 py-2 mb-2 bg-white rounded border flex justify-between">
                          <span>{prio.label}</span>
                          <span className="text-xs text-gray-400 uppercase">{prio.category==='universal'?'U':'G'}</span>
                        </div>
                      )}
                    </Draggable>
                  ))}
                  {p.placeholder}
                </div>
              )}
            </Droppable>

            {/* RIGHT – pick priority columns */}
            <div className="md:col-span-2">
              <div className="flex mb-4 space-x-4">
                <button onClick={()=>setTab('first')}  className={tab==='first'  ? 'font-bold text-blue-600':'text-gray-500'}>First</button>
                <button onClick={()=>setTab('second')} className={tab==='second' ? 'font-bold text-blue-600':'text-gray-500'}>Second</button>
                {isWorlds && <button onClick={()=>setTab('third')}  className={tab==='third' ? 'font-bold text-blue-600':'text-gray-500'}>Third</button>}
              </div>

              {tab==='first'  && <PriorityColumn id="first"  label="First‑Pick Priorities"  list={firstPriorities}  setList={setFirstPriorities} />}
              {tab==='second' && <PriorityColumn id="second" label="Second‑Pick Priorities" list={secondPriorities} setList={setSecondPriorities} />}
              {tab==='third'  && isWorlds && <PriorityColumn id="third" label="Third‑Pick Priorities"  list={thirdPriorities}  setList={setThirdPriorities} />}
            </div>
          </div>
        </DragDropContext>
      )}
    </div>
  );
};

export default Picklist;
