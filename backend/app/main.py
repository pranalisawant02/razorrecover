from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.schemas.transaction import TransactionCreate
from app.services.risk_engine import analyze_transaction
from app.services.recovery_engine import decide_recovery_action

import sqlite3
import json

from datetime import datetime


# ==================================================
# FASTAPI APP
# ==================================================

app = FastAPI(
    title="RazorRecover",
    description="AI-powered Revenue Recovery Agent"
)


# ==================================================
# CORS
# ==================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================================================
# DATABASE CONFIGURATION
# ==================================================

DATABASE = "razorrecover.db"

MAX_RETRIES = 3


def get_db_connection():

    conn = sqlite3.connect(DATABASE)

    conn.row_factory = sqlite3.Row

    return conn


# ==================================================
# CREATE DATABASE TABLES
# ==================================================

def initialize_database():

    conn = get_db_connection()

    cursor = conn.cursor()

    cursor.execute("""

        CREATE TABLE IF NOT EXISTS transactions (

            transaction_id TEXT PRIMARY KEY,

            customer_id TEXT NOT NULL,

            amount REAL NOT NULL,

            currency TEXT,

            status TEXT NOT NULL,

            failure_reason TEXT,

            risk_analysis TEXT,

            retry_count INTEGER DEFAULT 0,

            max_retries INTEGER DEFAULT 3,

            recovery_status TEXT DEFAULT 'pending',

            stopping_reason TEXT

        )

    """)


    cursor.execute("""

        CREATE TABLE IF NOT EXISTS audit_trail (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            transaction_id TEXT NOT NULL,

            timestamp TEXT NOT NULL,

            event TEXT NOT NULL,

            details TEXT NOT NULL,

            FOREIGN KEY(transaction_id)
            REFERENCES transactions(transaction_id)

        )

    """)


    conn.commit()

    conn.close()


initialize_database()


# ==================================================
# AUDIT TRAIL HELPERS
# ==================================================

def add_audit_event(transaction_id, event, details):

    conn = get_db_connection()

    cursor = conn.cursor()

    timestamp = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    cursor.execute("""

        INSERT INTO audit_trail
        (transaction_id, timestamp, event, details)

        VALUES (?, ?, ?, ?)

    """, (
        transaction_id,
        timestamp,
        event,
        details
    ))

    conn.commit()

    conn.close()


# ==================================================
# GET TRANSACTION
# ==================================================

def get_transaction_by_id(transaction_id):

    conn = get_db_connection()

    cursor = conn.cursor()

    cursor.execute("""

        SELECT *

        FROM transactions

        WHERE transaction_id = ?

    """, (transaction_id,))

    row = cursor.fetchone()

    conn.close()

    if row is None:
        return None

    transaction = dict(row)

    if transaction["risk_analysis"]:

        try:

            transaction["risk_analysis"] = json.loads(
                transaction["risk_analysis"]
            )

        except:

            transaction["risk_analysis"] = {}

    else:

        transaction["risk_analysis"] = {}

    return transaction


# ==================================================
# GET AUDIT EVENTS
# ==================================================

def get_audit_events(transaction_id):

    conn = get_db_connection()

    cursor = conn.cursor()

    cursor.execute("""

        SELECT timestamp, event, details

        FROM audit_trail

        WHERE transaction_id = ?

        ORDER BY id ASC

    """, (transaction_id,))

    rows = cursor.fetchall()

    conn.close()

    return [

        {
            "timestamp": row["timestamp"],
            "event": row["event"],
            "details": row["details"]
        }

        for row in rows

    ]


# ==================================================
# HOME
# ==================================================

@app.get("/")
def home():

    return {

        "message": "RazorRecover API is running",

        "project": "AI Revenue Recovery Agent",

        "database": "SQLite connected"

    }


# ==================================================
# HEALTH CHECK
# ==================================================

@app.get("/health")
def health():

    return {

        "status": "healthy",

        "database": "SQLite"

    }


