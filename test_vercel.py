"""Local adapter tests; no real database or email service required."""
import importlib.util
import json
from pathlib import Path
from http.server import HTTPServer
from http.client import HTTPConnection
from threading import Thread
import unittest
from unittest.mock import patch, MagicMock

spec = importlib.util.spec_from_file_location('vercel_entry', Path(__file__).parent / 'api/index.py')
entry = importlib.util.module_from_spec(spec)
spec.loader.exec_module(entry)

class VercelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.httpd = HTTPServer(('127.0.0.1', 0), entry.handler)
        cls.thread = Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()
    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown(); cls.httpd.server_close(); cls.thread.join()
    def request(self, path, body=None):
        c = HTTPConnection('127.0.0.1', self.httpd.server_port)
        c.request('POST' if body is not None else 'GET', path, body=body,
                  headers={'Content-Type':'application/json'})
        response = c.getresponse(); result = response.status, json.loads(response.read())
        c.close(); return result
    def test_health_without_database(self):
        self.assertEqual(self.request('/api/index?__route=health')[0], 200)
    def test_registration_route_reaches_validation(self):
        status, body = self.request('/api/index?__route=register', '{}')
        self.assertEqual(status, 400)
        self.assertFalse(body['success'])
        self.assertIn('required', body['message'])
    def test_cart_requires_login(self):
        self.assertEqual(self.request('/api/index?__route=cart')[0], 401)
    def test_ready_when_database_unavailable(self):
        with patch.object(entry, 'get_db_connection', return_value=None):
            self.assertEqual(self.request('/api/index?__route=ready')[0], 503)
    def test_ready_checks_schema(self):
        conn = MagicMock()
        with patch.object(entry, 'get_db_connection', return_value=conn):
            self.assertEqual(self.request('/api/ready')[0], 200)
        self.assertEqual(conn.cursor.return_value.execute.call_count, 13)
        conn.close.assert_called_once()
    def test_query_preserved(self):
        import products
        with patch.object(products, 'get_all_products', return_value={'products': [], 'total': 0, 'page': 1, 'limit': 12, 'total_pages': 0}) as get:
            self.request('/api/index?__route=products&search=phone&category=2')
            self.assertEqual(get.call_args.kwargs['search_query'], 'phone')
            self.assertEqual(get.call_args.kwargs['category_id'], '2')
    def test_bad_json_rejected(self):
        self.assertEqual(self.request('/api/register', '{')[0], 400)
        self.assertEqual(self.request('/api/register', '[]')[0], 400)
    def test_no_backend_static_exposure(self):
        self.assertEqual(self.request('/backend/config.py')[0], 404)
    def test_vercel_email_has_no_detached_thread(self):
        import email_service
        with patch.object(email_service, 'IS_VERCEL', True), patch.object(email_service, '_send_smtp_worker') as send, patch.object(email_service.threading, 'Thread') as thread:
            email_service.send_email_async('test@example.com', 'Test', '<p>Test</p>', 'Test')
            send.assert_called_once(); thread.assert_not_called()

if __name__ == '__main__':
    unittest.main()
