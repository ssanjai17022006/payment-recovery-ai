const API_BASE_URL = "http://127.0.0.1:5000";


/* =========================================================
   HELPERS
   ========================================================= */

function formatPercent(value) {
    const number = Number(value);

    if (!Number.isFinite(number)) {
        return "0.00%";
    }

    return `${(number * 100).toFixed(2)}%`;
}


function formatCurrency(value) {
    const number = Number(value);

    if (!Number.isFinite(number)) {
        return "₹0.00";
    }

    return `₹${number.toLocaleString("en-IN", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    })}`;
}


function formatNumber(value) {
    const number = Number(value);

    if (!Number.isFinite(number)) {
        return "0";
    }

    return number.toLocaleString("en-IN");
}


function normalizeProbability(value) {
    const number = Number(value);

    if (!Number.isFinite(number)) {
        return 0;
    }

    if (number > 1) {
        return number / 100;
    }

    return Math.max(0, Math.min(number, 1));
}


function escapeHtml(value) {
    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}


/* =========================================================
   DOM REFERENCES
   ========================================================= */

const healthStatus =
    document.getElementById("healthStatus");

const refreshButton =
    document.getElementById("refreshButton");

const transactionForm =
    document.getElementById("transactionForm");


/* =========================================================
   DASHBOARD KPI REFERENCES
   ========================================================= */

const totalTransactions =
    document.getElementById("totalTransactions");

const automateCount =
    document.getElementById("automateCount");

const reviewCount =
    document.getElementById("reviewCount");

const doNotRecoverCount =
    document.getElementById("doNotRecoverCount");

const automationRate =
    document.getElementById("automationRate");

const averageProbability =
    document.getElementById("averageProbability");

const averageProbabilityBar =
    document.getElementById("averageProbabilityBar");

const totalTransactionValue =
    document.getElementById("totalTransactionValue");

const automatedTransactionValue =
    document.getElementById("automatedTransactionValue");

const reviewTransactionValue =
    document.getElementById("reviewTransactionValue");

const potentialRecoverableValue =
    document.getElementById("potentialRecoverableValue");

const simulatedRecoveredAmount =
    document.getElementById("simulatedRecoveredAmount");

const pendingReviewValue =
    document.getElementById("pendingReviewValue");

const stoppedValue =
    document.getElementById("stoppedValue");

const recentTransactions =
    document.getElementById("recentTransactions");


/* =========================================================
   MODEL SIGNAL REFERENCES
   ========================================================= */

const dashboardProbabilityDisplay =
    document.getElementById(
        "dashboardProbabilityDisplay"
    );

const dashboardProbabilityBar =
    document.getElementById(
        "dashboardProbabilityBar"
    );


/* =========================================================
   FINANCIAL RECOVERY OVERVIEW REFERENCES
   ========================================================= */

const financialTotalValue =
    document.getElementById(
        "financialTotalValue"
    );

const financialAutomatedValue =
    document.getElementById(
        "financialAutomatedValue"
    );

const financialReviewValue =
    document.getElementById(
        "financialReviewValue"
    );

const financialPotentialValue =
    document.getElementById(
        "financialPotentialValue"
    );


/* =========================================================
   RESULT REFERENCES
   ========================================================= */

/*
 * The original HTML did not contain id="transactionResult".
 * Therefore we support both:
 *
 * 1. id="transactionResult"
 * 2. .transaction-result
 */
const transactionResult =
    document.getElementById("transactionResult") ||
    document.querySelector(".transaction-result");

const resultTransactionId =
    document.getElementById(
        "resultTransactionId"
    );

const decision =
    document.getElementById("decision");

const recoveryProbability =
    document.getElementById(
        "recoveryProbability"
    );

const recoveryProbabilityBar =
    document.getElementById(
        "recoveryProbabilityBar"
    );

const policyEvaluation =
    document.getElementById(
        "policyEvaluation"
    );

const decisionExplanation =
    document.getElementById(
        "decisionExplanation"
    );

const decisionReason =
    document.getElementById(
        "decisionReason"
    );

const formError =
    document.getElementById("formError");


/* =========================================================
   RECOVERY SIMULATION REFERENCES
   ========================================================= */

const recoverySimulation =
    document.getElementById(
        "recoverySimulation"
    );

const recoveryResult =
    document.getElementById(
        "recoveryResult"
    );

const recoveredAmount =
    document.getElementById(
        "recoveredAmount"
    );


/* =========================================================
   API HEALTH
   ========================================================= */