# ==================================================
# CREATE TRANSACTION
# ==================================================

@app.post("/transactions")
def create_transaction(transaction: TransactionCreate):

    transaction_data = transaction.model_dump()

    existing = get_transaction_by_id(
        transaction_data["transaction_id"]
    )

    if existing:

        raise HTTPException(
            status_code=400,
            detail="Transaction ID already exists"
        )


    # ----------------------------------------------
    # RISK ANALYSIS
    # ----------------------------------------------

    risk_analysis = analyze_transaction(transaction)


    # ----------------------------------------------
    # STORE TRANSACTION
    # ----------------------------------------------

    conn = get_db_connection()

    cursor = conn.cursor()

    cursor.execute("""

        INSERT INTO transactions (

            transaction_id,
            customer_id,
            amount,
            currency,
            status,
            failure_reason,
            risk_analysis,
            retry_count,
            max_retries,
            recovery_status,
            stopping_reason

        )

        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)

    """, (

        transaction_data["transaction_id"],

        transaction_data["customer_id"],

        transaction_data["amount"],

        transaction_data.get("currency", "INR"),

        transaction_data["status"],

        transaction_data.get("failure_reason"),

        json.dumps(risk_analysis),

        0,

        MAX_RETRIES,

        "pending",

        None

    ))

    conn.commit()

    conn.close()


    transaction_id = transaction_data["transaction_id"]


    # ----------------------------------------------
    # AUDIT EVENTS
    # ----------------------------------------------

    add_audit_event(

        transaction_id,

        "transaction_received",

        "Transaction stored permanently in SQLite database"

    )


    if transaction_data["status"].lower() == "failed":

        add_audit_event(

            transaction_id,

            "failure_detected",

            f"Failure reason: {transaction_data.get('failure_reason')}"

        )


        add_audit_event(

            transaction_id,

            "revenue_risk_detected",

            f"₹{risk_analysis.get('amount_at_risk', transaction_data['amount'])} marked as revenue at risk"

        )


    stored_transaction = get_transaction_by_id(
        transaction_id
    )

    stored_transaction["audit_trail"] = get_audit_events(
        transaction_id
    )


    return {

        "message": "Transaction stored and analyzed successfully",

        "transaction": stored_transaction

    }


# ==================================================
# GET ALL TRANSACTIONS
# ==================================================

@app.get("/transactions")
def get_transactions():

    conn = get_db_connection()

    cursor = conn.cursor()

    cursor.execute("""

        SELECT *

        FROM transactions

        ORDER BY rowid DESC

    """)

    rows = cursor.fetchall()

    conn.close()


    transactions = []


    for row in rows:

        transaction = dict(row)

        if transaction["risk_analysis"]:

            try:

                transaction["risk_analysis"] = json.loads(
                    transaction["risk_analysis"]
                )

            except:

                transaction["risk_analysis"] = {}

        else:

            transaction["risk_analysis"] = {}


        transactions.append(transaction)


    return {

        "total_transactions": len(transactions),

        "transactions": transactions

    }


# ==================================================
# GET FAILED TRANSACTIONS
# ==================================================

@app.get("/transactions/failed")
def get_failed_transactions():

    conn = get_db_connection()

    cursor = conn.cursor()

    cursor.execute("""

        SELECT *

        FROM transactions

        WHERE LOWER(status) = 'failed'

    """)

    rows = cursor.fetchall()

    conn.close()


    transactions = []


    for row in rows:

        transaction = dict(row)

        if transaction["risk_analysis"]:

            try:

                transaction["risk_analysis"] = json.loads(
                    transaction["risk_analysis"]
                )

            except:

                transaction["risk_analysis"] = {}

        else:

            transaction["risk_analysis"] = {}


        transaction["audit_trail"] = get_audit_events(
            transaction["transaction_id"]
        )

        transactions.append(transaction)


    return {

        "total_failed": len(transactions),

        "transactions": transactions

    }


