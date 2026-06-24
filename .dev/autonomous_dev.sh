#!/usr/bin/env bash
set -euo pipefail

PATH="/Users/alxy/.local/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
HERMES_BIN="$(command -v hermes)" || {
  printf "hermes not found in PATH\n" >&2
  exit 1
}
HERMES_PROFILE="hsh"
TELEGRAM_TARGET="${TELEGRAM_TARGET:-telegram}"
GITLAB_TARGET_BRANCH="${GITLAB_TARGET_BRANCH:-develop}"

STATE_DIR="$REPO_ROOT/.hermes"
LOG_DIR="$STATE_DIR/logs"
LOG_FILE="$LOG_DIR/openspec-cycle.log"
DIALOG_LOG_FILE="$LOG_DIR/openspec-dialog.log"
LOCK_DIR="$STATE_DIR/openspec-runner.lock"
PID_FILE="$LOCK_DIR/pid"

mkdir -p "$LOG_DIR"

gitlab_project_url() {
  git -C "$REPO_ROOT" remote get-url origin 2>/dev/null \
    | sed -E 's#^git@gitlab\.com:#https://gitlab.com/#; s#\.git$##'
}

log_gitlab_preflight() {
  remote_url="$(git -C "$REPO_ROOT" remote get-url origin 2>/dev/null || true)"
  project_url="$(gitlab_project_url)"

  {
    printf "[%s] GitLab local-only preflight\n" "$(date "+%Y-%m-%dT%H:%M:%S%z")"
    printf "Repo: %s\n" "$REPO_ROOT"
    printf "Origin: %s\n" "${remote_url:-<missing>}"
    printf "Project URL: %s\n" "${project_url:-<unknown>}"
    printf "Target branch: %s\n" "$GITLAB_TARGET_BRANCH"
    if command -v glab >/dev/null 2>&1; then
      printf "GitLab CLI: %s (not used in local-only mode)\n" "$(command -v glab)"
    else
      printf "GitLab CLI: unavailable; local-only runner will not create GitLab issues/MRs.\n"
    fi
  } >>"$LOG_FILE"
}

run_loop() {
  cd "$REPO_ROOT" || exit 1
  mkdir -p "$LOCK_DIR"

  existing_pid="$(cat "$PID_FILE" 2>/dev/null || true)"
  case "$existing_pid" in
    ""|*[!0-9]*)
      ;;
    "$$")
      ;;
    *)
      if kill -0 "$existing_pid" 2>/dev/null; then
        printf "[%s] Runner already active under PID %s; exiting duplicate run-loop.\n" \
          "$(date "+%Y-%m-%dT%H:%M:%S%z")" \
          "$existing_pid" >>"$LOG_FILE"
        exit 0
      fi
      ;;
  esac

  printf "%s\n" "$$" > "$PID_FILE"
  log_gitlab_preflight

  cleanup() {
    recorded_pid="$(cat "$PID_FILE" 2>/dev/null || true)"

    if [ "$recorded_pid" = "$$" ]; then
      rm -f "$PID_FILE"
      rmdir "$LOCK_DIR" 2>/dev/null || true
    fi
  }

  trap cleanup EXIT
  trap "exit 0" INT TERM

