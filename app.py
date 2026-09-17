import os
import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, make_response, session
from database import init_db, get_db, seed_demo_data
from auth import (
    hash_password, check_password, generate_token, decode_token,
    validate_registration, get_current_user, login_required,
    SECRET_KEY, TOKEN_COOKIE_NAME
)
import ai_service

app = Flask(__name__)
app.secret_key = SECRET_KEY

# Ensure database is initialized and seeded on startup
init_db()
seed_demo_data()

@app.context_processor
def inject_user():
    """Inject current user into all Jinja templates."""
    return {'current_user': get_current_user()}

# ==========================================
# PUBLIC WEB ROUTES
# ==========================================

@app.route('/')
def index():
    """Landing Page with project context, problem statement, features, and footer."""
    return render_template('index.html')

@app.route('/login')
def login_page():
    """Login Page."""
    if get_current_user():
        return redirect(url_for('dashboard'))
    return render_template('login.html', next=request.args.get('next', ''))

@app.route('/signup')
def signup_page():
    """Sign Up Page."""
    if get_current_user():
        return redirect(url_for('dashboard'))
    return render_template('signup.html')

@app.route('/forgot-password')
def forgot_password_page():
    """Forgot Password placeholder page."""
    return render_template('forgot_password.html')

@app.route('/logout')
def logout():
    """Logout action: clears session and authentication cookies."""
    session.clear()
    resp = make_response(redirect(url_for('login_page')))
    resp.delete_cookie(TOKEN_COOKIE_NAME)
    return resp

# ==========================================
# PROTECTED WEB ROUTES
# ==========================================

@app.route('/dashboard')
@login_required
def dashboard():
    """Student Dashboard overview."""
    user = get_current_user()
    today_str = datetime.date.today().isoformat()
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Today's study sessions
        cursor.execute(
            "SELECT * FROM study_sessions WHERE user_id = ? AND date = ? ORDER BY id DESC",
            (user['id'], today_str)
        )
        today_sessions = [dict(r) for r in cursor.fetchall()]
        
        # All pending sessions count
        cursor.execute(
            "SELECT COUNT(*) as count, SUM(duration) as total_duration FROM study_sessions WHERE user_id = ?",
            (user['id'],)
        )
        stats_row = cursor.fetchone()
        total_sessions = stats_row['count'] if stats_row else 0
        total_duration = stats_row['total_duration'] if stats_row and stats_row['total_duration'] else 0
        
        # Recent quiz score
        cursor.execute(
            "SELECT * FROM quizzes WHERE user_id = ? ORDER BY created_at DESC LIMIT 1",
            (user['id'],)
        )
        recent_quiz = cursor.fetchone()
        recent_quiz = dict(recent_quiz) if recent_quiz else None
        
        # Total quizzes count
        cursor.execute(
            "SELECT COUNT(*) as count FROM quizzes WHERE user_id = ?",
            (user['id'],)
        )
        quiz_count = cursor.fetchone()['count']
        
        # Weak topics count
        cursor.execute(
            "SELECT COUNT(*) as count FROM weak_topics WHERE user_id = ? AND status != 'Mastered'",
            (user['id'],)
        )
        weak_count = cursor.fetchone()['count']
        
        # Notes count
        cursor.execute(
            "SELECT COUNT(*) as count FROM notes WHERE user_id = ?",
            (user['id'],)
        )
        notes_count = cursor.fetchone()['count']

    return render_template(
        'dashboard.html',
        today_sessions=today_sessions,
        recent_quiz=recent_quiz,
        total_sessions=total_sessions,
        total_duration=total_duration,
        quiz_count=quiz_count,
        weak_count=weak_count,
        notes_count=notes_count
    )

@app.route('/chat')
@login_required
def chat_page():
    """AI Chatbot Interface."""
    user = get_current_user()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, message, sender, created_at FROM chat_messages WHERE user_id = ? ORDER BY id ASC",
            (user['id'],)
        )
        messages = [dict(r) for r in cursor.fetchall()]
    return render_template('chat.html', messages=messages)

