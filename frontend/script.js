const API_URL = "http://127.0.0.1:8000";

/* =========================
   GLOBAL STATE
========================= */

let selectedTransactionId = null;
let aiDecisionRequestId = 0;


/* =========================
   LOAD DASHBOARD
========================= */

async function loadDashboard() {
    try {
        const response = await fetch(`${API_URL}/dashboard`, {
            cache: "no-store"
        });

        if (!response.ok) {
            throw new Error("Backend connection failed");
        }

        const data = await response.json();

        const totalTransactions =
            document.getElementById("totalTransactions");

        const failedTransactions =
            document.getElementById("failedTransactions");

        const recoveredTransactions =
            document.getElementById("recoveredTransactions");

        const amountRecovered =
            document.getElementById("amountRecovered");

        const recoveryRate =
            document.getElementById("recoveryRate");


        if (totalTransactions) {
            totalTransactions.textContent =
                data.total_transactions ?? 0;
        }

        if (failedTransactions) {
            failedTransactions.textContent =
                data.failed_transactions ?? 0;
        }

        if (recoveredTransactions) {
            recoveredTransactions.textContent =
                data.recovered_transactions ?? 0;
        }

        if (amountRecovered) {
            amountRecovered.textContent =
                "₹" + (data.total_amount_recovered ?? 0);
        }

        if (recoveryRate) {
            recoveryRate.textContent =
                data.recovery_rate ?? "0%";
        }

        updateAPIStatus(true);

    } catch (error) {

        console.error("Dashboard error:", error);
        updateAPIStatus(false);
    }
}


/* =========================
   LOAD AI INSIGHTS
========================= */

async function loadInsights() {
    try {
        const response = await fetch(`${API_URL}/insights`, {
            cache: "no-store"
        });

        if (!response.ok) {
            throw new Error("Could not load AI insights");
        }

        const data = await response.json();

        const revenueAtRisk =
            document.getElementById("revenueAtRisk");

        const recoverableTransactions =
            document.getElementById("recoverableTransactions");

        const commonFailure =
            document.getElementById("commonFailure");

        const recommendedStrategy =
            document.getElementById("recommendedStrategy");


        if (revenueAtRisk) {
            revenueAtRisk.textContent =
                "₹" + (data.revenue_at_risk ?? 0);
        }

        if (recoverableTransactions) {
            recoverableTransactions.textContent =
                data.recoverable_transactions ?? 0;
        }

        if (commonFailure) {
            commonFailure.textContent =
                formatText(
                    data.most_common_failure || "-"
                );
        }

        if (recommendedStrategy) {
            recommendedStrategy.textContent =
                data.recommended_strategy ||
                "No recommendation available";
        }

    } catch (error) {

        console.error("Insights error:", error);

        const recommendedStrategy =
            document.getElementById("recommendedStrategy");

        if (recommendedStrategy) {
            recommendedStrategy.textContent =
                "AI insights unavailable";
        }
    }
}


/* =========================
   LOAD TRANSACTIONS
========================= */