# ==================================================
# AI RECOVERY DECISION ENGINE
# ==================================================

def generate_ai_decision(transaction):

    transaction_id = transaction["transaction_id"]

    reason = (
        transaction.get("failure_reason")
        or "unknown"
    ).lower()

    amount = float(
        transaction.get("amount", 0)
    )

    retry_count = int(
        transaction.get("retry_count", 0)
    )

    max_retries = int(
        transaction.get("max_retries", MAX_RETRIES)
    )


    # ----------------------------------------------
    # STOPPING RULE FIRST
    # ----------------------------------------------

    if retry_count >= max_retries:

        return {

            "transaction_id": transaction_id,

            "amount_at_risk": amount,

            "recovery_probability": 0,

            "priority": "stopped",

            "priority_score": 0,

            "risk_level": "recovery_limit_reached",

            "recommended_action": "stop_recovery",

            "decision_reason":
                f"Automatic recovery stopped because the maximum retry limit "
                f"of {max_retries} attempts has been reached."

        }


    # ----------------------------------------------
    # BASE RECOVERY PROBABILITY
    # ----------------------------------------------

    probability_map = {

        "network_error": 90,

        "payment_timeout": 82,

        "temporary_gateway_error": 85,

        "bank_server_error": 78,

        "insufficient_funds": 35,

        "card_declined": 30,

        "expired_card": 15,

        "fraud_suspected": 5

    }


    recovery_probability = probability_map.get(
        reason,
        25
    )


    # ----------------------------------------------
    # RETRY PENALTY
    # ----------------------------------------------

    retry_penalty = retry_count * 15

    recovery_probability -= retry_penalty


    if recovery_probability < 0:

        recovery_probability = 0


    # ----------------------------------------------
    # AMOUNT PRIORITY SCORE
    # ----------------------------------------------

    if amount >= 15000:

        amount_score = 40

    elif amount >= 10000:

        amount_score = 35

    elif amount >= 5000:

        amount_score = 25

    else:

        amount_score = 15


    # ----------------------------------------------
    # RECOVERY SCORE
    # ----------------------------------------------

    probability_score = recovery_probability * 0.5

    retry_score = (
        (max_retries - retry_count)
        / max_retries
    ) * 10


    priority_score = round(

        amount_score
        + probability_score
        + retry_score,

        1

    )


    if priority_score > 100:

        priority_score = 100


    # ----------------------------------------------
    # PRIORITY LEVEL
    # ----------------------------------------------

    if priority_score >= 75:

        priority = "high"

    elif priority_score >= 50:

        priority = "medium"

    else:

        priority = "low"


    # ----------------------------------------------
    # AI RECOMMENDED ACTION
    # ----------------------------------------------

    automatic_retry_reasons = [

        "network_error",

        "payment_timeout",

        "temporary_gateway_error",

        "bank_server_error"

    ]


    intervention_reasons = [

        "insufficient_funds",

        "card_declined",

        "expired_card"

    ]


    if reason in automatic_retry_reasons:

        if recovery_probability >= 50:

            recommended_action = "automatic_retry"

            decision_reason = (

                f"The failure appears temporary and has an estimated "
                f"{recovery_probability}% recovery probability. "
                f"The transaction is still within its retry limit, so a "
                f"bounded automatic retry is recommended."

            )

        else:

            recommended_action = "manual_review"

            decision_reason = (

                "Recovery probability has decreased after previous retry "
                "attempts. Manual review is recommended before continuing."

            )


    elif reason in intervention_reasons:

        recommended_action = "customer_intervention"

        decision_reason = (

            f"The failure reason '{reason}' is unlikely to be solved by "
            f"repeating the same payment attempt. Customer intervention or "
            f"an alternative payment method is recommended."

        )


    elif reason == "fraud_suspected":

        recommended_action = "stop_and_review"

        decision_reason = (

            "Automatic recovery is blocked because the transaction requires "
            "a security or compliance review."

        )


    else:

        recommended_action = "manual_review"

        decision_reason = (

            "The failure reason does not have enough confidence for automatic "
            "recovery. Manual investigation is recommended."

        )


    # ----------------------------------------------
    # RECOVERY OPPORTUNITY
    # ----------------------------------------------

    if recovery_probability >= 75:

        risk_level = "high_recovery_opportunity"

    elif recovery_probability >= 40:

        risk_level = "medium_recovery_opportunity"

    else:

        risk_level = "low_recovery_opportunity"


    return {

        "transaction_id": transaction_id,

        "amount_at_risk": amount,

        "recovery_probability": round(
            recovery_probability,
            1
        ),

        "priority": priority,

        "priority_score": priority_score,

        "risk_level": risk_level,

        "recommended_action": recommended_action,

        "decision_reason": decision_reason,

        "retry_count": retry_count,

        "max_retries": max_retries

    }


