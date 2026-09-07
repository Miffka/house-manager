"""A thin synchronous client over the Telegram Bot API.

Only the handful of methods the bot needs. Long-polling is done by the caller
(``run_bot``) via :meth:`TelegramClient.get_updates`.
"""

import httpx

DEFAULT_API_BASE = "https://api.telegram.org"


class TelegramError(RuntimeError):
    """The Bot API returned ``ok: false``."""


class TelegramClient:
    def __init__(self, token, api_base=DEFAULT_API_BASE, timeout=65.0):
        self._base_url = f"{api_base}/bot{token}"
        self._http = httpx.Client(timeout=timeout)

    def _call(self, method, **params):
        payload = {k: v for k, v in params.items() if v is not None}
        response = self._http.post(f"{self._base_url}/{method}", json=payload)
        response.raise_for_status()
        data = response.json()
        if not data.get("ok"):
            raise TelegramError(data.get("description", data))
        return data.get("result")

    def get_updates(self, offset=None, timeout=30):
        return self._call("getUpdates", offset=offset, timeout=timeout)

    def send_message(self, chat_id, text, reply_markup=None, parse_mode=None):
        return self._call(
            "sendMessage",
            chat_id=chat_id,
            text=text,
            reply_markup=reply_markup,
            parse_mode=parse_mode,
        )

    def answer_callback_query(self, callback_query_id, text=None):
        return self._call(
            "answerCallbackQuery",
            callback_query_id=callback_query_id,
            text=text,
        )

    def close(self):
        self._http.close()
