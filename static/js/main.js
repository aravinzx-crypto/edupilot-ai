// EduPilot AI - Client Interactivity Engine

// Toast Notification System
function showToast(message, type = 'success') {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `
    <span>${type === 'success' ? '✓' : '⚠️'}</span>
    <div>${message}</div>
  `;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// API Helper
async function apiCall(url, method = 'GET', data = null) {
  const options = {
    method,
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json'
    }
  };
  if (data) {
    options.body = JSON.stringify(data);
  }

  try {
    const response = await fetch(url, options);
    const json = await response.json();
    if (!response.ok) {
      throw new Error(json.error || (json.errors ? Object.values(json.errors)[0] : 'Request failed'));
    }
    return json;
  } catch (err) {
    console.error(`API Error on ${url}:`, err);
    throw err;
  }
}

// Mobile Menu Toggle
document.addEventListener('DOMContentLoaded', () => {
  const mobileToggle = document.getElementById('mobileMenuToggle');
  const sidebar = document.getElementById('appSidebar');

  if (mobileToggle && sidebar) {
    mobileToggle.addEventListener('click', () => {
      sidebar.classList.toggle('open');
    });

    document.addEventListener('click', (e) => {
      if (!sidebar.contains(e.target) && !mobileToggle.contains(e.target) && sidebar.classList.contains('open')) {
        sidebar.classList.remove('open');
      }
    });
  }
});

// Interactive Quiz Controller
class QuizRunner {
  constructor(containerId) {
    this.container = document.getElementById(containerId);
    this.questions = [];
    this.currentIndex = 0;
    this.score = 0;
    this.userAnswers = [];
    this.topic = '';
  }

  start(topic, questions) {
    this.topic = topic;
    this.questions = questions;
    this.currentIndex = 0;
    this.score = 0;
    this.userAnswers = [];
    this.renderQuestion();
  }

  renderQuestion() {
    if (!this.container) return;
    const q = this.questions[this.currentIndex];
    const total = this.questions.length;
    const progressPct = ((this.currentIndex) / total) * 100;

    this.container.innerHTML = `
      <div class="quiz-question-card">
        <div class="question-progress">
          <span>Question ${this.currentIndex + 1} of ${total}</span>
          <span>Topic: <strong>${this.topic}</strong></span>
        </div>
        <div class="progress-bar-track">
          <div class="progress-bar-fill" style="width: ${progressPct}%"></div>
        </div>

        <h3 style="margin-top: 24px; font-size: 1.25rem;">${q.question}</h3>

        <div class="options-list">
          ${q.options.map((opt, idx) => `
            <button class="option-btn" data-index="${idx}">${opt}</button>
          `).join('')}
        </div>

        <div id="quizFeedback" style="display: none;"></div>

        <div style="display: flex; justify-content: flex-end; margin-top: 20px;">
          <button id="nextQuestionBtn" class="btn btn-primary" style="display: none;">
            ${this.currentIndex + 1 === total ? 'Complete & Save Quiz' : 'Next Question →'}
          </button>
        </div>
      </div>
    `;

    const optionBtns = this.container.querySelectorAll('.option-btn');
    const feedbackDiv = this.container.querySelector('#quizFeedback');
    const nextBtn = this.container.querySelector('#nextQuestionBtn');

    optionBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        const selectedIdx = parseInt(btn.getAttribute('data-index'));
        const isCorrect = selectedIdx === q.correct_index;

        // Disable options
        optionBtns.forEach(b => b.disabled = true);

        if (isCorrect) {
          btn.classList.add('correct');
          this.score++;
        } else {
          btn.classList.add('wrong');
          optionBtns[q.correct_index].classList.add('correct');
        }

        this.userAnswers.push({ selectedIdx, correct: isCorrect });

        feedbackDiv.style.display = 'block';
        feedbackDiv.innerHTML = `
          <div class="explanation-box">
            <strong>${isCorrect ? '🎉 Correct!' : '💡 Explanation:'}</strong> ${q.explanation}
          </div>
        `;

        nextBtn.style.display = 'inline-flex';
      });
    });

    nextBtn.addEventListener('click', () => {
      if (this.currentIndex + 1 < total) {
        this.currentIndex++;
        this.renderQuestion();
      } else {
        this.finishQuiz();
      }
    });
  }

  async finishQuiz() {
    const total = this.questions.length;
    const pct = Math.round((this.score / total) * 100);

    // Save score to backend
    try {
      await apiCall('/api/quiz/submit', 'POST', {
        topic: this.topic,
        score: this.score,
        total_questions: total
      });
      showToast(`Quiz saved! Score: ${this.score}/${total}`);
    } catch (e) {
      showToast('Could not record score', 'error');
    }

    this.container.innerHTML = `
      <div class="quiz-question-card" style="text-align: center; padding: 48px 32px;">
        <div style="width: 80px; height: 80px; margin: 0 auto 20px; border-radius: 50%; background: ${pct >= 60 ? 'var(--color-success-soft)' : 'var(--color-gold-soft)'}; display: flex; align-items: center; justify-content: center; font-size: 2.2rem;">
          ${pct >= 60 ? '🏆' : '📚'}
        </div>
        <h2 style="font-size: 2rem; margin-bottom: 8px;">Quiz Completed!</h2>
        <p style="color: var(--color-text-muted); margin-bottom: 24px;">Topic: <strong>${this.topic}</strong></p>

        <div style="background: var(--color-bg); padding: 20px; border-radius: var(--radius-lg); max-width: 320px; margin: 0 auto 30px; border: 1px solid var(--color-border);">
          <div style="font-size: 3rem; font-weight: 800; color: var(--color-indigo);">${pct}%</div>
          <div style="font-weight: 600; color: var(--color-text-muted);">${this.score} out of ${total} correct</div>
        </div>

        <div style="display: flex; gap: 14px; justify-content: center; flex-wrap: wrap;">
          <a href="/quiz" class="btn btn-secondary">Take Another Quiz</a>
          <a href="/weak-topics" class="btn btn-accent">Review Weak Topics</a>
          <a href="/dashboard" class="btn btn-primary">Go to Dashboard</a>
        </div>
      </div>
    `;
  }
}
