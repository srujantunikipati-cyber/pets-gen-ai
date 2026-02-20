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

async def generate_video_job(ctx, job_req: dict):
    """
    Main Pipeline Job
    """
    import time
    start_time = time.time()
    
    topic = job_req.get("topic") or "funny pet roast"
    image_url_req = job_req.get("image_url")
    video_url_req = job_req.get("video_url")
    job_id = ctx["job_id"]
    redis = ctx["redis"]
    
    # Check cache to prevent duplicate renders
    cache_key = f"cache:video:{hash(topic + str(image_url_req) + str(video_url_req))}"
    cached_url = await redis.get(cache_key)
    if cached_url:
        logger.info(f"[{job_id}] Found cached video for topic: {topic}")
        return {
            "video_url": cached_url.decode('utf-8'),
            "duration": 10.0,
            "processing_time": 0.0,
            "estimated_cost": 0.0,
            "cached": True
        }

    work_dir = os.path.join(settings.TEMP_DIR, job_id)
    os.makedirs(work_dir, exist_ok=True)
    
    cost_steps = {}
    
    try:
        if video_url_req:
            logger.info(f"[{job_id}] Step 0: Processing Input Video (Whisper + IndicTrans2)")
            # Download input video
            input_video_path = os.path.join(work_dir, "input_video.mp4")
            async with httpx.AsyncClient(timeout=httpx.Timeout(60.0, connect=60.0)) as client:
                resp = await client.get(video_url_req)
                with open(input_video_path, "wb") as f:
                    f.write(resp.content)
            
            # --- VALIDATION 1: CHECK AUDIO ---
            logger.info(f"[{job_id}] Validating Audio Stream...")
            if not audio_extract_service.has_audio(input_video_path):
                raise Exception("No audio detected in the video. Please provide a video containing audio.")
                
            # --- VALIDATION 2: CHECK PET ---
            logger.info(f"[{job_id}] Validating Pet Content...")
            frame_path = os.path.join(work_dir, "frame.jpg")
            audio_extract_service.extract_frame(input_video_path, frame_path)
            
            is_pet = await vision_service.detect_pet_in_image(frame_path)
            if not is_pet:
                raise Exception("No pet detected in the video. Please upload a video clearly showing a pet.")
            
            # Extract audio
            input_audio_path = os.path.join(work_dir, "input_audio.wav")
            audio_extract_service.extract_audio(input_video_path, input_audio_path)
            
            # Transcribe via Whisper
            if stt_service:
                stt_result = await stt_service.transcribe_audio_file(input_audio_path)
                transcribed_text = stt_result.get("text", "")
                logger.info(f"[{job_id}] Whisper Transcription: {transcribed_text}")
                topic = transcribed_text
                
                # Try translation via local IndicTrans2 API
                ai4bharat_url = os.environ.get("AI4BHARAT_BASE_URL", "http://host.docker.internal:5000")
                async with httpx.AsyncClient() as client:
                    translator = AI4BharatClient(client, base_url=ai4bharat_url, translate_path="/translate")
                    try:
                        trans_result = await translator.translate_text(text=topic, target_language="en")
                        translated_text = trans_result.get("translated_text", topic)
                        logger.info(f"[{job_id}] IndicTrans2 Translation: {translated_text}")
                        topic = translated_text
                    except Exception as e:
                        logger.warning(f"[{job_id}] IndicTrans2 local translation failed: {e}. Falling back to Whisper text.")
            else:
                logger.warning(f"[{job_id}] Whisper not available, using empty topic")

        logger.info(f"[{job_id}] Step 1: Generating Script for '{topic}'")
        script_data = await script_service.generate_script(topic)
        cost_steps["script_generated"] = True
        
        script_text = script_data["script"]
        captions = script_data.get("captions", [])
        image_prompt = script_data.get("image_prompt", f"A funny photo of a pet: {topic}")
        
        logger.info(f"[{job_id}] Step 2: Generating Image")
        # Ensure we have an image URL. If user uploaded one, use it.
        if image_url_req:
            image_url = image_url_req
        else:
            image_url = await image_service.generate_image(image_prompt)
            cost_steps["image_generated"] = True
            
        logger.info(f"[{job_id}] Step 3: Generating Video (3s)")
        # We use the prompt + image to generate 3s video
        video_url = await fal_video_service.generate_video(image_url, image_prompt)
        cost_steps["video_generated"] = True
        
        # Download video to local
        # Downloading video_url to video_path
        video_path = os.path.join(work_dir, "source_video.mp4")
        async with httpx.AsyncClient(timeout=httpx.Timeout(60.0, connect=60.0)) as client:
            resp = await client.get(video_url)
            with open(video_path, "wb") as f:
                f.write(resp.content)
        
        logger.info(f"[{job_id}] Step 4: Generating TTS")
        audio_path = os.path.join(work_dir, "audio.mp3")
        await tts_service.generate_audio(script_text, audio_path)
        
        logger.info(f"[{job_id}] Step 5: Editing Video")
        final_output = os.path.join(settings.OUTPUT_DIR, f"{job_id}.mp4")
        
        editor_result = editor_service.process_video(
            video_path=video_path,
            audio_path=audio_path,
            captions=captions,
            output_path=final_output
        )
        
        total_cost = CostTracker.calculate_cost(cost_steps)
        processing_time = round(time.time() - start_time, 2)
        duration = editor_result.get("duration", 10.0)
        
        # Save to cache for 7 days
        await redis.setex(cache_key, 86400 * 7, final_output)
        
        return {
            "video_url": final_output,
            "duration": duration,
            "processing_time": processing_time,
            "estimated_cost": total_cost,
            "cached": False
        }

    except Exception as e:
        import traceback
        err_tb = traceback.format_exc()
        logger.error(f"Job {job_id} failed: {e}\n{err_tb}")
        return {"status": "failed", "error": str(e)}

async def startup(ctx):
    logger.info("Worker starting...")

async def shutdown(ctx):
    logger.info("Worker shutting down...")

class WorkerSettings:
    functions = [generate_video_job]
    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
    on_startup = startup
    on_shutdown = shutdown
