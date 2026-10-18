"""Scaffold checks: use real SQLite sessions, never a client-selected role."""
import hashlib
import os
import sqlite3
import tempfile
import time
import unittest
from fastapi.testclient import TestClient
from backend.app import app


class RoleBoundaries(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = self.tmp.name + '/test.db'
        self.env = os.environ.get('SIMPLECATER_DB')
        os.environ['SIMPLECATER_DB'] = self.path
        with sqlite3.connect(self.path) as db:
            db.executescript('CREATE TABLE users(id INTEGER,role TEXT,business_id INTEGER);'
                             'CREATE TABLE sessions(token_hash TEXT,user_id INTEGER,expires_at REAL);')
            for i, role in enumerate(('customer', 'owner'), 1):
                db.execute('INSERT INTO users VALUES(?,?,?)', (i, role, 1 if role == 'owner' else None))
                db.execute('INSERT INTO sessions VALUES(?,?,?)',
                           (hashlib.sha256(role.encode()).hexdigest(), i, time.time()+60))
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()
        if self.env is None:
            os.environ.pop('SIMPLECATER_DB', None)
        else:
            os.environ['SIMPLECATER_DB'] = self.env
        self.tmp.cleanup()

    def sign_in(self, role):
        self.client.cookies.set('simplecater_session', role)

    def test_anonymous_cannot_open_owner(self):
        self.assertEqual(self.client.get('/owner.html').status_code, 401)

    def test_customer_cannot_open_owner_or_summary(self):
        self.sign_in('customer')
        self.assertEqual(self.client.get('/owner.html').status_code, 403)
        self.assertEqual(self.client.post('/api/ai/summary', headers={'Origin':'http://testserver'}).status_code, 403)
        self.assertEqual(self.client.get('/customer.html').status_code, 200)

    def test_owner_cannot_open_customer_or_profiles(self):
        self.sign_in('owner')
        self.assertEqual(self.client.get('/customer.html').status_code, 403)
        self.assertEqual(self.client.get('/api/profile').status_code, 403)
        self.assertEqual(self.client.get('/owner.html').status_code, 200)

    def test_untrusted_origin_blocked(self):
        self.sign_in('customer')
        self.assertEqual(self.client.post('/api/orders',headers={'Origin':'https://other.example'}).status_code,403)

    def test_session_role_is_authoritative(self):
        self.sign_in('customer')
        self.assertEqual(self.client.get('/api/auth/me?role=owner').json()['role'], 'customer')

    def test_unimplemented_models_fail_explicitly(self):
        self.sign_in('owner')
        self.assertEqual(self.client.post('/api/ai/summary',headers={'Origin':'http://testserver'}).status_code,501)


if __name__ == '__main__':
    unittest.main()
