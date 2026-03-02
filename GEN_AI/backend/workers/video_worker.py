import asyncio
import logging
import os
import uuid
from arq import create_pool
from arq.connections import RedisSettings

from backend.config import settings
from backend.services.script_service import ScriptService
from backend.services.image_service import ImageService
from backend.services.fal_video_service import FalVideoService
from backend.services.tts_service import TTSService
from backend.services.editor_service import EditorService
from backend.services.cost_tracker import CostTracker
from backend.services.audio_extraction import AudioExtractionService
from backend.services.speech_to_text import get_speech_to_text_service
from backend.services.ai_translator import AI4BharatClient
from backend.services.vision_service import VisionService
from backend.services.profanity_filter import clean_text
from backend.services.pet_emotion_service import PetEmotionService
import httpx

logger = logging.getLogger(__name__)

# Initialize Services
script_service = ScriptService()
image_service = ImageService()
fal_video_service = FalVideoService()
tts_service = TTSService()
editor_service = EditorService()
audio_extract_service = AudioExtractionService()
stt_service = get_speech_to_text_service(model_size="base")
vision_service = VisionService()
emotionService: PetEmotionService | None = None
try:
    emotionService = PetEmotionService.get_instance()
except Exception as _emo_exc:
    logger.warning(f"PetEmotionService unavailable: {_emo_exc}")


