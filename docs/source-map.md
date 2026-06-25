# Source Map

This document maps the marketing repository to the upstream website, deployment, and runtime sources it is expected to stay aligned with.

| Product | Website narrative source | Visual/capture source | Deployment source | Runtime/service source |
| --- | --- | --- | --- | --- |
| Refiner | `src/refiner.jsx`, `src/refinerAnalysis.jsx`, `src/refinerResearch.jsx`, `src/refinerDelivery.jsx`, `src/seo/routeMeta.js` | `src/components/RefinerArchitectureAnimation.jsx`, `public/nmrefiner.png` | `ansible/continuum_tenant_refiner_site.yml`, `ansible/host_vars/spirit.yml` | `/home/pbisaacs/Developer/neuralmimicry/rag_demo` is the operator-facing workflow and job surface used by this repo |
| Continuum | `src/continuum.jsx`, `src/continuumOperations.jsx`, `src/continuumRecruitment.jsx`, `src/continuumSecurity.jsx`, `src/seo/routeMeta.js` | `src/components/ContinuumArchitectureAnimation.jsx`, `public/nmcontinuum.png` | shared `swarmhpc` Ansible control-plane tree, plus `ansible/host_vars/spirit.yml` | Continuum deployment logic is surfaced through `swarmhpc` and tenant orchestration patterns |
| Tracey | `src/tracey.jsx`, `src/traceyRuntime.jsx`, `src/traceyGovernance.jsx`, `src/traceyFleet.jsx`, `src/seo/routeMeta.js` | `src/components/TraceyArchitectureAnimation.jsx`, `public/nmtracey.png` | `ansible/tracey_site.yml` | host-agent deployment and closed-loop integration with Continuum |
| AARNN | `src/aarnnNeuroscience.jsx`, `src/aarnnNeuroscienceModel.jsx`, `src/aarnnNeuroscienceMind.jsx`, `src/aarnnNeuroscienceMedia.jsx`, `src/seo/routeMeta.js` | `src/components/AarnnAnimatedDiagrams.jsx`, `public/nmaarnn.png` | `ansible/continuum_tenant_aarnn_site.yml`, `ansible/CONTINUUM_TENANT_AARNN_ARCHITECTURE.md` | `/home/pbisaacs/Developer/neuralmimicry/aarnn_rust` and associated deployment patterns |
| Webots | `src/webots.jsx`, `src/lib/webotsAuth.js` | browser launch page and world cards; no dedicated website icon today | `ansible/continuum_tenant_webots_site.yml`, `ansible/host_vars/spirit.yml` | Webots broker with AARNN-aligned world metadata |

## Notes

- The website remains the primary public positioning source.
- The Ansible tree is the current deployment source of truth for hostnames, ingress, auth mode, and tenant/runtime shape.
- Product marks in `assets/brand/product-icons/` are copied from the website public asset set.
- The video prompts in this repo are intentionally grounded in the condensed product briefs and not in raw JSX alone, so they remain cheaper and more stable to feed into Refiner.
- Gail may still sit behind Refiner internally, but this repository uses Refiner as its runtime boundary.
