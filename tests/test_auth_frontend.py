"""Frontend Authentication and Route Protection Integration Test Suite."""

import json
import urllib.request
import urllib.parse
import pytest


BASE_NEXT = "http://127.0.0.1:3000"
BASE_FASTAPI = "http://127.0.0.1:8000"


class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


opener = urllib.request.build_opener(NoRedirectHandler)


def request_route(path: str, cookie_val: str = None):
    url = f"{BASE_NEXT}{path}"
    req = urllib.request.Request(url)
    if cookie_val:
        req.add_header("Cookie", f"kemsa_session={cookie_val}")
    try:
        res = opener.open(req)
        return res.status, res.headers.get("Location", "")
    except urllib.error.HTTPError as e:
        return e.code, e.headers.get("Location", "")


def encode_session(role: str, scope_id: str = None, scope_name: str = None) -> str:
    payload = {"role": role}
    if scope_id:
        payload["scopeId"] = scope_id
    if scope_name:
        payload["scopeName"] = scope_name
    return urllib.parse.quote(json.dumps(payload))


def test_unauthenticated_redirection():
    for path in ["/", "/national", "/county", "/facility"]:
        status, loc = request_route(path)
        assert status in [307, 308], f"Expected redirect for {path}, got {status}"
        assert "/login" in loc, f"Expected redirect to login for {path}, got {loc}"


def test_national_role_isolation():
    cookie = encode_session(role="national")
    status, loc = request_route("/national", cookie)
    assert status == 200

    # Blocked from county and facility
    status, loc = request_route("/county", cookie)
    assert status in [307, 308]
    assert "role_mismatch" in loc and "required=county" in loc

    status, loc = request_route("/facility", cookie)
    assert status in [307, 308]
    assert "role_mismatch" in loc and "required=facility" in loc


def test_county_role_isolation_and_scope():
    cookie = encode_session(role="county", scope_id="Kiambu", scope_name="Kiambu County")
    status, loc = request_route("/county", cookie)
    assert status == 200

    # Blocked from other roles
    status, loc = request_route("/national", cookie)
    assert status in [307, 308]
    assert "role_mismatch" in loc

    status, loc = request_route("/facility", cookie)
    assert status in [307, 308]
    assert "role_mismatch" in loc

    # Scope protection: cannot view another county
    status, loc = request_route("/county?county=Mombasa", cookie)
    assert status in [307, 308]
    assert "county_scope_violation" in loc and "attempted=Mombasa" in loc


def test_facility_role_isolation_and_scope():
    cookie = encode_session(role="facility", scope_id="FAC0001", scope_name="Nairobi Referral")
    status, loc = request_route("/facility", cookie)
    assert status == 200

    # Blocked from other roles
    status, loc = request_route("/national", cookie)
    assert status in [307, 308]
    assert "role_mismatch" in loc

    status, loc = request_route("/county", cookie)
    assert status in [307, 308]
    assert "role_mismatch" in loc

    # Scope protection: cannot view another facility
    status, loc = request_route("/facility?facility_id=FAC0002", cookie)
    assert status in [307, 308]
    assert "facility_scope_violation" in loc and "attempted=FAC0002" in loc
