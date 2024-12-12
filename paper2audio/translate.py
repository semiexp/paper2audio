import asyncio
from enum import Enum

import openai


class TranslateType(Enum):
    DEFAULT = 0
    SPEECH = 1
    ZUNDA = 2


PROMPTS = {
    TranslateType.DEFAULT: """
与えられた文章を日本語に翻訳してください。[a math expression 0] のような表記はそのままにしてください。
""",
    TranslateType.SPEECH: """
与えられた文章を日本語に翻訳してください。「OpenAI」→「オープンエーアイ」、「GPU」→「ジーピーユー」のように、英字からなる単語は必ずその読みのカタカナに置き換えるようにしてください。
""",
    TranslateType.ZUNDA: """
与えられた文章を日本語に翻訳してください。「変更する」→「変更するのだ」、「リンゴである」→「リンゴなのだ」のように、語尾を必ず「のだ」にするようにしてください。また、「OpenAI」→「オープンエーアイ」、「GPU」→「ジーピーユー」のように、英字からなる単語は必ずその読みのカタカナに置き換えるようにしてください。
""",
}


def run_translate(text: str, api_key: str, base_url: str | None = None, translate_type: TranslateType = TranslateType.DEFAULT) -> str:
    client = openai.Client(api_key=api_key, base_url=base_url)
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": PROMPTS[translate_type].strip()},
            {"role": "user", "content": text},
        ]
    )
    ret = resp.choices[0].message.content
    return ret


async def run_translate_many(texts: list[str], api_key: str, base_url: str | None = None, translate_type: TranslateType = TranslateType.DEFAULT) -> list[str]:
    client = openai.AsyncClient(api_key=api_key, base_url=base_url)
    
    requests = []
    for text in texts:
        requests.append(client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": PROMPTS[translate_type].strip()},
                {"role": "user", "content": text},
            ]
        ))

    responses = await asyncio.gather(*requests)
    ret = [resp.choices[0].message.content for resp in responses]
    return ret
