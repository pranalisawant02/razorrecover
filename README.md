
````markdown
# 🤖 RazorRecover

## AI-Powered Revenue Recovery Agent

**RazorRecover** is an AI-powered revenue recovery agent designed to detect revenue at risk, analyze failed transactions, determine the most appropriate recovery strategy, and execute a bounded recovery workflow.

Built for **Razorpay Buildathon – Track 03: AI Revenue Recovery**.

---

# 🚨 Problem

Revenue loss rarely happens in one clean step.

A payment may fail because of:

- Network errors
- Payment timeouts
- Insufficient funds
- Other payment-related failures

Simply detecting a failed transaction is not enough.

A recovery system should be able to answer:

- Is this transaction recoverable?
- What action should be taken?
- What is the probability of recovery?
- Should the system retry automatically?
- When should recovery stop?
- How much revenue was recovered?

---

# 💡 Solution

RazorRecover acts as an intelligent revenue recovery agent that:

1. Detects failed transactions.
2. Identifies revenue at risk.
3. Analyzes the failure reason.
4. Generates an AI-based recovery decision.
5. Estimates recovery probability.
6. Prioritizes recovery opportunities.
7. Recommends the appropriate recovery action.
8. Executes bounded recovery workflows.
9. Applies retry limits and stopping rules.
10. Tracks recovered revenue across transactions.
11. Maintains a complete audit trail.

---

# 🤖 AI Recovery Decision Engine

For every failed transaction, RazorRecover analyzes:

- Failure reason
- Amount at risk
- Retry count
- Maximum retry limit

The AI Decision Engine generates:

- Recovery Probability
- Transaction Priority
- Priority Score
- Recovery Opportunity
- Recommended Recovery Action
- Decision Reasoning

### Example Decisions

| Failure Reason | Recovery Probability | Recommended Action |
|---|---:|---|
| Network Error | 90% | Automatic Retry |
| Payment Timeout | 80% | Automatic Retry |
| Insufficient Funds | 35% | Customer Intervention |
| Unknown Failure | Low | Manual Review |

This ensures the system does not blindly retry every failed transaction.

---

# 🔄 Recovery Workflow

```text
Transaction Failure
        ↓
Revenue Risk Detection
        ↓
AI Recovery Analysis
        ↓
AI Decision
        ↓
Automatic Retry / Customer Intervention / Manual Review
        ↓
Bounded Recovery Workflow
        ↓
Recovery Success OR Stopping Rule
        ↓
Complete Audit Trail
````

---

# 🛑 Bounded Recovery & Stopping Rules

RazorRecover prevents unlimited retry attempts.

Recovery stops when:

* The maximum retry limit is reached.
* Automatic recovery is not suitable.
* Customer intervention is required.
* The transaction requires manual review.

This creates a controlled and bounded recovery workflow.

---

# 📊 Batch Recovery

The Batch Recovery Agent processes multiple failed transactions and provides measurable results.

It reports:

* Failed transactions processed
* AI decisions made
* Transactions recovered
* Transactions stopped
* Total amount recovered

This directly addresses the requirement of demonstrating **measured money recovered across a batch**.

---

# 🧾 Audit Trail

Every important event is recorded for transparency and traceability.

Events include:

* Transaction Received
* Failure Detected
* Revenue Risk Detected
* AI Recovery Analysis
* AI Decision
* Recovery Attempt
* Recovery Success
* Recovery Stopped

The audit trail makes every recovery decision traceable.

---

# 🏗️ System Architecture

```text
                    ┌──────────────────────┐
                    │  Frontend Dashboard  │
                    │ HTML / CSS / JS      │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │   FastAPI Backend    │
                    └──────────┬───────────┘
                               │
          ┌────────────────────┼────────────────────┐
          ▼                    ▼                    ▼
 ┌────────────────┐   ┌─────────────────┐   ┌────────────────┐
 │ Risk Analysis  │   │ AI Decision     │   │ Recovery Engine│
 │ Engine         │   │ Engine          │   │                │
 └────────────────┘   └─────────────────┘   └────────────────┘
          │                    │                    │
          └────────────────────┼────────────────────┘
                               ▼
                    ┌──────────────────────┐
                    │     Audit Trail      │
                    │     SQLite DB        │
                    └──────────────────────┘
