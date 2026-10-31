"use client";

import { Check, Download, Link2, Linkedin, Loader2, Twitter } from "lucide-react";
import { RefObject, useState } from "react";
import { THEMES, type CardTheme } from "@/lib/themes";
import type { RoastResult } from "@/types";

interface Props {
  cardRef: RefObject<HTMLDivElement>;
  result: RoastResult;
  theme: CardTheme;
  onTheme: (t: CardTheme) => void;
}

const slug = (s: string) => s.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "") || "product";

export function tweetUrl(result: RoastResult, pageUrl: string) {
  const text = `🔥 "${result.roast_title}"\n\nMy product just got roasted by RoastScribe — survival odds: ${result.cringe_metrics.survival_probability}.\n\nGet yours:`;
  return `https://twitter.com/intent/tweet?text=${encodeURIComponent(text)}&url=${encodeURIComponent(pageUrl)}&hashtags=RoastScribe,Hacktoberfest`;
}

export default function ShareButtons({ cardRef, result, theme, onTheme }: Props) {
  const [busy, setBusy] = useState(false);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const pageUrl = typeof window === "undefined" ? "" : window.location.origin;

  async function download() {
    if (!cardRef.current) return;
    setBusy(true);
    setError(null);
    try {
      // Lazy-load so the ~library stays out of the initial bundle.
      const { toPng } = await import("html-to-image");
      const dataUrl = await toPng(cardRef.current, { pixelRatio: 2, cacheBust: true, backgroundColor: "#0B0F19" });
      const a = document.createElement("a");
      a.download = `roast-${slug(result.product_name)}.png`;
      a.href = dataUrl;
      a.click();
    } catch {
      setError("Couldn't render the PNG. Try a screenshot instead.");
    } finally {
      setBusy(false);
    }
  }

  async function copy() {
    const text = `🔥 ${result.roast_title}\n${result.the_burn.map((b, i) => `${i + 1}. ${b}`).join("\n")}\n\nSurvival odds: ${result.cringe_metrics.survival_probability}\nRoasted by RoastScribe ${pageUrl}`;
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      setError("Clipboard is blocked by the browser.");
    }
  }

  return (
    <div className="mx-auto mt-6 max-w-xl space-y-4">
      <div className="flex flex-wrap items-center gap-2" role="radiogroup" aria-label="Card theme">
        <span className="mr-1 font-mono text-xs uppercase tracking-widest text-slate-400">Theme</span>
        {THEMES.map((t) => (
          <button
            key={t.id}
            role="radio"
            aria-checked={t.id === theme.id}
            onClick={() => onTheme(t)}
            className={`flex items-center gap-2 border-2 px-3 py-1.5 text-sm font-semibold transition ${
              t.id === theme.id ? "border-flame text-white" : "border-line text-slate-400 hover:text-white"
            }`}
          >
            <span className="h-3 w-3 border border-slate-500" style={{ background: t.paper }} aria-hidden />
            {t.name}
          </button>
        ))}
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        <button onClick={download} disabled={busy} className="btn-brut sm:col-span-2">
          {busy ? <Loader2 className="h-5 w-5 animate-spin" aria-hidden /> : <Download className="h-5 w-5" aria-hidden />}
          Download Receipt
        </button>
        <a href={tweetUrl(result, pageUrl)} target="_blank" rel="noreferrer" className="btn-ghost">
          <Twitter className="h-4 w-4" aria-hidden /> Share on X
        </a>
        <a
          href={`https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(pageUrl)}`}
          target="_blank"
          rel="noreferrer"
          className="btn-ghost"
        >
          <Linkedin className="h-4 w-4" aria-hidden /> Share on LinkedIn
        </a>
        <button onClick={copy} className="btn-ghost sm:col-span-2">
          {copied ? <Check className="h-4 w-4 text-green-400" aria-hidden /> : <Link2 className="h-4 w-4" aria-hidden />}
          {copied ? "Copied!" : "Copy roast text"}
        </button>
      </div>
      {error && (
        <p role="alert" className="text-sm text-hot">
          {error}
        </p>
      )}
    </div>
  );
}
