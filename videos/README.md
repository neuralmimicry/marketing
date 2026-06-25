# Video System

This folder holds the structured inputs for product and training video creation.

## What is versioned

Versioned here:
- deliverable manifests
- prompt packs
- product briefs and messaging references that prompts depend on

Not versioned by default:
- generated drafts under `build/`
- large raw/edit/export video files unless intentionally added under `media/`

## Deliverable types

- `product`: short commercial overview for external buyers
- `training`: deeper operational walkthrough for enablement or onboarding

## Workflow

1. Confirm the product brief is current.
2. Run `scripts/refiner_video_pipeline.py` to submit a draft job and collect the generated script and storyboard.
3. Record capture and voiceover.
4. Run `scripts/refiner_transcribe.sh` on the recorded media.
5. Edit captions and produce the final cut in the external editing stack.
