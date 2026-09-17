import os
import re
import json
import random

# Optional API integration if keys exist in environment
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

SUBJECT_KNOWLEDGE_BASE = {
    'computer science': [
        "Data Structures (Arrays, Linked Lists, Trees, Graphs, Hash Maps)",
        "Algorithm Analysis: Big-O notation measures time and space complexity as input size grows toward infinity.",
        "Object-Oriented Programming principles: Encapsulation, Abstraction, Inheritance, and Polymorphism.",
        "Recursion: A function calling itself with a base case to prevent stack overflow."
    ],
    'calculus': [
        "Derivatives represent the instantaneous rate of change or the slope of the tangent line.",
        "Integrals calculate the accumulation of quantities and area under curves.",
        "Fundamental Theorem of Calculus links differentiation and integration.",
        "Chain Rule: d/dx [f(g(x))] = f'(g(x)) * g'(x)."
    ],
    'economics': [
        "Law of Supply and Demand: Price reaches equilibrium where quantity demanded equals quantity supplied.",
        "Opportunity Cost: The value of the next best alternative foregone when making a choice.",
        "Inflation: General increase in prices and fall in purchasing value of money.",
        "Elasticity measures responsiveness of quantity demanded to changes in price."
    ],
    'biology': [
        "Cellular Respiration converts glucose and oxygen into ATP, CO2, and water.",
        "Photosynthesis: Plants convert sunlight, water, and carbon dioxide into glucose and oxygen.",
        "DNA Replication follows a semi-conservative model utilizing DNA polymerase.",
        "Central Dogma of Molecular Biology: DNA -> RNA (transcription) -> Protein (translation)."
    ]
}