async function loadTransactions() {
    try {
        const response = await fetch(`${API_URL}/transactions`, {
            cache: "no-store"
        });

        if (!response.ok) {
            throw new Error("Could not load transactions");
        }

        const data = await response.json();

        const tableBody =
            document.getElementById("transactionsTable");

        if (!tableBody) {
            return;
        }

        tableBody.innerHTML = "";

        if (
            !data.transactions ||
            data.transactions.length === 0
        ) {

            tableBody.innerHTML = `
                <tr>
                    <td colspan="7" class="empty-state">
                        No transactions available yet.
                    </td>
                </tr>
            `;

            return;
        }


        data.transactions.forEach(transaction => {

            let statusClass = "";

            const status =
                String(transaction.status || "")
                    .toLowerCase();


            if (status === "success") {
                statusClass = "status-success";

            } else if (status === "failed") {
                statusClass = "status-failed";

            } else if (status === "recovered") {
                statusClass = "status-recovered";
            }


            const row = document.createElement("tr");


            row.innerHTML = `
                <td class="transaction-id">
                    ${transaction.transaction_id}
                </td>

                <td>
                    ${transaction.customer_id}
                </td>

                <td class="amount">
                    ₹${transaction.amount}
                </td>

                <td>
                    ${formatText(
                        transaction.failure_reason || "-"
                    )}
                </td>

                <td>
                    <span class="status-badge ${statusClass}">
                        ${formatText(transaction.status)}
                    </span>
                </td>

                <td>
                    ${transaction.retry_count ?? 0}
                    /
                    ${transaction.max_retries ?? 3}
                </td>

                <td class="action-buttons">

                    <button
                        type="button"
                        class="audit-btn">
                        View Audit
                    </button>

                    <button
                        type="button"
                        class="ai-action-btn">
                        🤖 AI Decision
                    </button>

                </td>
            `;


            const auditButton =
                row.querySelector(".audit-btn");

            const aiButton =
                row.querySelector(".ai-action-btn");


            if (auditButton) {

                auditButton.addEventListener(
                    "click",
                    function (event) {

                        event.preventDefault();
                        event.stopPropagation();

                        viewAuditTrail(
                            transaction.transaction_id
                        );
                    }
                );
            }


            if (aiButton) {

                aiButton.addEventListener(
                    "click",
                    function (event) {

                        event.preventDefault();
                        event.stopPropagation();

                        showAIDecision(
                            transaction.transaction_id
                        );
                    }
                );
            }


            tableBody.appendChild(row);

        });

    } catch (error) {

        console.error(
            "Transactions error:",
            error
        );
    }
}


/* =========================
   RUN BATCH RECOVERY
========================= */

async function runBatchRecovery() {

    const resultMessage =
        document.getElementById("resultMessage");

    try {

        if (resultMessage) {

            resultMessage.innerHTML =
                "🤖 Running AI batch recovery...";

            resultMessage.classList.add("show");
        }


        const response = await fetch(
            `${API_URL}/recovery/batch`,
            {
                method: "POST",
                cache: "no-store"
            }
        );


        if (!response.ok) {
            throw new Error("Batch recovery failed");
        }


        const data = await response.json();


        if (resultMessage) {

            resultMessage.innerHTML = `
                <strong>✅ Batch Recovery Completed</strong>

                <br><br>

                Processed:
                <strong>
                    ${data.failed_transactions_processed ?? 0}
                </strong>

                &nbsp; | &nbsp;

                Recovered:
                <strong>
                    ${data.transactions_recovered ?? 0}
                </strong>

                &nbsp; | &nbsp;

                Stopped:
                <strong>
                    ${data.transactions_stopped ?? 0}
                </strong>

                <br><br>

                Total Revenue Recovered:
                <strong>
                    ₹${data.total_amount_recovered ?? 0}
                </strong>
            `;
        }


        await refreshDashboard();

    } catch (error) {

        console.error(
            "Batch recovery error:",
            error
        );

        if (resultMessage) {

            resultMessage.innerHTML =
                "❌ Batch recovery could not be completed.";

            resultMessage.classList.add("show");
        }
    }
}


/* =========================
   REFRESH DASHBOARD
========================= */

async function refreshDashboard() {

    await Promise.all([
        loadDashboard(),
        loadInsights(),
        loadTransactions()
    ]);

    /*
       IMPORTANT:
       AI Decision is NOT cleared here.
    */
}


/* =========================
   API STATUS
========================= */

function updateAPIStatus(isOnline) {

    const apiStatus =
        document.querySelector(".api-status");

    if (!apiStatus) {
        return;
    }


    if (isOnline) {

        apiStatus.innerHTML = `
            <span class="pulse"></span>
            <span>API ONLINE</span>
        `;

        apiStatus.style.color = "";

    } else {

        apiStatus.innerHTML = `
            <span class="pulse"></span>
            <span>API OFFLINE</span>
        `;

        apiStatus.style.color = "#f06464";
    }
}


