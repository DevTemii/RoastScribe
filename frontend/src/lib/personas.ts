import type { Persona } from "@/types";

/** Shown if the backend is unreachable so the UI still renders. */
export const FALLBACK_PERSONAS: Persona[] = [
  { id: "cynical_vc", name: "The Cynical VC", emoji: "💸", tagline: "Has seen 4,000 decks. Funded 3. Regrets 2.", catchphrases: [] },
  { id: "gordon_ramsay", name: "Chef Gordon", emoji: "🍳", tagline: "This landing page is so raw it's still mooing.", catchphrases: [] },
  { id: "senior_architect", name: "The Senior Architect", emoji: "🏗️", tagline: "Has an opinion about your folder structure. It's negative.", catchphrases: [] },
  { id: "gen_z_founder", name: "The Gen Z Founder", emoji: "💅", tagline: "Shipped three apps before lunch. All of them mid.", catchphrases: [] },
  { id: "nigerian_chef", name: "Chef Tunde", emoji: "🍲", tagline: "This startup’s flavor is as flat as pap without palm oil.", catchphrases: [] }
];

export const REPO_URL = process.env.NEXT_PUBLIC_REPO_URL ?? "https://github.com/your-org/roast-my-product";
