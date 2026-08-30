# Checkpoint 4A dependency repair

Google ADK 2.8 requires Google GenAI SDK 2.19 or newer. The previous `google-genai<2`
constraint caused pip's `ResolutionImpossible` failure before Cloud Text-to-Speech could
be installed.

Apply this overlay and run:

```bash
source .venv-adk/bin/activate
python -m pip install --upgrade -r apps/api/requirements.txt
python -m pytest -q
npm --prefix apps/web run build
git restore apps/web/tsconfig.tsbuildinfo
git diff --check
```
