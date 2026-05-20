import { useState, useEffect } from 'react';
import { Activity, Zap, AlertTriangle, Crosshair, ChevronRight } from 'lucide-react';

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

  // Staggered fade in
  const [mounted, setMounted] = useState(false);
  useEffect(() => { setMounted(true); }, []);

  const handleSlider = (key: string, val: number) => {
    setParams(p => ({ ...p, [key]: val }));
    setActiveParam(key);
    setTimeout(() => setActiveParam(null), 200);
  };

  const getReadoutClass = (key: string) => {
    return `font-tech text-right transition-colors duration-150 ${activeParam === key ? 'text-neon-cyan shadow-neon-blue drop-shadow-md' : 'text-metallic-silver'}`;
  };

  return (
    <div className="min-h-screen scanlines relative p-6 flex flex-col items-center">
      <div className="scanline-anim"></div>
      
      {/* Header */}
      <header className={`w-full max-w-[1400px] mb-8 flex justify-between items-center opacity-0 ${mounted ? 'animate-fade-in' : ''}`} style={{animationDelay: '0ms'}}>
        <div className="flex items-center gap-4">
          <Crosshair className="text-neon-blue w-8 h-8" />
          <div>
            <h1 className="font-orbitron text-2xl tracking-widest text-white uppercase shadow-neon-blue">
              Tesla Coil Optimizer <span className="text-neon-blue">// KRITTR</span>
            </h1>
            <p className="text-xs text-metallic-steel tracking-widest uppercase mt-1">Tactical Resonance Tuning System</p>
          </div>
        </div>
        <div className="text-right">
          <p className="text-xs text-metallic-silver">SYS.STATE: <span className="text-neon-cyan drop-shadow-[0_0_5px_#0ff]">ONLINE</span></p>
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
            <h3 className="absolute top-4 left-4 text-xs font-orbitron text-metallic-steel tracking-widest">RESONANCE TARGET</h3>
            
            {/* Fake SVG Gauge */}
            <div className="relative w-64 h-32 overflow-hidden mt-8">
              <div className="w-64 h-64 border-b-0 border-4 border-dashed border-metallic-steel rounded-full relative flex items-center justify-center">
                 {/* Optimal Zone */}
                 <div className="absolute top-0 left-0 w-full h-full border-4 border-neon-blue rounded-full border-b-transparent border-l-transparent transform rotate-45 opacity-50 shadow-neon-blue mix-blend-screen"></div>
                 
                 {/* Needle */}
                 <div 
                    className="absolute w-1 h-32 bg-neon-cyan shadow-neon-blue origin-bottom transition-transform duration-500 ease-out"
                    style={{ transform: `rotate(${(params.frequency - 250) * 0.3}deg)`, bottom: '50%' }}
                  ></div>
              </div>
            </div>
            <div className="mt-4 text-3xl font-tech text-white drop-shadow-[0_0_8px_#00BFFF]">{params.frequency.toFixed(1)} <span className="text-sm text-neon-blue">kHz</span></div>
          </div>

          {/* Waveform Display */}
          <div className="glass-panel h-1/2 p-4 relative overflow-hidden flex items-center justify-center bg-[#020204]">
             <h3 className="absolute top-4 left-4 text-xs font-orbitron text-metallic-steel tracking-widest z-10">WAVEFORM TELEMETRY</h3>
             {/* Scanlines internal to canvas */}
             <div className="absolute inset-0 bg-[linear-gradient(rgba(0,0,0,0)_50%,rgba(0,191,255,0.05)_50%)] bg-[length:100%_4px] pointer-events-none z-10"></div>
             
             {/* Simple CSS Waveform Representation */}
             <svg className="w-full h-32 animate-pulse-wave" preserveAspectRatio="none" viewBox="0 0 100 100">
                <path d="M0,50 Q12.5,0 25,50 T50,50 T75,50 T100,50" fill="none" stroke="#00BFFF" strokeWidth="1" />
                <path d="M0,50 Q12.5,100 25,50 T50,50 T75,50 T100,50" fill="none" stroke="#00BFFF" strokeWidth="0.5" strokeDasharray="2,2" opacity="0.5" />
             </svg>
          </div>

          {/* Status Row */}
          <div className="grid grid-cols-3 gap-4">
            <div className="glass-panel p-3 text-center">
              <p className="text-[10px] text-metallic-steel mb-1">TUNING STATUS</p>
              <p className="text-sm text-neon-cyan drop-shadow-[0_0_5px_#0ff]">LOCKED</p>
            </div>
            <div className="glass-panel p-3 text-center">
              <p className="text-[10px] text-metallic-steel mb-1">EFFICIENCY</p>
              <p className="text-sm text-white">92.4%</p>
            </div>
            <div className="glass-panel p-3 text-center border-neon-amber shadow-neon-amber">
              <p className="text-[10px] text-metallic-steel mb-1">ARC RISK</p>
              <p className="text-sm text-neon-amber drop-shadow-[0_0_5px_#FF8C00]">ELEVATED</p>
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
                <p className="text-[10px] text-metallic-steel mb-1 uppercase">Impedance Match</p>
                <p className="text-lg text-white">98.1%</p>
              </div>
              <div className="bg-[rgba(0,0,0,0.4)] p-3 border border-metallic-steel/20 rounded-sm">
                <p className="text-[10px] text-metallic-steel mb-1 uppercase">Transfer Efficiency</p>
                <p className="text-lg text-white">87.5%</p>
              </div>
              <div className="bg-[rgba(0,0,0,0.4)] p-3 border border-metallic-steel/20 rounded-sm">
                <p className="text-[10px] text-metallic-steel mb-1 uppercase">Rec. Duty Cycle</p>
                <p className="text-lg text-white">12.5% <span className="text-neon-blue text-xs">@ 400 BPS</span></p>
              </div>
            </div>
          </div>

          <div className="glass-panel p-6 flex-grow border-neon-red/30 shadow-[inset_0_0_10px_rgba(255,0,60,0.1)]">
            <h2 className="text-neon-red font-orbitron tracking-widest text-sm mb-4 pb-2 flex items-center gap-2">
              <AlertTriangle className="w-4 h-4"/> [ SAFETY FLAGS ]
            </h2>
            
            <ul className="space-y-3">
              <li className="flex items-start gap-2 text-xs text-neon-red drop-shadow-[0_0_2px_#FF003C]">
                <span className="mt-0.5">■</span>
                <span>CRITICAL: Primary voltage exceeds capacitor dielectric breakdown threshold.</span>
              </li>
              <li className="flex items-start gap-2 text-xs text-neon-amber drop-shadow-[0_0_2px_#FF8C00]">
                <span className="mt-0.5">■</span>
                <span>WARNING: High I²R thermal dissipation expected on secondary at specified frequency.</span>
              </li>
              <li className="flex items-start gap-2 text-xs text-metallic-silver">
                <span className="mt-0.5 text-neon-blue">■</span>
                <span>INFO: Radiative resistance models active for far-field estimation.</span>
              </li>
            </ul>
          </div>

          <button className="w-full bg-black border-2 border-neon-blue text-neon-blue font-orbitron tracking-[0.2em] py-4 rounded-sm hover:bg-neon-blue hover:text-black hover:shadow-neon-blue transition-all duration-300 uppercase flex justify-center items-center gap-2">
            <Zap className="w-5 h-5"/> Run Optimization
          </button>

        </section>

      </main>
    </div>
  );
}

export default App;
