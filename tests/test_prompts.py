from knitweb_lens import LocalFilesAdapter, RLMHarness, render_model_prompt


class PromptEchoLLM:
    def complete(self, query, context):
        return render_model_prompt(query, context)


def test_render_model_prompt_preserves_citation_contract(tmp_path):
    path = tmp_path / "source.md"
    path.write_text("Lens sends cited context to optional model adapters.", encoding="utf-8")
    session = RLMHarness().session("What does Lens send?", adapters=[LocalFilesAdapter([path])])

    prompt = render_model_prompt(session.query, session.ranked_chunks)

    assert "Answer the query using only the cited Lens context." in prompt
    assert "[1] source_id: local-files" in prompt
    assert f"[1] source_uri: {path}" in prompt
    assert "[1] cid_or_node:" in prompt
    assert "[1] text: Lens sends cited context" in prompt


def test_custom_llm_adapter_can_use_prompt_renderer(tmp_path):
    path = tmp_path / "source.md"
    path.write_text("Live adapters can reuse Lens prompt rendering.", encoding="utf-8")

    answer = RLMHarness(llm=PromptEchoLLM()).query("What can live adapters reuse?", adapters=[LocalFilesAdapter([path])])

    assert "Preserve citation numbers" in answer.text
    assert "[1] source_id: local-files" in answer.text
    assert answer.reliability["status"] == "answered"
