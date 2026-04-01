# Google Flow Agent

Standalone system to generate AI videos via Google Flow API. Uses a Chrome extension as browser bridge for authentication, reCAPTCHA solving, and API proxying.

```
┌──────────────────┐     WebSocket      ┌──────────────────────┐
│  Python Agent    │◄──────────────────►│  Chrome Extension     │
│  (FastAPI+SQLite)│     localhost:9222  │  (MV3 Service Worker) │
│                  │                    │                       │
│  - REST API :8100│  ── commands ──►   │  - Token capture      │
│  - Queue worker  │  ◄── results ──    │  - reCAPTCHA solve    │
│  - Post-process  │                    │  - API proxy          │
│  - SQLite DB     │                    │  (on labs.google)     │
└──────────────────┘                    └──────────────────────┘
```

## Quick Start

```bash
# 1. Load Chrome extension (chrome://extensions → Load unpacked → extension/)
# 2. Open labs.google/fx/tools/flow and sign in
# 3. Start agent
pip install -r requirements.txt
python -m agent.main

# 4. Verify
curl http://127.0.0.1:8100/health
# {"status":"ok","extension_connected":true}
```

## Core Concepts

### Reference Image System

Every visual element that should stay consistent gets a **reference image** — characters, locations, props. Each reference has a UUID `media_id` used in all scene generations via `imageInputs`.

| Entity Type | Aspect Ratio | Composition |
|-------------|-------------|-------------|
| `character` | Portrait | Full body head-to-toe, front-facing, centered |
| `location` | Landscape | Establishing shot, level horizon, atmospheric |
| `creature` | Portrait | Full body, natural stance, distinctive features |
| `visual_asset` | Portrait | Detailed view, textures, scale reference |

### Scene Prompts = Action Only

Scene prompts describe **what happens**, not character appearance. The reference images maintain visual consistency.

```
"Pippip juggling fish at Fish Stall, crowd watching in Open Market"
                  ↓
NOT: "Pippip the chubby orange tabby cat wearing a blue apron juggling..."
```

### Media ID = UUID

All `media_id` values are UUID format (`xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`). Never the base64 `CAMS...` mediaGenerationId.

## Pipeline

```
1. Create project      POST /api/projects (with entities + story)
2. Create video        POST /api/videos
3. Create scenes       POST /api/scenes (chain_type: ROOT → CONTINUATION)
4. Gen ref images      POST /api/requests {type: GENERATE_CHARACTER_IMAGE} per entity
   → Wait ALL complete, verify all have UUID media_id
5. Gen scene images    POST /api/requests {type: GENERATE_IMAGES} per scene
   → Wait ALL complete
6. Gen videos          POST /api/requests {type: GENERATE_VIDEO} per scene
   → Wait ALL complete (2-5 min each)
7. (Optional) Upscale  POST /api/requests {type: UPSCALE_VIDEO} (TIER_TWO only)
8. Download + concat   ffmpeg normalize + concat
```

### Example: Create Project with References

```bash
curl -X POST http://127.0.0.1:8100/api/projects \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Pippip the Fish Merchant",
    "story": "Pippip is a chubby orange tabby cat who sells fish at a market...",
    "characters": [
      {"name": "Pippip", "entity_type": "character", "description": "Chubby orange tabby cat with blue apron and straw hat"},
      {"name": "Fish Stall", "entity_type": "location", "description": "Small wooden market stall with thatched roof"},
      {"name": "Open Market", "entity_type": "location", "description": "Southeast Asian open-air morning market"},
      {"name": "Golden Fish", "entity_type": "visual_asset", "description": "Magnificent golden koi with shimmering scales"}
    ]
  }'
```

## Skills (AI Agent Workflows)

Ready-to-use workflow recipes in `skills/` (also available as `/slash-commands` in Claude Code):

### Basic Pipeline

| Skill | Description |
|-------|-------------|
| `/new-project` | Create project + entities + video + scenes interactively |
| `/gen-refs` | Generate reference images for all entities |
| `/gen-images` | Generate scene images with character refs |
| `/gen-videos` | Generate videos from scene images |
| `/concat` | Download + merge all scene videos |

### Advanced Video

| Skill | Description |
|-------|-------------|
| `/gen-chain-videos` | Auto start+end frame chaining for smooth transitions (i2v_fl) |
| `/insert-scene` | Multi-angle shots, cutaways, close-ups within a chain |
| `/creative-mix` | Analyze story + suggest all techniques (chain, insert, r2v, parallel) |

### Utilities

| Skill | Description |
|-------|-------------|
| `/status` | Full project dashboard + recommended next action |
| `/fix-uuids` | Repair any CAMS... media_ids to UUID format |

## Video Generation Techniques

