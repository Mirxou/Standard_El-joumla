#!/usr/bin/env python3
"""
نسخ احتياطي مشفر لقاعدة البيانات (Encrypted DB Backup)
"""
import os
from Crypto.Cipher import AES
import hashlib

def encrypt_file(input_path, output_path, password):
    key = hashlib.sha256(password.encode()).digest()
    with open(input_path, 'rb') as f:
        data = f.read()
    cipher = AES.new(key, AES.MODE_EAX)
    nonce = cipher.nonce
    ciphertext, tag = cipher.encrypt_and_digest(data)
    with open(output_path, 'wb') as f:
        f.write(nonce + tag + ciphertext)
    print(f'✅ تم إنشاء نسخة احتياطية مشفرة: {output_path}')

if __name__ == "__main__":
    db_path = 'data/standard_eljoumla.db'
    backup_path = f'backup_{os.path.basename(db_path)}.enc'
    password = input('أدخل كلمة مرور التشفير: ')
    encrypt_file(db_path, backup_path, password)
