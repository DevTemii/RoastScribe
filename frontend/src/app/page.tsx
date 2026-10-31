"use client";

import { AnimatePresence, motion } from "framer-motion";
import { Flame, Loader2 } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import ContributingBanner from "@/components/ContributingBanner";
import InputZone, { InputValue, validateInput } from "@/components/InputZone";
import Navbar from "@/components/Navbar";
import PersonaPicker from "@/components/PersonaPicker";
import RoastCard from "@/components/RoastCard";
import { createRoast, fetchPersonas } from "@/lib/api";
import ShareButtons from "@/components/ShareButtons";
import { FALLBACK_PERSONAS } from "@/lib/personas";
import { THEMES, type CardTheme } from "@/lib/themes";
import type { Persona, RoastResult, SpiceLevel } from "@/types";

const LOADING_LINES = [
  "Preheating the roaster…",
  "Reading your pitch so you don't have to…",
  "Counting buzzwords…",
  "Searching for a moat…",
  "Drafting the rescue plan…",
];

export default function Home() {
  const [input, setInput] = useState<InputValue>({ type: "idea", content: "" });
  const [personas, setPersonas] = useState<Persona[]>(FALLBACK_PERSONAS);
  const [persona, setPersona] = useState("cynical_vc");
  const [spice, setSpice] = useState<SpiceLevel>(2);
  const [loading, setLoading] = useState(false);
  const [lineIdx, setLineIdx] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<RoastResult | null>(null);
  const [theme, setTheme] = useState<CardTheme>(THEMES[0]);
  const resultRef = useRef<HTMLDivElement>(null);
  const cardRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchPersonas()
      .then((p) => p.length && setPersonas(p))
      .catch(() => undefined); // keep fallback list; the roast call surfaces the real error
  }, []);

  useEffect(() => {
    if (!loading) return;
    const t = setInterval(() => setLineIdx((i) => (i + 1) % LOADING_LINES.length), 1600);
    return () => clearInterval(t);
  }, [loading]);

  const active = useMemo(() => personas.find((p) => p.id === persona), [personas, persona]);
  const validation = validateInput(input);

  async function submit() {
    if (validation || loading) return;
    setError(null);
    setLoading(true);
    setLineIdx(0);
    try {
      const r = await createRoast({ input_type: input.type, content: input.content.trim(), persona, spice_level: spice });
      setResult(r);
      setTimeout(() => resultRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }), 100);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <ContributingBanner />
      <Navbar />
      <main className="mx-auto max-w-3xl px-5 pb-24 pt-12 sm:pt-16">
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="mb-10 text-center">
          <p className="mb-3 inline-block border border-flame px-2 py-1 font-mono text-xs uppercase tracking-widest text-flame">
            local-first · open source · Gemma 2
          </p>
          <h1 className="text-4xl font-bold leading-[1.05] tracking-tight sm:text-6xl">
            Get your product <span className="text-flame">roasted</span>.
            <br />
            Then get it <span className="text-hot">rescued</span>.
          </h1>
          <p className="mx-auto mt-4 max-w-xl text-slate-400">
            Drop an idea, a repo, a site or a screenshot. Receive a savage roast and a genuinely useful rescue plan on a
            shareable receipt.
          </p>
        </motion.div>

        <div className="space-y-8">
          <InputZone value={input} onChange={setInput} disabled={loading} />
          <PersonaPicker
            personas={personas}
            persona={persona}
            onPersona={setPersona}
            spice={spice}
            onSpice={setSpice}
            disabled={loading}
          />

          <div>
            <button onClick={submit} disabled={!!validation || loading} className="btn-brut w-full text-lg">
              {loading ? (
                <>
                  <Loader2 className="h-5 w-5 animate-spin" aria-hidden /> {LOADING_LINES[lineIdx]}
                </>
              ) : (
                <>
                  <Flame className="h-5 w-5" aria-hidden /> Roast me{active ? ` with ${active.name}` : ""}
                </>
              )}
            </button>
            <p className="mt-2 min-h-5 text-center text-sm" aria-live="polite">
              {error ? (
                <span role="alert" className="text-hot">
                  {error}
                </span>
              ) : input.content && validation ? (
                <span className="text-slate-500">{validation}</span>
              ) : null}
            </p>
          </div>
        </div>

        <AnimatePresence>
          {result && (
            <motion.section
              ref={resultRef}
              key={result.roast_title}
              initial={{ opacity: 0, y: 30, rotate: -1 }}
              animate={{ opacity: 1, y: 0, rotate: 0 }}
              className="mt-16 scroll-mt-6"
              aria-label="Your roast receipt"
            >
              <RoastCard
                ref={cardRef}
                result={result}
                personaName={active?.name}
                personaEmoji={active?.emoji}
                theme={theme}
              />
              <ShareButtons cardRef={cardRef} result={result} theme={theme} onTheme={setTheme} />
            </motion.section>
          )}
        </AnimatePresence>
      </main>
    </>
  );
}