async function checkApiHealth() {
    if (!healthStatus) {
        return;
    }

    try {
        const response = await fetch(
            `${API_BASE_URL}/health`
        );

        if (!response.ok) {
            throw new Error(
                "API unavailable"
            );
        }

        const data = await response.json();

        if (
            data.success ||
            data.status === "ok" ||
            data.status === "healthy"
        ) {
            healthStatus.textContent =
                "API Connected";

            healthStatus.classList.remove(
                "offline"
            );

            healthStatus.classList.add(
                "online"
            );
        } else {
            throw new Error(
                "Invalid health response"
            );
        }

    } catch (error) {
        console.error(
            "Health check failed:",
            error
        );

        healthStatus.textContent =
            "API Disconnected";

        healthStatus.classList.remove(
            "online"
        );

        healthStatus.classList.add(
            "offline"
        );
    }
}


/* =========================================================
   DASHBOARD STATS
   ========================================================= */

async function loadDashboardStats() {
    try {
        const response = await fetch(
            `${API_BASE_URL}/transactions/stats`
        );

        if (!response.ok) {
            throw new Error(
                `Stats request failed: ${response.status}`
            );
        }

        const data = await response.json();

        if (!data.success) {
            throw new Error(
                data.message ||
                "Unable to load statistics"
            );
        }

        const stats =
            data.stats || {};


        /* ---------------------------------------------
           TRANSACTION COUNTS
        --------------------------------------------- */

        if (totalTransactions) {
            totalTransactions.textContent =
                formatNumber(
                    stats.total ??
                    stats.total_transactions ??
                    0
                );
        }

        if (automateCount) {
            automateCount.textContent =
                formatNumber(
                    stats.automate_count ??
                    stats.automated_count ??
                    0
                );
        }

        if (reviewCount) {
            reviewCount.textContent =
                formatNumber(
                    stats.review_count ??
                    0
                );
        }

        if (doNotRecoverCount) {
            doNotRecoverCount.textContent =
                formatNumber(
                    stats.do_not_recover_count ??
                    stats.do_not_recover ??
                    0
                );
        }


        /* ---------------------------------------------
           AUTOMATION RATE
        --------------------------------------------- */

        if (automationRate) {
            const rate =
                Number(
                    stats.automation_rate ??
                    0
                );

            automationRate.textContent =
                `${rate.toFixed(2)}%`;
        }


        /* ---------------------------------------------
           AVERAGE RECOVERY PROBABILITY
        --------------------------------------------- */

        const avgProbability =
            normalizeProbability(
                stats.average_recovery_probability ??
                stats.average_probability ??
                0
            );

        if (averageProbability) {
            averageProbability.textContent =
                formatPercent(
                    avgProbability
                );
        }

        if (averageProbabilityBar) {
            averageProbabilityBar.style.width =
                `${Math.min(
                    avgProbability * 100,
                    100
                )}%`;
        }


        /* ---------------------------------------------
           MODEL SIGNAL
        --------------------------------------------- */

        if (dashboardProbabilityDisplay) {
            dashboardProbabilityDisplay.textContent =
                formatPercent(
                    avgProbability
                );
        }

        if (dashboardProbabilityBar) {
            dashboardProbabilityBar.style.width =
                `${Math.min(
                    avgProbability * 100,
                    100
                )}%`;
        }


        /* ---------------------------------------------
           TRANSACTION VALUES
        --------------------------------------------- */

        const totalValue =
            stats.total_value ??
            stats.total_transaction_value ??
            0;

        const automatedValue =
            stats.automated_value ??
            stats.automated_transaction_value ??
            0;

        const reviewValue =
            stats.review_value ??
            stats.review_transaction_value ??
            0;

        const potentialValue =
            stats.potential_recoverable_value ??
            0;


        if (totalTransactionValue) {
            totalTransactionValue.textContent =
                formatCurrency(
                    totalValue
                );
        }

        if (automatedTransactionValue) {
            automatedTransactionValue.textContent =
                formatCurrency(
                    automatedValue
                );
        }

        if (reviewTransactionValue) {
            reviewTransactionValue.textContent =
                formatCurrency(
                    reviewValue
                );
        }

        if (potentialRecoverableValue) {
            potentialRecoverableValue.textContent =
                formatCurrency(
                    potentialValue
                );
        }


        /* ---------------------------------------------
           FINANCIAL RECOVERY OVERVIEW
        --------------------------------------------- */

        if (financialTotalValue) {
            financialTotalValue.textContent =
                formatCurrency(
                    totalValue
                );
        }

        if (financialAutomatedValue) {
            financialAutomatedValue.textContent =
                formatCurrency(
                    automatedValue
                );
        }

        if (financialReviewValue) {
            financialReviewValue.textContent =
                formatCurrency(
                    reviewValue
                );
        }

        if (financialPotentialValue) {
            financialPotentialValue.textContent =
                formatCurrency(
                    potentialValue
                );


        }


        /* ---------------------------------------------
           RECOVERY SIMULATION METRICS
        --------------------------------------------- */

        if (simulatedRecoveredAmount) {
            simulatedRecoveredAmount.textContent =
                formatCurrency(
                    stats.simulated_recovered_amount ??
                    0
                );
        }

        if (pendingReviewValue) {
            pendingReviewValue.textContent =
                formatCurrency(
                    stats.pending_review_value ??
                    0
                );
        }

        if (stoppedValue) {
            stoppedValue.textContent =
                formatCurrency(
                    stats.stopped_value ??
                    0
                );
        }

    } catch (error) {
        console.error(
            "Failed to load dashboard statistics:",
            error
        );
    }
}