PROMPT=$(cat <<\PROMPT
Ты работаешь как автономный senior software engineer строго в текущем репозитории. Следуй OpenSpec, AGENTS.md, CLAUDE.md и остальным локальным инструкциям проекта.

Это не review-only и не advisory-режим. Твоя задача — доводить выбранную фичу до готового состояния реальными изменениями в репозитории. Если находишь исправимые блокеры, дефекты, неполные tasks, неархивированный OpenSpec change, красные проверки или слабые тесты — исправляй их сам, затем повторяй проверки. Не заканчивай цикл только GO/NO-GO отчетом, если блокер можно исправить локально.

Для этого автономного runner-а пользователь явно разрешил локальный цикл разработки по уже сформулированным ранее задачам/OpenSpec changes. Активные approved/готовые OpenSpec changes реализуй, проверяй и архивируй локально без отдельного запроса подтверждения. Если активных changes нет, но `openspec/specs/*` содержит утвержденные требования без соответствующей реализации, можно создать ровно один узкий implementation change на основе существующей capability spec; не создавай новые capability names и не добавляй продуктовые инициативы за пределами specs. Не выполняй cloud delivery: не создавай GitLab issue/MR, не push, не merge, не обновляй remote.

Если репозиторий уже инициализирован, но в нем еще нет коммитов, сначала создай один локальный baseline commit текущего безопасного состояния. Перед baseline commit проверь `.gitignore`, не добавляй `.env`, секреты, логи, caches, `__pycache__`, `.DS_Store` и runtime DB. Разрешено добавить проектные metadata-файлы вроде `openspec/config.yaml` и lockfile, если они нужны для воспроизводимости. После baseline commit продолжай обычный автономный цикл по активным changes.

Если возникает неустранимый локально blocker, пропиши финальное проблемное сообщение и заканчивай выполнение, после отправь сообщение о блокере командой:
hermes send --to telegram --subject "[StockSeeker autonomous blocker]" "<короткий отчет>"

В сообщении укажи: change-id, точный blocker, что уже проверено, безопасное состояние репозитория, какую команду/доступ/решение нужно дать. Не отправляй секреты, токены и приватные значения. Если Telegram-отправка не сработала, запиши ошибку отправки в финальный отчет и в лог, но не пытайся скрыть blocker.

Держи OpenSpec specs крупными и доменными:
- `openspec/changes/archive/*` — это история выполненных change-пакетов; она может расти по одному каталогу на feature.
- `openspec/specs/*` — это текущая карта возможностей продукта. Не создавай новую постоянную capability spec на каждый мелкий warning cleanup, refactor, guard, redaction или точечный bugfix.
- Перед созданием нового capability имени проверь существующие `openspec/specs/*`. Если изменение относится к уже существующей области, добавляй delta к этой области и после архивации обновляй существующую spec, а не создавай новую spec-директорию.
- Создавай новую `openspec/specs/<capability>/` только когда появляется действительно новая пользовательская/системная capability, которую нельзя естественно включить в существующую доменную spec.
- При работе с уже сформулированным ранее change предпочитай держать связанные мелкие правки внутри одной доменной capability, чтобы выполненный change уходил в archive, а `openspec/specs` оставался компактным и не дублировал архив по одному каталогу на каждую микрофичу.
- После архивации change перед commit обязательно проверь, нет ли одноименного дубликата:
  `openspec/specs/<change-id>` и `openspec/changes/archive/YYYY-MM-DD-<change-id>`.
  Если такой дубль есть, удали `openspec/specs/<change-id>` и оставь только archived change. Затем запусти `npx --yes @fission-ai/openspec@1.4.1 validate --all --strict --no-interactive`.
- Перед локальным завершением обязательно проверь командой, что пересечение имен `openspec/specs/*` с именами архивов `openspec/changes/archive/YYYY-MM-DD-*` равно 0. Если пересечение не 0, исправь это до финального отчета; не оставляй duplicate specs.

Перед выбором задачи проверь только локальное состояние: текущую ветку, git status, активные OpenSpec changes, archived specs и незавершенные локальные изменения. Не проверяй GitLab MR/issue/pipeline и не выполняй network delivery. Не начинай новую фичу, если нет уже сформулированного ранее OpenSpec change или явной локальной задачи от владельца.

Если активных OpenSpec changes или явно сформулированных ранее локальных задач нет, заверши цикл отчетом "локальных задач нет". Не выполняй глубокий discovery с целью найти новое улучшение, не создавай новый OpenSpec change и не реализуй новые улучшения самостоятельно.

На каждом запуске выполни один полный управляемый цикл:

1. Проверь текущую ветку, git status, незавершенные изменения, активные OpenSpec changes и состояние локальных задач. Не удаляй, не перезаписывай и не откатывай посторонние локальные изменения.

2. Если уже есть начатая локальная фича/OpenSpec change, сначала продолжай ее. Иначе выбери только из уже сформулированных ранее задач. Если таких задач нет, остановись с отчетом "локальных задач нет".

3. Проверь proposal, design, specs, acceptance criteria и tasks выбранной фичи. Если спецификация неполная, противоречивая, неоднозначная или нетестируемая, сначала доработай ее. Не начинай реализацию, пока требования и критерии приемки не станут однозначными.

4. Реализуй фичу полностью по спецификации. Делай минимальные и логически связанные изменения. При необходимости добавляй или обновляй тесты, документацию, миграции, конфигурацию и observability.

5. Выполни все релевантные проверки проекта:
   - OpenSpec validation;
   - unit, integration и end-to-end tests;
   - lint и formatting;
   - typecheck;
   - build;
   - другие проверки, указанные в документации репозитория.

   Не отключай проверки, не обходи hooks и не маскируй ошибки.

6. Проведи строгий self-review всего diff относительно спецификации. Проверь:
   - корректность реализации;
   - соответствие acceptance criteria;
   - regressions и edge cases;
   - security;
   - concurrency;
   - data integrity;
   - backward compatibility;
   - обработку ошибок;
   - качество и полноту тестов;
   - отсутствие посторонних изменений.

7. Исправь все найденные замечания. После исправлений повторно выполни review и проверки. Продолжай цикл review → исправления → проверки до тех пор, пока не останется существенных замечаний и все обязательные проверки не станут зелеными.

8. Только после полного соответствия спецификации:
   - отметь OpenSpec tasks выполненными;
   - выполни финальную OpenSpec validation;
   - архивируй change штатной командой проекта.

   Не архивируй незавершенную или непроверенную фичу.

9. Если локальная фича полностью готова и рабочее дерево позволяет безопасную фиксацию, создай один содержательный локальный commit только с относящимися к фиче изменениями. Формат сообщения:

   [openspec feature] <change-id>: <краткое описание>

   Не создавай пустой commit, не используй force push, не переписывай общую историю и не добавляй в commit посторонние изменения.

10. Не выполняй cloud delivery. После локального commit не push, не создавай MR, не merge в remote branch и не обращайся к GitLab API/CLI. В финальном отчете явно укажи, что изменения выполнены только локально.

11. За один запуск доводи максимум одну фичу до завершения, после чего заверши текущий запуск и выдай краткий отчет:
   - change-id и название фичи;
   - что было изменено;
   - какие проверки выполнены;
   - результаты review;
   - commit hash, если локальный commit был создан;
   - подтверждение, что push/MR/merge не выполнялись;
   - оставшиеся blockers или риски.

Следующий плановый запуск должен продолжить только незавершенную локальную работу или другую уже сформулированную ранее задачу. Если таких задач нет, он должен остановиться с отчетом "локальных задач нет".

При конфликте источников используй следующий приоритет:
1. локальные инструкции репозитория;
2. утвержденная OpenSpec;
3. acceptance criteria;
4. автоматические тесты;
5. фактическое поведение кода.

Работай автономно, но не делай предположений, противоречащих репозиторию или OpenSpec.
PROMPT
)
PROMPT="${PROMPT//\$\{GITLAB_TARGET_BRANCH:-develop\}/$GITLAB_TARGET_BRANCH}"

  while :; do
    printf "\n[%s] OpenSpec cycle started; profile=%s\n" \
      "$(date "+%Y-%m-%dT%H:%M:%S%z")" \
      "$HERMES_PROFILE"

    printf "\n[%s] Hermes dialog started; profile=%s\n" \
      "$(date "+%Y-%m-%dT%H:%M:%S%z")" \
      "$HERMES_PROFILE" >>"$DIALOG_LOG_FILE"

    run_output="$(mktemp "$STATE_DIR/openspec-dialog.XXXXXX")"
    set +e
    "$HERMES_BIN" -p "$HERMES_PROFILE" chat \
      -v \
      --checkpoints \
      --max-turns 180 \
      --yolo \
      --accept-hooks \
      --source autonomous-openspec \
      -q "$PROMPT" >"$run_output" 2>&1
    rc=$?
    set -e

    cat "$run_output" >>"$DIALOG_LOG_FILE"

    if grep -Eiq 'HTTP 403|HTML error page|Cloudflare|Please try again later' "$run_output"; then
      printf "[%s] Hermes dialog contained a fatal provider/network error; overriding exit to 1.\n" \
        "$(date "+%Y-%m-%dT%H:%M:%S%z")" >>"$DIALOG_LOG_FILE"
      rc=1
    fi
    rm -f "$run_output"

    printf "[%s] Hermes dialog finished, exit=%s\n" \
      "$(date "+%Y-%m-%dT%H:%M:%S%z")" \
      "$rc" >>"$DIALOG_LOG_FILE"

    if [ "$rc" -ne 0 ]; then
      "$HERMES_BIN" send --to "$TELEGRAM_TARGET" \
        --subject "[StockSeeker autonomous runner failed]" \
        "Hermes autonomous cycle exited with code $rc.
