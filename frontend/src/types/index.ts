export type InputType = "idea" | "github" | "url" | "image";
export type SpiceLevel = 1 | 2 | 3;

export interface Persona {
  id: string;
  name: string;
  emoji: string;
  tagline: string;
  catchphrases: string[];
}

export interface RoastRequest {
  input_type: InputType;
  content: string;
  persona: string;
  spice_level: SpiceLevel;
}

export interface RoastResult {
  product_name: string;
  one_line_summary: string;
  roast_title: string;
  the_burn: string[];
  cringe_metrics: {
    buzzword_score: string;
    buzzwords_found: string[];
    uniqueness_rating: string;
    survival_probability: string;
  };
  the_rescue: {
    fatal_flaw: string;
    who_might_actually_pay: string;
    the_pivot: string;
  };
  engine: "gemma" | "mock";
  persona: string | null;
}