```

---

# 🛠️ Technology Stack

## Backend

* Python
* FastAPI
* Pydantic
* Uvicorn
* SQLite

## Frontend

* HTML
* CSS
* JavaScript

---

# 📁 Project Structure

```text
razorrecover/
│
├── backend/
│   │
│   ├── app/
│   │   ├── models/
│   │   ├── schemas/
│   │   └── services/
│   │       ├── recovery_engine.py
│   │       └── risk_engine.py
│   │
│   ├── main.py
│   └── requirements.txt
│
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── script.js
│
├── scripts/
├── .env.example
├── .gitignore
└── README.md
```

---

# 🚀 How to Run RazorRecover

## 1. Clone the Repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
```

Move into the project folder:

```bash
cd razorrecover
```

---

## 2. Run the Backend

Open a terminal and move into the backend folder:

```bash
cd backend
```

Create a Python virtual environment:

```bash
python -m venv venv
```

### Activate the Virtual Environment

### Windows PowerShell

```powershell
venv\Scripts\Activate.ps1
```

### Windows Command Prompt

```cmd
venv\Scripts\activate
```

Install the required dependencies:

```bash
pip install -r requirements.txt
```

Start the FastAPI server:

```bash
uvicorn main:app --reload
```

The backend will run at:

```text
http://127.0.0.1:8000
```

You can also access the FastAPI documentation at:

```text
http://127.0.0.1:8000/docs
```

---

## 3. Run the Frontend

Open the `frontend` folder in VS Code.

Then:

1. Right-click on `index.html`
2. Click **Open with Live Server**

The frontend will open in your browser.

The frontend communicates with the FastAPI backend using REST APIs.

---

# 🎬 Demo Workflow

To demonstrate RazorRecover:

### Step 1 — Generate Demo Data

Click:

```text
Generate Demo Data
```

This creates sample transactions including successful and failed payments.

### Step 2 — Analyze Transactions

For a failed transaction, click:

```text
🤖 AI Decision
```

The system displays:

* Recovery probability
* Priority
* Recovery opportunity
* Recommended action
* AI decision reasoning

### Step 3 — View the Audit Trail

Click:

```text
View Audit
```

to see the complete transaction event history.

### Step 4 — Run Batch Recovery

Click:

```text
Run Batch Recovery
```

The recovery agent processes failed transactions and reports:

* Transactions processed
* Transactions recovered
* Transactions stopped
* Total revenue recovered

---

# 🎯 Key Features

* ✅ Revenue-at-risk detection
* 🤖 AI recovery decision engine
* 📈 Recovery probability estimation
* 🎯 Transaction prioritization
* 🔄 Automatic retry recommendations
* 👤 Customer intervention workflow
* 🔍 Manual review recommendations
* 🛑 Bounded recovery workflow
* 🔢 Maximum retry stopping rules
* 📊 Batch recovery analytics
* 💰 Measurable revenue recovered
* 🧾 Complete audit trail
* 📱 Interactive dashboard
* ⚡ Demo transaction generation

---

# 🔮 Future Improvements

* Razorpay Test Mode integration
* Real payment retry execution
* Machine-learning-based recovery probability prediction
* Customer notification workflows
* Checkout abandonment recovery
* Failed subscription recovery
* B2B receivables recovery
* Advanced recovery analytics

---

# 🏆 Razorpay Buildathon

### Track 03 — AI Revenue Recovery

RazorRecover goes beyond simply detecting failed payments.

It demonstrates an agentic recovery workflow that can:

**Detect → Analyze → Decide → Recover → Stop → Measure → Audit**

The system focuses on measurable revenue recovery while maintaining bounded workflows, stopping rules, and transparent audit trails.

---

# 👩‍💻 Author

**Pranali Sawant**

B.Tech – Artificial Intelligence & Machine Learning

```
