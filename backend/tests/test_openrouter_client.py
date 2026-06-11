import json
import unittest
from unittest.mock import AsyncMock, patch

import httpx
from fastapi import HTTPException

from app import openrouter_client


class _FakeStreamResponse:
    def __init__(self, lines: list[str], status_code: int = 200):
        self.status_code = status_code
        self._lines = lines

    async def aiter_lines(self):
        for line in self._lines:
            yield line

    async def aread(self) -> bytes:
        return b'{"error": "upstream failed"}'


class _FakeStreamCM:
    def __init__(self, response: _FakeStreamResponse):
        self._response = response

    async def __aenter__(self):
        return self._response

    async def __aexit__(self, *exc):
        return False


def _patch_stream(response: _FakeStreamResponse):
    return patch.object(
        httpx.AsyncClient,
        "stream",
        lambda self, *args, **kwargs: _FakeStreamCM(response),
    )


def _sse(payload: dict) -> str:
    return "data: " + json.dumps(payload)


class TestCallOpenrouterNonStreaming(unittest.IsolatedAsyncioTestCase):
    async def test_whitespace_only_200_body_raises_502(self):
        # OpenRouter pads long non-streaming responses with whitespace
        # keep-alives; if the provider dies the body is whitespace only.
        fake = httpx.Response(200, content=b" \n \n \n   \n")
        with patch.object(
            httpx.AsyncClient, "post", AsyncMock(return_value=fake)
        ):
            with self.assertRaises(HTTPException) as ctx:
                await openrouter_client._call_openrouter(
                    [{"role": "user", "content": "hi"}]
                )
        self.assertEqual(ctx.exception.status_code, 502)

    async def test_valid_json_body_passes_through(self):
        envelope = {"choices": [{"message": {"content": "hello"}}]}
        fake = httpx.Response(200, content=json.dumps(envelope).encode())
        with patch.object(
            httpx.AsyncClient, "post", AsyncMock(return_value=fake)
        ):
            data = await openrouter_client._call_openrouter(
                [{"role": "user", "content": "hi"}]
            )
        self.assertEqual(data, envelope)


class TestCallOpenrouterStreaming(unittest.IsolatedAsyncioTestCase):
    async def test_aggregates_content_deltas(self):
        lines = [
            ": OPENROUTER PROCESSING",
            "",
            _sse({"choices": [{"delta": {"content": "<html>"}}]}),
            _sse({"choices": [{"delta": {"content": "<body>hi</body>"}}]}),
            _sse(
                {
                    "choices": [
                        {"delta": {"content": "</html>"}, "finish_reason": "stop"}
                    ]
                }
            ),
            "data: [DONE]",
        ]
        with _patch_stream(_FakeStreamResponse(lines)):
            data = await openrouter_client._call_openrouter(
                [{"role": "user", "content": "viz"}],
                tool_choice="none",
                stream=True,
            )
        choice = data["choices"][0]
        self.assertEqual(
            choice["message"]["content"], "<html><body>hi</body></html>"
        )
        self.assertEqual(choice["finish_reason"], "stop")

    async def test_aggregates_tool_call_deltas(self):
        lines = [
            _sse(
                {
                    "choices": [
                        {
                            "delta": {
                                "tool_calls": [
                                    {
                                        "index": 0,
                                        "id": "call_1",
                                        "function": {
                                            "name": "seek_video",
                                            "arguments": '{"sec',
                                        },
                                    }
                                ]
                            }
                        }
                    ]
                }
            ),
            _sse(
                {
                    "choices": [
                        {
                            "delta": {
                                "tool_calls": [
                                    {
                                        "index": 0,
                                        "function": {"arguments": 'onds": 12}'},
                                    }
                                ]
                            },
                            "finish_reason": "tool_calls",
                        }
                    ]
                }
            ),
            "data: [DONE]",
        ]
        with _patch_stream(_FakeStreamResponse(lines)):
            data = await openrouter_client._call_openrouter(
                [{"role": "user", "content": "skip"}], stream=True
            )
        tool_calls = data["choices"][0]["message"]["tool_calls"]
        self.assertEqual(len(tool_calls), 1)
        self.assertEqual(tool_calls[0]["id"], "call_1")
        self.assertEqual(tool_calls[0]["function"]["name"], "seek_video")
        self.assertEqual(
            tool_calls[0]["function"]["arguments"], '{"seconds": 12}'
        )

    async def test_mid_stream_error_event_raises_502(self):
        lines = [
            _sse({"choices": [{"delta": {"content": "partial"}}]}),
            _sse({"error": {"message": "provider exploded", "code": 502}}),
        ]
        with _patch_stream(_FakeStreamResponse(lines)):
            with self.assertRaises(HTTPException) as ctx:
                await openrouter_client._call_openrouter(
                    [{"role": "user", "content": "viz"}], stream=True
                )
        self.assertEqual(ctx.exception.status_code, 502)

    async def test_non_200_stream_raises_502(self):
        with _patch_stream(_FakeStreamResponse([], status_code=429)):
            with self.assertRaises(HTTPException) as ctx:
                await openrouter_client._call_openrouter(
                    [{"role": "user", "content": "viz"}], stream=True
                )
        self.assertEqual(ctx.exception.status_code, 502)

    async def test_malformed_sse_line_is_skipped(self):
        lines = [
            "data: {not valid json",
            _sse(
                {
                    "choices": [
                        {"delta": {"content": "ok"}, "finish_reason": "stop"}
                    ]
                }
            ),
            "data: [DONE]",
        ]
        with _patch_stream(_FakeStreamResponse(lines)):
            data = await openrouter_client._call_openrouter(
                [{"role": "user", "content": "viz"}], stream=True
            )
        self.assertEqual(data["choices"][0]["message"]["content"], "ok")


if __name__ == "__main__":
    unittest.main()
