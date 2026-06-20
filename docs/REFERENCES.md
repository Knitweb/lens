# Research References

Primary sources used to shape Lens v1:

- OpenCog Hyperon: https://hyperon.opencog.org/
- Hyperon experimental repository: https://github.com/trueagi-io/hyperon-experimental
- LightRAG repository: https://github.com/HKUDS/LightRAG
- LlamaIndex repository: https://github.com/run-llama/llama_index
- LangChain repository: https://github.com/langchain-ai/langchain
- IPFS Kademlia DHT specification: https://specs.ipfs.tech/routing/kad-dht/
- libp2p Kademlia DHT specification: https://github.com/libp2p/specs/blob/master/kad-dht/README.md
- W3C Verifiable Credentials Data Model 2.0: https://www.w3.org/TR/vc-data-model-2.0/
- W3C Verifiable Credential Data Integrity: https://w3c.github.io/vc-data-integrity/
- W3C DID Core: https://www.w3.org/TR/did-1.0/
- W3C ActivityStreams 2.0 Vocabulary: https://www.w3.org/TR/activitystreams-vocabulary/
- W3C ActivityPub: https://www.w3.org/TR/activitypub/
- OriginTrail DKG docs: https://docs.origintrail.io/
- ClaudeClaw by moazbuilds: https://github.com/moazbuilds/claudeclaw
- ClaudeClaw by sbusso: https://github.com/sbusso/claudeclaw

Design translation:

- Use Hyperon/MeTTa as inspiration for symbolic chunk iteration over a graph,
  not as a required dependency.
- Use graph paths and relation weights as retrieval evidence.
- Keep content identity, source id, and provenance explicit in returned
  citations.
- Treat ActivityStreams as readable social evidence, while delegating
  ActivityPub delivery/federation to actual ActivityPub systems.
- Keep optional integrations outside the core package.
