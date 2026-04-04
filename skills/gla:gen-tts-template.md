# gla:gen-tts-template — Generate Voice Template

Create a reusable voice template for consistent narration across all scenes.

**IMPORTANT:** Always create a voice template BEFORE narrating scenes. Without a template, each scene generates with a slightly different voice. With a template, voice cloning ensures 100% consistency.

## Prerequisites

- OmniVoice installed: `pip install omnivoice` (Python 3.10)
- Server running: `curl http://127.0.0.1:8100/health`

## Workflow

### Step 1: Create Voice Template

```bash
curl -X POST http://127.0.0.1:8100/api/tts/templates \
  -H "Content-Type: application/json" \
  -d '{
    "name": "narrator_male_vn",
    "text": "Sample text in your target language. Make it 2-3 sentences for best results.",
    "instruct": "male, moderate pitch, young adult",
    "speed": 1.0
  }'
```

### Step 2: Listen & Verify

Open the returned `audio_path` and verify the voice matches your vision. If not, delete and recreate with different `instruct`.

### Step 3: Link to Project

```bash
curl -X PATCH http://127.0.0.1:8100/api/projects/<PID> \
  -H "Content-Type: application/json" \
  -d '{"narrator_ref_audio": "<audio_path from step 1>"}'
```

Or pass `template` name directly when narrating (recommended):
```bash
curl -X POST http://127.0.0.1:8100/api/videos/<VID>/narrate \
  -d '{"project_id": "<PID>", "template": "narrator_male_vn", "speed": 1.1}'
```

## Valid Instruct Terms

### English
- **Gender:** male, female
- **Age:** child, teenager, young adult, middle-aged, elderly
- **Pitch:** very low pitch, low pitch, moderate pitch, high pitch, very high pitch
- **Style:** whisper
- **Accent:** american accent, british accent, australian accent, canadian accent, indian accent, japanese accent, korean accent, chinese accent, russian accent, portuguese accent

### Tips
- Use comma + space between terms: `"male, low pitch, american accent"`
- Keep instruct short — 2-3 terms work best
- For Vietnamese narration, `"male, moderate pitch, young adult"` gives a clear documentary voice
- `speed: 1.1` gives slightly faster, more dynamic pacing

## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/tts/templates` | POST | Create voice template |
| `/api/tts/templates` | GET | List all templates |
| `/api/tts/templates/{name}` | GET | Get template details |
| `/api/tts/templates/{name}` | DELETE | Delete template |

## Important Notes

- Voice templates use **voice design** (instruct string) to generate an anchor voice
- When narrating scenes, the template WAV is used as **ref_audio** for voice cloning
- This ensures every scene sounds like the same narrator
- CPU mode only (MPS produces artifacts) — generation takes ~15-30s per template
- Template WAV is saved permanently in `output/tts/templates/`
