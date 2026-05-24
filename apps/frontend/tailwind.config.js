/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        bgmain: '#050508',
        neon: {
          blue: '#00BFFF',
          cyan: '#0ff',
          amber: '#FF8C00',
          red: '#FF003C'
        },
        metallic: {
          silver: '#A8B2C0',
          steel: '#C0C8D0'
        }
      },
      fontFamily: {
        tech: ['"Share Tech Mono"', 'monospace'],
        orbitron: ['"Orbitron"', 'sans-serif']
      },
      boxShadow: {
        'neon-blue': '0 0 10px rgba(0, 191, 255, 0.5), 0 0 20px rgba(0, 191, 255, 0.3)',
        'neon-amber': '0 0 10px rgba(255, 140, 0, 0.5), 0 0 20px rgba(255, 140, 0, 0.3)',
        'neon-red': '0 0 10px rgba(255, 0, 60, 0.5), 0 0 20px rgba(255, 0, 60, 0.3)',
        'panel': 'inset 0 0 20px rgba(0, 191, 255, 0.05)',
      },
      backgroundImage: {
        'radial-gradient': 'radial-gradient(circle at center, #11111a 0%, #050508 100%)',
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-out forwards',
        'pulse-wave': 'pulseWave 2s infinite linear',
        'scanline': 'scanline 8s linear infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0', transform: 'translateY(10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        pulseWave: {
          '0%, 100%': { opacity: '0.8', filter: 'drop-shadow(0 0 2px #00BFFF)' },
          '50%': { opacity: '0.4', filter: 'drop-shadow(0 0 8px #00BFFF)' },
        },
        scanline: {
          '0%': { transform: 'translateY(-100%)' },
          '100%': { transform: 'translateY(100vh)' }
        }
      }
    },
  },
  plugins: [],
}