# ==================================================
# INDIVIDUAL AI DECISION ENDPOINT
# ==================================================

@app.get("/transactions/{transaction_id}/ai-decision")
def ai_recovery_decision(transaction_id: str):

    transaction = get_transaction_by_id(
        transaction_id
    )


    if transaction is None:

        raise HTTPException(

            status_code=404,

            detail="Transaction not found"

        )


    # ----------------------------------------------
    # NO ACTION FOR SUCCESS / RECOVERED
    # ----------------------------------------------

    if transaction["status"].lower() != "failed":

        return {

            "transaction_id": transaction_id,

            "message":
                "Transaction does not currently require recovery",

            "recovery_probability": 0,

            "priority": "none",

            "priority_score": 0,

            "risk_level": "no_recovery_required",

            "recommended_action": "no_action",

            "decision_reason":
                "This transaction is not currently in a failed state."

        }


    decision = generate_ai_decision(
        transaction
    )


    # ----------------------------------------------
    # AUDIT TRAIL
    # ----------------------------------------------

    add_audit_event(

        transaction_id,

        "ai_decision",

        f"AI selected {decision['recommended_action']} "
        f"with {decision['recovery_probability']}% recovery probability "
        f"and priority score {decision['priority_score']}"

    )


    return decision


# ==================================================
# INDIVIDUAL RECOVERY
# ==================================================

@app.post("/transactions/{transaction_id}/recover")
def recover_transaction(transaction_id: str):

    transaction = get_transaction_by_id(
        transaction_id
    )


    if transaction is None:

        raise HTTPException(
            status_code=404,
            detail="Transaction not found"
        )


    if transaction["status"].lower() != "failed":

        raise HTTPException(
            status_code=400,
            detail="Only failed transactions can enter recovery"
        )


    decision = generate_ai_decision(
        transaction
    )


    # ----------------------------------------------
    # STOPPING RULE
    # ----------------------------------------------

    if decision["recommended_action"] in [

        "stop_recovery",

        "stop_and_review"

    ]:

        conn = get_db_connection()

        cursor = conn.cursor()

        cursor.execute("""

            UPDATE transactions

            SET recovery_status = ?,
                stopping_reason = ?

            WHERE transaction_id = ?

        """, (

            "stopped",

            decision["decision_reason"],

            transaction_id

        ))

        conn.commit()

        conn.close()


        add_audit_event(

            transaction_id,

            "recovery_stopped",

            decision["decision_reason"]

        )


        return {

            "message": "Recovery stopped",

            "decision": decision

        }


    # ----------------------------------------------
    # CUSTOMER INTERVENTION
    # ----------------------------------------------

    if decision["recommended_action"] != "automatic_retry":

        conn = get_db_connection()

        cursor = conn.cursor()

        cursor.execute("""

            UPDATE transactions

            SET recovery_status = ?,
                stopping_reason = ?

            WHERE transaction_id = ?

        """, (

            "manual_intervention_required",

            decision["decision_reason"],

            transaction_id

        ))

        conn.commit()

        conn.close()


        add_audit_event(

            transaction_id,

            "recovery_stopped",

            "Automatic recovery stopped. Customer or manual intervention required."

        )


        return {

            "message":
                "Automatic recovery not suitable",

            "decision": decision

        }


    # ----------------------------------------------
    # AUTOMATIC RETRY
    # ----------------------------------------------

    new_retry_count = (
        transaction["retry_count"] + 1
    )


    conn = get_db_connection()

    cursor = conn.cursor()


    cursor.execute("""

        UPDATE transactions

        SET retry_count = ?,
            status = ?,
            recovery_status = ?,
            stopping_reason = ?

        WHERE transaction_id = ?

    """, (

        new_retry_count,

        "recovered",

        "success",

        "Transaction recovered successfully",

        transaction_id

    ))


    conn.commit()

    conn.close()


    add_audit_event(

        transaction_id,

        "recovery_attempt",

        f"Bounded automatic retry attempt {new_retry_count} executed"

    )


    add_audit_event(

        transaction_id,

        "recovery_success",

        f"₹{transaction['amount']} recovered successfully"

    )


    return {

        "message":
            "Recovery attempt successful",

        "decision": decision,

        "transaction":
            get_transaction_by_id(transaction_id)

    }


