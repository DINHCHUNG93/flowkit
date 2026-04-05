Generate 4 YouTube-optimized thumbnail variants for a project video.

Usage: `/gla:thumbnail [project_id]`

## Step 1: Load project context

```bash
curl -s http://127.0.0.1:8100/api/projects/<PID>
curl -s "http://127.0.0.1:8100/api/videos?project_id=<PID>"
curl -s "http://127.0.0.1:8100/api/projects/<PID>/characters"
curl -s "http://127.0.0.1:8100/api/scenes?video_id=<VID>"
```

Extract and understand:
- **Story**: what is this video about? What is the conflict? What is at stake?
- **Main character(s)**: who drives the story? (must have media_id for refs)
- **Key conflict**: what dramatic moment defines the video?
- **Language**: match the project language for text on thumbnail

## Step 2: Create the HOOK

A YouTube thumbnail hook = ONE sentence that makes someone NEED to click.

Based on the story, create a hook by answering:
- "What question does this video answer?"
- "What impossible situation happens?"
- "What will the viewer NOT believe?"

Turn the hook into **2-4 bold words** for the thumbnail text. Examples:
- Military story about Iran blocking strait → "EO BIỂN TỬ THẦN" or "IRAN ATTACKS!"
- Romance about impossible love → "CÔ ẤY ĐÃ CHẾT?"
- Action about heist → "KHÔNG AI SỐNG SÓT"

The text MUST be:
- 2-4 words maximum
- In the project's language
- Provocative — creates curiosity gap
- Uses power words: ATTACK, DEATH, IMPOSSIBLE, SHOCK, SECRET, LAST, FINAL

## Step 3: Build 4 thumbnail prompts

**ALL prompts MUST include:**
1. The hook text as bold text IN the image (not overlay)
2. Character names in `character_names` for face consistency
3. The project's material style prefix

### Prompt template:

```
[MATERIAL_PREFIX] Bold YouTube thumbnail, [HOOK_TEXT] written in large bold white text 
with black outline at [POSITION: top/upper-left/upper-right] of frame.
[MAIN_CHARACTER] [ACTION + EXTREME EMOTION], [DRAMATIC ELEMENT behind/around character],
vivid [COLOR1] and [COLOR2], bright saturated colors, dramatic rim lighting,
simple blurred background, photorealistic, YouTube thumbnail style, 
designed to hook viewers and get clicks
```

### 4 variants — each uses different angle:

**V1 — Face + Text (hook via emotion):**
Main character face HUGE (50% of frame), extreme emotion, hook text at top.
Background: threat/explosion/danger barely visible.

**V2 — Action + Text (hook via stakes):**
Main character in action pose, overwhelming threat visible, hook text at top-left.
Wide enough to show the scale of danger.

**V3 — Confrontation + Text (hook via conflict):**
Hero vs villain/threat facing each other, hook text between them or at top.
Clear visual tension between two sides.

**V4 — Mystery + Text (hook via curiosity):**
Character reacting to something OFF-SCREEN, hook text as a question or cliffhanger.
Viewer can't see what character sees → must click.

## Step 4: Collect character refs

From entity list, include ALL main characters that have `media_id` in `character_names`.
This ensures faces match the video — critical for channel consistency.

If character refs fail (400 error), retry without refs but warn user.

## Step 5: Generate 4 thumbnails

SEQUENTIALLY with 8s cooldown between each:

```bash
for i in 1 2 3 4; do
  curl -s -m 90 -X POST "http://127.0.0.1:8100/api/projects/<PID>/generate-thumbnail" \
    -H "Content-Type: application/json" \
    -d '{
      "prompt": "<variant_prompt_with_text_embedded>",
      "character_names": ["<main_char1>", "<main_char2>"],
      "aspect_ratio": "LANDSCAPE",
      "output_filename": "thumbnail_v'$i'.png"
    }'
  sleep 8
done
```

If reCAPTCHA fails: retry that variant once.
If 400 (missing refs): retry without character_names.

## Step 6: Resize to YouTube (1280x720)

```bash
for i in 1 2 3 4; do
  ffmpeg -y -i "${DIR}/thumbnail_v${i}.png" \
    -vf "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2:color=black" \
    "${DIR}/thumbnail_v${i}_yt.png" 2>/dev/null
done
```

## Step 7: Show all 4 and evaluate

Display all 4 thumbnails using Read tool.

For EACH thumbnail, evaluate honestly:
- Is the text readable? Bold enough? Well-positioned?
- Is the face big enough (30-50% of frame)?
- Is the emotion extreme (not neutral)?
- Are colors bright and saturated (not dark/muted)?
- Would YOU click this on YouTube?
- Does it create curiosity — what happens next?

Rate each: STRONG / OK / WEAK with reason.

Ask user: "Which one? 1-4, 'regenerate N', or 'all' to redo everything"

## Step 8: Output

```
Thumbnails for: <project> — <video_title>
Hook text: <the hook words used>
Character refs: <names used>

V1 (Face+Text): [RATING] — thumbnail_v1_yt.png
V2 (Action+Text): [RATING] — thumbnail_v2_yt.png  
V3 (Confrontation+Text): [RATING] — thumbnail_v3_yt.png
V4 (Mystery+Text): [RATING] — thumbnail_v4_yt.png

Files: output/<project>/thumbnail_v*_yt.png (1280x720)
```
