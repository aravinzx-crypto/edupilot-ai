import unittest
import os
import json
import sqlite3

# Set test environment with long key
os.environ['EDUPILOT_SECRET_KEY'] = 'test-secret-key-edupilot-ai-production-grade-secret-key-32bytes-min'

from app import app
from database import get_db, init_db, DB_PATH
from auth import check_password, hash_password

class EduPilotTestCase(unittest.TestCase):
    def setUp(self):
        # Configure app for testing
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()

        # Initialize fresh DB
        init_db()
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM chat_messages")
            cursor.execute("DELETE FROM notes")
            cursor.execute("DELETE FROM weak_topics")
            cursor.execute("DELETE FROM quizzes")
            cursor.execute("DELETE FROM study_sessions")
            cursor.execute("DELETE FROM users")

    def clear_cookies(self):
        """Helper to clear test client cookies."""
        self.client.delete_cookie('edupilot_token')
        self.client.delete_cookie('session')

    def test_01_user_registration_and_bcrypt_hashing(self):
        """Test sign up validation, bcrypt hashing, and cookie issuance."""
        # Test invalid email
        res = self.client.post('/api/auth/signup', json={
            'name': 'Test Student',
            'email': 'invalid-email',
            'password': 'password123',
            'confirm_password': 'password123'
        })
        self.assertEqual(res.status_code, 400)
        self.assertIn('email', res.get_json()['errors'])

        # Test password mismatch
        res = self.client.post('/api/auth/signup', json={
            'name': 'Test Student',
            'email': 'student@test.edu',
            'password': 'password123',
            'confirm_password': 'different123'
        })
        self.assertEqual(res.status_code, 400)
        self.assertIn('confirm_password', res.get_json()['errors'])

        # Test valid registration
        res = self.client.post('/api/auth/signup', json={
            'name': 'Sarah Connor',
            'email': 'sarah@university.edu',
            'password': 'safePassword123',
            'confirm_password': 'safePassword123'
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(data['user']['email'], 'sarah@university.edu')

        # Verify password is stored hashed with bcrypt in DB, NOT plaintext
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT password_hash FROM users WHERE email = 'sarah@university.edu'")
            row = cursor.fetchone()
            self.assertIsNotNone(row)
            pw_hash = row['password_hash']
            self.assertNotEqual(pw_hash, 'safePassword123')
            self.assertTrue(pw_hash.startswith('$2b$') or pw_hash.startswith('$2a$'))
            self.assertTrue(check_password('safePassword123', pw_hash))

    def test_02_route_protection_and_unauthorized_redirect(self):
        """Verify unauthenticated requests to protected pages redirect to login."""
        protected_routes = ['/dashboard', '/chat', '/planner', '/notes', '/quiz', '/weak-topics', '/profile']
        for route in protected_routes:
            res = self.client.get(route, follow_redirects=False)
            self.assertEqual(res.status_code, 302, f"Route {route} did not redirect unauthenticated user.")
            self.assertIn('/login', res.headers.get('Location', ''))

        # API routes should return 401 Unauthorized
        api_res = self.client.get('/api/planner/sessions')
        self.assertEqual(api_res.status_code, 401)
        self.assertFalse(api_res.get_json()['success'])

    def test_03_login_and_session_access(self):
        """Verify login credentials, cookie setting, and access to protected dashboard."""
        # Register user
        self.client.post('/api/auth/signup', json={
            'name': 'James Miller',
            'email': 'james@college.edu',
            'password': 'mypassword99',
            'confirm_password': 'mypassword99'
        })

        # Clear cookies to simulate clean session
        self.clear_cookies()

        # Attempt login with wrong password
        fail_res = self.client.post('/api/auth/login', json={
            'email': 'james@college.edu',
            'password': 'wrongpassword'
        })
        self.assertEqual(fail_res.status_code, 401)

        # Correct login
        login_res = self.client.post('/api/auth/login', json={
            'email': 'james@college.edu',
            'password': 'mypassword99'
        })
        self.assertEqual(login_res.status_code, 200)
        self.assertTrue(login_res.get_json()['success'])

        # Now dashboard should render 200 OK
        dash_res = self.client.get('/dashboard')
        self.assertEqual(dash_res.status_code, 200)
        self.assertIn(b'James Miller', dash_res.data)

    def test_04_user_scoping_and_data_isolation(self):
        """Verify User A cannot access User B's study sessions, notes, or chat history."""
        # Create User A
        self.client.post('/api/auth/signup', json={
            'name': 'User A',
            'email': 'userA@test.edu',
            'password': 'passwordA123',
            'confirm_password': 'passwordA123'
        })
        # User A creates a study session
        self.client.post('/api/planner/sessions', json={
            'subject': 'Quantum Mechanics',
            'date': '2026-09-20',
            'duration': 60,
            'notes': 'Secret study notes for User A only'
        })
        # User A creates a note
        self.client.post('/api/notes', json={
            'topic': 'User A Private Note',
            'raw_text': 'Confidential research notes on dark matter.'
        })

        # Now switch to User B
        self.clear_cookies()
        self.client.post('/api/auth/signup', json={
            'name': 'User B',
            'email': 'userB@test.edu',
            'password': 'passwordB123',
            'confirm_password': 'passwordB123'
        })

        # User B queries study sessions
        res = self.client.get('/api/planner/sessions')
        sessions = res.get_json()['sessions']
        subjects = [s['subject'] for s in sessions]
        self.assertNotIn('Quantum Mechanics', subjects, "Data leakage: User B saw User A's session!")

        # User B queries notes
        res_notes = self.client.get('/api/notes')
        notes = res_notes.get_json()['notes']
        topics = [n['topic'] for n in notes]
        self.assertNotIn('User A Private Note', topics, "Data leakage: User B saw User A's note!")

    def test_05_study_planner_crud(self):
        """Verify study planner creation, completion toggle, and deletion."""
        self.client.post('/api/auth/signup', json={
            'name': 'Emma Watson',
            'email': 'emma@oxford.edu',
            'password': 'studyHard123',
            'confirm_password': 'studyHard123'
        })

        # Add session
        create_res = self.client.post('/api/planner/sessions', json={
            'subject': 'Linear Algebra',
            'date': '2026-09-22',
            'duration': 45,
            'notes': 'Eigenvalues and Eigenvectors'
        })
        self.assertEqual(create_res.status_code, 201)
        session_id = create_res.get_json()['session']['id']

        # Toggle completion
        toggle_res = self.client.patch(f'/api/planner/sessions/{session_id}/toggle')
        self.assertEqual(toggle_res.status_code, 200)
        self.assertTrue(toggle_res.get_json()['completed'])

        # Delete session
        del_res = self.client.delete(f'/api/planner/sessions/{session_id}')
        self.assertEqual(del_res.status_code, 200)

        # Verify gone
        list_res = self.client.get('/api/planner/sessions')
        ids = [s['id'] for s in list_res.get_json()['sessions']]
        self.assertNotIn(session_id, ids)

    def test_06_ai_chat_and_summarizer(self):
        """Verify chat response generation and note summarization."""
        self.client.post('/api/auth/signup', json={
            'name': 'Leo Rover',
            'email': 'leo@tech.edu',
            'password': 'passwordRover1',
            'confirm_password': 'passwordRover1'
        })

        # Send chat message
        chat_res = self.client.post('/api/chat/messages', json={
            'message': 'Explain recursion in simple terms'
        })
        self.assertEqual(chat_res.status_code, 200)
        reply = chat_res.get_json()['response']['message']
        self.assertIn('Recursion', reply)
        self.assertIn('Base Case', reply)

        # Summarize note
        note_res = self.client.post('/api/notes', json={
            'topic': 'Photosynthesis',
            'raw_text': 'Plants convert sunlight into chemical energy using chlorophyll. Oxygen is released as a byproduct.'
        })
        self.assertEqual(note_res.status_code, 201)
        summary = note_res.get_json()['note']['summary_text']
        self.assertIn('Core Concept Overview', summary)

    def test_07_quiz_generation_and_submission(self):
        """Verify dynamic quiz generation and recording score."""
        self.client.post('/api/auth/signup', json={
            'name': 'Devin Student',
            'email': 'devin@mit.edu',
            'password': 'devinPassword9',
            'confirm_password': 'devinPassword9'
        })

        # Generate quiz
        gen_res = self.client.post('/api/quiz/generate', json={'topic': 'Calculus'})
        self.assertEqual(gen_res.status_code, 200)
        questions = gen_res.get_json()['questions']
        self.assertEqual(len(questions), 5)

        # Submit quiz score
        sub_res = self.client.post('/api/quiz/submit', json={
            'topic': 'Calculus',
            'score': 4,
            'total_questions': 5
        })
        self.assertEqual(sub_res.status_code, 201)

        # Check history
        hist_res = self.client.get('/api/quiz/history')
        self.assertEqual(len(hist_res.get_json()['history']), 1)
        self.assertEqual(hist_res.get_json()['history'][0]['score'], 4)

    def test_08_weak_topics_and_profile_password_change(self):
        """Verify weak topics tracking and password change with current password check."""
        self.client.post('/api/auth/signup', json={
            'name': 'Carlos Rivera',
            'email': 'carlos@uni.edu',
            'password': 'originalPassword1',
            'confirm_password': 'originalPassword1'
        })

        # Add weak topic
        wt_res = self.client.post('/api/weak-topics', json={
            'topic': 'Dynamic Programming',
            'reason': 'Difficulty figuring out overlapping subproblems'
        })
        self.assertEqual(wt_res.status_code, 201)
        wt_id = wt_res.get_json()['topic']['id']

        # Update status
        st_res = self.client.patch(f'/api/weak-topics/{wt_id}/status', json={'status': 'Mastered'})
        self.assertEqual(st_res.status_code, 200)

        # Change password with wrong current password (should fail)
        bad_pw_res = self.client.post('/api/profile/change-password', json={
            'current_password': 'wrongCurrentPassword',
            'new_password': 'brandNewPassword1',
            'confirm_new_password': 'brandNewPassword1'
        })
        self.assertEqual(bad_pw_res.status_code, 400)

        # Change password with correct current password (should succeed)
        good_pw_res = self.client.post('/api/profile/change-password', json={
            'current_password': 'originalPassword1',
            'new_password': 'brandNewPassword1',
            'confirm_new_password': 'brandNewPassword1'
        })
        self.assertEqual(good_pw_res.status_code, 200)

        # Verify old password no longer logs in
        self.clear_cookies()
        old_login = self.client.post('/api/auth/login', json={
            'email': 'carlos@uni.edu',
            'password': 'originalPassword1'
        })
        self.assertEqual(old_login.status_code, 401)

        # Verify new password logs in
        new_login = self.client.post('/api/auth/login', json={
            'email': 'carlos@uni.edu',
            'password': 'brandNewPassword1'
        })
        self.assertEqual(new_login.status_code, 200)

if __name__ == '__main__':
    unittest.main()
