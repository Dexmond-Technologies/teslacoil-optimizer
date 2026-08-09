import { useState, useEffect, useRef } from 'react';
import { Zap, AlertTriangle, Crosshair, ChevronRight, RefreshCw, Activity } from 'lucide-react';
import CoilViewer3D from './components/CoilViewer3D';
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend } from 'chart.js';
import { Line } from 'react-chartjs-2';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend);
interface OptimizationResult {
  primary_resonant_frequency_khz: number;
  secondary_resonant_frequency_khz: number;
  coupling_k: number;
  efficiency_estimate_pct: number;
  estimated_spark_length_cm: number;
  safety_profile: {
    level: string;
    warnings: string[];
  };
}

function App() {
  const [params, setParams] = useState({
    priTurns: 5.5,
    secTurns: 1200,
    capacitance: 35.0,
    voltage: 15.0,
    frequency: 120.0,
    coupling: 0.15
  });

  const [activeParam, setActiveParam] = useState<string | null>(null);
  const [mounted, setMounted] = useState(false);

  // API State
  const [results, setResults] = useState<OptimizationResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // WebSocket Telemetry State
  const [telemetry, setTelemetry] = useState<{trial: number, tuning_error: number}[]>([]);
  const [isOptimizing, setIsOptimizing] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';
  const WS_BASE = API_BASE.replace(/^http/, 'ws');

  const runLiveOptimization = () => {
    if (isOptimizing) return;
    setIsOptimizing(true);
    setTelemetry([]);

    const ws = new WebSocket(`${WS_BASE}/api/ws/optimize`);
    wsRef.current = ws;
    
    ws.onopen = () => {
      ws.send(JSON.stringify({
        power_watts: params.voltage * 1000 * 0.03, // approx DRSSTC current
        capacitance_nf: params.capacitance
      }));
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.status === 'complete') {
        setIsOptimizing(false);
        ws.close();
      } else if (data.trial !== undefined) {
        setTelemetry(prev => {
          return [...prev, { trial: data.trial, tuning_error: data.tuning_error }];
        });
      }
    };
    
    ws.onerror = (err) => {
      console.error('WebSocket Error:', err);
      setIsOptimizing(false);
    };
    
    ws.onclose = () => setIsOptimizing(false);
  };

  useEffect(() => { 
    setMounted(true); 
  }, []);

  // Real-time API query with debouncing
  useEffect(() => {
    const fetchOptimization = async () => {
      setLoading(true);
      try {
        const response = await fetch(`${API_BASE}/api/optimize`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            primary_coil: {
              turns: params.priTurns,
              wire_gauge_awg: 4,
              diameter_mm: 150,
              height_mm: 50,
              material: "Copper",
              cooling_system: "Air"
            },
            secondary_coil: {
              turns: params.secTurns,
              wire_gauge_awg: 28,
              diameter_mm: 100,
              height_mm: 500,
              material: "Copper",
              cooling_system: "Air"
            },
            top_load: {
              major_diameter_mm: 300,
              minor_diameter_mm: 100
            },
            primary_capacitor: {
              capacitance_nf: params.capacitance,
              voltage_rating_kv: params.voltage
            },
            power_source: {
              voltage_v: params.voltage * 1000,
              frequency_hz: params.frequency,
              type: "DRSSTC"
            },
            infrastructure: {
              target_distance_km: 1.0,
              phased_array_nodes: 1,
              sync_ms: 0.0
            },
            environment: {
              altitude_m: 0.0,
              humidity_pct: 50.0
            },
            frontier_mode: false
          })
        });

        if (!response.ok) {
          throw new Error('Physics engine returned error');
        }

        const data = await response.json();
        setResults(data);
        setError(null);
      } catch (err: any) {
        setError(err.message || 'Physics engine offline');
      } finally {
        setLoading(false);
      }
    };

    const delayDebounce = setTimeout(() => {
      fetchOptimization();
    }, 150);

    return () => clearTimeout(delayDebounce);
  }, [params]);

  const handleSlider = (key: string, val: number) => {
    setParams(p => ({ ...p, [key]: val }));
    setActiveParam(key);
    setTimeout(() => setActiveParam(null), 200);
  };

  const getReadoutClass = (key: string) => {
    return `font-tech text-right transition-colors duration-150 ${activeParam === key ? 'text-neon-cyan shadow-neon-blue drop-shadow-md' : 'text-metallic-silver'}`;
  };

  const getSafetyLevelColor = (level?: string) => {
    switch (level?.toLowerCase()) {
      case 'green': return 'text-emerald-400 drop-shadow-[0_0_5px_#10b981]';
      case 'yellow': return 'text-neon-amber drop-shadow-[0_0_5px_#FF8C00]';
      case 'red': return 'text-neon-red drop-shadow-[0_0_5px_#FF003C]';
      default: return 'text-metallic-silver';
    }
  };

  return (
    <div className="min-h-screen scanlines relative p-6 flex flex-col items-center">
      <div className="scanline-anim"></div>
      
      {/* Header */}
      <header className={`w-full max-w-[1400px] mb-8 flex justify-between items-center opacity-0 ${mounted ? 'animate-fade-in' : ''}`} style={{animationDelay: '0ms'}}>
        <div className="flex items-center gap-4">
          <Crosshair className="text-neon-blue w-8 h-8 animate-spin-slow" />
          <div>
            <h1 className="font-orbitron text-2xl tracking-widest text-white uppercase shadow-neon-blue">
              Tesla Coil Optimizer <span className="text-neon-blue">// DIRECT LINK</span>
            </h1>
            <p className="text-xs text-metallic-steel tracking-widest uppercase mt-1">Tactical Resonance Tuning System</p>
          </div>
        </div>
        <div className="text-right flex items-center gap-4">
          {loading && <RefreshCw className="text-neon-cyan w-4 h-4 animate-spin" />}
          <div className="text-right">
            <p className="text-xs text-metallic-silver">SYS.STATE: <span className={error ? "text-neon-red" : "text-neon-cyan"}>{error ? "OFFLINE" : "ONLINE"}</span></p>
          </div>
        </div>
      </header>

      {/* Main Grid */}
      <main className="w-full max-w-[1400px] grid grid-cols-1 lg:grid-cols-12 gap-6 h-[80vh]">
        
        {/* Zone 1: Input Controls */}
        <section className={`lg:col-span-3 glass-panel p-6 flex flex-col opacity-0 ${mounted ? 'animate-fade-in' : ''}`} style={{animationDelay: '200ms'}}>
          <h2 className="text-neon-blue font-orbitron tracking-widest text-sm mb-6 border-b border-[rgba(0,191,255,0.3)] pb-2 flex items-center gap-2">
            <ChevronRight className="w-4 h-4"/> [ COIL PARAMETERS ]
          </h2>
          
          <div className="flex flex-col gap-8 flex-grow">
            {[
              { label: 'Primary Turns', key: 'priTurns', min: 1, max: 20, step: 0.1, unit: '' },
              { label: 'Secondary Turns', key: 'secTurns', min: 100, max: 5000, step: 10, unit: '' },
              { label: 'Capacitance', key: 'capacitance', min: 1, max: 200, step: 0.5, unit: ' nF' },
              { label: 'Input Voltage', key: 'voltage', min: 1, max: 50, step: 0.1, unit: ' kV' },
              { label: 'Op. Frequency', key: 'frequency', min: 10, max: 500, step: 1, unit: ' kHz' },
              { label: 'Coupling (k)', key: 'coupling', min: 0.05, max: 0.4, step: 0.01, unit: '' }
            ].map((p) => (
              <div key={p.key} className="relative group">
                <div className="flex justify-between mb-2">
                  <span className="text-xs text-metallic-steel uppercase tracking-wider group-hover:text-white transition-colors">{p.label}</span>
                  <span className={getReadoutClass(p.key)}>
                    {params[p.key as keyof typeof params].toFixed(1)}{p.unit}
                  </span>
                </div>
                <input 
                  type="range" 
                  min={p.min} max={p.max} step={p.step}
                  value={params[p.key as keyof typeof params]}
                  onChange={(e) => handleSlider(p.key, parseFloat(e.target.value))}
                />
              </div>
            ))}
          </div>
        </section>

        {/* Zone 2: Central Visualization */}
        <section className={`lg:col-span-6 flex flex-col gap-6 opacity-0 ${mounted ? 'animate-fade-in' : ''}`} style={{animationDelay: '400ms'}}>
          
          {/* Resonance Gauge */}
          <div className="glass-panel h-1/2 flex flex-col items-center justify-center relative p-4">
            <h3 className="absolute top-4 left-4 text-xs font-orbitron text-metallic-steel tracking-widest">SECONDARY RESONANCE</h3>
            
            {/* SVG Needle Gauge */}
            <div className="relative w-64 h-32 overflow-hidden mt-8">
              <div className="w-64 h-64 border-b-0 border-4 border-dashed border-metallic-steel rounded-full relative flex items-center justify-center">
                 {/* Optimal Zone (Active when mismatch is low) */}
                 <div className="absolute top-0 left-0 w-full h-full border-4 border-neon-blue rounded-full border-b-transparent border-l-transparent transform rotate-45 opacity-50 shadow-neon-blue mix-blend-screen"></div>
                 
                 {/* Dynamic Needle */}
                 <div 
                    className="absolute w-1 h-32 bg-neon-cyan shadow-neon-blue origin-bottom transition-transform duration-500 ease-out"
                    style={{ 
                      transform: `rotate(${results ? (results.secondary_resonant_frequency_khz - 250) * 0.3 : 0}deg)`, 
                      bottom: '50%' 
                    }}
                  ></div>
              </div>
            </div>
            
            <div className="mt-4 text-3xl font-tech text-white drop-shadow-[0_0_8px_#00BFFF]">
              {results ? results.secondary_resonant_frequency_khz.toFixed(2) : "0.00"}{' '}
              <span className="text-sm text-neon-blue">kHz</span>
            </div>
          </div>

          {/* 3D Parametric Viewer */}
          <div className="glass-panel h-1/2 p-0 relative overflow-hidden">
             <CoilViewer3D priTurns={params.priTurns} secTurns={params.secTurns} />
          </div>

          {/* Status Row */}
          <div className="grid grid-cols-3 gap-4">
            <div className="glass-panel p-3 text-center">
              <p className="text-[10px] text-metallic-steel mb-1">TUNING DELTA</p>
              <p className="text-sm text-neon-cyan drop-shadow-[0_0_5px_#0ff]">
                {results ? `${Math.abs(results.primary_resonant_frequency_khz - results.secondary_resonant_frequency_khz).toFixed(2)} kHz` : "0.00 kHz"}
              </p>
            </div>
            <div className="glass-panel p-3 text-center">
              <p className="text-[10px] text-metallic-steel mb-1">EFFICIENCY</p>
              <p className="text-sm text-white">
                {results ? `${results.efficiency_estimate_pct.toFixed(1)}%` : "0.0%"}
              </p>
            </div>
            <div className="glass-panel p-3 text-center border-neon-amber shadow-neon-amber">
              <p className="text-[10px] text-metallic-steel mb-1">SAFETY PROFILE</p>
              <p className={`text-sm uppercase ${getSafetyLevelColor(results?.safety_profile.level)}`}>
                {results ? results.safety_profile.level : "UNKNOWN"}
              </p>
            </div>
          </div>

        </section>

        {/* Zone 3: Output & Warnings */}
        <section className={`lg:col-span-3 flex flex-col gap-6 opacity-0 ${mounted ? 'animate-fade-in' : ''}`} style={{animationDelay: '600ms'}}>
          
          <div className="glass-panel p-6">
            <h2 className="text-neon-blue font-orbitron tracking-widest text-sm mb-6 border-b border-[rgba(0,191,255,0.3)] pb-2 flex items-center gap-2">
              <ChevronRight className="w-4 h-4"/> [ OPTIMIZATION OUTPUT ]
            </h2>
            
            <div className="space-y-4">
              <div className="bg-[rgba(0,0,0,0.4)] p-3 border border-metallic-steel/20 rounded-sm">
                <p className="text-[10px] text-metallic-steel mb-1 uppercase">Primary Frequency</p>
                <p className="text-lg text-white">
                  {results ? `${results.primary_resonant_frequency_khz.toFixed(2)} kHz` : "0.00 kHz"}
                </p>
              </div>
              <div className="bg-[rgba(0,0,0,0.4)] p-3 border border-metallic-steel/20 rounded-sm">
                <p className="text-[10px] text-metallic-steel mb-1 uppercase">Coupling Coefficient (k)</p>
                <p className="text-lg text-white">
                  {results ? results.coupling_k.toFixed(3) : "0.000"}
                </p>
              </div>
              <div className="bg-[rgba(0,0,0,0.4)] p-3 border border-metallic-steel/20 rounded-sm">
                <p className="text-[10px] text-metallic-steel mb-1 uppercase">Est. Spark Length</p>
                <p className="text-lg text-white">
                  {results ? `${results.estimated_spark_length_cm.toFixed(1)} cm` : "0.0 cm"}
                </p>
              </div>
            </div>
          </div>

          <div className="glass-panel p-6 flex-grow border-neon-red/30 shadow-[inset_0_0_10px_rgba(255,0,60,0.1)] overflow-y-auto max-h-[300px]">
            <h2 className="text-neon-red font-orbitron tracking-widest text-sm mb-4 pb-2 flex items-center gap-2">
              <AlertTriangle className="w-4 h-4"/> [ SAFETY FLAGS ]
            </h2>
            
            <ul className="space-y-3">
              {results && results.safety_profile.warnings.length > 0 ? (
                results.safety_profile.warnings.map((warning, index) => (
                  <li key={index} className="flex items-start gap-2 text-xs text-neon-amber drop-shadow-[0_0_2px_#FF8C00]">
                    <span className="mt-0.5">■</span>
                    <span>{warning}</span>
                  </li>
                ))
              ) : (
                <li className="flex items-start gap-2 text-xs text-emerald-400 drop-shadow-[0_0_2px_#10b981]">
                  <span className="mt-0.5">■</span>
                  <span>System operates within nominal safety parameters.</span>
                </li>
              )}
              {error && (
                <li className="flex items-start gap-2 text-xs text-neon-red drop-shadow-[0_0_2px_#FF003C]">
                  <span className="mt-0.5">■</span>
                  <span>API Connection Error: {error}. Launch the Python API microservice.</span>
                </li>
              )}
            </ul>
          </div>

          <button 
            onClick={runLiveOptimization}
            disabled={isOptimizing}
            className={`w-full border-2 font-orbitron tracking-[0.2em] py-4 rounded-sm transition-all duration-300 uppercase flex justify-center items-center gap-2 ${isOptimizing ? 'bg-neon-blue text-black shadow-neon-blue border-neon-blue' : 'bg-black border-neon-blue text-neon-blue hover:bg-neon-blue hover:text-black hover:shadow-neon-blue'}`}>
            {isOptimizing ? <RefreshCw className="w-5 h-5 animate-spin" /> : <Zap className="w-5 h-5"/>}
            {isOptimizing ? 'Optimizing...' : 'Run Optimization'}
          </button>

        </section>

      </main>

      {/* Zone 4: Telemetry Chart */}
      <section className={`w-full max-w-[1400px] mt-6 glass-panel p-6 opacity-0 ${mounted ? 'animate-fade-in' : ''}`} style={{animationDelay: '800ms'}}>
        <h2 className="text-neon-cyan font-orbitron tracking-widest text-sm mb-4 border-b border-[rgba(0,255,255,0.3)] pb-2 flex items-center gap-2">
          <Activity className="w-4 h-4"/> [ GENETIC ALGORITHM CONVERGENCE ]
        </h2>
        <div className="w-full h-64 bg-[rgba(0,0,0,0.5)] rounded-sm border border-[rgba(0,191,255,0.1)] p-2">
          {telemetry.length > 0 ? (
            <Line 
              data={{
                labels: telemetry.map(t => t.trial),
                datasets: [{
                  label: 'Tuning Mismatch (kHz)',
                  data: telemetry.map(t => Math.max(1e-4, t.tuning_error)),
                  borderColor: '#0ff',
                  backgroundColor: 'rgba(0, 255, 255, 0.2)',
                  borderWidth: 2,
                  pointRadius: 1,
                  tension: 0.1
                }]
              }}
              options={{
                responsive: true,
                maintainAspectRatio: false,
                animation: { duration: 0 },
                plugins: { legend: { display: false } },
                scales: {
                  x: { display: false },
                  y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#A8B2C0' }, type: 'logarithmic' }
                }
              }}
            />
          ) : (
             <div className="w-full h-full flex items-center justify-center text-metallic-steel text-xs uppercase tracking-widest">
               Awaiting Optimization Trigger...
             </div>
          )}
        </div>
      </section>

    </div>
  );
}

export default App;
