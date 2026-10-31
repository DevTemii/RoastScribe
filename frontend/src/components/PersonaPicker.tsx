"use client";

import type { Persona, SpiceLevel } from "@/types";

interface Props {
  personas: Persona[];
  persona: string;
  onPersona: (id: string) => void;
  spice: SpiceLevel;
  onSpice: (s: SpiceLevel) => void;
  disabled?: boolean;
}

const SPICES: { level: SpiceLevel; label: string }[] = [
  { level: 1, label: "Mild" },
  { level: 2, label: "Medium" },
  { level: 3, label: "Inferno" },
];

export default function PersonaPicker({ personas, persona, onPersona, spice, onSpice, disabled }: Props) {
  return (
    <div className="space-y-6">
      <fieldset disabled={disabled}>
        <legend className="mb-3 font-mono text-xs uppercase tracking-widest text-slate-400">Pick your roaster</legend>
        <div className="grid gap-3 sm:grid-cols-2">
          {personas.map((p) => {
            const active = p.id === persona;
            return (
              <label
                key={p.id}
                className={`flex cursor-pointer gap-3 border-2 p-4 transition has-[:focus-visible]:outline has-[:focus-visible]:outline-2 has-[:focus-visible]:outline-hot ${
                  active ? "border-flame bg-flame/10 shadow-brut" : "border-line bg-panel/60 hover:border-slate-500"
                }`}
              >
                <input
                  type="radio"
                  name="persona"
                  value={p.id}
                  checked={active}
                  onChange={() => onPersona(p.id)}
                  className="sr-only"
                />
                <span className="text-3xl" aria-hidden>
                  {p.emoji}
                </span>
                <span>
                  <span className="block font-bold">{p.name}</span>
                  <span className="block text-sm text-slate-400">{p.tagline}</span>
                </span>
              </label>
            );
          })}
        </div>
      </fieldset>

      <fieldset disabled={disabled}>
        <legend className="mb-3 font-mono text-xs uppercase tracking-widest text-slate-400">Spice level</legend>
        <div className="grid grid-cols-3 gap-3">
          {SPICES.map(({ level, label }) => {
            const active = spice === level;
            return (
              <label
                key={level}
                className={`cursor-pointer border-2 px-3 py-3 text-center text-sm font-bold transition has-[:focus-visible]:outline has-[:focus-visible]:outline-2 has-[:focus-visible]:outline-hot ${
                  active ? "border-hot bg-hot/10 text-white shadow-brut-hot" : "border-line bg-panel/60 text-slate-400 hover:text-white"
                }`}
              >
                <input
                  type="radio"
                  name="spice"
                  checked={active}
                  onChange={() => onSpice(level)}
                  className="sr-only"
                />
                <span aria-hidden>{"🌶️".repeat(level)}</span> {label}
              </label>
            );
          })}
        </div>
      </fieldset>
    </div>
  );
}
