# EduPilot AI — Personal AI Study Companion for College Students

> **Tagline**: *"Study smarter with EduPilot AI — Your Personal Study Companion"*  
> **Design Objective**: Built to help college students manage studies effectively, understand complex topics with an intelligent 24/7 assistant, organize study schedules, generate instant study summaries, and prepare confidently for examinations.

---

## 🚀 Features & Architecture

### 1. Production-Ready Authentication
- **Secure Password Hashing**: Real `bcrypt` hashing with salt rounds.
- **Signed Tokens & Sessions**: JWT with secure `HttpOnly` and `SameSite=Lax` cookies.
- **Route Protection**: All student dashboard routes and API endpoints verify authentication before rendering or executing database queries.
- **Strict Data Isolation**: Every study session, quiz result, weak topic, note, and chat message is strictly scoped by `user_id`.

### 2. The 10 Core Application Pages
1. **Landing Page (`/`)**: Hero section featuring the exact project tagline and problem framing, 4 core feature cards (*Private AI tutor*, *Study planner*, *Instant summaries*, *Smart quizzes*), and privacy footer badge.
2. **Sign Up Page (`/signup`)**: Real account creation with client and server-side validation (minimum 6-character passwords, matching confirm password, valid email check).
3. **Login Page (`/login`)**: Real authentication against stored bcrypt hashes, "Forgot password" link, plus a **One-Click Demo Student** button.
4. **Student Dashboard (`/dashboard`)**: Personalized greeting by student name, live metric cards (today's study sessions, recent quiz percentage, weak topics count, total study hours), today's interactive timetable with quick-completion checkboxes, and a quick-action launchpad.
5. **AI Chatbot (`/chat`)**: Chat bubble interface with conversational history persistence, suggested academic prompts (*Recursion*, *Exam Tips*, *Data Structures*, *Calculus*, *Economics*), code syntax highlighting, and clear history option.
6. **Study Planner (`/planner`)**: Form to add study sessions (subject, date, duration, notes) with filtering by status (All, Pending, Done), real-time completion toggling, and deletion.
7. **AI Notes & Summaries (`/notes`)**: Paste lecture or textbook content to extract structured summaries (Core Concept Overview, Key Takeaways, Terminology, and Rapid Exam Flash Facts). Includes clipboard copying and deletion.
8. **Smart Quiz Generator (`/quiz`)**: Topic selector (or custom exam subject input) that dynamically generates an interactive 5-question multiple-choice quiz with immediate answer feedback, detailed explanations, score calculation, and persistent history tracking.
9. **Weak Topics Tracker (`/weak-topics`)**: Dedicated mastery log with difficulty reasons, status toggling (*Needs Review* / *Mastered*), and direct launch actions (*Ask AI Tutor to Explain* or *Quiz This Topic*).
10. **Settings & Profile (`/profile`)**: Update student name and preferred study language (English, Spanish, French, German, Hindi, Mandarin), change password with current password verification, and account data isolation details.

---

## 🎨 Visual Design Palette
- **Deep Indigo**: `#2D1B69` (Headers, brand logo, strong accents)
- **Vivid Violet-Blue**: `#6C63FF` (Primary actions, active states, progress indicators)
- **Warm Gold**: `#FFC857` (Action highlights, badges, scores)
- **Light Calm Background**: `#F7F7FB`
- **Typography**: Google Fonts *Plus Jakarta Sans* for readable body text and *Outfit* for bold display headings.

---

## 🛠️ Quick Start

### 1. Install Dependencies
```bash
python -m pip install flask pyjwt bcrypt
```

### 2. Run the Application
```bash
python app.py
```
Open your browser and navigate to:
```
http://127.0.0.1:5000
```

### 3. Demo Credentials (Pre-seeded)
- **Email**: `demo@edupilot.ai`
- **Password**: `demostudent123`
*(Or simply click "Sign In as Demo Student" on the login page)*

### 4. Run Automated Test Suite
```bash
python -m unittest tests/test_edupilot.py
```
All 8 test suites verify:
- Bcrypt password hashing
- Session & JWT token authentication
- Route protection and unauthorized redirects
- User scoping & data isolation (User A cannot access User B's records)
- Study planner CRUD operations
- AI chat & summarizer services
- Quiz generator & score recording
- Weak topics tracker & password change with current password check
