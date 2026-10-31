# Contributing to RoastScribe 🔥

Thanks for helping us roast responsibly! RoastScribe is built to be extended:
**personas**, **parsers**, **buzzword lists** and **card themes** are all
plugins you can add without touching the core.

Look for issues labelled `good first issue` and `hacktoberfest`.

## 1. Clone and run locally

```bash
git clone https://github.com/<you>/roast-my-product.git
cd roast-my-product
```

**Model (optional — a mock engine runs if Ollama is offline):**

```bash
ollama run gemma2:2b
```

**Backend**

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate    macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python run.py            # http://localhost:8000  (docs at /docs)
pytest -q
```

**Frontend**

```bash
cd frontend
npm install
npm run dev              # http://localhost:3000
```

## 2. Add a persona

1. Copy `backend/app/plugins/personas/cynical_vc.json` to `<your_id>.json`.
2. Fill in `id`, `name`, `emoji`, `tagline`, `voice_traits`, `catchphrases`,
   `pet_peeves`, and `mock_openers` (used by the offline mock engine).
3. The persona is auto-discovered by the backend (`GET /api/personas`) and the
   frontend picker. No code change needed.
4. Run `pytest` — `tests/test_personas.py` validates every persona file.

Guidelines: be witty and specific to tech/startups. Roast the **product**,
never the person. No slurs, no harassment.

## 3. Add a parser

1. Create `backend/app/parsers/<name>_parser.py` exposing a function that
   returns a `ParsedInput` (see `schemas/roast.py`).
2. Register it in `backend/app/parsers/__init__.py`.
3. Use `httpx` with a timeout; fail gracefully with a helpful message.
4. Add a test with mocked HTTP responses (no live network in CI).

## 4. Add buzzwords

Add a JSON file in `backend/app/plugins/buzzwords/` shaped like
`{"name": "...", "words": ["synergy", ...]}`. It is picked up automatically.

## 5. Add a card theme

Card themes live in `frontend/src/lib/themes.ts`. Add an entry with
background, ink and accent colours; it appears in the theme switcher.

## 6. Open a PR

- Branch: `feat/persona-burned-out-staff-eng`
- Commits: [Conventional Commits](https://www.conventionalcommits.org/)
  (`feat(personas): add ...`)
- Fill in the PR template and link the issue.
- Be kind. See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