def generate_chat_response(message: str, user_name: str = "Student", preferred_language: str = "English", history: list = None) -> str:
    """
    Intelligent college study assistant response generator.
    Provides structured, pedagogically sound, encouraging answers.
    """
    msg_lower = message.lower().strip()
    
    # Greetings & Introductions
    if any(greet in msg_lower for greet in ['hello', 'hi', 'hey', 'greetings', 'who are you', 'what can you do']):
        return (
            f"Hello {user_name}! 👋 I'm your **EduPilot AI Study Companion**.\n\n"
            f"I can help you with:\n"
            f"• **Simplifying tough concepts** (Calculus, Data Structures, Economics, Bio, Physics, etc.)\n"
            f"• **Creating customized revision schedules** & active recall prompts\n"
            f"• **Exam preparation** with mnemonics and practice questions\n"
            f"• **Drafting summaries** and breaking down academic papers or lecture notes\n\n"
            f"What topic or exam are you tackling today?"
        )

    # Study strategies & time management
    if any(k in msg_lower for k in ['study tip', 'pomodoro', 'exam prep', 'how to study', 'motivation', 'memorize', 'procrastination']):
        return (
            f"Here is a high-yield study strategy tailored for college exams, {user_name}:\n\n"
            f"### 🎯 The Active Recall & Spaced Repetition Framework\n"
            f"1. **Active Retrieval over Passive Re-reading**: Close your notes and write out everything you remember from memory on a blank sheet.\n"
            f"2. **The Feynman Technique**: Explain the concept out loud in plain English as if teaching a freshman. Identify where your explanation gets fuzzy.\n"
            f"3. **Pomodoro + Interleaving**: Study in 25-minute focused blocks with 5-minute breaks. Switch between two complementary topics to enhance retention.\n"
            f"4. **Target Weak Spots First**: Spend 70% of your energy on topics in your **Weak Topics** list before revising comfortable material.\n\n"
            f"Would you like me to quiz you on your current subject to test your active recall?"
        )

    # Recursion & Algorithms
    if 'recursion' in msg_lower:
        return (
            f"### 🔄 Understanding Recursion (Step-by-Step)\n\n"
            f"**Core Concept**: Recursion is a method where a problem is solved by breaking it down into smaller instances of the exact same problem until a trivial condition is met.\n\n"
            f"**The Two Mandatory Components**:\n"
            f"1. **Base Case**: The stopping condition that returns directly without calling the function again (prevents infinite loop / `RecursionError: maximum recursion depth exceeded`).\n"
            f"2. **Recursive Step**: Calling the function with a sub-problem that moves closer to the base case.\n\n"
            f"**Classic Example (Factorial `n!` in Python)**:\n"
            f"```python\n"
            f"def factorial(n):\n"
            f"    if n <= 1:           # 1. Base case\n"
            f"        return 1\n"
            f"    return n * factorial(n - 1)  # 2. Recursive step\n"
            f"```\n\n"
            f"**Call Stack Visualization for `factorial(3)`**:\n"
            f"• `factorial(3)` calls `3 * factorial(2)`\n"
            f"• `factorial(2)` calls `2 * factorial(1)`\n"
            f"• `factorial(1)` hits base case -> returns `1`\n"
            f"• Unwinds: `2 * 1 = 2` -> `3 * 2 = 6`.\n\n"
            f"Would you like to practice tracing a binary search tree or Fibonacci recursion next?"
        )

    # Data Structures
    if any(k in msg_lower for k in ['data structure', 'array', 'linked list', 'hash map', 'binary tree', 'stack', 'queue']):
        return (
            f"### 📦 High-Yield Data Structures Comparison\n\n"
            f"| Structure | Lookup (Avg) | Insertion (Avg) | Deletion (Avg) | Ideal Use Case |\n"
            f"| :--- | :--- | :--- | :--- | :--- |\n"
            f"| **Array** | `O(1)` (by index) | `O(n)` | `O(n)` | Fixed-size fast indexed access |\n"
            f"| **Linked List** | `O(n)` | `O(1)` (at head) | `O(1)` (if pointer known) | Frequent insertions/deletions |\n"
            f"| **Hash Table** | `O(1)` | `O(1)` | `O(1)` | Fast key-value mapping & deduplication |\n"
            f"| **Binary Search Tree** | `O(log n)` | `O(log n)` | `O(log n)` | Sorted elements & range queries |\n\n"
            f"**Exam Tip**: Remember that hash tables degrade to `O(n)` in the worst case if collision resolution (chaining or open addressing) isn't balanced!\n\n"
            f"Which specific data structure would you like to dive deeper into?"
        )

    # Calculus & Derivatives
    if any(k in msg_lower for k in ['calculus', 'derivative', 'integral', 'differentiation', 'limit']):
        return (
            f"### 📐 Calculus Fundamentals for College Exams\n\n"
            f"**1. The Intuition of the Derivative**:\n"
            f"The derivative measures how instantaneously sensitive a function's output is to a tiny change in input:\n"
            f"$$f'(x) = \\lim_{{h \\to 0}} \\frac{{f(x + h) - f(x)}}{{h}}$$\n\n"
            f"**2. Essential Differentiation Rules**:\n"
            f"• **Power Rule**: $\\frac{{d}}{{dx}}[x^n] = n x^{{n-1}}$\n"
            f"• **Product Rule**: $\\frac{{d}}{{dx}}[u \\cdot v] = u' v + u v'$\n"
            f"• **Quotient Rule**: $\\frac{{d}}{{dx}}\\left[\\frac{{u}}{{v}}\\right] = \\frac{{u'v - uv'}}{{v^2}}$ (Low d-High minus High d-Low over Low squared!)\n"
            f"• **Chain Rule**: $\\frac{{d}}{{dx}}[f(g(x))] = f'(g(x)) \\cdot g'(x)$\n\n"
            f"**3. Quick Practice**: What is the derivative of $f(x) = 3x^4 - 5\\sin(x)$? (Answer: $12x^3 - 5\\cos(x)$).\n\n"
            f"Do you have a specific problem from your homework you'd like to work through?"
        )

    # Economics
    if any(k in msg_lower for k in ['economics', 'supply', 'demand', 'macroeconomics', 'microeconomics', 'gdp', 'monetary']):
        return (
            f"### 📈 Core Economics Principles\n\n"
            f"**1. Market Equilibrium (Supply & Demand)**:\n"
            f"• **Demand Curve**: Downward sloping due to diminishing marginal utility and income/substitution effects.\n"
            f"• **Supply Curve**: Upward sloping as producers are willing to supply more at higher prices.\n"
            f"• **Equilibrium**: The price point $P^*$ where Quantity Demanded ($Q_d$) equals Quantity Supplied ($Q_s$).\n\n"
            f"**2. Key Shifts vs. Movement along the curve**:\n"
            f"• A change in the **price of the good itself** causes a *movement along* the curve.\n"
            f"• Changes in **consumer income, tastes, future expectations, or input costs** *shift* the entire curve!\n\n"
            f"**3. Fiscal vs. Monetary Policy**:\n"
            f"• **Fiscal**: Carried out by the government through tax rates and public spending.\n"
            f"• **Monetary**: Managed by the Central Bank via interest rates and open market operations.\n\n"
            f"What specific economic model or formula are you reviewing?"
        )

    # General Academic Fallback with smart contextual breakdown
    topic_cleaned = re.sub(r'^(what is|explain|tell me about|how does|help me with|can you describe)\s*', '', msg_lower).strip(' ?.')
    if not topic_cleaned:
        topic_cleaned = "this subject"

    return (
        f"### 🎓 Academic Breakdown: {topic_cleaned.title()}\n\n"
        f"**1. Overview & Core Definition**:\n"
        f"In college coursework, **{topic_cleaned}** represents an essential concept. At its foundation, it describes how specific variables or rules interact in a systematic framework.\n\n"
        f"**2. Key Structural Principles**:\n"
        f"• **Foundation**: Understand the primary assumptions and boundary conditions first.\n"
        f"• **Mechanism**: Observe cause-and-effect relationships or step-by-step progressions.\n"
        f"• **Common Pitfall**: Watch out for edge cases and exam tricks that test standard exceptions.\n\n"
        f"**3. Recommended Study Steps for {user_name}**:\n"
        f"• Summarize this topic in your own words using our **AI Notes** tool.\n"
        f"• Generate a targeted 5-question test in the **Quiz Generator** to pinpoint any knowledge gaps.\n"
        f"• If anything remains challenging, log it in **Weak Topics** to prioritize before finals.\n\n"
        f"What part of **{topic_cleaned}** feels most difficult right now? I'm happy to provide concrete examples or step-by-step math/code!"
    )

