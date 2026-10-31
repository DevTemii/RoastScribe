"use client";

import { Globe, Github, ImageIcon, Lightbulb, Loader2, UploadCloud, CheckCircle2 } from "lucide-react";
import { useRef, useState } from "react";
import type { InputType } from "@/types";

const TABS: { id: InputType; label: string; icon: typeof Globe }[] = [
  { id: "idea", label: "The Idea", icon: Lightbulb },
  { id: "github", label: "GitHub Repo", icon: Github },
  { id: "url", label: "Live Website", icon: Globe },
  { id: "image", label: "Screenshot", icon: ImageIcon },
];

const REPO_RE = /^(https?:\/\/(www\.)?github\.com\/)?[\w.-]+\/[\w.-]+?(\.git)?\/?$/;
const MAX_IMAGE_MB = 5;

export interface InputValue {
  type: InputType;
  content: string;
}

interface Props {
  value: InputValue;
  onChange: (v: InputValue) => void;
  disabled?: boolean;
}

/** Returns an error message, or null when the current input is submittable. */
export function validateInput({ type, content }: InputValue): string | null {
  const c = content.trim();
  if (!c) return "Give me something to roast.";
  if (type === "idea" && c.length < 15) return "A bit more, please — at least a sentence.";
  if (type === "github" && !REPO_RE.test(c)) return "Use owner/repo or a github.com URL.";
  if (type === "url" && !/^(https?:\/\/)?[\w-]+(\.[\w-]+)+/.test(c)) return "That doesn't look like a URL.";
  return null;
}

export default function InputZone({ value, onChange, disabled }: Props) {
  const [drag, setDrag] = useState(false);
  const [fileName, setFileName] = useState<string | null>(null);
  const [fileError, setFileError] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const switchTab = (type: InputType) => {
    setFileError(null);
    setFileName(null);
    onChange({ type, content: "" });
  };

  const readFile = (file: File | undefined) => {
    if (!file) return;
    setFileError(null);
    if (!/^image\/(png|jpe?g|webp)$/.test(file.type)) return setFileError("PNG, JPG or WebP only.");
    if (file.size > MAX_IMAGE_MB * 1024 * 1024) return setFileError(`Max ${MAX_IMAGE_MB}MB.`);
    const reader = new FileReader();
    reader.onload = () => {
      setFileName(file.name);
      onChange({ type: "image", content: String(reader.result) });
    };
    reader.readAsDataURL(file);
  };

  const githubOk = value.type === "github" && REPO_RE.test(value.content.trim());

  return (
    <section aria-label="What should we roast?" className="border-2 border-line bg-panel/60">
      <div role="tablist" aria-label="Input type" className="grid grid-cols-2 border-b-2 border-line sm:grid-cols-4">
        {TABS.map(({ id, label, icon: Icon }) => {
          const active = value.type === id;
          return (
            <button
              key={id}
              role="tab"
              id={`tab-${id}`}
              aria-selected={active}
              aria-controls="input-panel"
              disabled={disabled}
              onClick={() => switchTab(id)}
              className={`flex items-center justify-center gap-2 px-3 py-3.5 text-sm font-bold transition ${
                active ? "bg-flame text-ink" : "text-slate-400 hover:bg-line hover:text-white"
              }`}
            >
              <Icon className="h-4 w-4" aria-hidden /> {label}
            </button>
          );
        })}
      </div>

      <div id="input-panel" role="tabpanel" aria-labelledby={`tab-${value.type}`} className="p-4 sm:p-5">
        {value.type === "idea" && (
          <>
            <label htmlFor="idea" className="mb-2 block font-mono text-xs uppercase tracking-widest text-slate-400">
              Your elevator pitch
            </label>
            <textarea
              id="idea"
              rows={5}
              maxLength={4000}
              disabled={disabled}
              value={value.content}
              onChange={(e) => onChange({ type: "idea", content: e.target.value })}
              placeholder="Uber for dog walking, but with AI-native blockchain synergy…"
              className="field resize-y"
            />
            <p className="mt-1 text-right font-mono text-xs text-slate-500">{value.content.length}/4000</p>
          </>
        )}

        {value.type === "github" && (
          <>
            <label htmlFor="repo" className="mb-2 block font-mono text-xs uppercase tracking-widest text-slate-400">
              Public repository
            </label>
            <input
              id="repo"
              disabled={disabled}
              value={value.content}
              onChange={(e) => onChange({ type: "github", content: e.target.value })}
              placeholder="owner/repo or https://github.com/owner/repo"
              className="field font-mono"
              spellCheck={false}
            />
            <p className="mt-2 flex items-center gap-2 font-mono text-xs text-slate-400" aria-live="polite">
              {githubOk ? (
                <>
                  <CheckCircle2 className="h-4 w-4 text-green-400" aria-hidden /> Valid repo — we&apos;ll auto-fetch the
                  README, dependencies and recent commits.
                </>
              ) : value.content ? (
                <>
                  <Loader2 className="h-4 w-4" aria-hidden /> Waiting for a valid owner/repo…
                </>
              ) : (
                "We read the README, package.json / requirements.txt and commit messages."
              )}
            </p>
          </>
        )}

        {value.type === "url" && (
          <>
            <label htmlFor="url" className="mb-2 block font-mono text-xs uppercase tracking-widest text-slate-400">
              Website URL
            </label>
            <input
              id="url"
              type="text"
              inputMode="url"
              disabled={disabled}
              value={value.content}
              onChange={(e) => onChange({ type: "url", content: e.target.value })}
              placeholder="https://your-startup.com"
              className="field font-mono"
              spellCheck={false}
            />
            <p className="mt-2 font-mono text-xs text-slate-500">
              We scrape the title, hero headline and CTAs. Public sites only.
            </p>
          </>
        )}

        {value.type === "image" && (
          <>
            <div
              onDragOver={(e) => {
                e.preventDefault();
                setDrag(true);
              }}
              onDragLeave={() => setDrag(false)}
              onDrop={(e) => {
                e.preventDefault();
                setDrag(false);
                readFile(e.dataTransfer.files[0]);
              }}
              onClick={() => fileRef.current?.click()}
              onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && fileRef.current?.click()}
              role="button"
              tabIndex={0}
              aria-label="Upload a screenshot"
              className={`flex min-h-48 cursor-pointer flex-col items-center justify-center gap-3 border-2 border-dashed p-6 text-center transition ${
                drag ? "border-hot bg-hot/10" : "border-line hover:border-flame"
              }`}
            >
              {value.content ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img src={value.content} alt="Screenshot preview" className="max-h-56 border-2 border-line" />
              ) : (
                <UploadCloud className="h-10 w-10 text-flame" aria-hidden />
              )}
              <p className="text-sm text-slate-300">
                {fileName ?? "Drag & drop a PNG, JPG or WebP — or click to browse"}
              </p>
            </div>
            <input
              ref={fileRef}
              type="file"
              accept="image/png,image/jpeg,image/webp"
              className="sr-only"
              onChange={(e) => readFile(e.target.files?.[0])}
            />
            {fileError && (
              <p role="alert" className="mt-2 text-sm text-hot">
                {fileError}
              </p>
            )}
          </>
        )}
      </div>
    </section>
  );
}