| Technique | API Type | Use Case |
|-----------|----------|----------|
| **i2v** | `GENERATE_VIDEO` | Image → video (standard) |
| **i2v_fl** | `GENERATE_VIDEO` + endImage | Start+end frame → smooth scene transitions |
| **r2v** | `GENERATE_VIDEO_REFS` | Reference images → video (intros, dream sequences) |
| **Upscale** | `UPSCALE_VIDEO` | Video → 4K (TIER_TWO only) |

## API Reference

### CRUD Endpoints

| Resource | Create | List | Get | Update | Delete |
|----------|--------|------|-----|--------|--------|
| Project | `POST /api/projects` | `GET /api/projects` | `GET /api/projects/{id}` | `PATCH /api/projects/{id}` | `DELETE /api/projects/{id}` |
| Character | `POST /api/characters` | `GET /api/characters` | `GET /api/characters/{id}` | `PATCH /api/characters/{id}` | `DELETE /api/characters/{id}` |
| Video | `POST /api/videos` | `GET /api/videos?project_id=` | `GET /api/videos/{id}` | `PATCH /api/videos/{id}` | `DELETE /api/videos/{id}` |
| Scene | `POST /api/scenes` | `GET /api/scenes?video_id=` | `GET /api/scenes/{id}` | `PATCH /api/scenes/{id}` | `DELETE /api/scenes/{id}` |
| Request | `POST /api/requests` | `GET /api/requests` | `GET /api/requests/{id}` | `PATCH /api/requests/{id}` | — |

### Special Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /health` | Server + extension status |
| `GET /api/flow/status` | Extension connection details |
| `GET /api/flow/credits` | User credits + tier |
| `GET /api/requests/pending` | Pending request queue |
| `GET /api/projects/{id}/characters` | Entities linked to project |

### Request Types

| Type | Required Fields | Async? | reCAPTCHA? |
|------|----------------|--------|------------|
| `GENERATE_CHARACTER_IMAGE` | character_id, project_id | No | Yes |
| `GENERATE_IMAGES` | scene_id, project_id, video_id, orientation | No | Yes |
| `GENERATE_VIDEO` | scene_id, project_id, video_id, orientation | Yes | Yes |
| `GENERATE_VIDEO_REFS` | scene_id, project_id, video_id, orientation | Yes | Yes |
| `UPSCALE_VIDEO` | scene_id, project_id, video_id, orientation | Yes | Yes |

## Worker Behavior

- **10s cooldown** between API calls (anti-spam, configurable via `API_COOLDOWN`)
- **Reference blocking** — scene image gen refuses if any referenced entity is missing `media_id`
- **Skip completed** — won't re-generate already-completed assets
- **Cascade clear** — regenerating image auto-resets downstream video + upscale
- **Retry** — failed requests retry up to 5 times
- **UUID enforcement** — extracts UUID from fifeUrl if response doesn't provide it directly

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `API_HOST` | `127.0.0.1` | REST API bind address |
| `API_PORT` | `8100` | REST API port |
| `WS_HOST` | `127.0.0.1` | WebSocket server bind |
| `WS_PORT` | `9222` | WebSocket server port |
| `POLL_INTERVAL` | `5` | Worker poll interval (seconds) |
| `MAX_RETRIES` | `5` | Max retries per request |
| `VIDEO_POLL_TIMEOUT` | `420` | Video gen poll timeout (seconds) |
| `API_COOLDOWN` | `10` | Seconds between API calls (anti-spam) |

## Architecture

```
agent/
├── main.py              # FastAPI app + WebSocket server
├── config.py            # Configuration (loads models.json)
├── models.json          # Video/upscale/image model mappings
├── db/
│   ├── schema.py        # SQLite schema (aiosqlite)
│   └── crud.py          # Async CRUD with column whitelisting
├── models/              # Pydantic models + Literal enums
├── api/                 # REST routes (projects, videos, scenes, characters, requests, flow)
├── services/
│   ├── flow_client.py   # WS bridge to extension
│   ├── headers.py       # Randomized browser headers
│   ├── scene_chain.py   # Continuation scene logic
│   └── post_process.py  # ffmpeg trim/merge/music
└── worker/
    └── processor.py     # Queue processor + poller

extension/               # Chrome MV3 extension
skills/                  # AI agent workflow recipes
.claude/commands/        # Claude Code slash commands
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Extension shows "Agent disconnected" | Start `python -m agent.main` |
| Extension shows "No token" | Open labs.google/fx/tools/flow |
| `CAPTCHA_FAILED: NO_FLOW_TAB` | Need a Google Flow tab open |
| 403 MODEL_ACCESS_DENIED | Tier mismatch — auto-detect should handle it |
| Scene images inconsistent | Check all refs have `media_id` (UUID). Run `/fix-uuids` |
| media_id starts with CAMS... | Run `/fix-uuids` to extract UUID from URL |
| Upscale permission denied | Requires PAYGATE_TIER_TWO account |

## License

MIT
