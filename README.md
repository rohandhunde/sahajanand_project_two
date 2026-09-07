# Minutes — frontend for the meeting-analysis API

```
meeting-app/
├── backend.py        # your original code, byte-for-byte unchanged
├── main.py            # imports backend.app and mounts the UI onto it
├── static/
│   └── index.html      # the frontend (upload, progress, results)
├── requirements.txt
└── README.md
```

## Why two Python files

`main.py` imports the `app` object from `backend.py` and adds two things:
CORS and a route that serves `static/index.html` at `/`. That's the
"wrapping" of a frontend around your code without touching its API logic.

## One backend change: long recordings

`backend.py` now differs from your original in one place. Sarvam's
`speech_to_text.transcribe()` only accepts clips up to 30 seconds — it's
a synchronous, short-audio endpoint. Meeting recordings are almost always
longer, so that call was replaced with a `transcribe_audio()` helper that
uses Sarvam's **batch job API** instead: create a job, upload the file,
start it, poll until it's done (up to 30 minutes), then read the
transcript out of the downloaded JSON output. It supports recordings up
to an hour. Nothing else in `backend.py` changed — same request/response
shape, same route, same structured-output extraction.

Because a batch job can take a couple of minutes on longer files, the UI's
progress messages now sit on "Sarvam is transcribing your recording…" for
longer instead of implying the request is stuck.

## Setup

1. Put your `.env` in this folder with:
   ```
   SARVAM_API_KEY=...
   GROQ_API_KEY=...
   ```
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

## Run

```
uvicorn main:app --reload
```

Open **http://localhost:8000** — that's the frontend. It calls
`POST /api/meetings/upload` on the same server, so there's nothing else
to configure.

(If you ever run `uvicorn backend:app` directly instead, the API still
works exactly as before at `/api/meetings/upload` — you just won't get
the UI at `/`, since that route only exists in `main.py`.)

## What the UI does

- Drag-and-drop or browse for an audio file.
- Sends it to `/api/meetings/upload` as `multipart/form-data` under the
  `file` field, matching `UploadFile = File(...)` in your endpoint.
- Shows staged progress text (upload → transcribe → extract) while the
  single request is in flight, since fetch doesn't expose server-side
  progress.
- Renders the response: summary, decision, action items, risks/blockers,
  open questions, participants, and the full transcript (collapsible).
- Reads the response keys exactly as your endpoint returns them,
  including the existing `transctipt` and `decions` field names — no
  need to rename anything server-side for the UI to work.