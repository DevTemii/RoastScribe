/**
 * Card themes. To add one, append an entry here — it shows up in the
 * theme switcher automatically. Keep ink/paper contrast >= 4.5:1.
 */
export interface CardTheme {
  id: string;
  name: string;
  paper: string;
  ink: string;
  muted: string;
  accent: string;
}

export const THEMES: CardTheme[] = [
  { id: "receipt", name: "Receipt", paper: "#F5F0E6", ink: "#171717", muted: "#6b6b6b", accent: "#d62d00" },
  { id: "terminal", name: "Terminal", paper: "#0a1410", ink: "#b6ffcb", muted: "#6fae85", accent: "#ff7a45" },
  { id: "crimson", name: "Crimson", paper: "#1a0b12", ink: "#ffe3ee", muted: "#c08aa0", accent: "#ff2e93" },
];
