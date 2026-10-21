/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        display: ['Cal Sans', 'Inter', 'system-ui', 'sans-serif'],
      },
      colors: {
        surface: {
          DEFAULT: '#0a0a0f',
          raised: '#12121a',
          card: 'rgba(255,255,255,0.03)',
        },
        accent: {
          DEFAULT: '#6366f1',
          glow: '#818cf8',
          muted: '#4f46e5',
        },
        credible: '#22c55e',
        suspicious: '#ef4444',
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'mesh': 'radial-gradient(at 40% 20%, rgba(99,102,241,0.15) 0px, transparent 50%), radial-gradient(at 80% 0%, rgba(139,92,246,0.1) 0px, transparent 50%), radial-gradient(at 0% 50%, rgba(59,130,246,0.08) 0px, transparent 50%)',
      },
      boxShadow: {
        glow: '0 0 40px rgba(99,102,241,0.15)',
        'glow-lg': '0 0 80px rgba(99,102,241,0.2)',
        glass: '0 8px 32px rgba(0,0,0,0.37)',
      },
      animation: {
        'pulse-slow': 'pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
    },
  },
  plugins: [],
}
