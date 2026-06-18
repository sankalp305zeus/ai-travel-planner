/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        bg: "#0F0F0F",
        surface: "#1A1A1A",
        border: "#2A2A2A",
        accent: "#E8C547",
        "accent-2": "#4ECDC4",
        text: "#F0EDE8",
        muted: "#888580",
        success: "#5CB85C",
        warn: "#E8A547",
        error: "#E85C47",
      },
      fontFamily: {
        display: ["Playfair Display", "serif"],
        sans: ["Inter", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
    },
  },
  plugins: [],
}
