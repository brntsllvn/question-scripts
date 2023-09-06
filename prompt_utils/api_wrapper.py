import aiohttp
import json
import os

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

ENDPOINT = 'https://api.openai.com/v1/chat/completions'
HEADERS = {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {OPENAI_API_KEY}'
}


def construct_body(model, role, prompt, temperature):
    return {
        "model": model,
        "messages": [
            {"role": "system", "content": role},
            {"role": "user", "content": prompt}
        ],
        "temperature": temperature
    }


async def execute_prompt(session, body):
    try:
        async with session.post(ENDPOINT, headers=HEADERS, data=json.dumps(body)) as response:
            res = await response.json()
            try:
                if res.get("choices", None) is None:
                    if res.get("error"):
                        print(res.get("error").get("message"))
                        return None, None
                content = res.get("choices")[0].get("message").get("content")
                usage = res.get("usage")
                return content, usage
            except (TypeError, AttributeError, IndexError) as e:
                print(f'Result contained error: {e}. Skipping question...')
                return None, None
    except aiohttp.ServerDisconnectedError:
        print(f'Server disconnected. Skipping question...')
        return None, None
    except Exception as e:
        print(f'Exception occurred: {str(e)}. Skipping question...')
        return None, None
