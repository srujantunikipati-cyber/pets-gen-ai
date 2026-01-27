#!/usr/bin/env python3
"""
Simplified IndicTrans2 Inference Server with Mock Mode for Testing

This server provides two modes:
1. MOCK mode: Returns simple translations without loading models (for testing)
2. FULL mode: Uses actual IndicTrans2 models (requires HuggingFace token)

Set INDICTRANS_MODE=mock for testing without model download.
"""

import os
import sys
from typing import Optional

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

# Check mode
MOCK_MODE = os.getenv("INDICTRANS_MODE", "mock").lower() == "mock"

if not MOCK_MODE:
    try:
        import torch  # type: ignore[import-not-found]
        from transformers import AutoModelForSeq2SeqLM, AutoTokenizer  # type: ignore[import-untyped]
        from IndicTransToolkit.processor import IndicProcessor  # type: ignore[import-not-found]
    except ImportError:
        print("ERROR: IndicTransToolkit not installed. Run: pip install IndicTransToolkit")
        sys.exit(1)

# Language code mapping
ISO_TO_FLORES = {
    "hi": "hin_Deva",
    "bn": "ben_Beng",
    "gu": "guj_Gujr",
    "mr": "mar_Deva",
    "kn": "kan_Knda",
    "te": "tel_Telu",
    "ml": "mal_Mlym",
    "ta": "tam_Taml",
    "pa": "pan_Guru",
    "or": "ory_Orya",
    "as": "asm_Beng",
    "ur": "urd_Arab",
    "en": "eng_Latn",
    "auto": "auto",
}

# Simple mock translations for testing
MOCK_TRANSLATIONS = {
    "hi": {"en": " (translated from Hindi)"},
    "bn": {"en": " (translated from Bengali)"},
    "gu": {"en": " (translated from Gujarati)"},
    "mr": {"en": " (translated from Marathi)"},
    "ta": {"en": " (translated from Tamil)"},
    "te": {"en": " (translated from Telugu)"},
}


class TranslateRequest(BaseModel):
    input: str = Field(..., description="Text to translate")
    source_language: str = Field("auto", description="Source language ISO code")
    target_language: str = Field("en", description="Target language ISO code")


class TranslateResponse(BaseModel):
    output: str = Field(..., description="Translated text")
    source_language: str = Field(..., description="Source language")
    target_language: str = Field(..., description="Target language")


# Global model components (only used in FULL mode)
model = None
tokenizer = None
ip = None
DEVICE = "cpu"

if not MOCK_MODE:
    DEVICE = "cuda" if torch.cuda.is_available() else "cpu"  # type: ignore


def mock_translate(text: str, src_lang: str, tgt_lang: str) -> str:
    """Simple mock translation for testing."""
    suffix = MOCK_TRANSLATIONS.get(src_lang, {}).get(tgt_lang, f" (translated from {src_lang} to {tgt_lang})")
    return text + suffix


def load_model():
    """Load IndicTrans2 model (only in FULL mode)."""
    global model, tokenizer, ip

    if MOCK_MODE:
        print("⚠️  Running in MOCK mode - translations are simulated")
        print("   Set INDICTRANS_MODE=full to use real models")
        return

    print(f"Loading IndicTrans2 model on {DEVICE}...")
    model_name = "ai4bharat/indictrans2-indic-en-dist-200M"

    try:
        tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)  # type: ignore
        model = AutoModelForSeq2SeqLM.from_pretrained(  # type: ignore
            model_name,
            trust_remote_code=True,
            torch_dtype=torch.float16 if DEVICE == "cuda" else torch.float32  # type: ignore
        ).to(DEVICE)  # type: ignore
        ip = IndicProcessor(inference=True)  # type: ignore
        print(f"✅ Model loaded successfully on {DEVICE}")
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        print("\nFalling back to MOCK mode...")
        # Cannot change global MOCK_MODE here, just continue in current mode
        pass


def translate_full(text: str, src_lang: str, tgt_lang: str) -> str:
    """Translate using actual IndicTrans2 model."""
    if model is None or tokenizer is None or ip is None:
        raise RuntimeError("Model not loaded. Ensure FULL mode is enabled and models are initialized.")

    # Convert ISO to FLORES codes
    src_lang = ISO_TO_FLORES.get(src_lang, src_lang)
    tgt_lang = ISO_TO_FLORES.get(tgt_lang, tgt_lang)

    if src_lang == "auto":
        src_lang = "hin_Deva"  # Default to Hindi

    try:
        batch = ip.preprocess_batch([text], src_lang, tgt_lang)  # type: ignore[union-attr]
        inputs = tokenizer(  # type: ignore[misc]
            batch,
            truncation=True,
            padding="longest",
            return_tensors="pt",
            return_attention_mask=True,
        ).to(DEVICE)  # type: ignore[union-attr]

        with torch.no_grad():  # type: ignore[attr-defined]
            generated_tokens = model.generate(  # type: ignore[union-attr]
                **inputs,
                use_cache=True,
                min_length=0,
                max_length=256,
                num_beams=5,
                num_return_sequences=1,
            )

        with tokenizer.as_target_tokenizer():  # type: ignore
            generated_tokens = tokenizer.batch_decode(  # type: ignore
                generated_tokens.detach().cpu().tolist(),  # type: ignore
                skip_special_tokens=True,
                clean_up_tokenization_spaces=True,
            )

        translations = ip.postprocess_batch(generated_tokens, lang=tgt_lang)  # type: ignore
        return translations[0] if translations else text
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Translation failed: {str(e)}")


# Create FastAPI app
app = FastAPI(
    title="IndicTrans2 Inference Server",
    description="Translation API for Indian languages (Mock Mode for Testing)",
    version="1.0.0"
)


@app.on_event("startup")
async def startup_event():
    """Initialize on startup."""
    load_model()


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "ok",
        "mode": "mock" if MOCK_MODE else "full",
        "model": "IndicTrans2",
        "device": DEVICE if not MOCK_MODE else "N/A",
        "message": "IndicTrans2 inference server is running" + (" in MOCK mode" if MOCK_MODE else "")
    }


@app.post("/translate", response_model=TranslateResponse)
async def translate(request: TranslateRequest):
    """Translate text between supported languages."""
    try:
        if MOCK_MODE:
            translated = mock_translate(
                request.input,
                request.source_language,
                request.target_language
            )
        else:
            if not model or not tokenizer:
                raise HTTPException(status_code=503, detail="Model not loaded")
            translated = translate_full(
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
        "mode": "mock" if MOCK_MODE else "full",
        "model_loaded": not MOCK_MODE and (model is not None),
        "device": DEVICE if not MOCK_MODE else "N/A"
    }


if __name__ == "__main__":
    mode_str = "MOCK" if MOCK_MODE else "FULL"
    print("=" * 60)
    print(f"IndicTrans2 Inference Server ({mode_str} MODE)")
    print("=" * 60)
    if MOCK_MODE:
        print("⚠️  Running in MOCK mode - for testing only")
        print("   Translations are simulated and not accurate")
        print("   Set INDICTRANS_MODE=full for real translations")
    else:
        print(f"Device: {DEVICE}")
    print("Starting server on http://localhost:5000")
    print("=" * 60)

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=5000,
        log_level="info"
    )