async def generate_video_job(ctx, job_req: dict):
    """
    Main Pipeline Job.

    Inputs (from job_req):
      topic        — free-text description (used when no video_url is given)
      image_url    — optional, skips image generation if provided
      video_url    — optional, triggers: audio validation → pet detection →
                     Whisper STT → IndicTrans2 translation → profanity filter
    """
    import time
    start_time = time.time()

    raw_topic: str = job_req.get("topic") or ""
    image_url_req: str | None = job_req.get("image_url")
    video_url_req: str | None = job_req.get("video_url")
    job_id: str = ctx["job_id"]
    redis = ctx["redis"]

    work_dir = os.path.join(settings.TEMP_DIR, job_id)
    os.makedirs(work_dir, exist_ok=True)

    cost_steps: dict = {}

    # Holds the final English, clean topic used for script/prompt generation
    topic: str = raw_topic.strip() or "funny pet roast"
    detected_lang: str | None = None   # Whisper-detected language code
    detected_pet: str | None = None    # YOLO-detected pet label (may include multiple species)
    detected_emotion: str | None = None  # TF emotion model result

    try:
        # ================================================================
        # STEP 0 — Process input video (if provided)
        # ================================================================
        if video_url_req:
            logger.info(f"[{job_id}] Step 0: Processing Input Video")

            # ── 0a. Download ──────────────────────────────────────────────
            input_video_path = os.path.join(work_dir, "input_video.mp4")
            logger.info(f"[{job_id}]   0a. Downloading video from URL...")
            async with httpx.AsyncClient(timeout=httpx.Timeout(90.0, connect=30.0)) as client:
                resp = await client.get(video_url_req)
                resp.raise_for_status()
                with open(input_video_path, "wb") as f:
                    f.write(resp.content)
            logger.info(f"[{job_id}]   Downloaded: {os.path.getsize(input_video_path):,} bytes")

            # ── 0b. Validate audio stream ─────────────────────────────────
            logger.info(f"[{job_id}]   0b. Validating audio stream...")
            if not audio_extract_service.has_audio(input_video_path):
                raise ValueError(
                    "No audio detected in the video. "
                    "Please provide a video that contains a voice/sound track."
                )

            # ── 0c. Extract frames → detect pet(s) via YOLO (multi-frame + multi-scale) ──
            logger.info(f"[{job_id}]   0c. Detecting pet(s) with YOLOv3-tiny (multi-frame, multi-scale)...")
            frame_path = os.path.join(work_dir, "frame.jpg")

            # Sample up to 20 evenly-spread frames — scan ALL to catch multi-pet scenes
            duration = audio_extract_service.get_video_duration(input_video_path)
            n_samples = 20 if duration > 2.0 else max(1, int(duration))
            offsets = [duration * i / n_samples for i in range(1, n_samples + 1)]

            # Accumulate every species seen across ALL frames.
            # Track both best-confidence and frame-count so we can filter noise.
            species_best:   dict[str, float] = {}   # label -> highest conf seen
            species_frames: dict[str, int]   = {}   # label -> frames it appeared in
            total_detection_frames = 0              # frames where ANY pet was found

            # Minimum per-frame confidence to count a species toward frame-count.
            # Keep this at 0.15 so we don't let sub-noise blips inflate counts.
            PER_FRAME_MIN_CONF = 0.15

            for offset in offsets:
                audio_extract_service.extract_frame_at(input_video_path, frame_path, offset_seconds=offset)
                frame_species = await _detect_all_pets_in_frame(vision_service, frame_path)
                if not frame_species:
                    continue
                total_detection_frames += 1
                for lbl, conf in frame_species.items():
                    if conf > species_best.get(lbl, 0.0):
                        species_best[lbl] = conf
                    if conf >= PER_FRAME_MIN_CONF:
                        species_frames[lbl] = species_frames.get(lbl, 0) + 1

            if species_best:
                # ── Filter: keep primary always; keep secondary only when it
                #    passes BOTH a confidence gate AND a frequency gate.
                #
                #  • Primary  = species with highest best-confidence → always kept.
                #  • Secondary min conf  : 0.25  (rules out weak YOLO guesses)
                #  • Secondary min frames: max(2, ceil(30% of detection frames))
                #    e.g. 20 det-frames → need ≥ 6; 8 frames → need ≥ 3; 2 → need ≥ 2
                import math
                primary = max(species_best, key=lambda k: species_best[k])
                min_frames_secondary = max(2, math.ceil(total_detection_frames * 0.30))

                valid_species = [primary]
                for lbl in species_best:
                    if lbl == primary:
                        continue
                    if (species_best[lbl] >= 0.25
                            and species_frames.get(lbl, 0) >= min_frames_secondary):
                        valid_species.append(lbl)

                # Sort valid species by best-confidence descending
                valid_species.sort(key=lambda k: species_best[k], reverse=True)
                detected_pet = _format_pet_label(valid_species)
                logger.info(
                    f"[{job_id}]   Detected pet(s): {detected_pet} "
                    f"(best_conf={species_best}, frames={species_frames}, "
                    f"min_frames_threshold={min_frames_secondary})"
                )
            else:
                # SOFT GATE: YOLO-tiny has ~45% mAP and often misses pets that are
                # partially visible, backlit, or at unusual angles.  We do NOT reject
                # the video — instead we proceed with a generic 'pet' label so the
                # pipeline always completes.
                logger.warning(
                    f"[{job_id}]   YOLO could not identify a specific pet species in "
                    f"any of {n_samples} sampled frames — proceeding with generic 'pet' label."
                )
                detected_pet = None  # generic; GPT/prompt builders fall back to 'pet'

            # ── 0c-ii. Pet emotion detection (5-frame majority vote) ──────
            if emotionService is not None:
                try:
                    emo_scores: dict[str, float] = {}
                    emo_offsets = [duration * p for p in (0.20, 0.35, 0.50, 0.65, 0.80)]
                    emo_path = os.path.join(work_dir, "emo_frame.jpg")
                    for emo_off in emo_offsets:
                        audio_extract_service.extract_frame_at(
                            input_video_path, emo_path, offset_seconds=emo_off
                        )
                        if not os.path.exists(emo_path):
                            continue
                        with open(emo_path, "rb") as _f:
                            _frame_bytes = _f.read()
                        emo_result = await emotionService.predict_from_bytes(
                            _frame_bytes, filename="emo_frame.jpg"
                        )
                        if not emo_result.uncertain:
                            emo_scores[emo_result.label] = (
                                emo_scores.get(emo_result.label, 0.0) + emo_result.confidence
                            )
                    if emo_scores:
                        detected_emotion = max(emo_scores, key=lambda k: emo_scores[k])
                        logger.info(
                            f"[{job_id}]   Pet emotion: {detected_emotion} "
                            f"(votes={emo_scores})"
                        )
                    else:
                        logger.info(f"[{job_id}]   Pet emotion: all frames uncertain — skipping")
                except Exception as _emo_err:
                    logger.warning(f"[{job_id}]   Emotion detection failed ({_emo_err}) — skipping")

            # ── 0d. Extract audio to WAV (16 kHz mono) ────────────────────
            logger.info(f"[{job_id}]   0d. Extracting audio for Whisper...")
            input_audio_path = os.path.join(work_dir, "input_audio.wav")
            audio_extract_service.extract_audio(input_video_path, input_audio_path)

            # ── 0e. Whisper STT ───────────────────────────────────────────
            if stt_service is not None:
                logger.info(f"[{job_id}]   0e. Transcribing with Whisper...")
                stt_result = await stt_service.transcribe_audio_file(input_audio_path)

                transcribed_text: str = stt_result.get("text", "").strip()
                detected_lang = (stt_result.get("language") or "").lower().strip()

                logger.info(
                    f"[{job_id}]   Whisper: lang='{detected_lang}' "
                    f"text='{transcribed_text[:100]}...'"
                )

                if not transcribed_text:
                    logger.warning(
                        f"[{job_id}]   Whisper returned empty transcription — "
                        f"keeping default topic: '{topic}'"
                    )
                else:
                    topic = transcribed_text
            else:
                logger.warning(f"[{job_id}]   Whisper not available — using topic: '{topic}'")

            # ── 0f. IndicTrans2 translation (skip if already English) ─────
            if topic and detected_lang and detected_lang != "en":
                logger.info(
                    f"[{job_id}]   0f. Translating '{detected_lang}' → 'en' via IndicTrans2..."
                )
                ai4bharat_url = os.environ.get(
                    "AI4BHARAT_BASE_URL", "http://host.docker.internal:5000"
                )
                async with httpx.AsyncClient(
                    timeout=httpx.Timeout(30.0, connect=10.0)
                ) as http_client:
                    translator = AI4BharatClient(
                        http_client,
                        base_url=ai4bharat_url,
                        translate_path="/translate",
                    )
                    try:
                        trans_result = await translator.translate_text(
                            text=topic,
                            source_language=detected_lang,   # ← pass Whisper-detected language
                            target_language="en",
                        )
                        translated_text: str = trans_result.get("translated_text", "").strip()
                        if translated_text:
                            logger.info(
                                f"[{job_id}]   IndicTrans2: '{topic[:60]}' "
                                f"→ '{translated_text[:60]}'"
                            )
                            topic = translated_text
                        else:
                            logger.warning(
                                f"[{job_id}]   IndicTrans2 returned empty string — "
                                f"keeping Whisper transcription."
                            )
                    except Exception as exc:
                        logger.warning(
                            f"[{job_id}]   IndicTrans2 translation failed ({exc}) — "
                            f"falling back to Whisper transcription."
                        )
            elif detected_lang == "en":
                logger.info(
                    f"[{job_id}]   0f. Language is already English — skipping translation."
                )
            else:
                logger.info(
                    f"[{job_id}]   0f. No detected language info — skipping translation."
                )

            # ── 0g. Profanity filter on final English topic ───────────────
            logger.info(f"[{job_id}]   0g. Applying profanity filter...")
            topic, was_filtered = clean_text(topic)
            if was_filtered:
                logger.warning(
                    f"[{job_id}]   Profanity detected and replaced in topic text."
                )
            # Fallback if topic became empty or only asterisks after filtering
            if not topic.replace("*", "").replace(" ", "").strip():
                logger.warning(
                    f"[{job_id}]   Topic reduced to empty after filtering — "
                    f"using default."
                )
                topic = f"a funny {detected_pet or 'pet'}"

        elif raw_topic:
            # No video_url — but topic was passed directly: still filter it
            logger.info(f"[{job_id}] Applying profanity filter to provided topic...")
            topic, was_filtered = clean_text(raw_topic.strip())
            if was_filtered:
                logger.warning(f"[{job_id}] Profanity replaced in topic.")
            if not topic.replace("*", "").replace(" ", "").strip():
                topic = "funny pet roast"

        # Re-compute cache key AFTER translation/filtering so the key reflects
        # actual content, not the raw unprocessed input values
        cache_key = f"cache:video:{hash(topic + str(image_url_req) + str(video_url_req))}"
        cached_url = await redis.get(cache_key)
        if cached_url:
            logger.info(f"[{job_id}] Cache HIT for topic: '{topic[:60]}'")
            return {
                "video_url": cached_url.decode("utf-8"),
                "duration": 10.0,
                "processing_time": 0.0,
                "estimated_cost": 0.0,
                "cached": True,
            }

        logger.info(f"[{job_id}] Final topic for generation: '{topic[:120]}'")

        # ================================================================
        # STEP 1 — Generate script (roast + captions + image_prompt)
        # ================================================================
        logger.info(f"[{job_id}] Step 1: Generating Script via GPT-4o-mini...")
        script_data = await script_service.generate_script(
            topic,
            pet_type=detected_pet,
            detected_language=detected_lang,
            pet_emotion=detected_emotion,
        )
        cost_steps["script_generated"] = True

        script_text: str = script_data["script"]
        captions: list = script_data.get("captions", [])
        raw_image_prompt: str = script_data.get(
            "image_prompt",
            f"A funny photorealistic {detected_pet or 'pet'}: {topic}"
        )

        # ================================================================
        # STEP 1b — Build optimised fal.ai prompts
        # ================================================================
        fal_image_prompt = ScriptService.build_fal_image_prompt(
            raw_image_prompt, topic, pet_type=detected_pet, pet_emotion=detected_emotion
        )
        fal_video_prompt = ScriptService.build_fal_video_prompt(fal_image_prompt, script_text)

        logger.info(f"[{job_id}]   fal image prompt: {fal_image_prompt[:100]}...")
        logger.info(f"[{job_id}]   fal video prompt: {fal_video_prompt[:100]}...")

        # ================================================================
        # STEP 2 — Generate image (Flux Schnell) or use provided image_url
        # ================================================================
        logger.info(f"[{job_id}] Step 2: Image generation...")
        if image_url_req:
            image_url = image_url_req
            logger.info(f"[{job_id}]   Using provided image URL.")
        else:
            image_url = await image_service.generate_image(fal_image_prompt)
            cost_steps["image_generated"] = True
            logger.info(f"[{job_id}]   Image generated: {image_url[:80]}...")

        # ================================================================
        # STEP 3 — Generate 3s video (Kling 1.6)
        # ================================================================
        logger.info(f"[{job_id}] Step 3: Video generation (Kling 1.6)...")
        generated_video_url = await fal_video_service.generate_video(
            image_url, fal_video_prompt
        )
        cost_steps["video_generated"] = True
        logger.info(f"[{job_id}]   Video URL: {generated_video_url[:80]}...")

        # Download generated video
        video_path = os.path.join(work_dir, "source_video.mp4")
        async with httpx.AsyncClient(timeout=httpx.Timeout(90.0, connect=30.0)) as client:
            resp = await client.get(generated_video_url)
            resp.raise_for_status()
            with open(video_path, "wb") as f:
                f.write(resp.content)

        # ================================================================
        # STEP 4 — Text-to-speech (Edge-TTS)
        # ================================================================
        logger.info(f"[{job_id}] Step 4: Generating TTS audio...")
        audio_path = os.path.join(work_dir, "audio.mp3")
        await tts_service.generate_audio(script_text, audio_path)

        # ================================================================
        # STEP 5 — Assemble final video (FFmpeg)
        # ================================================================
        logger.info(f"[{job_id}] Step 5: Editing final video with FFmpeg...")
        final_output = os.path.join(settings.OUTPUT_DIR, f"{job_id}.mp4")
        editor_result = editor_service.process_video(
            video_path=video_path,
            audio_path=audio_path,
            captions=captions,
            output_path=final_output,
        )

        total_cost = CostTracker.calculate_cost(cost_steps)
        processing_time = round(time.time() - start_time, 2)
        duration = editor_result.get("duration", 10.0)

        # Cache for 7 days
        await redis.setex(cache_key, 86400 * 7, final_output)

        logger.info(
            f"[{job_id}] ✓ Job complete — duration={duration}s "
            f"cost=${total_cost:.4f} time={processing_time}s"
        )
        return {
            "video_url": final_output,
            "duration": duration,
            "processing_time": processing_time,
            "estimated_cost": total_cost,
            "cached": False,
        }

    except ValueError as exc:
        # Validation errors (no audio, no pet) — user-facing message
        logger.error(f"[{job_id}] Validation error: {exc}")
        return {"status": "failed", "error": str(exc)}

    except Exception as exc:
        import traceback
        logger.error(f"[{job_id}] Job failed: {exc}\n{traceback.format_exc()}")
        return {"status": "failed", "error": str(exc)}

    finally:
        import shutil
        if os.path.exists(work_dir):
            try:
                shutil.rmtree(work_dir)
                logger.info(f"[{job_id}] Temp directory cleaned: {work_dir}")
            except Exception as exc:
                logger.error(f"[{job_id}] Failed to clean temp dir: {exc}")


