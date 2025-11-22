from src.services.security_service import SecurityService


class FakeDB2FA:
    def __init__(self):
        self.rows = {}

    def execute_query(self, q, params=()):
        ql = q.lower()
        if ql.startswith('create table'):  # table creation ignored
            return []
        if 'replace into user_2fa' in ql:
            user_id, secret, enabled_at = params
            self.rows['user_2fa'] = [{'user_id': user_id, 'secret': secret, 'enabled_at': enabled_at}]
            return []
        if 'select secret from user_2fa' in ql:
            return self.rows.get('user_2fa', [])
        if 'insert into login_attempts' in ql:
            return []
        if 'select count(*) as cnt from login_attempts' in ql:
            return [{'cnt': 0}]
        return []

    def fetch_all(self, q, params=()):
        return []


def test_enable_and_verify_2fa(monkeypatch):
    try:
        import pyotp
    except Exception:  # if pyotp missing skip
        return
    db = FakeDB2FA()
    svc = SecurityService(db)
    r = svc.enable_2fa(42)
    assert r['success'] is True and 'secret' in r
    secret = r['secret']
    # generate current code via pyotp to verify
    code = pyotp.TOTP(secret).now()
    assert svc.verify_2fa(42, code) is True
