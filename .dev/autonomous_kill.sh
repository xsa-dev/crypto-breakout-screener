#!/usr/bin/env bash
set -u

REPO_ROOT="$(git rev-parse --show-toplevel)" || exit 1
LOCK_DIR="$REPO_ROOT/.hermes/openspec-runner.lock"
PID_FILE="$LOCK_DIR/pid"
LAUNCH_LABEL="terra-appolox-openspec-runner"

cleanup_lock() {
  rm -f "$PID_FILE"
  rmdir "$LOCK_DIR" 2>/dev/null || true
}

remove_launch_job() {
  if command -v launchctl >/dev/null 2>&1; then
    launchctl remove "$LAUNCH_LABEL" >/dev/null 2>&1 || true
  fi
}

if [ ! -f "$PID_FILE" ]; then
  remove_launch_job
  cleanup_lock
  printf "Runner not active: PID file is missing\n"
  exit 0
fi

PID="$(cat "$PID_FILE" 2>/dev/null || true)"

case "$PID" in
  ""|*[!0-9]*)
    remove_launch_job
    cleanup_lock
    printf "Runner not active: removed invalid PID file\n"
    exit 0
    ;;
esac

if ! kill -0 "$PID" 2>/dev/null; then
  remove_launch_job
  cleanup_lock
  printf "Runner not active: removed stale PID %s\n" "$PID"
  exit 0
fi

remove_launch_job
kill "$PID"

for _ in 1 2 3 4 5 6 7 8 9 10 \
  11 12 13 14 15 16 17 18 19 20 \
  21 22 23 24 25 26 27 28 29 30 \
  31 32 33 34 35 36 37 38 39 40; do
  if ! kill -0 "$PID" 2>/dev/null; then
    cleanup_lock
    printf "Stopped runner: PID %s\n" "$PID"
    exit 0
  fi
  sleep 0.5
done

printf "Runner still active after SIGTERM: PID %s\n" "$PID" >&2
exit 1
