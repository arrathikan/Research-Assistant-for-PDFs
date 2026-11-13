/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#FFF1EB",
          100: "#FBE4DA",
          200: "#F0C9BB",
          300: "#E78B70",
          400: "#DB6240",
          500: "#D14B24",
          600: "#C6360A",
          700: "#A82E0A",
          800: "#85270D",
          900: "#63200E",
        },
      },
    },
  },
  plugins: [],
};
