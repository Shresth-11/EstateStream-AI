/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        masal: {
          bg: '#fbf8f3',
          card: '#ffffff',
          border: '#ede5da',
          borderLight: '#f3ece3',
          red: '#d94336',
          redHover: '#c43529',
          redLight: '#feece8',
          redText: '#b83226',
          ink: '#191512',
          inkLight: '#322d28',
          muted: '#6b635b',
          mutedLight: '#8c8278',
          sand: '#f4ede4',
          sandLight: '#f9f5ef',
        },
      },
      fontFamily: {
        sans: ['Plus Jakarta Sans', 'Outfit', 'Inter', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        'masal': '0 4px 20px -2px rgba(40, 30, 20, 0.06)',
        'masal-lg': '0 12px 30px -4px rgba(40, 30, 20, 0.08)',
        'masal-hover': '0 16px 36px -4px rgba(217, 67, 54, 0.12)',
      },
    },
  },
  plugins: [],
}
