import asyncio
from services.speech_to_text import get_speech_to_text_service

async def run_test():
    stt = get_speech_to_text_service("tiny")
    if stt:
        print("STT Service Loaded!")
    else:
        print("STT failed to load")

if __name__ == "__main__":
    asyncio.run(run_test())
