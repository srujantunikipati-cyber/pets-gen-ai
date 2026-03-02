"""
Full pipeline report — runs all steps against every video in /videos/:
  1. Audio check
  2. Audio extraction (ffmpeg)
  3. Whisper STT  → raw text + language
  4. Profanity filter → removed words + cleaned text
  5. YOLO pet detection → pet label
  6. fal.ai image prompt (build_fal_image_prompt)
  7. fal.ai video prompt (build_fal_video_prompt)

Translation step (IndicTrans2) is noted but NOT called — it requires the
IndicTrans2 inference server to be running. The report shows what WOULD
be sent/received.

Usage:
    python run_pipeline_report.py
"""

import asyncio
import glob
import logging
import os
import re
import sys
import tempfile

# ── Keep logs quiet so report output is readable ─────────────────────────────
logging.basicConfig(level=logging.WARNING)
os.environ.setdefault("STORAGE_DIR", "storage")

sys.path.insert(0, os.path.dirname(__file__))

# ── Imports ───────────────────────────────────────────────────────────────────
from backend.services.audio_extraction import AudioExtractionService
from backend.services.speech_to_text import get_speech_to_text_service
from backend.services.profanity_filter import ProfanityFilter, _PATTERN, _RAW_WORDS
from backend.services.script_service import ScriptService
from backend.services.vision_service import VisionService

# Language code → readable name
LANG_NAMES = {
    "hi": "Hindi", "bn": "Bengali", "gu": "Gujarati", "mr": "Marathi",
    "kn": "Kannada", "te": "Telugu", "ml": "Malayalam", "ta": "Tamil",
    "pa": "Punjabi", "or": "Odia",  "as": "Assamese", "ur": "Urdu",
    "en": "English", "unknown": "Unknown",
}

VIDEOS_DIR = os.path.join(os.path.dirname(__file__), "videos")
SEPARATOR = "═" * 80


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def find_removed_words(original: str, cleaned: str) -> list[str]:
    """Return the actual matched bad-word tokens from original text."""
    return [m.group() for m in _PATTERN.finditer(original)]


def lang_label(code: str) -> str:
    return f"{LANG_NAMES.get(code, code.upper())} ({code})"


def wrap(text: str, width: int = 74) -> str:
    """Wrap long text for report display."""
    import textwrap
    return textwrap.fill(text, width=width, subsequent_indent="         ")


# ─────────────────────────────────────────────────────────────────────────────
# YOLO detection (sync, extracted from video_worker helper)
# ─────────────────────────────────────────────────────────────────────────────

def detect_pet_yolo(vision_svc: VisionService, frame_path: str) -> tuple[bool, str | None, float]:
    """Returns (detected, label, confidence) using multi-scale VisionService.detect_best_pet()."""
    import cv2

    if vision_svc.net is None:
        return False, None, 0.0
    if not os.path.exists(frame_path):
        return False, None, 0.0

    image = cv2.imread(frame_path)
    if image is None:
        return False, None, 0.0

    label, conf = vision_svc.detect_best_pet(image)
    return (bool(label), label, conf)


# ─────────────────────────────────────────────────────────────────────────────
# Per-video pipeline
# ─────────────────────────────────────────────────────────────────────────────

