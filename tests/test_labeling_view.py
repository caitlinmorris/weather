from presence.eval.label_tool import _labeling_lines
from presence.pipeline.transcript_parser import parse_transcript
from tests.synthetic import write_synthetic_transcript

def test_labeling_view_keeps_conversation_collapses_churn(tmp_path):
    f = tmp_path / "s.jsonl"
    write_synthetic_transcript(f)
    lines = _labeling_lines(list(parse_transcript(f)))
    text = "\n".join(lines)
    assert "YOU: add a sorting function" in text
    assert "TOOL_RESULT" not in text
    assert "(ran tools" not in text
    # short non-question assistant lines + tool results collapse to markers
    assert "assistant/tool steps ⋯" in text
