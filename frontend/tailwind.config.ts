import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        navy: { 900: "#0b1530", 800: "#0f1b3d", 700: "#16254f", 600: "#1f3166" },
        brand: { 500: "#3b82f6", 600: "#2563eb", 700: "#1d4ed8" },
      },
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "-apple-system", "Segoe UI", "Roboto", "sans-serif"],
      },
      boxShadow: { card: "0 1px 2px rgba(16,24,40,.05), 0 1px 3px rgba(16,24,40,.06)" },
    },
  },
  plugins: [],
} satisfies Config;