/* =========================================================
   RECENT TRANSACTIONS
   ========================================================= */

async function loadRecentTransactions() {
    if (!recentTransactions) {
        return;
    }

    try {
        const response = await fetch(
            `${API_BASE_URL}/transactions/recent`
        );

        if (!response.ok) {
            throw new Error(
                `Recent transactions request failed: ${response.status}`
            );
        }

        const data =
            await response.json();

        const transactions =
            Array.isArray(data)
                ? data
                : (
                    data.transactions ||
                    []
                );

        renderRecentTransactions(
            transactions
        );

    } catch (error) {
        console.error(
            "Failed to load recent transactions:",
            error
        );

        recentTransactions.innerHTML = `
            <div class="empty-state">
                Unable to load recent transactions.
            </div>
        `;
    }
}


/* =========================================================
   RENDER RECENT TRANSACTIONS
   ========================================================= */

function renderRecentTransactions(
    transactions
) {
    if (!recentTransactions) {
        return;
    }

    if (
        !transactions ||
        transactions.length === 0
    ) {
        recentTransactions.innerHTML = `
            <div class="empty-state">
                No transactions available.
            </div>
        `;

        return;
    }

    recentTransactions.innerHTML =
        transactions
            .map(transaction => {

                const probability =
                    normalizeProbability(
                        transaction.recovery_probability ??
                        transaction.probability ??
                        0
                    );

                const decisionValue =
                    transaction.decision ||
                    transaction.action ||
                    "—";

                const amount =
                    Number(
                        transaction.amount ?? 0
                    );

                return `
                    <div class="transaction-row">

                        <div class="transaction-id">
                            ${escapeHtml(
                                transaction.transaction_id ??
                                "—"
                            )}
                        </div>

                        <div>
                            ${escapeHtml(
                                transaction.payment_method ??
                                "—"
                            )}
                        </div>

                        <div>
                            ${escapeHtml(
                                transaction.bank ??
                                "—"
                            )}
                        </div>

                        <div>
                            ${formatCurrency(
                                amount
                            )}
                        </div>

                        <div>
                            ${formatPercent(
                                probability
                            )}
                        </div>

                        <div>
                            <span class="decision-badge ${getDecisionClass(
                                decisionValue
                            )}">
                                ${escapeHtml(
                                    decisionValue
                                )}
                            </span>
                        </div>

                    </div>
                `;
            })
            .join("");
}


/* =========================================================
   DECISION CSS CLASS
   ========================================================= */

function getDecisionClass(
    decisionValue
) {
    switch (decisionValue) {

        case "AUTOMATE":
            return "automate";

        case "REVIEW":
            return "review";

        case "DO_NOT_RECOVER":
            return "do-not-recover";

        default:
            return "";
    }
}


/* =========================================================
   FORM DATA
   ========================================================= */

function getFormData() {
    const formData =
        new FormData(
            transactionForm
        );

    return {
        payment_method:
            formData.get(
                "payment_method"
            ),

        bank:
            formData.get("bank"),

        failure_code:
            formData.get(
                "failure_code"
            ),

        failure_stage:
            formData.get(
                "failure_stage"
            ),

        amount:
            Number(
                formData.get("amount")
            ),

        retry_count:
            Number(
                formData.get("retry_count")
            ),

        is_recurring:
            formData.get(
                "is_recurring"
            ) === "true"
    };
}


