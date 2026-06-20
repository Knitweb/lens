# Optional Live Model Adapters

Lens keeps the base package offline and dependency-free. A live model adapter is
an optional object that implements:

```python
class MyLLM:
    def complete(self, query, context):
        ...
```

`context` is a sequence of ranked chunks. Use `render_model_prompt(query,
context)` to preserve the citation contract before sending context to a model.

```python
from knitweb_lens import LocalFilesAdapter, RLMHarness, render_model_prompt


class MyLiveLLM:
    def complete(self, query, context):
        prompt = render_model_prompt(query, context)
        return call_my_model(prompt)


answer = RLMHarness(llm=MyLiveLLM()).query(
    "What does Lens preserve?",
    adapters=[LocalFilesAdapter(["README.md"])],
)
```

## Boundary

Live adapters should stay outside the base package unless they require only the
Python standard library and keep credentials optional.

Do not add these to `knitweb-lens` core:

- mandatory OpenAI, local model, vector, graph database, or DKG SDK dependency;
- background daemons or agent runtimes;
- storage, signing, transport, anchoring, or publishing behavior;
- answers that drop Lens citation numbers or source references.

The base package owns retrieval, context selection, reliability, abstention, and
citation rendering. The live adapter owns only model completion.
