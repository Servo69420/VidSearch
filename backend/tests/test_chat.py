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

        async def _side_effect(messages, tool_choice="auto", model=None):
            if tool_choice == "none":
                raise HTTPException(status_code=502, detail="x")
            return _oai("Muting the video.", tool_calls)

        with patch.object(chat_module, "_call_openrouter", _side_effect):
            content, tc = await chat_module._run_chat_loop([])
        self.assertEqual(content, "Muting the video.")
        self.assertEqual(tc, tool_calls)

    async def test_round2_timeout_keeps_round1_content(self):
        tool_calls = [_tc("c1", "play_video")]

        async def _side_effect(messages, tool_choice="auto", model=None):
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


class TestBuildFollowupTurns(unittest.TestCase):
    def test_returns_two_turns(self):
        tool_calls = [_tc("a", "seek_video"), _tc("b", "play_video")]
        turns = chat_module._build_followup_turns(tool_calls, "hello")
        self.assertEqual(len(turns), 2)

    def test_first_turn_is_assistant(self):
        turns = chat_module._build_followup_turns([_tc("a", "seek_video")], "hi")
        self.assertEqual(turns[0]["role"], "assistant")

    def test_second_turn_is_user(self):
        turns = chat_module._build_followup_turns([_tc("a", "seek_video")], "hi")
        self.assertEqual(turns[1]["role"], "user")

    def test_round1_content_preserved_in_assistant_turn(self):
        turns = chat_module._build_followup_turns([_tc("a", "seek_video")], "preamble")
        self.assertEqual(turns[0]["content"], "preamble")

    def test_empty_round1_content_gets_default_message(self):
        turns = chat_module._build_followup_turns([_tc("a", "play_video")], "")
        self.assertIsNotNone(turns[0]["content"])
        self.assertGreater(len(turns[0]["content"]), 0)


class TestStripToolCallLiterals(unittest.TestCase):
    def test_strips_bracketed_toolcall_repr(self):
        text = "[ToolCall(func_name='seek_video', parameters={'seconds': 428.0})] Jumping now."
        self.assertEqual(
            chat_module._strip_tool_call_literals(text), "Jumping now."
        )

    def test_strips_unbracketed_toolcall_repr(self):
        text = "ToolCall(func_name='play_video', parameters={}) Starting playback."
        self.assertEqual(
            chat_module._strip_tool_call_literals(text), "Starting playback."
        )

    def test_strips_multiple_occurrences(self):
        text = (
            "[ToolCall(func_name='seek_video', parameters={'seconds': 10})] then "
            "[ToolCall(func_name='play_video', parameters={})] done."
        )
        self.assertEqual(
            chat_module._strip_tool_call_literals(text), "then  done."
        )

    def test_leaves_normal_text_unchanged(self):
        text = "I jumped to 2:00 and resumed playback."
        self.assertEqual(chat_module._strip_tool_call_literals(text), text)

    def test_strips_truncated_json_tool_call_fragment(self):
        text = (
            'mentioned around [].[{"tool_call_id": "651", "tool_type": "'
        )
        self.assertEqual(
            chat_module._strip_tool_call_literals(text),
            "mentioned around []",
        )

    def test_strips_complete_json_tool_call_fragment(self):
        text = (
            'Done [{"tool_call_id": "abc", "name": "seek_video"}] cool.'
        )
        self.assertEqual(
            chat_module._strip_tool_call_literals(text),
            "Done cool.",
        )

    def test_strips_bare_json_tool_call_dict(self):
        text = 'Here: {"tool_call_id": "xyz"} finished.'
        self.assertEqual(
            chat_module._strip_tool_call_literals(text),
            "Here: finished.",
        )

    def test_empty_input_returns_empty(self):
        self.assertEqual(chat_module._strip_tool_call_literals(""), "")

    async def _run_loop_with_hallucinated_literal(self):
        tool_calls = [_tc("c1", "seek_video", '{"seconds": 428}')]
        hallucinated = (
            "[ToolCall(func_name='seek_video', parameters={'seconds': 428.0})]"
            " Jumping to 7:08."
        )
        mock = AsyncMock(
            side_effect=[_oai("", tool_calls), _oai(hallucinated, None)]
        )
        with patch.object(chat_module, "_call_openrouter", mock):
            return await chat_module._run_chat_loop([])

    def test_run_loop_strips_literal_from_final_content(self):
        import asyncio

        content, _ = asyncio.run(self._run_loop_with_hallucinated_literal())
        self.assertEqual(content, "Jumping to 7:08.")


