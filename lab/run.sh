#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
HERE="$(pwd)"

export COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-webminh22}"
export PYTHONUNBUFFERED=1
export IMAGE="${IMAGE:-webmin-lab:2.670}"
export IMAGE_LOCK="${IMAGE_LOCK:-/tmp/webmin-lab-image.lock}"

PIN_COMMIT="3a2b2b8671c0669c129f5275b3dd1853106ae02b"
PIN_TAG="2.670"
REPO_URL="${WEBMIN_SRC_URL:-https://github.com/webmin/webmin.git}"
SRC="${HERE}/src"

LABEL="WEBMIN-H22-LDAP-MV"
WITNESS="WEBMIN-H22-LDAP-MV"
BASE="http://127.0.0.1:18470"

down() {
  echo "== docker compose down -v =="
  docker compose -p "${COMPOSE_PROJECT_NAME}" down -v --remove-orphans || true
}

fail_setup() {
  local reason="$1"
  echo "FAIL ${LABEL} ${reason} ${WITNESS}" | tee poc-last-run.txt
  docker compose -p "${COMPOSE_PROJECT_NAME}" logs --no-color --tail=160 webmin ldap || true
  down
  exit 1
}

lock_build() {
  python3 - "$IMAGE_LOCK" "$IMAGE" "$@" <<'PY'
import fcntl
import os
import subprocess
import sys

lock_path, image = sys.argv[1], sys.argv[2]
cmd = sys.argv[3:]
fd = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o644)
fcntl.flock(fd, fcntl.LOCK_EX)
try:
    inspect = subprocess.run(
        ["docker", "image", "inspect", image],
        capture_output=True,
        check=False,
    )
    if inspect.returncode == 0:
        print(f"IOC reuse-image {image}", flush=True)
        sys.exit(0)
    print(f"IOC build-image {image}", flush=True)
    os.lseek(fd, 0, os.SEEK_SET)
    os.ftruncate(fd, 0)
    os.write(fd, f"{os.getpid()}\n".encode("ascii"))
    rc = subprocess.call(cmd)
finally:
    fcntl.flock(fd, fcntl.LOCK_UN)
    os.close(fd)
sys.exit(rc)
PY
}

ensure_pin() {
  if [[ -d "${SRC}/.git" ]]; then
    local got
    got="$(git -C "${SRC}" rev-parse HEAD)"
    if [[ "${got}" == "${PIN_COMMIT}" && -f "${SRC}/setup.sh" && -f "${SRC}/ldap-useradmin/save_user.cgi" ]]; then
      echo "IOC reuse-src ${PIN_COMMIT}"
      return 0
    fi
  fi
  rm -rf "${SRC}"
  echo "== git clone --depth 1 --branch ${PIN_TAG} ${REPO_URL} =="
  GIT_TERMINAL_PROMPT=0 git clone --depth 1 --branch "${PIN_TAG}" "${REPO_URL}" "${SRC}" \
    || fail_setup "clone-failed"
  local got
  got="$(git -C "${SRC}" rev-parse HEAD)"
  echo "IOC cloned-sha=${got}"
  if [[ "${got}" != "${PIN_COMMIT}" ]]; then
    fail_setup "pin-mismatch"
  fi
}

if grep -E '^\s+-\s+"[^"]+:[0-9]+"' docker-compose.yml | grep -v '127.0.0.1'; then
  fail_setup "lab-compose-not-loopback"
fi

trap down EXIT

chmod +x poc.py entrypoint.sh

echo "== py_compile poc.py =="
python3 -m py_compile poc.py

echo "== docker compose down (clean) =="
down

ensure_pin
if [[ ! -f "${SRC}/setup.sh" || ! -f "${SRC}/ldap-useradmin/save_user.cgi" ]]; then
  fail_setup "webmin-src-missing"
fi
if [[ "$(cat "${SRC}/version")" != "${PIN_TAG}" ]]; then
  fail_setup "webmin-src-pin"
fi

echo "== docker build ${IMAGE} (lock ${IMAGE_LOCK}) =="
build_ok=0
for attempt in $(seq 1 12); do
  if lock_build docker build -t "${IMAGE}" -f Dockerfile "${SRC}"; then
    build_ok=1
    break
  fi
  echo "IOC image-build-retry attempt=${attempt}"
  sleep 20
done
if [[ "${build_ok}" != 1 ]]; then
  fail_setup "image-build-failed"
fi

echo "== docker compose up =="
up_ok=0
for attempt in $(seq 1 12); do
  if docker compose -p "${COMPOSE_PROJECT_NAME}" up -d --no-build; then
    up_ok=1
    break
  fi
  echo "IOC compose-up-retry attempt=${attempt}"
  sleep 15
  down
done
if [[ "${up_ok}" != 1 ]]; then
  fail_setup "compose-up-failed"
fi

echo "== wait ldap labuser =="
ldap_ok=0
for i in $(seq 1 60); do
  if docker compose -p "${COMPOSE_PROJECT_NAME}" exec -T ldap \
      ldapsearch -x -H ldap://127.0.0.1:389 \
      -D cn=admin,dc=lab,dc=invalid -w labldap \
      -b ou=People,dc=lab,dc=invalid '(uid=labuser)' dn >/dev/null 2>&1; then
    ldap_ok=1
    echo "IOC ldap-user-ready attempt=${i}"
    break
  fi
  echo "IOC ldap-user-wait attempt=${i}"
  sleep 3
done
if [[ "${ldap_ok}" != 1 ]]; then
  fail_setup "ldap-not-ready"
fi

echo "== wait ${BASE}/session_login.cgi =="
ready=0
for i in $(seq 1 60); do
  code="$(curl -sS -o /tmp/webmin-h22-ready.html -w '%{http_code}' --max-time 8 \
    "${BASE}/session_login.cgi" || true)"
  if [[ "${code}" == "200" || "${code}" == "401" ]]; then
    ready=1
    echo "IOC webmin-http-ready attempt=${i} http=${code}"
    break
  fi
  echo "IOC webmin-http-wait attempt=${i} http=${code}"
  sleep 3
done
if [[ "${ready}" != 1 ]]; then
  fail_setup "webmin-not-ready"
fi

echo "== poc.py =="
set +e
python3 ./poc.py
rc=$?
set -e

if [[ ! -f poc-last-run.txt ]] || ! tail -n 1 poc-last-run.txt | grep -qE '^(SUCCESS|FAIL) '; then
  echo "FAIL ${LABEL} poc-exit-${rc} ${WITNESS}" >> poc-last-run.txt
  rc=1
fi

if [[ "${rc}" != 0 ]]; then
  docker compose -p "${COMPOSE_PROJECT_NAME}" logs --no-color --tail=80 webmin ldap || true
fi

exit "${rc}"
