"""
Makes the narration audio for every joke in randomJokes.txt
"""

import asyncio

import edge_tts

from alexa_jokes import AUDIO_FOLDER, find_jokes_file, load_jokes

VOICE = "en-US-AvaMultilingualNeural"
RATE = "-5%"       
PITCH = "+0Hz"      
REMAKE_ALL = True   


async def make_all(jokes):
    for number, (setup, punchline) in enumerate(jokes, start=1):
        for part, text in (("setup", setup), ("punchline", punchline)):
            target = AUDIO_FOLDER / f"joke_{number:02d}_{part}.mp3"
            if target.exists() and not REMAKE_ALL:
                continue
            print(f"Making {target.name}: {text}")
            speech = edge_tts.Communicate(text, VOICE, rate=RATE, pitch=PITCH)
            await speech.save(str(target))


def main():
    path = find_jokes_file()
    if path is None:
        print("Could not find randomJokes.txt")
        return
    jokes = load_jokes(path)
    AUDIO_FOLDER.mkdir(parents=True, exist_ok=True)

    asyncio.run(make_all(jokes))

    print(f"\nDone. {len(jokes)} jokes, voice {VOICE}. Audio is in {AUDIO_FOLDER}")
    print("Put your laugh sound at assets/audio/laugh.mp3")


if __name__ == "__main__":
    main()