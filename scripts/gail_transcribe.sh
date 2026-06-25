#!/usr/bin/env bash
set -euo pipefail

echo "scripts/gail_transcribe.sh is deprecated; use scripts/refiner_transcribe.sh." >&2
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "$SCRIPT_DIR/refiner_transcribe.sh" "$@"
