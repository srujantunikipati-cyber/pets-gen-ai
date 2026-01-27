#!/usr/bin/env python3
"""
Simple FastAPI inference server for IndicTrans2 translation.
Provides a REST API endpoint compatible with the Pet Roast backend.
"""

import os
import sys
from typing import Optional

import torch  # type: ignore
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

# Add IndicTrans2 directories to path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(SCRIPT_DIR, "huggingface_interface"))

# Import IndicTrans2 components
try:
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer  # type: ignore[import-untyped]
    from IndicTransToolkit.processor import IndicProcessor  # type: ignore[import-not-found]
except ImportError:
    print("ERROR: Required packages not installed. Run: pip install IndicTransToolkit")
    sys.exit(1)


# Language code mapping (simplified for common Indian languages)
ISO_TO_FLORES = {
    "hi": "hin_Deva",   # Hindi
    "bn": "ben_Beng",   # Bengali
    "gu": "guj_Gujr",   # Gujarati
    "mr": "mar_Deva",   # Marathi
    "kn": "kan_Knda",   # Kannada
    "te": "tel_Telu",   # Telugu
    "ml": "mal_Mlym",   # Malayalam
    "ta": "tam_Taml",   # Tamil
    "pa": "pan_Guru",   # Punjabi
    "or": "ory_Orya",   # Odia
    "as": "asm_Beng",   # Assamese
    "ur": "urd_Arab",   # Urdu
    "en": "eng_Latn",   # English
    "auto": "auto",     # Auto-detect
}


class TranslateRequest(BaseModel):
    input: str = Field(..., description="Text to translate")
    source_language: str = Field("auto", description="Source language ISO code (e.g., 'hi', 'en')")
    target_language: str = Field("en", description="Target language ISO code")


class TranslateResponse(BaseModel):
    output: str = Field(..., description="Translated text")
    source_language: str = Field(..., description="Detected or specified source language")
    target_language: str = Field(..., description="Target language")


# Global model and processor
model = None
tokenizer = None
ip = None
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"  # type: ignore


def load_model():
    """Load IndicTrans2 model on server startup."""
    global model, tokenizer, ip

    print(f"Loading IndicTrans2 model on {DEVICE}...")

    # Use the smaller distilled model for faster inference
    # For Indic -> English translation
    model_name = "ai4bharat/indictrans2-indic-en-dist-200M"

    try:
        print("Downloading/loading tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained(  # type: ignore
            model_name,
            trust_remote_code=True,
            token=False  # Use public model without authentication
        )

        print("Downloading/loading model (this may take several minutes on first run)...")
        model = AutoModelForSeq2SeqLM.from_pretrained(  # type: ignore
            model_name,
            trust_remote_code=True,
            token=False,  # Use public model without authentication
            torch_dtype=torch.float16 if DEVICE == "cuda" else torch.float32  # type: ignore
        ).to(DEVICE)  # type: ignore

        print("Initializing IndicProcessor...")
        ip = IndicProcessor(inference=True)  # type: ignore
        print(f"✅ Model loaded successfully on {DEVICE}")

    except Exception as e:
        print(f"❌ Error loading model: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure you have internet connection for first-time model download")
        print("2. The model is ~800MB and may take time to download")
        print("3. Check if you have enough disk space (~2GB free)")
        print(f"4. Model cache location: {os.path.expanduser('~/.cache/huggingface/')}")
        sys.exit(1)
def translate_text(text: str, src_lang: str, tgt_lang: str) -> str:
    """
    Translate text using IndicTrans2.

    Args:
        text: Input text to translate
        src_lang: Source language (ISO code or FLORES code)
        tgt_lang: Target language (ISO code or FLORES code)

    Returns:
        Translated text
    """
    # Convert ISO codes to FLORES codes if needed
    if src_lang in ISO_TO_FLORES:
        src_lang = ISO_TO_FLORES[src_lang]
    if tgt_lang in ISO_TO_FLORES:
        tgt_lang = ISO_TO_FLORES[tgt_lang]

    # For auto-detection, assume Hindi if not English
    if src_lang == "auto":
        src_lang = "hin_Deva"  # Default to Hindi for Indian languages

    try:
        # Preprocess
        batch = ip.preprocess_batch([text], src_lang, tgt_lang)  # type: ignore

        # Tokenize
        inputs = tokenizer(  # type: ignore
            batch,
            truncation=True,
            padding="longest",
            return_tensors="pt",
            return_attention_mask=True,
        ).to(DEVICE)  # type: ignore

        # Generate translation
        with torch.no_grad():  # type: ignore
            generated_tokens = model.generate(  # type: ignore
                **inputs,
                use_cache=True,
                min_length=0,
                max_length=256,
                num_beams=5,
                num_return_sequences=1,
            )

        # Decode
        with tokenizer.as_target_tokenizer():  # type: ignore
            generated_tokens = tokenizer.batch_decode(  # type: ignore
                generated_tokens.detach().cpu().tolist(),  # type: ignore
                skip_special_tokens=True,
                clean_up_tokenization_spaces=True,
            )

        # Postprocess
        translations = ip.postprocess_batch(generated_tokens, lang=tgt_lang)  # type: ignore

        return translations[0] if translations else text

    except Exception as e:
        print(f"Translation error: {e}")
        raise HTTPException(status_code=500, detail=f"Translation failed: {str(e)}")


# Create FastAPI app
app = FastAPI(
    title="IndicTrans2 Inference Server",
    description="Translation API for Indian languages using IndicTrans2",
    version="1.0.0"
)


@app.on_event("startup")
async def startup_event():
    """Load model on server startup."""
    load_model()


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "ok",
        "model": "IndicTrans2",
        "device": DEVICE,
        "message": "IndicTrans2 inference server is running"
    }


@app.post("/translate", response_model=TranslateResponse)
async def translate(request: TranslateRequest):
    """
    Translate text from source language to target language.

    Supported languages: hi, bn, gu, mr, kn, te, ml, ta, pa, or, as, ur, en
    """
    if not model or not tokenizer:
        raise HTTPException(status_code=503, detail="Model not loaded yet")

    try:
        translated = translate_text(
            request.input,
            request.source_language,
            request.target_language
        )

        return TranslateResponse(
            output=translated,
            source_language=request.source_language,
            target_language=request.target_language
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "model_loaded": model is not None,
        "device": DEVICE,
        "cuda_available": torch.cuda.is_available()
    }


if __name__ == "__main__":
    print("=" * 60)
    print("IndicTrans2 Inference Server")
    print("=" * 60)
    print(f"Device: {DEVICE}")
    print("Starting server on http://localhost:5000")
    print("=" * 60)

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=5000,
        log_level="info"
    )
