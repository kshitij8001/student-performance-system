import os
import sys
import unittest

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app

class StudentPerformanceSystemTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()

    def test_health_check(self):
        """Test Kubernetes health probe endpoint."""
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        json_data = response.get_json()
        self.assertEqual(json_data.get('status'), 'ok')
        self.assertEqual(json_data.get('app'), 'student-performance-system')

    def test_unauthenticated_redirect_dashboard(self):
        """Unauthenticated user accessing root should be redirected to login."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.headers.get('Location', ''))

    def test_unauthenticated_redirect_routes(self):
        """Protected faculty routes should redirect to /login when not authenticated."""
        for path in ['/add_student', '/add_course', '/add_teacher', '/add_department']:
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 302)
                self.assertIn('/login', response.headers.get('Location', ''))

    def test_login_page_renders(self):
        """Login page should render successfully with HTTP 200."""
        response = self.client.get('/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Sign In', response.data)
        self.assertIn(b'username', response.data)
        self.assertIn(b'password', response.data)

    def test_logout_redirects_to_login(self):
        """Logging out should redirect back to login."""
        with self.client.session_transaction() as sess:
            sess['user'] = 'testuser'
        response = self.client.get('/logout')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.headers.get('Location', ''))

if __name__ == '__main__':
    unittest.main()