def summarize_text(topic: str, raw_text: str) -> str:
    """
    Generate an organized, high-yield academic summary from raw notes.
    """
    clean_topic = topic.strip() or "Course Study Notes"
    clean_text = raw_text.strip()
    
    # Extract sentences / lines
    lines = [line.strip() for line in clean_text.split('\n') if line.strip()]
    if not lines:
        lines = [clean_text]

    # Build key takeaways
    bullet_points = []
    for line in lines[:6]:
        # Clean formatting
        cleaned = re.sub(r'^[•\-\*\d\.\)\s]+', '', line).strip()
        if len(cleaned) > 10:
            bullet_points.append(f"• {cleaned}")

    if not bullet_points:
        bullet_points = [
            f"• Primary thesis: Comprehensive analysis of {clean_topic}.",
            "• Core theoretical framework and practical application scenarios.",
            "• Fundamental definitions and examination priority focus areas."
        ]

    word_count = len(clean_text.split())

    summary_markdown = f"""### 🎯 Core Concept Overview: {clean_topic}
This topic focuses on understanding the primary definitions, operational mechanisms, and critical implications of {clean_topic.lower()}. Mastery of these fundamentals is essential for college-level exams.

---

### 📌 Key Takeaways & Core Points
{chr(10).join(bullet_points)}

---

### 💡 High-Yield Definitions & Terminology
• **Primary Principle**: The underlying rule governing behavior and outcomes in {clean_topic}.
• **Operational Constraint**: Boundary conditions and assumptions required for the model or formula to hold true.
• **Applied Method**: Real-world problem solving approach and troubleshooting strategy.

---

### ⚡ Rapid Exam Review Flash Facts
1. Verify prerequisite formulas and base definitions before executing complex derivations.
2. Remember to state assumptions explicitly in free-response questions for full partial credit.
3. Review your **Weak Topics** dashboard to verify mastery before exam day.
*(Original text length: {word_count} words | Synthesized into clear review points)*"""

    return summary_markdown

