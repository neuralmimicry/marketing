# Refiner Video Pipeline

## What this workflow does

This workflow submits marketing drafts to Refiner's `topic_research` job system and uses Refiner's STT endpoint to verify recorded media. Gail can remain configured behind Refiner, but operators in this repository should talk to Refiner rather than to Gail directly.

## Responsibility split

Refiner owns:
- prompt execution
- structured topic research
- job submission, queueing, and status tracking
- script and storyboard drafting
- asset-list generation
- references output
- transcription access for recorded audio or video files

The editing stack outside this repository still owns:
- screen recording
- voiceover capture
- timeline editing
- colour, audio mix, and final master export

## Draft a video pack

List the available product and training targets:

```bash
python3 scripts/refiner_video_pipeline.py list
```

Preview the request Refiner will receive:

```bash
python3 scripts/refiner_video_pipeline.py draft refiner --kind product --print-only
```

Run a real draft against the local Refiner backend:

```bash
python3 scripts/refiner_video_pipeline.py draft refiner --kind training \
  --username "$REFINER_USERNAME" \
  --password "$REFINER_PASSWORD" \
  --cookie-jar build/refiner/refiner.cookies \
  --llm-provider openai \
  --llm-model gpt-5.2
```

Authenticated job submission requires one of:
- `--username` plus `--password`
- a reusable `--cookie-jar` created by an earlier login
- `--refiner-access-token` on instances that expose bearer-token auth

The runner sends the prompt text into a `topic_research` job so Refiner owns the queue, job lifecycle, and final output paths.

The runner disables Jira and Confluence discovery by default so the workflow stays on the local marketing pack. Add `--allow-live-discovery` only when you intentionally want Refiner to query those configured systems too.

Generated output lands under `build/refiner/<product>/<kind>/`:
- `*-draft.md`
- `*-references.md`
- `*-job.json`

Context files are passed to Refiner as absolute paths. If the Refiner backend is running on a different host, those paths must exist on that host too.

## Transcribe captured media with Refiner

Once a rough cut or voiceover exists, transcribe it through Refiner:

```bash
scripts/refiner_transcribe.sh media/refiner/refiner-training-v1.mp4 build/refiner-training-transcript.json
```

The helper returns Refiner's JSON response. It can reuse the same Refiner session settings as draft submission, or it can use `REFINER_STT_TOKEN` when the STT route is configured for token access.

Typical next steps are:
- extract `.text` into a caption-editing working file
- turn the transcript into subtitles in the editor of choice
- compare the transcript against the approved script and fix terminology drift

## Review checklist

- Does the draft stay within the product brief and shared positioning rules?
- Does it make at least one governance or control point explicit?
- Does the storyboard use only product surfaces that currently exist?
- Are runtime hostnames or auth modes described exactly as the source material states them?
- Has Refiner-managed transcription been used to verify the recorded voiceover before final export?
