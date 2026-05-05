/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#EBF1F9',
          100: '#D6E3F3',
          200: '#ADC7E7',
          300: '#6593DC',
          400: '#3871DC',
          500: '#2F5EA2',
          600: '#0056D6',
          700: '#11297F',
          800: '#0E2068',
          900: '#0A1750',
          950: '#060E33',
        },
        accent: {
          50: '#FFF7EF',
          100: '#FFEAD4',
          200: '#FFD0A8',
          300: '#FFB070',
          400: '#FF8838',
          500: '#FF551D',
          600: '#FF4203',
          700: '#CC3000',
        },
        secondary: {
          50: '#F6F6F6',
          100: '#E6E6E6',
          200: '#CCCCCC',
          300: '#999999',
          400: '#808080',
          500: '#666666',
          600: '#4D4D4D',
          700: '#333333',
          800: '#1e293b',
          900: '#0f172a',
        },
        success: {
          50: '#E9F9EE',
          100: '#D1F3DD',
          500: '#0C8930',
          600: '#0A7228',
        },
        warning: {
          50: '#FFF8E0',
          100: '#FFF0C2',
          500: '#FF9900',
          600: '#D97706',
        },
        danger: {
          50: '#FEF2F2',
          100: '#FEE2E2',
          500: '#AF1D1D',
          600: '#991B1B',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-in-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'slide-down': 'slideDown 0.3s ease-out',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        slideDown: {
          '0%': { transform: 'translateY(-10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
      },
    },
  },
  plugins: [],
}
