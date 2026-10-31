import { forwardRef } from "react";
import { THEMES, type CardTheme } from "@/lib/themes";
import type { RoastResult } from "@/types";

/** Deterministic barcode: same product -> same bars. */
function Barcode({ seed }: { seed: string }) {
  let h = 2166136261;
  for (const ch of seed) h = Math.imul(h ^ ch.charCodeAt(0), 16777619) >>> 0;
  const bars: { x: number; w: number }[] = [];
  let x = 0;
  for (let i = 0; i < 48; i++) {
    h = Math.imul(h ^ (h >>> 13), 1274126177) >>> 0;
    const w = 1 + (h % 3);
    if (i % 2 === 0) bars.push({ x, w });
    x += w + 1;
  }
  return (
    <svg viewBox={`0 0 ${x} 40`} className="h-12 w-full" preserveAspectRatio="none" aria-hidden>
      {bars.map((b, i) => (
        <rect key={i} x={b.x} y={0} width={b.w} height={40} style={{ fill: "var(--c-ink)" }} />
      ))}
    </svg>
  );
}

const Dotted = () => <hr className="my-4 border-0 border-t-2 border-dotted border-[var(--c-muted)]" />;

function verdict(survival: number) {
  if (survival < 15) return { label: "DECEASED", cls: "border-red-700 text-red-700" };
  if (survival < 35) return { label: "CRITICAL", cls: "border-orange-600 text-orange-600" };
  return { label: "ON LIFE SUPPORT", cls: "border-amber-600 text-amber-700" };
}

interface Props {
  result: RoastResult;
  personaName?: string;
  personaEmoji?: string;
  theme?: CardTheme;
}

const RoastCard = forwardRef<HTMLDivElement, Props>(function RoastCard({ result, personaName, personaEmoji, theme = THEMES[0] }, ref) {
  const m = result.cringe_metrics;
  const survival = parseInt(m.survival_probability, 10) || 0;
  const v = verdict(survival);
  const receiptNo = (Math.abs([...result.product_name].reduce((a, c) => a * 31 + c.charCodeAt(0), 7)) % 900000) + 100000;
  const date = new Date().toISOString().slice(0, 10);

  return (
    <div
      ref={ref}
      className="relative mx-auto w-full max-w-xl bg-[var(--c-paper)] p-6 font-mono text-[13px] leading-relaxed text-[var(--c-ink)] sm:p-8"
      style={
        {
          "--c-paper": theme.paper,
          "--c-ink": theme.ink,
          "--c-muted": theme.muted,
          "--c-accent": theme.accent,
          boxShadow: "0 0 0 2px #FF4500",
        } as React.CSSProperties
      }
    >
      <header className="text-center">
        <p className="text-[11px] tracking-[0.3em] text-[var(--c-muted)]">ROASTSCRIBE • PRODUCT AUTOPSY</p>
        <h2 className="mt-2 text-2xl font-extrabold uppercase leading-tight tracking-tight">{result.product_name}</h2>
        <p className="mt-1 text-[var(--c-muted)]">
          {personaEmoji} {personaName ?? "Anonymous critic"}
        </p>
        <p className="mt-1 text-[11px] text-[var(--c-muted)]">
          No. {receiptNo} · {date} · engine: {result.engine}
        </p>
      </header>

      <Dotted />

      <p className="text-[11px] uppercase tracking-widest text-[var(--c-muted)]">What you actually are</p>
      <p className="font-semibold">{result.one_line_summary}</p>

      <div className="relative mt-5 border-2 border-dashed border-[var(--c-ink)] p-3 text-center">
        <p className="text-lg font-extrabold uppercase leading-snug text-[var(--c-accent)]">“{result.roast_title}”</p>
      </div>

      <Dotted />

      <p className="mb-2 text-[11px] uppercase tracking-widest text-[var(--c-muted)]">The burn</p>
      <ol className="space-y-3">
        {result.the_burn.map((b, i) => (
          <li key={i} className="flex gap-3">
            <span className="font-extrabold text-[var(--c-accent)]">{String(i + 1).padStart(2, "0")}</span>
            <span>{b}</span>
          </li>
        ))}
      </ol>

      <Dotted />

      <p className="mb-2 text-[11px] uppercase tracking-widest text-[var(--c-muted)]">Cringe metrics</p>
      <dl className="space-y-1">
        <Row k="Buzzword score" v={m.buzzword_score} />
        <Row k="Uniqueness" v={m.uniqueness_rating} />
        <Row k="Survival odds" v={m.survival_probability} />
      </dl>
      <div className="mt-2 h-3 border-2 border-[var(--c-ink)]" role="img" aria-label={`Survival probability ${survival}%`}>
        <div className="h-full bg-[var(--c-accent)]" style={{ width: `${Math.max(2, Math.min(100, survival))}%` }} />
      </div>
      {m.buzzwords_found.length > 0 && (
        <p className="mt-3 flex flex-wrap gap-1.5">
          {m.buzzwords_found.map((w) => (
            <span key={w} className="border border-[var(--c-ink)] px-1.5 py-0.5 text-[11px] uppercase">
              {w}
            </span>
          ))}
        </p>
      )}

      <div
        className={`mt-5 inline-block -rotate-6 border-4 px-3 py-1 text-lg font-extrabold tracking-widest ${v.cls}`}
        aria-label={`Verdict: ${v.label}`}
      >
        {v.label}
      </div>

      <Dotted />

      <p className="mb-2 text-[11px] uppercase tracking-widest text-[var(--c-muted)]">🛟 The rescue arc</p>
      <dl className="space-y-3">
        <Block k="Fatal flaw" v={result.the_rescue.fatal_flaw} />
        <Block k="Who might actually pay" v={result.the_rescue.who_might_actually_pay} />
        <Block k="The pivot" v={result.the_rescue.the_pivot} />
      </dl>

      <Dotted />

      <footer className="text-center">
        <Barcode seed={result.product_name + result.roast_title} />
        <p className="mt-1 text-[10px] tracking-[0.25em] text-[var(--c-muted)]">THANK YOU FOR BEING ROASTED</p>
        <p className="text-[10px] text-[var(--c-muted)]">roastscribe · open source · Hacktoberfest 🎃</p>
      </footer>
    </div>
  );
});

const Row = ({ k, v }: { k: string; v: string }) => (
  <div className="flex justify-between gap-4">
    <dt className="text-[var(--c-muted)]">{k}</dt>
    <dd className="text-right font-bold">{v}</dd>
  </div>
);

const Block = ({ k, v }: { k: string; v: string }) => (
  <div>
    <dt className="font-bold uppercase text-[var(--c-accent)]">▸ {k}</dt>
    <dd>{v}</dd>
  </div>
);

export default RoastCard;
