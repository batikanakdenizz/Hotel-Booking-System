/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        // Refined navy + warm coral. Slightly more saturated, less "primary blue".
        brand: {
          50:  "#eef4fc",
          100: "#d8e6f7",
          200: "#abc7ec",
          300: "#7ba6de",
          400: "#4d86d1",
          500: "#2466c5",
          600: "#1b51a3",
          700: "#143e7e",
          800: "#0d2956",
          900: "#06152e",
        },
        accent: {
          DEFAULT: "#f4485a", // deeper, more saturated coral
          dark:    "#d92d40",
        },
      },
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "-apple-system", "Segoe UI", "Roboto", "sans-serif"],
      },
      boxShadow: {
        card:      "0 1px 2px rgba(15, 23, 42, 0.04), 0 4px 12px rgba(15, 23, 42, 0.06)",
        "card-md": "0 4px 10px rgba(15, 23, 42, 0.06), 0 12px 24px rgba(15, 23, 42, 0.08)",
        "card-lg": "0 8px 16px rgba(15, 23, 42, 0.08), 0 24px 48px rgba(15, 23, 42, 0.12)",
        glow:      "0 0 0 4px rgba(36, 102, 197, 0.18)",
      },
      borderRadius: {
        "4xl": "2rem",
      },
      keyframes: {
        "fade-in-up": {
          "0%":   { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
      },
      animation: {
        "fade-in-up": "fade-in-up 0.4s ease-out both",
      },
    },
  },
  plugins: [],
};