# ==================================================
# BATCH RECOVERY
# ==================================================

@app.post("/recovery/batch")
def batch_recovery():

    conn = get_db_connection()

    cursor = conn.cursor()

    cursor.execute("""

        SELECT *

        FROM transactions

        WHERE LOWER(status) = 'failed'

    """)

    rows = cursor.fetchall()

    conn.close()


    processed = 0

    recovered_count = 0

    recovered_amount = 0

    stopped_count = 0

    results = []


    for row in rows:

        transaction = dict(row)

        transaction_id = transaction["transaction_id"]

        processed += 1


        decision = generate_ai_decision(
            transaction
        )


        add_audit_event(

            transaction_id,

            "agent_analysis",

            f"AI selected {decision['recommended_action']} "
            f"with {decision['recovery_probability']}% recovery probability"

        )


        # ------------------------------------------
        # AUTOMATIC RETRY
        # ------------------------------------------

        if decision["recommended_action"] == "automatic_retry":

            new_retry_count = (
                transaction["retry_count"] + 1
            )


            conn = get_db_connection()

            cursor = conn.cursor()

            cursor.execute("""

                UPDATE transactions

                SET retry_count = ?,
                    status = ?,
                    recovery_status = ?,
                    stopping_reason = ?

                WHERE transaction_id = ?

            """, (

                new_retry_count,

                "recovered",

                "success",

                "Transaction recovered successfully",

                transaction_id

            ))

            conn.commit()

            conn.close()


            add_audit_event(

                transaction_id,

                "recovery_attempt",

                f"Automatic retry attempt {new_retry_count}"

            )


            add_audit_event(

                transaction_id,

                "recovery_success",

                f"₹{transaction['amount']} recovered"

            )


            recovered_count += 1

            recovered_amount += transaction["amount"]


            results.append({

                "transaction_id": transaction_id,

                "action": "automatic_retry",

                "result": "recovered",

                "amount_recovered":
                    transaction["amount"]

            })


        # ------------------------------------------
        # STOP / MANUAL INTERVENTION
        # ------------------------------------------

        else:

            conn = get_db_connection()

            cursor = conn.cursor()

            cursor.execute("""

                UPDATE transactions

                SET recovery_status = ?,
                    stopping_reason = ?

                WHERE transaction_id = ?

            """, (

                "stopped",

                decision["decision_reason"],

                transaction_id

            ))

            conn.commit()

            conn.close()


            add_audit_event(

                transaction_id,

                "recovery_stopped",

                decision["decision_reason"]

            )


            stopped_count += 1


            results.append({

                "transaction_id": transaction_id,

                "action":
                    decision["recommended_action"],

                "result": "not_recovered",

                "amount_recovered": 0

            })


    return {

        "message": "Batch recovery completed",

        "failed_transactions_processed": processed,

        "ai_decisions_made": processed,

        "transactions_recovered": recovered_count,

        "transactions_stopped": stopped_count,

        "total_amount_recovered": recovered_amount,

        "results": results

    }