/* =========================
   VIEW AUDIT TRAIL
========================= */

async function viewAuditTrail(transactionId) {

    const auditContent =
        document.getElementById("auditContent");

    const auditPanel =
        document.getElementById("audit");


    if (!auditContent) {
        return;
    }


    auditContent.className = "audit-loading";

    auditContent.innerHTML = `
        Loading audit trail for
        <strong>${transactionId}</strong>...
    `;


    if (auditPanel) {

        auditPanel.scrollIntoView({
            behavior: "smooth",
            block: "start"
        });
    }


    try {

        const response = await fetch(
            `${API_URL}/transactions/${encodeURIComponent(transactionId)}/audit`,
            {
                cache: "no-store"
            }
        );


        if (!response.ok) {
            throw new Error("Could not load audit trail");
        }


        const data = await response.json();


        let timelineHTML = `
            <div class="audit-transaction-id">
                Transaction:
                <strong>
                    ${data.transaction_id}
                </strong>
            </div>

            <div class="audit-timeline">
        `;


        if (
            !data.audit_trail ||
            data.audit_trail.length === 0
        ) {

            timelineHTML += `
                <div class="audit-empty">
                    No audit events found for this transaction.
                </div>
            `;

        } else {

            data.audit_trail.forEach(event => {

                timelineHTML += `
                    <div class="audit-event">

                        <div class="audit-dot"></div>

                        <div class="audit-event-content">

                            <div class="audit-event-top">

                                <strong>
                                    ${formatAuditEvent(event.event)}
                                </strong>

                                <span>
                                    ${event.timestamp}
                                </span>

                            </div>

                            <p>
                                ${event.details}
                            </p>

                        </div>

                    </div>
                `;
            });
        }


        timelineHTML += `
            </div>
        `;


        auditContent.className = "";
        auditContent.innerHTML = timelineHTML;

    } catch (error) {

        console.error(
            "Audit trail error:",
            error
        );

        auditContent.className =
            "audit-empty";

        auditContent.innerHTML = `
            ❌ Could not load the audit trail for
            <strong>${transactionId}</strong>.
        `;
    }
}


/* =========================
   FORMAT AUDIT EVENT
========================= */

function formatAuditEvent(event) {

    const eventNames = {

        transaction_received:
            "Transaction Received",

        failure_detected:
            "Failure Detected",

        revenue_risk_detected:
            "Revenue Risk Detected",

        agent_analysis:
            "AI Recovery Analysis",

        ai_decision:
            "AI Recovery Decision",

        recovery_attempt:
            "Recovery Attempt",

        recovery_success:
            "Recovery Successful",

        recovery_stopped:
            "Recovery Stopped"
    };


    return eventNames[event] ||
        formatText(event || "");
}


/* =========================
   CLEAR AUDIT TRAIL
========================= */

function closeAuditTrail() {

    const auditContent =
        document.getElementById("auditContent");

    if (!auditContent) {
        return;
    }


    auditContent.className =
        "audit-empty";


    auditContent.innerHTML = `
        Select <strong>View Audit</strong>
        from any transaction to see the complete
        event timeline.
    `;
}


/* =========================
   AI RECOVERY DECISION
========================= */