class TestStripReasoningTokens(unittest.TestCase):
    def test_harmony_keeps_only_final_channel(self):
        text = (
            "<|channel|>analysis<|message|>The user wants the capital. Let me "
            "think.<|end|><|start|>assistant<|channel|>final<|message|>"
            "The capital is Paris."
        )
        self.assertEqual(
            chat_module._strip_reasoning_tokens(text), "The capital is Paris."
        )

    def test_harmony_without_final_drops_analysis_segment(self):
        text = (
            "<|channel|>analysis<|message|>internal musing here<|end|>"
            "The actual answer."
        )
        self.assertEqual(
            chat_module._strip_reasoning_tokens(text), "The actual answer."
        )


class TestSplitVizRequest(unittest.TestCase):
    def test_no_tool_calls(self):
        description, player_calls = chat_module._split_viz_request([])
        self.assertIsNone(description)
        self.assertEqual(player_calls, [])

    def test_player_calls_pass_through_without_viz(self):
        calls = [_tc("c1", "play_video"), _tc("c2", "seek_video")]
        description, player_calls = chat_module._split_viz_request(calls)
        self.assertIsNone(description)
        self.assertEqual(player_calls, calls)

    def test_viz_call_is_extracted_and_stripped(self):
        viz = _tc(
            "c1",
            chat_module.VIZ_TOOL_NAME,
            '{"description": "a KVL timeline"}',
        )
        player = _tc("c2", "pause_video")
        description, player_calls = chat_module._split_viz_request(
            [viz, player]
        )
        self.assertEqual(description, "a KVL timeline")
        self.assertEqual(player_calls, [player])

    def test_viz_call_with_bad_arguments_yields_empty_description(self):
        viz = _tc("c1", chat_module.VIZ_TOOL_NAME, "not json")
        description, player_calls = chat_module._split_viz_request([viz])
        self.assertEqual(description, "")
        self.assertEqual(player_calls, [])

    def test_strips_think_block(self):
        text = "<think>hmm, let me reason about this</think>The answer is 42."
        self.assertEqual(
            chat_module._strip_reasoning_tokens(text), "The answer is 42."
        )

    def test_strips_thinking_block_case_insensitive(self):
        text = "<Thinking>secret</Thinking>Visible answer."
        self.assertEqual(
            chat_module._strip_reasoning_tokens(text), "Visible answer."
        )

    def test_strips_malformed_pipe_variants(self):
        # The exact surface form users reported: missing/misplaced pipes.
        text = "<|channel>thought goes here<channel|>Real reply."
        self.assertEqual(
            chat_module._strip_reasoning_tokens(text), "Real reply."
        )

    def test_strips_stray_control_tokens(self):
        text = "<|start|>assistant<|message|>Hello world.<|end|>"
        self.assertEqual(
            chat_module._strip_reasoning_tokens(text), "Hello world."
        )

    def test_leaves_normal_text_unchanged(self):
        text = "Here is a plain answer with no reasoning tokens."
        self.assertEqual(chat_module._strip_reasoning_tokens(text), text)

    def test_empty_input_returns_empty(self):
        self.assertEqual(chat_module._strip_reasoning_tokens(""), "")

    def test_strip_tool_call_literals_also_removes_reasoning(self):
        text = (
            "<think>plan the jump</think>"
            "[ToolCall(func_name='seek_video', parameters={'seconds': 10})] "
            "Jumping to 0:10."
        )
        self.assertEqual(
            chat_module._strip_tool_call_literals(text), "Jumping to 0:10."
        )


class TestToolCallFallbackText(unittest.TestCase):
    def test_joins_tool_names_with_underscores_replaced(self):
        text = chat_module._tool_call_fallback_text(
            [_tc("a", "seek_video"), _tc("b", "play_video")]
        )
        self.assertEqual(text, "*seek video*, *play video*")


if __name__ == "__main__":
    unittest.main()