/* =========================================================
   PREDICTION
   ========================================================= */

async function predictTransaction() {
    if (!transactionForm) {
        return;
    }

    if (formError) {
        formError.textContent = "";
    }

    const transaction =
        getFormData();

    try {

        /*
         * ---------------------------------------------
         * SEND TRANSACTION TO BACKEND
         * ---------------------------------------------
         */

        const response =
            await fetch(
                `${API_BASE_URL}/predict`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body:
                        JSON.stringify(
                            transaction
                        )
                }
            );


        /*
         * ---------------------------------------------
         * PARSE RESPONSE
         * ---------------------------------------------
         */

        const data =
            await response.json();


        /*
         * ---------------------------------------------
         * HANDLE API ERROR
         * ---------------------------------------------
         */

        if (!response.ok) {
            throw new Error(
                data.message ||
                data.error ||
                "Prediction failed"
            );
        }


        /*
         * ---------------------------------------------
         * RENDER RESULT IMMEDIATELY
         *
         * IMPORTANT:
         * Do NOT wait for dashboard/recent
         * transactions before rendering the result.
         * ---------------------------------------------
         */

        updatePredictionResult(
            data
        );


        /*
         * ---------------------------------------------
         * SHOW RESULT SECTION
         * ---------------------------------------------
         */

        if (transactionResult) {

            transactionResult.classList.add(
                "visible"
            );

            /*
             * Give the browser a moment to
             * update the DOM before scrolling.
             */
            setTimeout(() => {

                transactionResult.scrollIntoView({
                    behavior: "smooth",
                    block: "start"
                });

            }, 50);
        }


        /*
         * ---------------------------------------------
         * REFRESH DASHBOARD AFTER RESULT RENDERING
         *
         * These operations are intentionally not
         * allowed to control the result panel.
         * ---------------------------------------------
         */

        await Promise.all([
            loadDashboardStats(),
            loadRecentTransactions()
        ]);

    } catch (error) {

        console.error(
            "Prediction failed:",
            error
        );

        if (formError) {
            formError.textContent =
                error.message ||
                "Unable to process transaction.";
        }
    }
}


/* =========================================================
   UPDATE PREDICTION RESULT
   ========================================================= */

function updatePredictionResult(
    data
) {
    if (!data) {
        console.error(
            "updatePredictionResult received empty response"
        );

        return;
    }


    console.log(
        "Prediction response:",
        data
    );


    /*
     * Backend response:
     *
     * {
     *     success: true,
     *     prediction: {...},
     *     simulation: true
     * }
     */

    const prediction =
        data.prediction ||
        data;


    /* ---------------------------------------------
       DECISION
    --------------------------------------------- */

    const decisionValue =
        prediction.decision ||
        data.decision ||
        "—";


    /* ---------------------------------------------
       PROBABILITY
    --------------------------------------------- */

    const probability =
        normalizeProbability(
            prediction.recovery_probability ??
            data.recovery_probability ??
            0
        );


    /* ---------------------------------------------
       RISK
    --------------------------------------------- */

    const riskLevel =
        prediction.risk_level ||
        data.risk_level ||
        "—";


    /* ---------------------------------------------
       POLICY RULE
    --------------------------------------------- */

    const policyRule =
        prediction.policy_rule ||
        data.policy_rule ||
        "—";


    /* ---------------------------------------------
       EXPLANATION
    --------------------------------------------- */

    const explanation =
        prediction.explanation ??
        data.explanation ??
        [];


    /* ---------------------------------------------
       REASON
    --------------------------------------------- */

    const reason =
        prediction.reason ||
        data.reason ||
        "";


    /* ---------------------------------------------
       TRANSACTION ID
    --------------------------------------------- */

    const transactionId =
        prediction.transaction_id ||
        data.transaction_id ||
        "—";


    /*
     * ---------------------------------------------
     * RECOVERY SIMULATION
     *
     * Current backend may return recovery fields
     * directly inside prediction rather than
     * inside data.recovery.
     *
     * Therefore support both structures.
     * ---------------------------------------------
     */

    const recovery =
        data.recovery ||
        prediction.recovery ||
        (
            (
                prediction.recovery_attempted !== undefined
            ) ||
            (
                prediction.recovery_result !== undefined
            ) ||
            (
                prediction.recovered_amount !== undefined
            ) ||
            (
                prediction.stopped_reason !== undefined
            )
                ? prediction
                : null
        );


    /* ---------------------------------------------
       TRANSACTION ID
    --------------------------------------------- */

    if (resultTransactionId) {

        resultTransactionId.textContent =
            transactionId;
    }


    /* ---------------------------------------------
       DECISION
    --------------------------------------------- */

    if (decision) {

        decision.textContent =
            decisionValue;

        decision.className =
            `decision-value ${getDecisionClass(
                decisionValue
            )}`;
    }


    /* ---------------------------------------------
       PROBABILITY
    --------------------------------------------- */

    if (recoveryProbability) {

        recoveryProbability.textContent =
            formatPercent(
                probability
            );
    }

    if (recoveryProbabilityBar) {

        recoveryProbabilityBar.style.width =
            `${Math.min(
                probability * 100,
                100
            )}%`;
    }


    /* ---------------------------------------------
       POLICY
    --------------------------------------------- */

    updatePolicyEvaluation(
        riskLevel,
        policyRule
    );


    /* ---------------------------------------------
       EXPLANATION
    --------------------------------------------- */

    updateDecisionExplanation(
        explanation,
        reason,
        prediction
    );


    /* ---------------------------------------------
       RECOVERY SIMULATION
    --------------------------------------------- */

    updateRecoverySimulation(
        recovery
    );


    /* ---------------------------------------------
       RESULT CONTAINER
    --------------------------------------------- */

    if (transactionResult) {

        transactionResult.classList.add(
            "visible"
        );
    }
}