Repo: $REPO_ROOT
Profile: $HERMES_PROFILE
Cycle log: $LOG_FILE
Dialog log: $DIALOG_LOG_FILE" >>"$LOG_FILE" 2>&1 || true
    fi

    now=$(date +%s)
    sleep_for=$((900 - now % 900))

    printf "[%s] OpenSpec cycle finished, exit=%s; next slot in %ss\n" \
      "$(date "+%Y-%m-%dT%H:%M:%S%z")" \
      "$rc" \
      "$sleep_for"

    sleep "$sleep_for"
  done
}

if [ "${1:-}" = "--run-loop" ]; then
  run_loop
  exit 0
fi

acquire_lock() {
  # Предыдущая версия с flock оставляла обычный lock-файл.
  if [ -e "$LOCK_DIR" ] && [ ! -d "$LOCK_DIR" ]; then
    rm -f "$LOCK_DIR" || return 1
  fi

  if mkdir "$LOCK_DIR" 2>/dev/null; then
    return 0
  fi

  old_pid="$(cat "$PID_FILE" 2>/dev/null || true)"

  case "$old_pid" in
    ""|*[!0-9]*)
      ;;
    *)
      if kill -0 "$old_pid" 2>/dev/null; then
        printf "OpenSpec runner is already active (PID %s).\n" "$old_pid"
        exit 0
      fi
      ;;
  esac

  # Процесс уже отсутствует: удаляем протухшую блокировку.
  rm -f "$PID_FILE"

  if ! rmdir "$LOCK_DIR" 2>/dev/null; then
    printf "Cannot remove stale lock directory: %s\n" "$LOCK_DIR" >&2
    return 1
  fi

  if ! mkdir "$LOCK_DIR" 2>/dev/null; then
    printf "Another runner acquired the lock concurrently.\n" >&2
    return 1
  fi
}

