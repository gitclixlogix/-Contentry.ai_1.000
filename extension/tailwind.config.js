/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{tsx,ts,jsx,js}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#F9F5FF',
          100: '#F4EBFF',
          200: '#E9D7FE',
          300: '#D6BBFB',
          400: '#B692F6',
          500: '#6941C6',
          600: '#7F56D9',
          700: '#6941C6',
          800: '#53389E',
          900: '#42307D',
        },
        dark: {
          text: '#101828',
          secondary: '#344054',
          tertiary: '#667085',
        }
      },
      fontFamily: {
        inter: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