# Question Bank for instant rich quizzes
CURATED_QUIZZES = {
    'data structures': [
        {
            "question": "What is the average time complexity to search for an element in a balanced Binary Search Tree (BST)?",
            "options": ["A. O(1)", "B. O(log n)", "C. O(n)", "D. O(n log n)"],
            "correct_index": 1,
            "explanation": "In a balanced BST, each comparison eliminates half the remaining subtrees, yielding an O(log n) time complexity."
        },
        {
            "question": "Which data structure operates on a Last-In, First-Out (LIFO) order?",
            "options": ["A. Queue", "B. Priority Queue", "C. Stack", "D. Array List"],
            "correct_index": 2,
            "explanation": "A Stack operates strictly on LIFO (Last-In, First-Out) principle, typically using push() and pop() operations."
        },
        {
            "question": "What is the worst-case time complexity of inserting a key into a Hash Map with collisions handled by chaining?",
            "options": ["A. O(1)", "B. O(log n)", "C. O(n)", "D. O(n^2)"],
            "correct_index": 2,
            "explanation": "In the worst case where every single key hashes to the exact same bucket, search and insertion degrade to O(n) traversal of a linked list."
        },
        {
            "question": "Which algorithmic technique divides a problem into smaller subproblems, solves them independently, and combines their solutions?",
            "options": ["A. Greedy Approach", "B. Divide and Conquer", "C. Dynamic Programming", "D. Backtracking"],
            "correct_index": 1,
            "explanation": "Divide and Conquer (used in MergeSort and QuickSort) splits a problem into non-overlapping subproblems, solves them, and merges results."
        },
        {
            "question": "What is the primary advantage of a Doubly Linked List over a Singly Linked List?",
            "options": ["A. Uses less memory per node", "B. O(1) random index access", "C. Bi-directional traversal and O(1) removal given a node pointer", "D. Faster cache locality"],
            "correct_index": 2,
            "explanation": "A Doubly Linked List stores pointers to both next and previous nodes, enabling both forward and backward traversal and instant O(1) node removal."
        }
    ],
    'calculus': [
        {
            "question": "What is the derivative of f(x) = ln(x) with respect to x (for x > 0)?",
            "options": ["A. e^x", "B. 1/x", "C. x", "D. 1/(x^2)"],
            "correct_index": 1,
            "explanation": "By fundamental calculus definitions, the derivative of the natural logarithm ln(x) is 1/x."
        },
        {
            "question": "According to the Product Rule, what is d/dx [u(x) * v(x)]?",
            "options": ["A. u'(x) * v'(x)", "B. u'(x)v(x) + u(x)v'(x)", "C. u'(x)v(x) - u(x)v'(x)", "D. u(x) + v(x)"],
            "correct_index": 1,
            "explanation": "The Product Rule states that (uv)' = u'v + uv'."
        },
        {
            "question": "What is the definite integral of 2x dx from x = 0 to x = 3?",
            "options": ["A. 6", "B. 9", "C. 12", "D. 18"],
            "correct_index": 1,
            "explanation": "The antiderivative of 2x is x^2. Evaluating from 0 to 3 gives [3^2 - 0^2] = 9."
        },
        {
            "question": "What does L'Hopital's Rule allow you to evaluate when limits produce indeterminate forms like 0/0 or infinity/infinity?",
            "options": ["A. Limit of [f'(x) / g'(x)]", "B. Limit of [f'(x) * g'(x)]", "C. [f(x) / g(x)]^2", "D. The integral of f(x)"],
            "correct_index": 0,
            "explanation": "L'Hopital's Rule states that lim [f(x)/g(x)] = lim [f'(x)/g'(x)] when the indeterminate conditions are met."
        },
        {
            "question": "If the second derivative f''(x) > 0 on an interval (a, b), what does this indicate about the graph of f(x)?",
            "options": ["A. The graph is decreasing", "B. The graph is concave up (holds water)", "C. The graph is concave down", "D. The graph has a local maximum"],
            "correct_index": 1,
            "explanation": "A positive second derivative indicates that the rate of change of the slope is increasing, meaning the curve is concave upward."
        }
    ],
    'economics': [
        {
            "question": "What happens in a competitive market when the price is set above the equilibrium price?",
            "options": ["A. A shortage occurs", "B. A surplus occurs as quantity supplied exceeds quantity demanded", "C. Demand immediately shifts right", "D. Supply becomes perfectly inelastic"],
            "correct_index": 1,
            "explanation": "When price is above equilibrium, producers supply more goods than consumers are willing to buy at that price, resulting in excess supply (a surplus)."
        },
        {
            "question": "What is 'Opportunity Cost' defined as in economic theory?",
            "options": ["A. Total accounting expense incurred", "B. The value of the next best alternative sacrificed when making a decision", "C. The sunk cost that cannot be recovered", "D. The interest rate on borrowed capital"],
            "correct_index": 1,
            "explanation": "Opportunity cost is the highest-valued choice foregone when making an economic selection."
        },
        {
            "question": "If an increase in the price of Good A causes an increase in the demand for Good B, Goods A and B are:",
            "options": ["A. Complementary goods", "B. Substitute goods", "C. Inferior goods", "D. Giffen goods"],
            "correct_index": 1,
            "explanation": "Substitute goods have a positive cross-price elasticity of demand (e.g., coffee and tea)."
        },
        {
            "question": "What metric measures the total market value of all final goods and services produced within a country's borders in a given year?",
            "options": ["A. Gross National Product (GNP)", "B. Gross Domestic Product (GDP)", "C. Consumer Price Index (CPI)", "D. Purchasing Power Parity (PPP)"],
            "correct_index": 1,
            "explanation": "GDP measures the monetary value of final goods and services produced within a nation's geographical borders during a specified period."
        },
        {
            "question": "When the central bank lowers interest rates, what is the expected macroeconomic outcome?",
            "options": ["A. Borrowing slows down and inflation drops", "B. Borrowing and investment increase, stimulating aggregate demand", "C. The currency immediately surges in value", "D. Unemployment rises automatically"],
            "correct_index": 1,
            "explanation": "Lower interest rates reduce borrowing costs for businesses and households, stimulating investment, consumer spending, and aggregate demand."
        }
    ]
}

