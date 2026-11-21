from collections import defaultdict, deque
from math import ceil
from threading import Lock
from time import monotonic

from flask import Blueprint, current_app, jsonify, request
from jwt import InvalidTokenError

from backend.src.login_and_create_account.use_case.login_use_case import login_user
from backend.src.login_and_create_account.use_case.token_use_case import decode_user_token

blueprint_login = Blueprint("blueprint_login", __name__)

_LOGIN_FAILURES = defaultdict(deque)
_LOGIN_FAILURES_LOCK = Lock()
_LOGIN_WINDOW_SECONDS = 60
_MAX_LOGIN_FAILURES = 5


def _reserve_login_attempt(client_ip, now):
    with _LOGIN_FAILURES_LOCK:
        attempts = _LOGIN_FAILURES[client_ip]
        while attempts and now - attempts[0][0] >= _LOGIN_WINDOW_SECONDS:
            attempts.popleft()
        if len(attempts) >= _MAX_LOGIN_FAILURES:
            retry_after = max(1, ceil(_LOGIN_WINDOW_SECONDS - (now - attempts[0][0])))
            return None, retry_after
        marker = object()
        attempts.append((now, marker))
        return marker, None


def _finish_login_attempt(client_ip, marker, status_code):
    if status_code == 401:
        return
    with _LOGIN_FAILURES_LOCK:
        attempts = _LOGIN_FAILURES.get(client_ip)
        if attempts:
            for attempt in attempts:
                if attempt[1] is marker:
                    attempts.remove(attempt)
                    break
            if not attempts:
                _LOGIN_FAILURES.pop(client_ip, None)


@blueprint_login.post("/api/login")
@blueprint_login.post("/login")
def login():
    client_ip = request.remote_addr or "unknown"
    if not request.is_json:
        return jsonify({"ok": False, "message": "O corpo deve estar em formato JSON."}), 415

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"ok": False, "message": "O corpo JSON enviado é inválido."}), 400

    now = monotonic()
    marker, retry_after = _reserve_login_attempt(client_ip, now)
    if retry_after is not None:
        response = jsonify({
            "ok": False,
            "message": "Muitas tentativas de login. Aguarde um minuto e tente novamente.",
        })
        response.headers["Retry-After"] = str(retry_after)
        response.headers["Cache-Control"] = "no-store"
        return response, 429

    response_data, status_code = login_user(
        data.get("email"), data.get("password"), current_app.config["JWT_SECRET_KEY"]
    )
    _finish_login_attempt(client_ip, marker, status_code)
    response = jsonify(response_data)
    response.headers["Cache-Control"] = "no-store"
    return response, status_code


@blueprint_login.get("/api/auth/session")
def verify_session():
    authorization = request.headers.get("Authorization", "")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        response = jsonify({"ok": False, "message": "Sessão inválida ou expirada."})
        response.headers["Cache-Control"] = "no-store"
        return response, 401

    try:
        decode_user_token(token, current_app.config["JWT_SECRET_KEY"])
    except InvalidTokenError:
        response = jsonify({"ok": False, "message": "Sessão inválida ou expirada."})
        response.headers["Cache-Control"] = "no-store"
        return response, 401

    response = jsonify({"ok": True})
    response.headers["Cache-Control"] = "no-store"
    return response, 200
