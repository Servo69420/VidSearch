VIDEO_PLAYER_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "play_video",
            "description": (
                "Start or resume video playback. Use when the user asks "
                "to play, start, or resume the video."
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "pause_video",
            "description": (
                "Pause video playback. Use when the user asks "
                "to pause or stop the video."
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "seek_video",
            "description": (
                "Seek to a specific time in the video. Use when the user "
                "asks to jump to, go to, or skip to a specific timestamp. "
                "Convert timestamps like '2:30' to seconds (150)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "seconds": {
                        "type": "number",
                        "description": "Time in seconds to seek to.",
                    }
                },
                "required": ["seconds"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "mute_video",
            "description": (
                "Mute the video. Use when the user asks to mute "
                "or silence the video."
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "unmute_video",
            "description": (
                "Unmute the video. Use when the user asks to unmute "
                "or turn the sound back on."
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "request_visualization",
            "description": (
                "Generate an interactive visual (chart, diagram, timeline, "
                "comparison, etc.) about the video content when it would "
                "genuinely help the user understand. A separate specialised "
                "model builds the visual from the transcript — you only need "
                "to describe clearly what should be visualized."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "description": {
                        "type": "string",
                        "description": (
                            "What to visualize and why, e.g. 'timeline of the "
                            "key events discussed' or 'bar chart comparing the "
                            "approaches mentioned'."
                        ),
                    }
                },
                "required": ["description"],
            },
        },
    },
]
