import json
from typing import Any, Optional


def try_parse_json(raw_text: str) -> Optional[Any]:
    if not raw_text:
        return None
    text = raw_text.strip()
    candidates = [text]

    first_object = text.find('{')
    last_object = text.rfind('}')
    if first_object != -1 and last_object != -1 and last_object > first_object:
        candidates.append(text[first_object:last_object + 1])

    first_array = text.find('[')
    last_array = text.rfind(']')
    if first_array != -1 and last_array != -1 and last_array > first_array:
        candidates.append(text[first_array:last_array + 1])

    for candidate in candidates:
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            continue
    return None
