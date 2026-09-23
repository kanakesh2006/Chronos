"use client";

import { useEffect, useState } from "react";

type TraceEvent = any;

export default function Dashboard() {
  const [events, setEvents] = useState<TraceEvent[]>([]);
  
  useEffect(() => {
    const ws = new WebSocket("ws://localhost:8000/ws/telemetry");
    
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        setEvents((prev) => [...prev, data]);
      } catch (err) {
        console.error("Failed to parse telemetry event", err);
      }
    };
    
    return () => {
      ws.close();
    };
  }, []);

  return (
    <main className="p-8 max-w-6xl mx-auto space-y-8 bg-zinc-50 min-h-screen">
      <h1 className="text-3xl font-bold tracking-tight text-zinc-900">Chronos Telemetry Dashboard</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <section className="bg-white p-6 rounded-xl shadow-sm border border-zinc-200">
          <h2 className="text-xl font-semibold mb-4 text-zinc-800">Live Event Timeline</h2>
          <div className="space-y-3 h-96 overflow-y-auto font-mono text-sm">
            {events.length === 0 ? (
              <p className="text-zinc-500 italic">Waiting for events...</p>
            ) : (
              events.map((e, idx) => (
                <div key={idx} className="p-3 bg-zinc-50 rounded border border-zinc-100">
                  <span className="text-blue-600 font-semibold">{e.timestamp || new Date().toISOString()}</span>
                  <pre className="mt-2 text-zinc-700 whitespace-pre-wrap">
                    {JSON.stringify(e, null, 2)}
                  </pre>
                </div>
              ))
            )}
          </div>
        </section>
        
        <section className="bg-white p-6 rounded-xl shadow-sm border border-zinc-200">
          <h2 className="text-xl font-semibold mb-4 text-zinc-800">System State</h2>
          <div className="h-96 flex items-center justify-center border-2 border-dashed border-zinc-200 rounded-lg bg-zinc-50">
            <p className="text-zinc-500">Visualization canvas ready</p>
          </div>
        </section>
      </div>
    </main>
  );
}