acquire_lock || exit 1

rm -f "$PID_FILE"

if command -v launchctl >/dev/null 2>&1; then
  LAUNCH_LABEL="stockseeker-openspec-runner"
  LEGACY_LAUNCH_LABEL="terra-appolox-openspec-runner"
  launchctl remove "$LAUNCH_LABEL" >/dev/null 2>&1 || true
  launchctl remove "$LEGACY_LAUNCH_LABEL" >/dev/null 2>&1 || true
  launchctl submit \
    -l "$LAUNCH_LABEL" \
    -o "$LOG_FILE" \
    -e "$LOG_FILE" \
    -- "$SCRIPT_DIR/autonomous_dev.sh" --run-loop
else
  perl -MPOSIX=setsid -e '
    if (fork) {
      exit 0;
    }
    setsid() or die "setsid failed: $!";
    open STDIN, "<", "/dev/null" or die "stdin redirect failed: $!";
    open STDOUT, ">>", $ARGV[0] or die "stdout redirect failed: $!";
    open STDERR, ">&", \*STDOUT or die "stderr redirect failed: $!";
    exec @ARGV[1..$#ARGV] or die "exec failed: $!";
  ' "$LOG_FILE" "$SCRIPT_DIR/autonomous_dev.sh" --run-loop
fi

RUNNER_PID=""
for _ in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20; do
  if [ -f "$PID_FILE" ]; then
    candidate_pid="$(cat "$PID_FILE" 2>/dev/null || true)"
    case "$candidate_pid" in
      ""|*[!0-9]*)
        ;;
      *)
        if kill -0 "$candidate_pid" 2>/dev/null; then
          RUNNER_PID="$candidate_pid"
          break
        fi
        ;;
    esac
  fi
  sleep 0.2
done

if [ -z "$RUNNER_PID" ]; then
  printf "Runner failed to stay active.\nCycle log: %s\nDialog log: %s\n" \
    "$LOG_FILE" \
    "$DIALOG_LOG_FILE" >&2
  rm -f "$PID_FILE"
  rmdir "$LOCK_DIR" 2>/dev/null || true
  exit 1
fi

printf "Started PID %s\nProfile: %s\nCycle log: %s\nDialog log: %s\n" \
  "$RUNNER_PID" \
  "$HERMES_PROFILE" \
  "$LOG_FILE" \
  "$DIALOG_LOG_FILE"