# ---------------------------------------------------------------------------
# Helper — detect pet and also return the label
# ---------------------------------------------------------------------------

def _format_pet_label(species_list: list[str]) -> str:
    """Convert a list of species names to a natural English string.
    e.g. ['dog'] → 'dog'
         ['dog', 'cat'] → 'dog and cat'
         ['dog', 'cat', 'sheep'] → 'dog, cat, and sheep'
    """
    if len(species_list) == 1:
        return species_list[0]
    if len(species_list) == 2:
        return f"{species_list[0]} and {species_list[1]}"
    return ", ".join(species_list[:-1]) + f", and {species_list[-1]}"


async def _detect_all_pets_in_frame(
    vision_svc: VisionService, frame_path: str
) -> dict[str, float]:
    """
    Run multi-scale YOLO detection via VisionService.detect_all_pets().
    Returns a dict {pet_label: best_confidence} for EVERY species found
    in the frame (supports multi-pet videos).
    """
    if vision_svc.net is None:
        logger.warning("VisionService model not loaded — skipping pet detection.")
        return {}

    if not os.path.exists(frame_path):
        logger.error(f"Frame file not found: {frame_path}")
        return {}

    try:
        import cv2
        image = cv2.imread(frame_path)
        if image is None:
            logger.error(f"Cannot read frame: {frame_path}")
            return {}

        found = vision_svc.detect_all_pets(image)
        if found:
            summary = ", ".join(f"{l}={c:.3f}" for l, c in found.items())
            logger.info(f"YOLO detected in frame: {summary}")
        return found

    except Exception as exc:
        logger.error(f"YOLO detection error: {exc}")
        return {}


async def startup(ctx):
    logger.info("ARQ Worker starting...")


async def shutdown(ctx):
    logger.info("ARQ Worker shutting down...")


class WorkerSettings:
    functions = [generate_video_job]
    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
    on_startup = startup
    on_shutdown = shutdown
