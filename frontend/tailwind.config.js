/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        // Booking.com-inspired palette: deep navy primary + warm coral accent.
        brand: {
          50:  "#eef4fb",
          100: "#d4e3f5",
          200: "#aac6e8",
          300: "#7fa9da",
          400: "#558ccd",
          500: "#2c6fc0",
          600: "#21589a",
          700: "#194374",
          800: "#102d4e",
          900: "#081830",
        },
        accent: {
          DEFAULT: "#ff5a5f", // Airbnb coral
          dark:    "#e74950",
        },
      },
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "-apple-system", "Segoe UI", "Roboto", "sans-serif"],
      },
      boxShadow: {
        card: "0 1px 3px rgba(0,0,0,0.04), 0 4px 12px rgba(0,0,0,0.06)",
      },
    },
  },
  plugins: [],
};