# ==================================================
# GET AUDIT TRAIL
# ==================================================

@app.get("/transactions/{transaction_id}/audit")
def get_audit_trail(transaction_id: str):

    transaction = get_transaction_by_id(
        transaction_id
    )


    if transaction is None:

        raise HTTPException(
            status_code=404,
            detail="Transaction not found"
        )


    return {

        "transaction_id": transaction_id,

        "audit_trail":
            get_audit_events(transaction_id)

    }


# ==================================================
# AI INSIGHTS
# ==================================================

@app.get("/insights")
def get_insights():

    conn = get_db_connection()

    cursor = conn.cursor()

    cursor.execute("""

        SELECT *

        FROM transactions

        WHERE LOWER(status) = 'failed'

    """)

    rows = cursor.fetchall()

    conn.close()


    failed_transactions = [

        dict(row)

        for row in rows

    ]


    revenue_at_risk = sum(

        transaction["amount"]

        for transaction in failed_transactions

    )


    recoverable_transactions = []


    for transaction in failed_transactions:

        decision = generate_ai_decision(
            transaction
        )


        if decision["recommended_action"] == "automatic_retry":

            recoverable_transactions.append(
                transaction
            )


    failure_reasons = {}


    for transaction in failed_transactions:

        reason = (

            transaction.get(
                "failure_reason"
            )

            or "unknown"

        )


        failure_reasons[reason] = (

            failure_reasons.get(reason, 0) + 1

        )


    most_common_failure = "No failures detected"


    if failure_reasons:

        most_common_failure = max(

            failure_reasons,

            key=failure_reasons.get

        )


    if len(recoverable_transactions) > 0:

        recommended_strategy = (

            "Run bounded automatic recovery for high-confidence temporary failures"

        )

    elif len(failed_transactions) > 0:

        recommended_strategy = (

            "Automatic recovery is not recommended. Use customer intervention or manual review."

        )

    else:

        recommended_strategy = (

            "No recovery action is currently required"

        )


    return {

        "failed_transactions":
            len(failed_transactions),

        "revenue_at_risk":
            revenue_at_risk,

        "recoverable_transactions":
            len(recoverable_transactions),

        "most_common_failure":
            most_common_failure,

        "recommended_strategy":
            recommended_strategy

    }


# ==================================================
# DASHBOARD
# ==================================================

@app.get("/dashboard")
def dashboard():

    conn = get_db_connection()

    cursor = conn.cursor()


    cursor.execute(
        "SELECT COUNT(*) FROM transactions"
    )

    total = cursor.fetchone()[0]


    cursor.execute("""

        SELECT COUNT(*)

        FROM transactions

        WHERE LOWER(status) = 'success'

    """)

    successful = cursor.fetchone()[0]


    cursor.execute("""

        SELECT COUNT(*)

        FROM transactions

        WHERE LOWER(status) = 'failed'

    """)

    failed = cursor.fetchone()[0]


    cursor.execute("""

        SELECT COUNT(*)

        FROM transactions

        WHERE LOWER(status) = 'recovered'

    """)

    recovered = cursor.fetchone()[0]


    cursor.execute("""

        SELECT COALESCE(SUM(amount), 0)

        FROM transactions

        WHERE LOWER(status) = 'recovered'

    """)

    total_amount_recovered = cursor.fetchone()[0]


    cursor.execute("""

        SELECT COUNT(*)

        FROM transactions

        WHERE recovery_status = 'stopped'

        OR recovery_status =
        'manual_intervention_required'

    """)

    stopped = cursor.fetchone()[0]


    conn.close()


    recovery_candidates = recovered + stopped


    recovery_rate = 0


    if recovery_candidates > 0:

        recovery_rate = round(

            (
                recovered
                / recovery_candidates
            ) * 100,

            2

        )


    return {

        "total_transactions": total,

        "successful_transactions": successful,

        "failed_transactions": failed,

        "recovered_transactions": recovered,

        "stopped_transactions": stopped,

        "total_amount_recovered":
            total_amount_recovered,

        "recovery_rate":
            f"{recovery_rate}%"

    }


