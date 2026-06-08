/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        // Editorial luxury: deep midnight navy primary + warm champagne gold accent.
        // Inspired by boutique hotel branding (Aman, Six Senses, Park Hyatt).
        brand: {
          50:  "#eef2f7",
          100: "#d6dfeb",
          200: "#aebed1",
          300: "#7d96b3",
          400: "#516f93",
          500: "#344e6c",
          600: "#243a55",
          700: "#192a3f",
          800: "#101c2c",
          900: "#080f1a",
        },
        accent: {
          DEFAULT: "#c9a96e", // champagne gold
          dark:    "#a88b56",
        },
      },
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "-apple-system", "Segoe UI", "Roboto", "sans-serif"],
        serif: ["'Playfair Display'", "Georgia", "'Times New Roman'", "serif"],
      },
      boxShadow: {
        card:      "0 1px 2px rgba(8, 15, 26, 0.05), 0 4px 14px rgba(8, 15, 26, 0.07)",
        "card-md": "0 4px 10px rgba(8, 15, 26, 0.07), 0 14px 28px rgba(8, 15, 26, 0.10)",
        "card-lg": "0 8px 20px rgba(8, 15, 26, 0.10), 0 28px 56px rgba(8, 15, 26, 0.14)",
        glow:      "0 0 0 4px rgba(52, 78, 108, 0.18)",
        "glow-accent": "0 0 0 4px rgba(201, 169, 110, 0.30)",
      },
      borderRadius: {
        "4xl": "2rem",
      },
      keyframes: {
        "fade-in-up": {
          "0%":   { opacity: "0", transform: "translateY(12px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "fade-in": {
          "0%":   { opacity: "0" },
          "100%": { opacity: "1" },
        },
        "subtle-zoom": {
          "0%":   { transform: "scale(1)" },
          "100%": { transform: "scale(1.06)" },
        },
      },
      animation: {
        "fade-in-up": "fade-in-up 0.6s ease-out both",
        "fade-in":    "fade-in 0.8s ease-out both",
        "subtle-zoom": "subtle-zoom 18s ease-out both",
      },
    },
  },
  plugins: [],
};