/* =========================================================
   POLICY EVALUATION
   ========================================================= */

function updatePolicyEvaluation(
    riskLevel,
    policyRule
) {
    if (!policyEvaluation) {
        return;
    }

    policyEvaluation.innerHTML = `
        <div class="policy-risk">
            <strong>Risk Level:</strong>
            ${escapeHtml(riskLevel)}
        </div>

        <div class="policy-rule">
            <strong>Policy Rule:</strong>
            ${escapeHtml(policyRule)}
        </div>
    `;
}


/* =========================================================
   DECISION EXPLANATION
   ========================================================= */

function updateDecisionExplanation(
    explanation,
    reason,
    prediction
) {
    if (!decisionExplanation) {
        return;
    }

    let explanationItems = [];


    /* ---------------------------------------------
       BACKEND EXPLANATION
    --------------------------------------------- */

    if (Array.isArray(explanation)) {

        explanationItems =
            explanation.filter(
                item =>
                    item !== null &&
                    item !== undefined
            );

    } else if (
        typeof explanation === "string"
    ) {

        explanationItems =
            [explanation];
    }


    /*
     * Backend explanation is the source of truth.
     */

    if (explanationItems.length > 0) {

        decisionExplanation.innerHTML =
            explanationItems
                .map(
                    item =>
                        `<li>${escapeHtml(
                            item
                        )}</li>`
                )
                .join("");

    } else {

        /*
         * -----------------------------------------
         * FALLBACK EXPLANATION
         * -----------------------------------------
         */

        const fallback = [];

        const failureCode =
            prediction.failure_code;

        const retryCount =
            Number(
                prediction.retry_count ?? 0
            );

        const amount =
            Number(
                prediction.amount ?? 0
            );

        const probability =
            normalizeProbability(
                prediction.recovery_probability ??
                0
            );


        if (
            failureCode ===
            "CARD_BLOCKED"
        ) {

            fallback.push(
                "Card is blocked, so recovery is stopped by policy."
            );

        } else if (
            retryCount >= 3
        ) {

            fallback.push(
                "Maximum retry limit reached."
            );

        } else if (
            failureCode ===
            "BANK_TIMEOUT"
        ) {

            fallback.push(
                "Bank timeout requires manual review because retrying may create duplicate-charge risk."
            );

        } else if (
            amount >= 7500
        ) {

            fallback.push(
                "High-value transaction requires additional review."
            );

        } else if (
            probability >= 0.70
        ) {

            fallback.push(
                "High recovery probability supports automated recovery."
            );

        } else if (
            probability >= 0.40
        ) {

            fallback.push(
                "Medium recovery probability requires review."
            );

        } else {

            fallback.push(
                "Low recovery probability does not justify recovery."
            );
        }


        decisionExplanation.innerHTML =
            fallback
                .map(
                    item =>
                        `<li>${escapeHtml(
                            item
                        )}</li>`
                )
                .join("");
    }


    /* ---------------------------------------------
       POLICY REASON
    --------------------------------------------- */

    if (decisionReason) {

        decisionReason.textContent =
            reason || "";
    }
}


/* =========================================================
   RECOVERY SIMULATION
   ========================================================= */