# ==================================================
# CLEAR ALL TRANSACTIONS
# ==================================================

@app.delete("/transactions")
def clear_transactions():

    conn = get_db_connection()

    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM audit_trail"
    )

    cursor.execute(
        "DELETE FROM transactions"
    )

    conn.commit()

    conn.close()


    return {

        "message":
            "All transactions and audit records cleared successfully"

    }


# ==================================================
# GENERATE DEMO TRANSACTIONS
# ==================================================

@app.post("/demo/generate")
def generate_demo_transactions():

    demo_transactions = [

        {
            "transaction_id": "DEMO_1001",
            "customer_id": "CUST_001",
            "amount": 5000,
            "currency": "INR",
            "status": "failed",
            "failure_reason": "network_error"
        },

        {
            "transaction_id": "DEMO_1002",
            "customer_id": "CUST_002",
            "amount": 12000,
            "currency": "INR",
            "status": "failed",
            "failure_reason": "payment_timeout"
        },

        {
            "transaction_id": "DEMO_1003",
            "customer_id": "CUST_003",
            "amount": 7500,
            "currency": "INR",
            "status": "failed",
            "failure_reason": "insufficient_funds"
        },

        {
            "transaction_id": "DEMO_1004",
            "customer_id": "CUST_004",
            "amount": 2500,
            "currency": "INR",
            "status": "success",
            "failure_reason": None
        }

    ]


    conn = get_db_connection()

    cursor = conn.cursor()

    created = 0

    skipped = 0


    for transaction in demo_transactions:

        cursor.execute(

            """

            SELECT transaction_id

            FROM transactions

            WHERE transaction_id = ?

            """,

            (transaction["transaction_id"],)

        )


        existing = cursor.fetchone()


        if existing:

            skipped += 1

            continue


        risk_analysis = {

            "amount_at_risk":

                transaction["amount"]

                if transaction["status"] == "failed"

                else 0

        }


        cursor.execute("""

            INSERT INTO transactions (

                transaction_id,
                customer_id,
                amount,
                currency,
                status,
                failure_reason,
                risk_analysis,
                retry_count,
                max_retries,
                recovery_status,
                stopping_reason

            )

            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)

        """, (

            transaction["transaction_id"],

            transaction["customer_id"],

            transaction["amount"],

            transaction["currency"],

            transaction["status"],

            transaction["failure_reason"],

            json.dumps(risk_analysis),

            0,

            MAX_RETRIES,

            "pending",

            None

        ))


        created += 1


    conn.commit()

    conn.close()


    # ----------------------------------------------
    # CREATE AUDIT EVENTS
    # ----------------------------------------------

    for transaction in demo_transactions:

        transaction_id = transaction["transaction_id"]

        stored = get_transaction_by_id(
            transaction_id
        )


        if stored:

            audit_events = get_audit_events(
                transaction_id
            )


            if len(audit_events) == 0:

                add_audit_event(

                    transaction_id,

                    "transaction_received",

                    "Demo transaction generated for Buildathon demonstration"

                )


                if transaction["status"] == "failed":

                    add_audit_event(

                        transaction_id,

                        "failure_detected",

                        f"Failure reason: {transaction['failure_reason']}"

                    )


                    add_audit_event(

                        transaction_id,

                        "revenue_risk_detected",

                        f"₹{transaction['amount']} marked as revenue at risk"

                    )


    return {

        "message":
            "Demo transactions generated successfully",

        "transactions_created":
            created,

        "transactions_skipped":
            skipped

    }