@app.route('/planner')
@login_required
def planner_page():
    """Study Planner page."""
    user = get_current_user()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM study_sessions WHERE user_id = ? ORDER BY date ASC, id ASC",
            (user['id'],)
        )
        sessions = [dict(r) for r in cursor.fetchall()]
    return render_template('planner.html', sessions=sessions, today=datetime.date.today().isoformat())

@app.route('/notes')
@login_required
def notes_page():
    """AI Notes / Summary page."""
    user = get_current_user()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM notes WHERE user_id = ? ORDER BY created_at DESC",
            (user['id'],)
        )
        notes = [dict(r) for r in cursor.fetchall()]
    return render_template('notes.html', notes=notes)

@app.route('/quiz')
@login_required
def quiz_page():
    """Quiz Generator page."""
    user = get_current_user()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM quizzes WHERE user_id = ? ORDER BY created_at DESC",
            (user['id'],)
        )
        quiz_history = [dict(r) for r in cursor.fetchall()]
    return render_template('quiz.html', quiz_history=quiz_history)

@app.route('/weak-topics')
@login_required
def weak_topics_page():
    """Weak Topics Tracker page."""
    user = get_current_user()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM weak_topics WHERE user_id = ? ORDER BY id DESC",
            (user['id'],)
        )
        topics = [dict(r) for r in cursor.fetchall()]
    return render_template('weak_topics.html', topics=topics)

@app.route('/profile')
@login_required
def profile_page():
    """Profile and Settings page."""
    user = get_current_user()
    return render_template('profile.html', user=user)

# ==========================================
# REST API ENDPOINTS
# ==========================================

# 1. Authentication APIs
@app.route('/api/auth/signup', methods=['POST'])
def api_signup():
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    confirm_password = data.get('confirm_password', '')

    errors = validate_registration(name, email, password, confirm_password)
    if errors:
        return jsonify({'success': False, 'errors': errors}), 400

    # Check for existing email
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        if cursor.fetchone():
            return jsonify({'success': False, 'errors': {'email': 'An account with this email already exists.'}}), 400

        # Hash password and insert
        pw_hash = hash_password(password)
        cursor.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (name, email, pw_hash)
        )
        user_id = cursor.lastrowid

        # Insert a welcome study session and starter chat message
        cursor.execute(
            "INSERT INTO study_sessions (user_id, subject, date, duration, notes, completed) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, "Welcome to EduPilot AI", datetime.date.today().isoformat(), 30, "Get familiar with the dashboard, AI tutor, and study planner.", 0)
        )
        cursor.execute(
            "INSERT INTO chat_messages (user_id, message, sender) VALUES (?, ?, ?)",
            (user_id, f"Welcome to EduPilot AI, {name}! I am your personal study companion. Ask me anything about your coursework, or ask for an exam study strategy to begin.", "ai")
        )

    # Generate token
    token = generate_token(user_id, email, name)
    session['token'] = token

    resp = make_response(jsonify({
        'success': True,
        'message': 'Account created successfully!',
        'user': {'id': user_id, 'name': name, 'email': email},
        'redirect': url_for('dashboard')
    }))
    resp.set_cookie(TOKEN_COOKIE_NAME, token, httponly=True, max_age=7 * 24 * 3600, samesite='Lax')
    return resp

@app.route('/api/auth/login', methods=['POST'])
def api_login():
    data = request.get_json() or {}
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    if not email or not password:
        return jsonify({'success': False, 'error': 'Please provide both email and password.'}), 400

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, email, password_hash FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()

        if not user or not check_password(password, user['password_hash']):
            return jsonify({'success': False, 'error': 'Invalid email address or password.'}), 401

        user_id = user['id']
        name = user['name']

    token = generate_token(user_id, email, name)
    session['token'] = token

    resp = make_response(jsonify({
        'success': True,
        'message': 'Logged in successfully!',
        'user': {'id': user_id, 'name': name, 'email': email},
        'redirect': request.args.get('next') or url_for('dashboard')
    }))
    resp.set_cookie(TOKEN_COOKIE_NAME, token, httponly=True, max_age=7 * 24 * 3600, samesite='Lax')
    return resp