function updateRecoverySimulation(
    recovery
) {
    if (!recoverySimulation) {
        return;
    }


    /*
     * No recovery information.
     */

    if (!recovery) {

        recoverySimulation.innerHTML = `
            <div class="simulation-status">
                No simulation result available.
            </div>
        `;

        if (recoveryResult) {
            recoveryResult.textContent =
                "—";
        }

        if (recoveredAmount) {
            recoveredAmount.textContent =
                "₹0.00";
        }

        return;
    }


    /*
     * ---------------------------------------------
     * EXTRACT SIMULATION FIELDS
     * ---------------------------------------------
     */

    const attempted =
        recovery.recovery_attempted === true;


    const result =
        recovery.recovery_result ||
        "unknown";


    const amount =
        Number(
            recovery.recovered_amount ??
            0
        );


    const stoppedReason =
        recovery.stopped_reason ||
        "";


    /* ---------------------------------------------
       RESULT VALUE
    --------------------------------------------- */

    if (recoveryResult) {

        recoveryResult.textContent =
            formatRecoveryResult(
                result
            );
    }


    /* ---------------------------------------------
       RECOVERED AMOUNT
    --------------------------------------------- */

    if (recoveredAmount) {

        recoveredAmount.textContent =
            formatCurrency(
                amount
            );
    }


    /* ---------------------------------------------
       STATUS TEXT
    --------------------------------------------- */

    let statusText = "";


    if (
        result === "success"
    ) {

        statusText =
            "Recovery attempt simulated successfully.";

    } else if (
        result === "failure"
    ) {

        statusText =
            "Recovery attempt was simulated but did not recover the payment.";

    } else if (
        result === "pending"
    ) {

        statusText =
            stoppedReason ||
            "Manual review is pending.";

    } else if (
        result === "not_attempted"
    ) {

        statusText =
            stoppedReason ||
            "Recovery was not attempted.";

    } else {

        statusText =
            "Simulation completed.";
    }


    /* ---------------------------------------------
       SIMULATION DETAILS
    --------------------------------------------- */

    recoverySimulation.innerHTML = `
        <div class="simulation-status">
            ${escapeHtml(statusText)}
        </div>

        <div class="simulation-details">

            <div>
                <strong>Attempted:</strong>
                ${attempted ? "Yes" : "No"}
            </div>

            <div>
                <strong>Result:</strong>
                ${escapeHtml(
                    formatRecoveryResult(
                        result
                    )
                )}
            </div>

            <div>
                <strong>Recovered Amount:</strong>
                ${formatCurrency(
                    amount
                )}
            </div>

            ${
                stoppedReason
                    ? `
                        <div>
                            <strong>Reason:</strong>
                            ${escapeHtml(
                                stoppedReason
                            )}
                        </div>
                    `
                    : ""
            }

        </div>
    `;
}


/* =========================================================
   RECOVERY RESULT FORMAT
   ========================================================= */

function formatRecoveryResult(
    result
) {
    switch (result) {

        case "success":
            return "SUCCESS";

        case "failure":
            return "FAILURE";

        case "pending":
            return "PENDING REVIEW";

        case "not_attempted":
            return "NOT ATTEMPTED";

        default:
            return String(
                result || "UNKNOWN"
            )
                .replaceAll(
                    "_",
                    " "
                )
                .toUpperCase();
    }
}


/* =========================================================
   REFRESH DASHBOARD
   ========================================================= */

async function refreshDashboard() {

    await checkApiHealth();

    await Promise.all([
        loadDashboardStats(),
        loadRecentTransactions()
    ]);
}


/* =========================================================
   EVENT LISTENERS
   ========================================================= */

if (transactionForm) {

    transactionForm.addEventListener(
        "submit",
        async event => {

            event.preventDefault();

            await predictTransaction();
        }
    );
}


if (refreshButton) {

    refreshButton.addEventListener(
        "click",
        async () => {

            await refreshDashboard();
        }
    );
}


/* =========================================================
   INITIAL LOAD
   ========================================================= */

async function initializeDashboard() {

    await checkApiHealth();

    await Promise.all([
        loadDashboardStats(),
        loadRecentTransactions()
    ]);
}


/*
 * Because the script is loaded near the end
 * of the HTML, initialize immediately if the
 * DOM is already ready. Otherwise wait for it.
 */

if (
    document.readyState ===
    "loading"
) {

    document.addEventListener(
        "DOMContentLoaded",
        initializeDashboard
    );

} else {

    initializeDashboard();
}