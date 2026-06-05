/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // Command Center palette: tactical greens on near-black.
        warroom: {
          bg: "#0a0e0a",
          panel: "#11160f",
          border: "#1f2b1a",
          accent: "#5ef38c",
          amber: "#ffb347",
          danger: "#ff5b5b",
          muted: "#7d8b78",
        },
      },
      fontFamily: {
        mono: ["ui-monospace", "SFMono-Regular", "Menlo", "Consolas", "monospace"],
      },
    },
  },
  plugins: [],
};
