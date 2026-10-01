/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        brand: { DEFAULT: "#25D366", dark: "#128C7E" },
        surface: { DEFAULT: "#18181b", raised: "#1f1f23", border: "#2d2d32" },
      },
    },
  },
  plugins: [],
};
