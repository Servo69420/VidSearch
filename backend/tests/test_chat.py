import unittest
from unittest.mock import AsyncMock, patch

import httpx
from fastapi import HTTPException

from app.routers import chat as chat_module


def _oai(content: str | None, tool_calls: list | None) -> dict:
    msg: dict = {}
    if content is not None:
        msg["content"] = content
    if tool_calls is not None:
        msg["tool_calls"] = tool_calls
    return {"choices": [{"message": msg}]}


def _tc(call_id: str, name: str, args: str = "{}") -> dict:
    return {
        "id": call_id,
        "type": "function",
        "function": {"name": name, "arguments": args},
    }


class TestRunChatLoop(unittest.IsolatedAsyncioTestCase):
    async def test_pure_chat_single_round(self):
        mock = AsyncMock(return_value=_oai("Hello there.", None))
        with patch.object(chat_module, "_call_openrouter", mock):
            content, tool_calls = await chat_module._run_chat_loop(
                [{"role": "user", "content": "hi"}]
            )
        self.assertEqual(content, "Hello there.")
        self.assertEqual(tool_calls, [])
        mock.assert_awaited_once()

    async def test_tool_call_with_empty_content_triggers_second_call(self):
        tool_calls = [_tc("call_1", "seek_video", '{"seconds": 120}')]
        mock = AsyncMock(
            side_effect=[
                _oai("", tool_calls),
                _oai("I jumped to 2:00 in the video.", None),
            ]
        )
        with patch.object(chat_module, "_call_openrouter", mock):
            content, tc = await chat_module._run_chat_loop(
                [{"role": "user", "content": "skip to 2:00"}]
            )
        self.assertEqual(content, "I jumped to 2:00 in the video.")
        self.assertEqual(tc, tool_calls)
        self.assertEqual(mock.await_count, 2)

    async def test_second_call_uses_tool_choice_none(self):
        tool_calls = [_tc("c1", "play_video")]
        mock = AsyncMock(
            side_effect=[_oai("", tool_calls), _oai("Playing now.", None)]
        )
        with patch.object(chat_module, "_call_openrouter", mock):
            await chat_module._run_chat_loop([{"role": "user", "content": "play"}])
        second_kwargs = mock.await_args_list[1].kwargs
        self.assertEqual(second_kwargs.get("tool_choice"), "none")

    async def test_round2_content_replaces_round1_text(self):
        tool_calls = [_tc("c1", "pause_video")]
        mock = AsyncMock(
            side_effect=[
                _oai("Pausing.", tool_calls),
                _oai("The video is now paused.", None),
            ]
        )
        with patch.object(chat_module, "_call_openrouter", mock):
            content, tc = await chat_module._run_chat_loop([])
        self.assertEqual(content, "The video is now paused.")
        self.assertEqual(tc, tool_calls)

    async def test_round2_empty_falls_back_to_round1_content(self):
        tool_calls = [_tc("c1", "pause_video")]
        mock = AsyncMock(
            side_effect=[_oai("Pausing the video.", tool_calls), _oai("", None)]
        )
        with patch.object(chat_module, "_call_openrouter", mock):
            content, tc = await chat_module._run_chat_loop([])
        self.assertEqual(content, "Pausing the video.")
        self.assertEqual(tc, tool_calls)

    async def test_round2_failure_keeps_round1_content(self):
        tool_calls = [_tc("c1", "mute_video")]

        async def _side_effect(messages, tool_choice="auto"):
            if tool_choice == "none":
                raise HTTPException(status_code=502, detail="x")
            return _oai("Muting the video.", tool_calls)

        with patch.object(chat_module, "_call_openrouter", _side_effect):
            content, tc = await chat_module._run_chat_loop([])
        self.assertEqual(content, "Muting the video.")
        self.assertEqual(tc, tool_calls)

    async def test_round2_timeout_keeps_round1_content(self):
        tool_calls = [_tc("c1", "play_video")]

        async def _side_effect(messages, tool_choice="auto"):
            if tool_choice == "none":
                raise httpx.TimeoutException("timeout")
            return _oai("Starting playback.", tool_calls)

        with patch.object(chat_module, "_call_openrouter", _side_effect):
            content, tc = await chat_module._run_chat_loop([])
        self.assertEqual(content, "Starting playback.")
        self.assertEqual(tc, tool_calls)

    async def test_round1_error_propagates(self):
        mock = AsyncMock(side_effect=HTTPException(status_code=502, detail="x"))
        with patch.object(chat_module, "_call_openrouter", mock):
            with self.assertRaises(HTTPException):
                await chat_module._run_chat_loop([])

    async def test_round1_timeout_propagates(self):
        mock = AsyncMock(side_effect=httpx.TimeoutException("timeout"))
        with patch.object(chat_module, "_call_openrouter", mock):
            with self.assertRaises(httpx.TimeoutException):
                await chat_module._run_chat_loop([])

    async def test_both_rounds_empty_falls_back_to_tool_name_text(self):
        tool_calls = [_tc("c1", "seek_video")]
        mock = AsyncMock(
            side_effect=[_oai("", tool_calls), _oai("", None)]
        )
        with patch.object(chat_module, "_call_openrouter", mock):
            content, tc = await chat_module._run_chat_loop([])
        self.assertEqual(content, "*seek video*")
        self.assertEqual(tc, tool_calls)

    async def test_round2_returns_extra_tool_calls_are_ignored(self):
        round1_calls = [_tc("c1", "seek_video", '{"seconds": 30}')]
        round2_calls = [_tc("c2", "play_video")]
        mock = AsyncMock(
            side_effect=[
                _oai("", round1_calls),
                _oai("Jumped to 0:30 and playing.", round2_calls),
            ]
        )
        with patch.object(chat_module, "_call_openrouter", mock):
            content, tc = await chat_module._run_chat_loop([])
        self.assertEqual(content, "Jumped to 0:30 and playing.")
        self.assertEqual(tc, round1_calls)


class TestBuildToolResultTurns(unittest.TestCase):
    def test_builds_assistant_then_one_tool_turn_per_call(self):
        tool_calls = [_tc("a", "seek_video"), _tc("b", "play_video")]
        turns = chat_module._build_tool_result_turns(tool_calls, "hello")
        self.assertEqual(len(turns), 3)
        self.assertEqual(turns[0]["role"], "assistant")
        self.assertEqual(turns[0]["content"], "hello")
        self.assertEqual(turns[0]["tool_calls"], tool_calls)
        self.assertEqual(turns[1]["role"], "tool")
        self.assertEqual(turns[1]["tool_call_id"], "a")
        self.assertEqual(turns[2]["tool_call_id"], "b")

    def test_tool_result_content_is_json_dispatched_stub(self):
        turns = chat_module._build_tool_result_turns([_tc("x", "play_video")], "")
        self.assertIn("dispatched", turns[1]["content"])

    def test_assistant_content_is_null_when_round1_content_empty(self):
        turns = chat_module._build_tool_result_turns([_tc("x", "play_video")], "")
        self.assertIsNone(turns[0]["content"])

    def test_assistant_content_preserved_when_round1_text_present(self):
        turns = chat_module._build_tool_result_turns(
            [_tc("x", "play_video")], "preamble"
        )
        self.assertEqual(turns[0]["content"], "preamble")


class TestToolCallFallbackText(unittest.TestCase):
    def test_joins_tool_names_with_underscores_replaced(self):
        text = chat_module._tool_call_fallback_text(
            [_tc("a", "seek_video"), _tc("b", "play_video")]
        )
        self.assertEqual(text, "*seek video*, *play video*")


if __name__ == "__main__":
    unittest.main()