@app.route('/api/auth/logout', methods=['POST'])
def api_logout():
    session.clear()
    resp = make_response(jsonify({'success': True, 'message': 'Logged out.'}))
    resp.delete_cookie(TOKEN_COOKIE_NAME)
    return resp

@app.route('/api/auth/me', methods=['GET'])
def api_me():
    user = get_current_user()
    if not user:
        return jsonify({'authenticated': False}), 200
    return jsonify({'authenticated': True, 'user': user}), 200

# 2. AI Chat APIs
@app.route('/api/chat/messages', methods=['GET'])
@login_required
def api_get_chat_messages():
    user = get_current_user()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, message, sender, created_at FROM chat_messages WHERE user_id = ? ORDER BY id ASC",
            (user['id'],)
        )
        messages = [dict(r) for r in cursor.fetchall()]
    return jsonify({'success': True, 'messages': messages})

@app.route('/api/chat/messages', methods=['POST'])
@login_required
def api_send_chat_message():
    user = get_current_user()
    data = request.get_json() or {}
    message_text = data.get('message', '').strip()

    if not message_text:
        return jsonify({'success': False, 'error': 'Message cannot be empty.'}), 400

    # Save user message
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO chat_messages (user_id, message, sender) VALUES (?, ?, ?)",
            (user['id'], message_text, 'user')
        )

        # Generate intelligent assistant response
        cursor.execute(
            "SELECT message, sender FROM chat_messages WHERE user_id = ? ORDER BY id DESC LIMIT 6",
            (user['id'],)
        )
        history = [dict(r) for r in cursor.fetchall()]
        
        ai_reply = ai_service.generate_chat_response(
            message_text,
            user_name=user['name'],
            preferred_language=user.get('preferred_language', 'English'),
            history=history
        )

        cursor.execute(
            "INSERT INTO chat_messages (user_id, message, sender) VALUES (?, ?, ?)",
            (user['id'], ai_reply, 'ai')
        )
        ai_msg_id = cursor.lastrowid

    return jsonify({
        'success': True,
        'response': {
            'id': ai_msg_id,
            'message': ai_reply,
            'sender': 'ai',
            'created_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    })

@app.route('/api/chat/messages', methods=['DELETE'])
@login_required
def api_clear_chat():
    user = get_current_user()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM chat_messages WHERE user_id = ?", (user['id'],))
        # Add fresh greeting
        cursor.execute(
            "INSERT INTO chat_messages (user_id, message, sender) VALUES (?, ?, ?)",
            (user['id'], f"Chat history cleared. How can I assist your studies today, {user['name']}?", 'ai')
        )
    return jsonify({'success': True, 'message': 'Chat history cleared.'})

# 3. Study Planner APIs
@app.route('/api/planner/sessions', methods=['GET'])
@login_required
def api_get_sessions():
    user = get_current_user()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM study_sessions WHERE user_id = ? ORDER BY date ASC, id ASC",
            (user['id'],)
        )
        sessions = [dict(r) for r in cursor.fetchall()]
    return jsonify({'success': True, 'sessions': sessions})

@app.route('/api/planner/sessions', methods=['POST'])
@login_required
def api_add_session():
    user = get_current_user()
    data = request.get_json() or {}
    subject = data.get('subject', '').strip()
    date_val = data.get('date', '').strip()
    duration = data.get('duration')
    notes = data.get('notes', '').strip()

    if not subject:
        return jsonify({'success': False, 'error': 'Subject is required.'}), 400
    if not date_val:
        return jsonify({'success': False, 'error': 'Date is required.'}), 400
    try:
        duration_int = int(duration)
        if duration_int <= 0:
            raise ValueError()
    except (TypeError, ValueError):
        return jsonify({'success': False, 'error': 'Duration must be a positive number of minutes.'}), 400

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO study_sessions (user_id, subject, date, duration, notes, completed) VALUES (?, ?, ?, ?, ?, 0)",
            (user['id'], subject, date_val, duration_int, notes)
        )
        new_id = cursor.lastrowid
        cursor.execute("SELECT * FROM study_sessions WHERE id = ?", (new_id,))
        session_row = dict(cursor.fetchone())

    return jsonify({'success': True, 'session': session_row}), 201

@app.route('/api/planner/sessions/<int:session_id>/toggle', methods=['PATCH'])
@login_required
def api_toggle_session(session_id):
    user = get_current_user()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, completed FROM study_sessions WHERE id = ? AND user_id = ?", (session_id, user['id']))
        session_row = cursor.fetchone()
        if not session_row:
            return jsonify({'success': False, 'error': 'Session not found.'}), 404
        
        new_status = 0 if session_row['completed'] else 1
        cursor.execute("UPDATE study_sessions SET completed = ? WHERE id = ? AND user_id = ?", (new_status, session_id, user['id']))

    return jsonify({'success': True, 'completed': bool(new_status)})

@app.route('/api/planner/sessions/<int:session_id>', methods=['DELETE'])
@login_required
def api_delete_session(session_id):
    user = get_current_user()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM study_sessions WHERE id = ? AND user_id = ?", (session_id, user['id']))
        if cursor.rowcount == 0:
            return jsonify({'success': False, 'error': 'Session not found.'}), 404
    return jsonify({'success': True, 'message': 'Session deleted.'})

# 4. AI Notes & Summary APIs
@app.route('/api/notes', methods=['GET'])
@login_required
def api_get_notes():
    user = get_current_user()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM notes WHERE user_id = ? ORDER BY created_at DESC", (user['id'],))
        notes = [dict(r) for r in cursor.fetchall()]
    return jsonify({'success': True, 'notes': notes})

@app.route('/api/notes', methods=['POST'])
@login_required
def api_create_note():
    user = get_current_user()
    data = request.get_json() or {}
    topic = data.get('topic', '').strip()
    raw_text = data.get('raw_text', '').strip()

    if not topic:
        return jsonify({'success': False, 'error': 'Topic title is required.'}), 400
    if not raw_text:
        return jsonify({'success': False, 'error': 'Please provide notes or content to summarize.'}), 400

    # Summarize with AI service
    summary_text = ai_service.summarize_text(topic, raw_text)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO notes (user_id, topic, raw_text, summary_text) VALUES (?, ?, ?, ?)",
            (user['id'], topic, raw_text, summary_text)
        )
        new_id = cursor.lastrowid
        cursor.execute("SELECT * FROM notes WHERE id = ?", (new_id,))
        note_row = dict(cursor.fetchone())

    return jsonify({'success': True, 'note': note_row}), 201

