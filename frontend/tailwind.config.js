/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js}'],
  theme: {
    extend: {
      colors: {
        msc: {
          blue:     '#1a3fa0',
          bluedark: '#122d78',
          red:      '#cc1820',
          reddark:  '#a01218',
        }
      },
      fontFamily: {
        sans: ['Segoe UI', 'system-ui', 'sans-serif']
      }
    }
  },
  plugins: []
}
