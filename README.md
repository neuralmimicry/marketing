# NeuralMimicry Marketing Repository

## Sponsor NeuralMimicry

NeuralMimicry is an independent open-source initiative building neuromorphic AI, autonomous systems, and developer tooling. This repository holds the brand assets, messaging frameworks, and media resources that tell that story. If our work resonates with you, please consider supporting us.

**[☕ Support us on Crowdfunder](https://www.crowdfunder.co.uk/p/qr/aWggxwPW?utm_campaign=sharemodal&utm_medium=referral&utm_source=shortlink)**

---

This repository is the working home for NeuralMimicry marketing information, reusable messaging, brand assets, media planning, and video-production resources.

It is grounded in three live source trees:
- commercial website: `${NM_LOCAL_REPO_ROOT}.ai-website`
- deployment inventory and install playbooks: `${SWARMHPC_ROOT}/swarmhpc/ansible`
- Refiner workflow platform used for marketing drafts and transcripts: `${NM_LOCAL_REPO_ROOT}/rag_demo`

## Product scope

Primary commercial products and product-adjacent surfaces tracked here:
- Refiner
- Continuum
- Tracey
- AARNN
- Webots

Gail remains an internal Refiner dependency for orchestration and transcription where configured, but this repository now treats Refiner as the operator-facing workflow surface.

## Repository map

- `catalog/`: machine-readable product inventory and source references
- `products/`: human-readable briefs for each marketed product
- `assets/brand/`: copied product marks from the commercial website
- `docs/messaging/`: shared language and positioning rules
- `docs/workflows/`: operating playbooks for creating and maintaining marketing outputs
- `videos/manifests/`: structured deliverable definitions for product and training videos
- `videos/prompts/`: prompt packs for Refiner topic-research drafting
- `media/`: per-product folders for raw, edit, export, caption, and thumbnail assets
- `scripts/`: local automation for Refiner job submission and Refiner-managed transcription
- `build/`: generated drafts and workflow job artefacts; intentionally ignored by git

## Working model

1. Update the product briefs and source map whenever the website or deployment code changes.
2. Keep prompts and manifests in git; treat generated drafts as build artefacts.
3. Use Refiner to draft video scripts, storyboards, and asset lists.
4. Use Refiner to manage topic-research jobs and transcript generation, letting it delegate to its configured backend services internally.
5. Keep final, approved assets under `media/<product>/` once they exist.

## Quick start

List available draft targets:

```bash
python3 scripts/refiner_video_pipeline.py list
```

Preview the Refiner job payload for a product video:

```bash
python3 scripts/refiner_video_pipeline.py draft refiner --kind product --print-only
```

Run a real Refiner draft with an authenticated session:

```bash
python3 scripts/refiner_video_pipeline.py draft refiner --kind product \
  --username "$REFINER_USERNAME" \
  --password "$REFINER_PASSWORD" \
  --cookie-jar build/refiner/refiner.cookies
```

Job submission requires an authenticated Refiner session. Use `--username/--password`, a reusable `--cookie-jar`, or `--refiner-access-token` on instances that expose bearer access tokens.

The runner disables Jira and Confluence discovery by default so drafts stay grounded in this repository's product pack. Add `--allow-live-discovery` only when you explicitly want Refiner to query those configured systems.

Generated output lands under `build/refiner/<product>/<kind>/`:
- `*-draft.md`
- `*-references.md`
- `*-job.json`

Transcribe a recorded video or audio file through Refiner:

```bash
scripts/refiner_transcribe.sh media/refiner/refiner-product-overview-v1.mp4 build/refiner-transcript.json
```

The transcription helper accepts the same Refiner session options as the draft runner and can also use `REFINER_STT_TOKEN` when the backend is configured for token-based STT access.

## Current constraint

This repository now supports grounded drafting, storyboarding, job-tracked research, and Refiner-managed transcription workflows. Final video mastering and render automation are still external to the repo and should be handled by the chosen editing stack after Refiner generates the planning and transcript artefacts.
