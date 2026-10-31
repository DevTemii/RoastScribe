import { REPO_URL } from "@/lib/personas";

export default function ContributingBanner() {
  return (
    <a
      href={`${REPO_URL}/blob/main/CONTRIBUTING.md`}
      target="_blank"
      rel="noreferrer"
      className="block border-b-2 border-flame bg-flame px-4 py-2 text-center text-sm font-bold text-ink transition hover:bg-hot"
    >
      🎃 Hacktoberfest Ready — Add your own persona or parser on GitHub!
    </a>
  );
}
