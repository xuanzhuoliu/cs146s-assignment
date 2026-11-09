#!/usr/bin/env python3
"""Export visible assistant messages and tool exchanges from a Droid session.

The original PTY transcript is retained separately. This readable export omits
session/account metadata, injected system reminders, and reasoning blocks.
It preserves the text, inputs, and results of visible tool exchanges verbatim.
"""
import argparse
import json
from pathlib import Path


def export(source: Path, destination: Path) -> None:
    records = []
    for line in source.read_text().splitlines():
        row = json.loads(line)
        message = row.get("message", {})
        content = message.get("content", [])
        if not isinstance(content, list):
            continue
        blocks = []
        for block in content:
            if not isinstance(block, dict):
                continue
            kind = block.get("type")
            if kind == "text" and message.get("role") == "assistant":
                blocks.append({"type": kind, "text": block.get("text", "")})
            elif kind == "tool_use":
                blocks.append({key: block[key] for key in
                               ("type", "id", "name", "input") if key in block})
            elif kind == "tool_result":
                blocks.append({key: block[key] for key in
                               ("type", "tool_use_id", "is_error", "content")
                               if key in block})
        if blocks:
            records.append({"timestamp": row.get("timestamp"),
                            "role": message.get("role"), "content": blocks})
    destination.write_text(json.dumps({"source_session": source.name,
                                      "records": records}, indent=2,
                                     ensure_ascii=False) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    export(args.source, args.destination)
