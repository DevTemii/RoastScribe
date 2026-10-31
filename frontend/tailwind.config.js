/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#0B0F19", // page background
        panel: "#111827",
        line: "#1F2937",
        flame: "#FF4500",
        hot: "#FF2E93",
        paper: "#F5F0E6", // receipt paper
      },
      fontFamily: {
        display: ["var(--font-display)", "system-ui", "sans-serif"],
        mono: ["var(--font-mono)", "ui-monospace", "monospace"],
      },
      boxShadow: {
        brut: "4px 4px 0 0 #FF4500",
        "brut-hot": "4px 4px 0 0 #FF2E93",
      },
      keyframes: {
        flicker: {
          "0%,100%": { opacity: "1" },
          "50%": { opacity: "0.82" },
        },
      },
      animation: { flicker: "flicker 2.4s ease-in-out infinite" },
    },
  },
  plugins: [],
};
