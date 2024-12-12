import argparse
import asyncio
import json
import os

from paper2audio.arxiv import load_from_arxiv
from paper2audio.translate import run_translate_many
from paper2audio.speech import synthesize


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-key", type=str, default="apikey.txt")
    parser.add_argument("--abstract-only", action="store_true")
    parser.add_argument("--base-url", type=str, default=None)
    parser.add_argument("--output-audio", action="store_true")
    parser.add_argument("--translation-dir", type=str, default="translations")
    parser.add_argument("--voice-dir", type=str, default="voices")
    parser.add_argument("url", type=str)
    args = parser.parse_args()

    os.makedirs(args.translation_dir, exist_ok=True)

    url = args.url
    if not url.startswith("https://arxiv.org/html/"):
        raise ValueError("only arXiv HTML pages are supported")

    if url.endswith("/"):
        url = url[:-1]

    paper = load_from_arxiv(url)

    if args.abstract_only:
        texts = [paper.abstract]
    else:
        texts = paper.texts()
    tags = paper.all_tags()

    out_text_path = os.path.join(args.translation_dir, os.path.basename(url) + ".json")
    out_md_path = os.path.join(args.translation_dir, os.path.basename(url) + ".md")

    if os.path.exists(out_text_path):
        print("Translation already exists")

        with open(out_text_path, "r") as f:
            data = json.load(f)
            tags = data["tags"]
            texts = data["original"]
            translated = data["translated"]
            texts_math = data["original_math"]
            translated_math = data["translated_math"]
    else:
        with open(args.api_key, "r") as fp:
            api_key = fp.read().strip()
        translated = await run_translate_many(texts, api_key, base_url=args.base_url)

        for orig, trans in zip(texts, translated):
            print("-" * 80)
            print(f"Original: {orig}")
            print(f"Translated: {trans}")

        texts_math = [paper.restore_math_expr(text) for text in texts]
        translated_math = [paper.restore_math_expr(text) for text in translated]

        with open(out_text_path, "w") as f:
            data = {
                "tags": tags,
                "original": texts,
                "translated": translated,
                "original_math": texts_math,
                "translated_math": translated_math,
            }
            json.dump(data, f, indent=2, ensure_ascii=False)

    if os.path.exists(out_md_path):
        print("Markdown output already exists")
    else:
        with open(out_md_path, "w") as f:
            for tag, orig, trans in zip(tags, texts_math, translated_math):
                if tag == "p":
                    f.write(f"{orig}\n\n")
                    f.write(f"{trans}\n\n")
                else:
                    if tag == "h1":
                        prefix = "#"
                    elif tag == "h2":
                        prefix = "##"
                    elif tag == "h3":
                        prefix = "###"
                    else:
                        prefix = "####"

                    f.write(f"{prefix} {orig} / {trans}\n\n")

    if args.output_audio:
        os.makedirs(args.voice_dir, exist_ok=True)

        out_voice_path = os.path.join(args.voice_dir, os.path.basename(url) + ".wav")
        synthesized = synthesize("\n".join(translated))
        with open(out_voice_path, "wb") as f:
            f.write(synthesized)


if __name__ == "__main__":
    asyncio.run(main())