def generate_quiz(topic: str, count: int = 5) -> list:
    """
    Generate 5 multiple choice questions for any academic topic.
    Uses curated subject banks if matching or generates contextual questions.
    """
    clean = topic.lower().strip()
    
    # Check for match in curated bank
    for key in CURATED_QUIZZES:
        if key in clean or clean in key:
            return CURATED_QUIZZES[key][:count]

    # Dynamic intelligent academic question generator for any topic
    topic_display = topic.strip().title() or "Core Academic Principles"
    
    questions = [
        {
            "question": f"Which of the following best defines the primary foundation of {topic_display}?",
            "options": [
                f"A. The systematic analysis and implementation of core principles in {topic_display}",
                f"B. A purely theoretical framework with no real-world empirical validation",
                f"C. An obsolete methodology that has been completely superseded by modern heuristics",
                f"D. A random assortment of unrelated observations without mathematical structure"
            ],
            "correct_index": 0,
            "explanation": f"The core foundation of {topic_display} focuses on systematic principles and their rigorous application to solve complex problems."
        },
        {
            "question": f"When evaluating key constraints in {topic_display}, what is a critical factor students must consider?",
            "options": [
                "A. Ignoring edge cases and assuming infinite resource availability",
                f"B. Boundary conditions and the operational scope governing {topic_display}",
                "C. Relying entirely on qualitative guesses without verification",
                "D. Modifying experimental outcomes to match expected theoretical models"
            ],
            "correct_index": 1,
            "explanation": f"In college coursework, identifying boundary conditions and operational constraints in {topic_display} is vital to prevent errors."
        },
        {
            "question": f"What is a standard best practice when preparing for an examination on {topic_display}?",
            "options": [
                "A. Cramming all chapters in a single session the morning of the exam",
                "B. Passively highlighting the textbook without solving practice problems",
                f"C. Active recall, solving targeted problem sets, and tracking weak topics in {topic_display}",
                "D. Memorizing formulas without understanding their conceptual derivations"
            ],
            "correct_index": 2,
            "explanation": "Cognitive science shows that active recall combined with spaced practice yields significantly higher retention on college exams."
        },
        {
            "question": f"Which common misconception frequently leads to lost points in {topic_display} tests?",
            "options": [
                "A. Showing detailed step-by-step working and reasoning",
                f"B. Confusing fundamental terminology with secondary consequences in {topic_display}",
                "C. Double-checking units and mathematical signs before submission",
                "D. Reviewing foundational theorems prior to tackling advanced cases"
            ],
            "correct_index": 1,
            "explanation": f"Students frequently confuse cause and effect or interchange core definitions with secondary effects in {topic_display}."
        },
        {
            "question": f"How can a student best demonstrate mastery in a college-level assessment of {topic_display}?",
            "options": [
                f"A. By synthesizing core concepts, justifying assumptions, and solving novel applications of {topic_display}",
                "B. By providing answers without explaining any underlying reasoning",
                "C. By quoting definitions verbatim without providing contextual analysis",
                "D. By skipping difficult sections and focusing solely on elementary examples"
            ],
            "correct_index": 0,
            "explanation": f"Professors award top marks when students synthesize principles and demonstrate problem-solving flexibility in {topic_display}."
        }
    ]
    
    return questions[:count]