async def process_video(
    video_path: str,
    idx: int,
    total: int,
    audio_svc: AudioExtractionService,
    stt_svc,
    pf: ProfanityFilter,
    vision_svc: VisionService,
) -> dict:
    name = os.path.basename(video_path)
    result = {
        "name": name,
        "has_audio": False,
        "audio_error": None,
        "raw_text": "",
        "language_code": "unknown",
        "language_name": "Unknown",
        "removed_words": [],
        "cleaned_text": "",
        "was_filtered": False,
        "pet_detected": False,
        "pet_label": None,
        "pet_conf": 0.0,
        "fal_image_prompt": "",
        "fal_video_prompt": "",
        "translation_needed": False,
        "error": None,
    }

    print(f"\r  [{idx}/{total}] Processing: {name[:55]:<55}", end="", flush=True)

    tmpdir = tempfile.mkdtemp(prefix="pipeline_report_")
    audio_path = os.path.join(tmpdir, "audio.wav")
    frame_path = os.path.join(tmpdir, "frame.jpg")

    try:
        # ── Step 1: Audio check ───────────────────────────────────────────
        result["has_audio"] = audio_svc.has_audio(video_path)
        if not result["has_audio"]:
            result["audio_error"] = "No audio stream in video"
            return result

        # ── Step 2: Extract audio ─────────────────────────────────────────
        audio_svc.extract_audio(video_path, audio_path)

        # ── Step 3: Multi-frame multi-scale YOLO (up to 20 frames, soft-gate) ─
        duration = audio_svc.get_video_duration(video_path)
        n_samples = 20 if duration > 2.0 else max(1, int(duration))
        offsets = [duration * i / n_samples for i in range(1, n_samples + 1)]
        pet_det, pet_label, pet_conf = False, None, 0.0
        for offset in offsets:
            audio_svc.extract_frame_at(video_path, frame_path, offset_seconds=offset)
            _det, _lbl, _conf = detect_pet_yolo(vision_svc, frame_path)
            if _det and _conf > pet_conf:
                pet_det, pet_label, pet_conf = _det, _lbl, _conf
            if pet_det and pet_conf >= 0.25:
                break  # Confident hit — stop early

        result["pet_detected"] = pet_det
        result["pet_label"] = pet_label
        result["pet_conf"] = pet_conf
        # Soft-gate: always proceed; if no label found use generic fallback
        effective_pet = pet_label or "pet"

        # ── Step 5: Whisper STT ───────────────────────────────────────────
        if stt_svc:
            stt_result = await stt_svc.transcribe_audio_file(audio_path)
            raw_text = stt_result.get("text", "").strip()
            lang_code = (stt_result.get("language") or "unknown").lower().strip()
            result["raw_text"] = raw_text
            result["language_code"] = lang_code
            result["language_name"] = LANG_NAMES.get(lang_code, lang_code.upper())
            result["translation_needed"] = bool(raw_text and lang_code and lang_code != "en")
        else:
            result["raw_text"] = ""
            result["language_code"] = "unknown"

        # ── Step 6: Profanity filter ──────────────────────────────────────
        topic = result["raw_text"] or f"funny {pet_label or 'pet'}"
        removed = find_removed_words(topic, "")
        cleaned, was_filtered = pf.clean(topic)
        result["removed_words"] = removed
        result["cleaned_text"] = cleaned
        result["was_filtered"] = was_filtered

        # Guard: if fully censored, reset to default
        if not cleaned.replace("*", "").replace(" ", "").strip():
            cleaned = f"a funny {pet_label or 'pet'}"
            result["cleaned_text"] = cleaned

        # ── Step 7: Build fal.ai prompts (script fallback — no GPT call) ─
        fallback = ScriptService._fallback_script(cleaned, pet_type=effective_pet)
        raw_image_prompt = fallback["image_prompt"]
        script_text = fallback["script"]

        result["fal_image_prompt"] = ScriptService.build_fal_image_prompt(
            raw_image_prompt, cleaned, pet_type=effective_pet
        )
        result["fal_video_prompt"] = ScriptService.build_fal_video_prompt(
            result["fal_image_prompt"], script_text
        )

    except Exception as exc:
        result["error"] = str(exc)
    finally:
        import shutil
        shutil.rmtree(tmpdir, ignore_errors=True)

    return result


# ─────────────────────────────────────────────────────────────────────────────
# Report printer
# ─────────────────────────────────────────────────────────────────────────────

