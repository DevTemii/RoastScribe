import { Flame, Github } from "lucide-react";
import { REPO_URL } from "@/lib/personas";

export default function Navbar() {
  return (
    <header className="border-b-2 border-line">
      <nav className="mx-auto flex max-w-5xl items-center justify-between px-5 py-4" aria-label="Main">
        <a href="/" className="flex items-center gap-2 text-xl font-bold tracking-tight">
          <Flame className="h-6 w-6 text-flame animate-flicker" aria-hidden />
          <span>
            Roast<span className="text-flame">Scribe</span>
          </span>
        </a>
        <div className="flex items-center gap-3">
          <span className="hidden border border-line px-2 py-1 font-mono text-xs text-slate-400 sm:inline">
            powered by Gemma 2
          </span>
          <a href={REPO_URL} target="_blank" rel="noreferrer" className="btn-ghost">
            <Github className="h-4 w-4" aria-hidden /> Star on GitHub
          </a>
        </div>
      </nav>
    </header>
  );
}
