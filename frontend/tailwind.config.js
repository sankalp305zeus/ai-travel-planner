/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        canvas: '#040914',
        surface: 'rgba(14, 23, 41, 0.6)',
        'surface-solid': '#0E1729',
        border: 'rgba(0, 229, 255, 0.15)',
        'border-strong': 'rgba(0, 229, 255, 0.4)',
        cyan: '#00E5FF',
        coral: '#FF3366',
        text: '#E8F0FF',
        muted: '#7A8BA6',
      },
      fontFamily: {
        heading: ['"Plus Jakarta Sans"', 'sans-serif'],
        body: ['Inter', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
      boxShadow: {
        'glow-cyan': '0 0 40px rgba(0, 229, 255, 0.3)',
        'glow-coral': '0 0 40px rgba(255, 51, 102, 0.4)',
      },
    },
  },
  plugins: [],
}