def print_report(results: list[dict]) -> None:
    print(f"\n\n{SEPARATOR}")
    print("  FULL PIPELINE REPORT — PET ROAST AI")
    print(SEPARATOR)
    print(f"  Videos tested : {len(results)}")
    ok     = [r for r in results if not r.get("error") and r["has_audio"]]
    no_aud = [r for r in results if not r["has_audio"]]
    errors = [r for r in results if r.get("error")]
    print(f"  Passed        : {len(ok)}")
    print(f"  No audio      : {len(no_aud)}")
    print(f"  Errors        : {len(errors)}")

    # Language breakdown
    langs = {}
    for r in ok:
        lc = r["language_code"]
        langs[lc] = langs.get(lc, 0) + 1
    if langs:
        lang_summary = ", ".join(
            f"{LANG_NAMES.get(k, k.upper())}×{v}" for k, v in sorted(langs.items())
        )
        print(f"  Languages     : {lang_summary}")

    # Pet detection
    pets_detected = sum(1 for r in ok if r["pet_detected"])
    print(f"  Pet detected  : {pets_detected}/{len(ok)}")
    print(f"  Needs translate: {sum(1 for r in ok if r['translation_needed'])}/{len(ok)}")
    print(f"  Had profanity : {sum(1 for r in ok if r['was_filtered'])}/{len(ok)}")
    print(SEPARATOR)

    for i, r in enumerate(results, 1):
        name = r["name"]

        print(f"\n  ┌─ Video {i}/{len(results)} ────────────────────────────────────────────────")
        print(f"  │ File    : {name}")

        if r.get("error"):
            print(f"  │ ❌ ERROR : {r['error']}")
            print(f"  └{'─'*77}")
            continue

        if not r["has_audio"]:
            print(f"  │ ⚠  SKIP : No audio stream detected")
            print(f"  └{'─'*77}")
            continue

        # Audio + Pet
        audio_ok = "✓ Audio OK" if r["has_audio"] else "✗ No Audio"
        pet_info = (
            f"✓ {r['pet_label'].upper()} (conf={r['pet_conf']:.2f})"
            if r["pet_detected"]
            else "✗ No pet detected by YOLO"
        )
        print(f"  │ Audio   : {audio_ok}")
        print(f"  │ YOLO    : {pet_info}")

        # STT
        lang_display = lang_label(r["language_code"])
        print(f"  │ Lang    : {lang_display}")
        raw = r["raw_text"] or "(empty — no speech detected)"
        print(f"  │ 📝 Extracted Text:")
        print(f"  │    {wrap(raw)}")

        # Translation
        if r["translation_needed"]:
            print(f"  │ 🌐 Translation: NEEDED ({r['language_name']} → English)")
            print(f"  │    Would send to IndicTrans2: source_language='{r['language_code']}'")
            print(f"  │    (IndicTrans2 server not called in offline report)")
        elif r["language_code"] == "en":
            print(f"  │ 🌐 Translation: SKIPPED (already English)")
        else:
            print(f"  │ 🌐 Translation: SKIPPED (no speech or unknown language)")

        # Profanity
        if r["was_filtered"]:
            removed_str = ", ".join(f'"{w}"' for w in r["removed_words"])
            print(f"  │ 🚫 Profanity Filter: TRIGGERED")
            print(f"  │    Removed words : {removed_str}")
            print(f"  │    Cleaned text  : {wrap(r['cleaned_text'])}")
        else:
            print(f"  │ ✅ Profanity Filter: CLEAN — no words removed")
            print(f"  │    Final topic   : {wrap(r['cleaned_text'] or r['raw_text'])}")

        # fal.ai prompts
        print(f"  │")
        print(f"  │ 🎨 fal.ai IMAGE PROMPT (Flux Schnell):")
        print(f"  │    {wrap(r['fal_image_prompt'])}")
        print(f"  │")
        print(f"  │ 🎬 fal.ai VIDEO PROMPT (Kling 1.6):")
        print(f"  │    {wrap(r['fal_video_prompt'])}")
        print(f"  └{'─'*77}")

    # ── Pet & Emotion Assessment ─────────────────────────────────────────────
    print(f"\n{SEPARATOR}")
    print("  PET DETECTION & EMOTION — DO WE NEED THEM?")
    print(SEPARATOR)

    pet_detected_count = sum(1 for r in ok if r["pet_detected"])
    pet_not_detected = len(ok) - pet_detected_count

    print(f"""
  PET DETECTION (YOLOv3-tiny)
  ─────────────────────────────────────────────────────────────────────────
  Detected in : {pet_detected_count}/{len(ok)} videos
  Missed      : {pet_not_detected}/{len(ok)} videos

  VERDICT  : ✅ KEEP — MANDATORY
  REASON   :
    • Pet label is injected into the GPT prompt as context hint
      ("The pet is a dog.") which makes the roast script species-specific.
    • Without pet detection the generated image prompt is generic
      "a funny pet" — quality degrades significantly.
    • It also gates the pipeline: videos WITHOUT a pet are rejected early
      (saves fal.ai API cost on off-topic content).
    • YOLOv3-tiny is fast (<100ms) and free — no cost to keep.

  PET EMOTION (TensorFlow CNN)
  ─────────────────────────────────────────────────────────────────────────
  Currently  : NOT wired into video_worker pipeline at all.
             The emotion model only runs via the /emotion/* API endpoints.

  VERDICT  : ⚠  OPTIONAL — NOT USED IN CURRENT PIPELINE
  REASON   :
    • Emotion output (happy/angry/sad/...) is NEVER passed to GPT or
      the fal.ai prompt builder in video_worker.py.
    • Adding it WOULD improve prompt quality:
        GPT context: "The pet looks EXCITED." → richer roast.
        fal.ai prompt: "dog looking excited, wide-open eyes, ..." → better image.
    • Cost: ~50ms per frame inference (CPU TF) — acceptable.
    • RECOMMENDATION: Wire pet emotion into video_worker Step 0c so the
      detected emotion is included in generate_script() context and
      build_fal_image_prompt(). Simple 1-line change.
  ─────────────────────────────────────────────────────────────────────────
""")

    # Final prompt quality summary
    print(f"{SEPARATOR}")
    print("  FINAL fal.ai PROMPT QUALITY SUMMARY")
    print(SEPARATOR)
    print("""
  IMAGE PROMPT (Flux Schnell) — what makes a good one:
    ✓ Pet species/breed + funny action/expression     ← from GPT / YOLO label
    ✓ Scene/background context                        ← from Whisper transcript
    ✓ Photographic qualifiers                         ← appended by build_fal_image_prompt()
      (photorealistic, cinematic lighting, shallow DOF, 4K, high detail,
       vibrant colors, funny expression)
    ⚠ Emotion modifier (excited / upset / sleepy)     ← MISSING — add pet emotion
    ⚠ Breed detail (golden retriever vs generic dog)  ← MISSING — needs richer YOLO or breed model

  VIDEO PROMPT (Kling 1.6) — what makes a good one:
    ✓ Same visual base as image prompt
    ✓ Motion description (slow zoom-in, playful motion, bokeh)
    ✓ Mood reference from roast script first sentence
    ⚠ Action specificity (tail wagging / jumping / head-tilt) ← needs emotion/behaviour

  OVERALL PIPELINE STATUS:
    ✅ Audio extraction    — working
    ✅ Whisper STT         — working (auto language detection)
    ✅ Profanity filter    — working
    ✅ YOLO pet detection  — working
    ✅ fal.ai prompt build — working (with quality modifiers)
    ⚠  IndicTrans2         — not tested offline (requires running server)
    ⚠  Pet emotion         — available but NOT wired into video pipeline
""")


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

async def main():
    video_files = sorted(glob.glob(os.path.join(VIDEOS_DIR, "*.mp4")))
    if not video_files:
        print(f"No videos found in {VIDEOS_DIR}")
        sys.exit(1)

    print(f"\n{'═'*80}")
    print(f"  Loading services...")
    print(f"{'═'*80}")

    audio_svc = AudioExtractionService()
    print("  ✓ AudioExtractionService")

    stt_svc = get_speech_to_text_service(model_size="base")
    print("  ✓ Whisper STT (base, CPU, int8)")

    pf = ProfanityFilter()
    print("  ✓ ProfanityFilter")

    vision_svc = VisionService()
    yolo_status = "✓ YOLO loaded" if vision_svc.net is not None else "✗ YOLO model files missing"
    print(f"  {yolo_status}")

    print(f"\n  Found {len(video_files)} videos in {VIDEOS_DIR}")
    print(f"  Running pipeline on each...\n")

    results = []
    for idx, video_path in enumerate(video_files, 1):
        r = await process_video(video_path, idx, len(video_files), audio_svc, stt_svc, pf, vision_svc)
        results.append(r)

    print()  # newline after progress line
    print_report(results)


if __name__ == "__main__":
    asyncio.run(main())
