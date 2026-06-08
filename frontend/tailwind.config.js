/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        // Monochrome luxury: warm ink/charcoal primary + champagne gold accent.
        // No more booking-blue. Reads as Aman / Ritz-Carlton / Park Hyatt.
        brand: {
          50:  "#f7f6f4",
          100: "#ebe9e4",
          200: "#d0ccc3",
          300: "#aaa498",
          400: "#787266",
          500: "#4e4a40",
          600: "#393630",
          700: "#272521",
          800: "#1a1816",
          900: "#0e0d0b",
        },
        accent: {
          DEFAULT: "#c9a96e", // champagne gold
          dark:    "#a88b56",
          light:   "#e2c79a",
        },
        ivory: {
          DEFAULT: "#faf8f4",
          50:  "#faf8f4",
          100: "#f3efe7",
        },
      },
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "-apple-system", "Segoe UI", "Roboto", "sans-serif"],
        serif: ["'Playfair Display'", "Georgia", "'Times New Roman'", "serif"],
      },
      boxShadow: {
        card:      "0 1px 2px rgba(14, 13, 11, 0.04), 0 4px 14px rgba(14, 13, 11, 0.06)",
        "card-md": "0 4px 10px rgba(14, 13, 11, 0.06), 0 14px 28px rgba(14, 13, 11, 0.09)",
        "card-lg": "0 8px 20px rgba(14, 13, 11, 0.10), 0 28px 56px rgba(14, 13, 11, 0.14)",
        glow:      "0 0 0 4px rgba(78, 74, 64, 0.18)",
        "glow-accent": "0 0 0 4px rgba(201, 169, 110, 0.30)",
      },
      borderRadius: {
        "4xl": "2rem",
      },
      keyframes: {
        "fade-in-up": {
          "0%":   { opacity: "0", transform: "translateY(16px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "fade-in": {
          "0%":   { opacity: "0" },
          "100%": { opacity: "1" },
        },
        "subtle-zoom": {
          "0%":   { transform: "scale(1)" },
          "100%": { transform: "scale(1.08)" },
        },
        "bounce-soft": {
          "0%,100%": { transform: "translateY(0)" },
          "50%":     { transform: "translateY(6px)" },
        },
      },
      animation: {
        "fade-in-up":  "fade-in-up 0.7s ease-out both",
        "fade-in":     "fade-in 0.9s ease-out both",
        "subtle-zoom": "subtle-zoom 22s ease-out both",
        "bounce-soft": "bounce-soft 2.4s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};
