from types import SimpleNamespace
from src.services.security_service import SecurityService

class FakeDB:
    def __init__(self):
        self.data = {"user_2fa": [], "login_attempts": []}
    def execute_query(self, q, params=()):
        ql = q.lower().strip()
        if ql.startswith("create table"):
            return []
        if ql.startswith("replace into user_2fa"):
            user_id, secret, enabled_at = params
            self.data["user_2fa"] = [
                {"user_id": user_id, "secret": secret, "enabled_at": enabled_at}
            ]
            return []
        if ql.startswith("select secret from user_2fa"):
            return self.data["user_2fa"]
        if ql.startswith("insert into login_attempts"):
            username, ip, user_agent, success, created_at = params
            self.data["login_attempts"].append({
                "username": username, "ip": ip, "user_agent": user_agent,
                "success": success, "created_at": created_at
            })
            return []
        if ql.startswith("select count(*) as cnt from login_attempts"):
            # simplistic: count failures
            cnt = sum(1 for r in self.data["login_attempts"] if r["success"] == 0)
            return [{"cnt": cnt}]
        return []
    def fetch_all(self, q, params=()):
        return []


def test_password_strength():
    svc = SecurityService(FakeDB())
    weak = svc.password_strength("pass")
    strong = svc.password_strength("Str0ng!Passw0rd#2024")
    assert weak["rating"] in ("weak", "medium")
    assert strong["rating"] == "strong"


def test_bruteforce_block():
    svc = SecurityService(FakeDB())
    for _ in range(5):
        svc.record_login_attempt("u", False)
    assert svc.is_blocked("u", max_failures=5) is True
