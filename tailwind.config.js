/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./Client/**/*.{html,js}"],
  theme: {
    extend: {
      colors: {
        coral: {
          300: '#FF9E99', // Soft coral for focus ring (light)
          400: '#FF8A78', // Lighter coral for hover/focus (dark)
          500: '#FF6F61', // Primary coral for buttons (light)
          600: '#F65344', // Darker coral for buttons (dark)
          700: '#E03C31', // Darkest coral for active states
        },
      },
    },
  },
  plugins: [],
}