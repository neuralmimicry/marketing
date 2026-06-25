# Refiner

## Positioning

Refiner is NeuralMimicry's governed engineering workflow platform. It brings Jira statistics, Jira quality analysis, Confluence analysis, topic research, project solving, and delivery pipelines into one operating surface instead of spreading them across disconnected scripts and tools.

## Best fit

- Engineering leaders with fragmented delivery visibility
- Delivery managers who need evidence rather than opinion
- Platform teams evaluating AI assistance but unwilling to lose auditability
- Technical buyers who need to inspect controls, not just outcomes

## Proof themes

- Explicit workflow routing is a core part of the product story.
- Context gathering stays deliberately narrow before reasoning begins.
- Plan, act, verify, reflect is the clearest explanation of the agentic loop.
- Delivery work remains governed through staged execution and approvals.
- The service surface includes jobs, auth, OIDC, RAG, MCP, tokens, voice, metrics, and public API docs.

## Capture ideas

- `RefinerArchitectureAnimation` from the website
- product icon `assets/brand/product-icons/nmrefiner.png`
- Refiner CLI workflow help and documented modes
- Refiner control-plane UI or API docs
- examples of analysis, research, and delivery outputs rather than generic chat shots

## Training angle

Show a real sequence: choose workflow, submit or configure the run, inspect output, review verification, and show where governance and operational controls live.

## Source of truth

- Website: `${NM_LOCAL_REPO_ROOT}.ai-website/src/refiner.jsx`
- Supporting pages: `refinerAnalysis.jsx`, `refinerResearch.jsx`, `refinerDelivery.jsx`
- Deployment: `${SWARMHPC_ROOT}/swarmhpc/ansible/continuum_tenant_refiner_site.yml`
- Host/runtime settings: `${SWARMHPC_ROOT}/swarmhpc/ansible/host_vars/spirit.yml`
- Runtime repo and job/control-plane surface: `${NM_LOCAL_REPO_ROOT}/rag_demo`
- Internal orchestration dependency behind Refiner: `${NM_LOCAL_REPO_ROOT}/gail`
