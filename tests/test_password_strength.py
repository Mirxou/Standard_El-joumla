#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""اختبارات دالة قياس قوة كلمة المرور"""
import pytest
from src.core.database_manager import DatabaseManager
from src.services.security_service import SecurityService

@pytest.fixture
def security(tmp_path):
    db_path = tmp_path / 'sec.db'
    dm = DatabaseManager(str(db_path))
    dm.initialize()
    return SecurityService(dm)

@pytest.mark.parametrize('pwd,expected_rating', [
    ('pass', 'weak'),
    ('Password12', 'medium'),
    ('Str0ng!Passw0rd', 'strong')
])
def test_password_strength_ratings(security, pwd, expected_rating):
    res = security.password_strength(pwd)
    assert res['rating'] == expected_rating

def test_password_strength_feedback(security):
    res = security.password_strength('password')
    assert 'تجنب الكلمات الشائعة' in ' '.join(res['feedback'])

