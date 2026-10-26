[README_SETUP.md](https://github.com/user-attachments/files/33983908/README_SETUP.md)
# Video Employee Bot — Setup

## Files to replace

1. Replace the repository's `main.py` with the supplied `main.py`.
2. Replace `.github/workflows/auto_video.yml` with the supplied `auto_video.yml`.
3. Replace `requirements.txt` with the supplied `requirements.txt`.

## GitHub Actions secrets

Open the repository on GitHub → **Settings → Secrets and variables → Actions → New repository secret**.

Required for the best automated workflow:

- `GEMINI_API_KEY`: enables fresh scripts with varied topics, funny Urdu narration and line-specific visual queries. Without it, curated fallback scripts are used.
- `PEXELS_API_KEY`: recommended for relevant stock photos and portrait video clips. Without it, the generator tries image-search/generated-photo fallbacks and cannot fetch videos from the Pexels API.
- `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`: optional; set both to enable Telegram delivery.
- `GOOGLE_TTS_API_KEY`: optional. This must be a Google Cloud Text-to-Speech API key with the API enabled (billing may be required). When present and `TTS_PROVIDER` is `auto`, the code tries the higher-quality `ur-IN-Chirp3-HD-Charon` voice first. This is an Urdu-India voice, not a Pakistani-local voice. If it fails or is not configured, the code falls back to Microsoft's `ur-PK-AsadNeural` voice and its word-boundary timing metadata.

Do not paste API keys directly into `main.py` or commit them to the repository.

## Optional GitHub repository variables

Under **Settings → Secrets and variables → Actions → Variables**, you may set:

- `TTS_PROVIDER`: `auto`, `edge`, or `google`. Default is `auto`.
- `GOOGLE_TTS_VOICE`: default `ur-IN-Chirp3-HD-Charon`.
- `TTS_VOICE`: default `ur-PK-AsadNeural`; use `ur-PK-UzmaNeural` to try the Pakistani Urdu female voice.
- `TTS_RATE`: default `-3%` for a calmer pace.
- `TTS_PITCH`: default `-1Hz`.
- `GEMINI_MODEL`: default `gemini-3.8-flash`.

## Scheduling and downloading output

The workflow can be run manually from **Actions → Video Employee Bot → Run workflow**. It is also scheduled daily for 20:00 Pakistan time (15:00 UTC). After the job completes, open its run and download the `generated-reel-*` artifact; it contains the MP4 and a JSON manifest listing narration and visual queries for each beat.

The workflow uploads artifacts for seven days. It also saves changes to `used_topics.json` back to the repository after a successful run.

## What the code improves

- One spoken sentence per visual beat where possible; scenes split at punctuation so each beat can get a dedicated visual query.
- Pexels results stay in relevance order rather than being randomly shuffled, and the current `/v1/videos/search` endpoint is used.
- Caption parsing uses word-boundary events only, avoiding duplicate whole-sentence caption events. Captions use short groups and an Urdu-capable Nafees font installed by the workflow.
- Common English tech terms are converted to Urdu-script pronunciation hints before both TTS and caption generation.
- Optional Google Cloud TTS can improve voice quality, but its default Chirp 3 HD voice uses Urdu (India). The Pakistani Urdu Edge voice remains the free fallback.
- Every output MP4 has a same-name JSON manifest so you can inspect which narration and visual queries were used.

No automated generator can guarantee that every web search result perfectly matches a line, or that every synthetic voice sounds human. Pexels results and the resulting reel should still be reviewed; the manifest makes visual mismatches easier to identify.