async function showAIDecision(transactionId) {

    console.log(
        "AI Decision clicked:",
        transactionId
    );


    const decisionContent =
        document.getElementById("aiDecisionContent");

    const aiPanel =
        document.getElementById("aiDecision");


    if (!decisionContent) {

        console.error(
            "AI Decision container not found"
        );

        return;
    }


    /* Store selected transaction */

    selectedTransactionId = transactionId;


    /* Create unique request ID */

    const currentRequestId =
        ++aiDecisionRequestId;


    /* SHOW LOADING STATE */

    decisionContent.className = "";

    decisionContent.innerHTML = `
        <div class="loading-state">

            <div class="ai-loading-icon">
                🤖
            </div>

            <strong>
                Analyzing ${transactionId}
            </strong>

            <p>
                Generating AI recovery recommendation...
            </p>

        </div>
    `;


    if (aiPanel) {

        aiPanel.scrollIntoView({
            behavior: "smooth",
            block: "start"
        });
    }


    try {

        const url =
            `${API_URL}/transactions/${encodeURIComponent(transactionId)}/ai-decision`;


        const response = await fetch(
            url,
            {
                method: "GET",
                cache: "no-store"
            }
        );


        if (!response.ok) {

            throw new Error(
                `Backend returned error ${response.status}`
            );
        }


        const data = await response.json();


        console.log(
            "AI Decision response:",
            data
        );


        /* Prevent old requests overwriting new ones */

        if (
            currentRequestId !== aiDecisionRequestId
        ) {
            return;
        }


        if (
            selectedTransactionId !== transactionId
        ) {
            return;
        }


        const currentDecisionContent =
            document.getElementById(
                "aiDecisionContent"
            );


        if (!currentDecisionContent) {
            return;
        }


        /* =========================
           NO ACTION REQUIRED
        ========================= */

        if (
            data.recommended_action === "no_action"
        ) {

            currentDecisionContent.className = "";

            currentDecisionContent.innerHTML = `
                <div class="ai-no-action">

                    <div class="ai-transaction-id">

                        Selected Transaction:

                        <strong>
                            ${data.transaction_id || transactionId}
                        </strong>

                    </div>

                    <h3>
                        ✓ No Recovery Required
                    </h3>

                    <p>
                        ${
                            data.message ||
                            "This transaction does not currently require recovery."
                        }
                    </p>

                </div>
            `;

            return;
        }


        /* =========================
           AI DECISION RESULT
        ========================= */

        currentDecisionContent.className = "";

        currentDecisionContent.innerHTML = `

            <div class="ai-transaction-id">

                Selected Transaction:

                <strong>
                    ${data.transaction_id || transactionId}
                </strong>

            </div>


            <div class="ai-decision-grid">


                <div class="ai-decision-card probability-card">

                    <span class="ai-label">
                        RECOVERY PROBABILITY
                    </span>

                    <strong>
                        ${data.recovery_probability ?? 0}%
                    </strong>

                    <small>
                        Estimated recovery likelihood
                    </small>

                </div>


                <div class="ai-decision-card">

                    <span class="ai-label">
                        PRIORITY
                    </span>

                    <strong>
                        ${formatText(
                            data.priority || "unknown"
                        ).toUpperCase()}
                    </strong>

                    <small>
                        Priority Score:
                        ${data.priority_score ?? 0}
                    </small>

                </div>


                <div class="ai-decision-card">

                    <span class="ai-label">
                        RECOVERY OPPORTUNITY
                    </span>

                    <strong>
                        ${formatText(
                            data.risk_level || "unknown"
                        ).toUpperCase()}
                    </strong>

                    <small>
                        Based on failure analysis
                    </small>

                </div>


                <div class="ai-decision-card action-card">

                    <span class="ai-label">
                        AI RECOMMENDED ACTION
                    </span>

                    <strong>
                        ${formatText(
                            data.recommended_action || "unknown"
                        ).toUpperCase()}
                    </strong>

                    <small>
                        Suggested recovery workflow
                    </small>

                </div>


            </div>


            <div class="ai-reasoning">

                <span class="ai-label">
                    🤖 AI DECISION REASONING
                </span>

                <p>
                    ${
                        data.decision_reason ||
                        "No detailed reasoning was provided."
                    }
                </p>

            </div>
        `;


        console.log(
            "AI Decision displayed:",
            transactionId
        );

    } catch (error) {

        console.error(
            "AI Decision error:",
            error
        );


        if (
            currentRequestId !== aiDecisionRequestId
        ) {
            return;
        }


        if (
            selectedTransactionId !== transactionId
        ) {
            return;
        }


        const currentDecisionContent =
            document.getElementById(
                "aiDecisionContent"
            );


        if (!currentDecisionContent) {
            return;
        }


        currentDecisionContent.className =
            "ai-error";


        currentDecisionContent.innerHTML = `

            <h3>
                ❌ Unable to generate AI recovery decision
            </h3>

            <p>

                Transaction:

                <strong>
                    ${transactionId}
                </strong>

            </p>

            <small>
                ${error.message}
            </small>
        `;
    }
}