@app.route('/api/notes/<int:note_id>', methods=['DELETE'])
@login_required
def api_delete_note(note_id):
    user = get_current_user()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM notes WHERE id = ? AND user_id = ?", (note_id, user['id']))
        if cursor.rowcount == 0:
            return jsonify({'success': False, 'error': 'Note not found.'}), 404
    return jsonify({'success': True, 'message': 'Note deleted.'})

# 5. Quiz Generator APIs
@app.route('/api/quiz/generate', methods=['POST'])
@login_required
def api_generate_quiz():
    data = request.get_json() or {}
    topic = data.get('topic', '').strip()
    if not topic:
        return jsonify({'success': False, 'error': 'Please provide a quiz topic.'}), 400

    questions = ai_service.generate_quiz(topic, count=5)
    return jsonify({'success': True, 'topic': topic, 'questions': questions})

@app.route('/api/quiz/submit', methods=['POST'])
@login_required
def api_submit_quiz():
    user = get_current_user()
    data = request.get_json() or {}
    topic = data.get('topic', '').strip()
    score = data.get('score')
    total_questions = data.get('total_questions', 5)

    if not topic or score is None:
        return jsonify({'success': False, 'error': 'Topic and score are required.'}), 400

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO quizzes (user_id, topic, score, total_questions) VALUES (?, ?, ?, ?)",
            (user['id'], topic, int(score), int(total_questions))
        )
        quiz_id = cursor.lastrowid
        cursor.execute("SELECT * FROM quizzes WHERE id = ?", (quiz_id,))
        quiz_row = dict(cursor.fetchone())

    return jsonify({'success': True, 'quiz': quiz_row}), 201