/* =========================
   CLEAR AI DECISION
========================= */

function clearAIDecision() {

    aiDecisionRequestId++;

    selectedTransactionId = null;


    const decisionContent =
        document.getElementById(
            "aiDecisionContent"
        );


    if (!decisionContent) {
        return;
    }


    decisionContent.className =
        "ai-empty-state";


    decisionContent.innerHTML = `

        🤖 Select a transaction and click

        <strong>AI Decision</strong>

        to analyze its recovery strategy.

    `;
}


/* =========================
   GENERATE DEMO DATA
========================= */

async function generateDemoData() {

    const resultMessage =
        document.getElementById("resultMessage");


    try {

        if (resultMessage) {

            resultMessage.innerHTML =
                "⚡ Generating realistic demo transactions...";

            resultMessage.classList.add("show");
        }


        const response = await fetch(
            `${API_URL}/demo/generate`,
            {
                method: "POST",
                cache: "no-store"
            }
        );


        if (!response.ok) {
            throw new Error(
                "Could not generate demo data"
            );
        }


        const data =
            await response.json();


        if (resultMessage) {

            resultMessage.innerHTML = `

                ⚡ Demo data generated successfully.

                <br><br>

                Created:
                <strong>
                    ${data.transactions_created ?? 0}
                </strong>

                transaction(s).

                &nbsp; | &nbsp;

                Skipped:
                <strong>
                    ${data.transactions_skipped ?? 0}
                </strong>

                existing transaction(s).

            `;
        }


        await refreshDashboard();

    } catch (error) {

        console.error(
            "Demo generation error:",
            error
        );

        if (resultMessage) {

            resultMessage.innerHTML =
                "❌ Could not generate demo transactions.";

            resultMessage.classList.add("show");
        }
    }
}


/* =========================
   CLEAR ALL DATA
========================= */

async function clearAllData() {

    const confirmed = confirm(
        "Are you sure you want to delete all transactions and audit history?"
    );


    if (!confirmed) {
        return;
    }


    const resultMessage =
        document.getElementById("resultMessage");


    try {

        if (resultMessage) {

            resultMessage.innerHTML =
                "🗑 Clearing all transaction data...";

            resultMessage.classList.add("show");
        }


        const response = await fetch(
            `${API_URL}/transactions`,
            {
                method: "DELETE",
                cache: "no-store"
            }
        );


        if (!response.ok) {
            throw new Error(
                "Could not clear data"
            );
        }


        const data =
            await response.json();


        if (resultMessage) {

            resultMessage.innerHTML =
                `🗑 ${data.message}`;

            resultMessage.classList.add("show");
        }


        closeAuditTrail();
        clearAIDecision();

        await refreshDashboard();

    } catch (error) {

        console.error(
            "Clear data error:",
            error
        );

        if (resultMessage) {

            resultMessage.innerHTML =
                "❌ Could not clear transactions.";

            resultMessage.classList.add("show");
        }
    }
}


/* =========================
   HELPER: FORMAT TEXT
========================= */

function formatText(value) {

    if (
        value === null ||
        value === undefined ||
        value === ""
    ) {
        return "-";
    }


    return String(value)
        .replaceAll("_", " ");
}


/* =========================
   INITIAL LOAD
========================= */

document.addEventListener(
    "DOMContentLoaded",
    function () {

        refreshDashboard();

    }
);