@app.route('/api/quiz/history', methods=['GET'])
@login_required
def api_get_quiz_history():
    user = get_current_user()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM quizzes WHERE user_id = ? ORDER BY created_at DESC", (user['id'],))
        history = [dict(r) for r in cursor.fetchall()]
    return jsonify({'success': True, 'history': history})

# 6. Weak Topics APIs
@app.route('/api/weak-topics', methods=['GET'])
@login_required
def api_get_weak_topics():
    user = get_current_user()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM weak_topics WHERE user_id = ? ORDER BY id DESC", (user['id'],))
        topics = [dict(r) for r in cursor.fetchall()]
    return jsonify({'success': True, 'topics': topics})

@app.route('/api/weak-topics', methods=['POST'])
@login_required
def api_add_weak_topic():
    user = get_current_user()
    data = request.get_json() or {}
    topic = data.get('topic', '').strip()
    reason = data.get('reason', '').strip()

    if not topic:
        return jsonify({'success': False, 'error': 'Topic is required.'}), 400
    if not reason:
        return jsonify({'success': False, 'error': 'Reason or difficulty explanation is required.'}), 400

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO weak_topics (user_id, topic, reason, status) VALUES (?, ?, ?, 'Needs Review')",
            (user['id'], topic, reason)
        )
        topic_id = cursor.lastrowid
        cursor.execute("SELECT * FROM weak_topics WHERE id = ?", (topic_id,))
        topic_row = dict(cursor.fetchone())

    return jsonify({'success': True, 'topic': topic_row}), 201

@app.route('/api/weak-topics/<int:topic_id>/status', methods=['PATCH'])
@login_required
def api_update_weak_topic_status(topic_id):
    user = get_current_user()
    data = request.get_json() or {}
    new_status = data.get('status', 'Mastered').strip()

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE weak_topics SET status = ? WHERE id = ? AND user_id = ?",
            (new_status, topic_id, user['id'])
        )
        if cursor.rowcount == 0:
            return jsonify({'success': False, 'error': 'Topic not found.'}), 404

    return jsonify({'success': True, 'status': new_status})

@app.route('/api/weak-topics/<int:topic_id>', methods=['DELETE'])
@login_required
def api_delete_weak_topic(topic_id):
    user = get_current_user()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM weak_topics WHERE id = ? AND user_id = ?", (topic_id, user['id']))
        if cursor.rowcount == 0:
            return jsonify({'success': False, 'error': 'Topic not found.'}), 404
    return jsonify({'success': True, 'message': 'Topic removed.'})

# 7. Profile & Settings APIs
@app.route('/api/profile', methods=['PATCH'])
@login_required
def api_update_profile():
    user = get_current_user()
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    preferred_language = data.get('preferred_language', 'English').strip()

    if not name or len(name) < 2:
        return jsonify({'success': False, 'error': 'Full name must be at least 2 characters.'}), 400

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET name = ?, preferred_language = ? WHERE id = ?",
            (name, preferred_language, user['id'])
        )

    return jsonify({'success': True, 'message': 'Profile updated successfully!', 'name': name, 'preferred_language': preferred_language})

@app.route('/api/profile/change-password', methods=['POST'])
@login_required
def api_change_password():
    user = get_current_user()
    data = request.get_json() or {}
    current_password = data.get('current_password', '')
    new_password = data.get('new_password', '')
    confirm_new_password = data.get('confirm_new_password', '')

    if not current_password or not new_password:
        return jsonify({'success': False, 'error': 'All fields are required.'}), 400

    if len(new_password) < 6:
        return jsonify({'success': False, 'error': 'New password must be at least 6 characters long.'}), 400

    if new_password != confirm_new_password:
        return jsonify({'success': False, 'error': 'New passwords do not match.'}), 400

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT password_hash FROM users WHERE id = ?", (user['id'],))
        row = cursor.fetchone()
        if not row or not check_password(current_password, row['password_hash']):
            return jsonify({'success': False, 'error': 'Current password is incorrect.'}), 400

        new_hash = hash_password(new_password)
        cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_hash, user['id']))

    return jsonify({'success': True, 'message': 'Password updated successfully!'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
