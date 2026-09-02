const API_BASE_URL = "http://127.0.0.1:5000";


// ============================================================
// DOM REFERENCES
// ============================================================

const apiStatus =
    document.getElementById("apiStatus");

const apiStatusText =
    document.getElementById("apiStatusText");

const refreshDashboard =
    document.getElementById("refreshDashboard");

const transactionForm =
    document.getElementById("transactionForm");

const analyzeButton =
    document.getElementById("analyzeButton");


// Dashboard

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

const recentTransactions =
    document.getElementById("recentTransactions");


// Result panel

const decision =
    document.getElementById("decision");

const recoveryProbability =
    document.getElementById("recoveryProbability");

const recoveryProbabilityBar =
    document.getElementById("recoveryProbabilityBar");

const policyEvaluation =
    document.getElementById("policyEvaluation");

const decisionExplanation =
    document.getElementById("decisionExplanation");

const decisionReason =
    document.getElementById("decisionReason");

const transactionResult =
    document.getElementById("transactionResult");

const resultTransactionId =
    document.getElementById("resultTransactionId");

const formError =
    document.getElementById("formError");


// ============================================================
// PAGE INITIALIZATION
// ============================================================

document.addEventListener("DOMContentLoaded", () => {

    checkAPIHealth();

    loadDashboardStats();

    loadRecentTransactions();

});


// ============================================================
// API HEALTH CHECK
// ============================================================

async function checkAPIHealth() {

    try {

        const response =
            await fetch(
                `${API_BASE_URL}/health`
            );

        if (!response.ok) {

            throw new Error(
                "API unavailable"
            );
        }

        const data =
            await response.json();


        if (data.status === "healthy") {

            if (apiStatusText) {

                apiStatusText.textContent =
                    "API Connected";
            }

            if (apiStatus) {

                apiStatus.classList.remove(
                    "checking",
                    "disconnected"
                );

                apiStatus.classList.add(
                    "connected"
                );
            }

        } else {

            if (apiStatusText) {

                apiStatusText.textContent =
                    "API Unhealthy";
            }

            if (apiStatus) {

                apiStatus.classList.remove(
                    "checking",
                    "connected"
                );

                apiStatus.classList.add(
                    "disconnected"
                );
            }
        }

    } catch (error) {

        console.error(
            "API health check failed:",
            error
        );

        if (apiStatusText) {

            apiStatusText.textContent =
                "API Offline";
        }

        if (apiStatus) {

            apiStatus.classList.remove(
                "checking",
                "connected"
            );

            apiStatus.classList.add(
                "disconnected"
            );
        }
    }
}


// ============================================================
// REFRESH BUTTON
// ============================================================

if (refreshDashboard) {

    refreshDashboard.addEventListener(
        "click",
        async () => {

            refreshDashboard.disabled = true;

            refreshDashboard.textContent =
                "Refreshing...";

            await Promise.all([
                checkAPIHealth(),
                loadDashboardStats(),
                loadRecentTransactions()
            ]);

            refreshDashboard.disabled = false;

            refreshDashboard.textContent =
                "Refresh";
        }
    );
}


// ============================================================
// LOAD DASHBOARD STATISTICS
// ============================================================

async function loadDashboardStats() {

    try {

        const response =
            await fetch(
                `${API_BASE_URL}/transactions/stats`
            );

        if (!response.ok) {

            throw new Error(
                "Failed to load statistics"
            );
        }

        const stats =
            await response.json();

        console.log(
            "Dashboard stats:",
            stats
        );


        // ----------------------------------------------------
        // KPI COUNTS
        // ----------------------------------------------------

        if (totalTransactions) {

            totalTransactions.textContent =
                stats.total_transactions ?? 0;
        }

        if (automateCount) {

            automateCount.textContent =
                stats.automate_count ?? 0;
        }

        if (reviewCount) {

            reviewCount.textContent =
                stats.review_count ?? 0;
        }

        if (doNotRecoverCount) {

            doNotRecoverCount.textContent =
                stats.do_not_recover_count ?? 0;
        }


        // ----------------------------------------------------
        // AUTOMATION RATE
        // ----------------------------------------------------

        let rate =
            stats.automation_rate;


        if (
            rate === undefined ||
            rate === null
        ) {

            const total =
                Number(
                    stats.total_transactions ?? 0
                );

            const automate =
                Number(
                    stats.automate_count ?? 0
                );

            rate =
                total > 0
                    ? (automate / total) * 100
                    : 0;
        }


        if (automationRate) {

            automationRate.textContent =
                `${Number(rate).toFixed(1)}%`;
        }


        // ----------------------------------------------------
        // AVERAGE PROBABILITY
        // ----------------------------------------------------

        const avgProbability =
            Number(
                stats.average_recovery_probability ?? 0
            );


        if (averageProbability) {

            averageProbability.textContent =
                `${(
                    avgProbability * 100
                ).toFixed(2)}%`;
        }


        if (averageProbabilityBar) {

            averageProbabilityBar.style.width =
                `${Math.min(
                    avgProbability * 100,
                    100
                )}%`;
        }


        // ----------------------------------------------------
        // FINANCIAL METRICS
        // ----------------------------------------------------

        if (totalTransactionValue) {

            totalTransactionValue.textContent =
                formatCurrency(
                    stats.total_transaction_value
                );
        }


        if (automatedTransactionValue) {

            automatedTransactionValue.textContent =
                formatCurrency(
                    stats.automated_transaction_value
                );
        }


        if (reviewTransactionValue) {

            reviewTransactionValue.textContent =
                formatCurrency(
                    stats.review_transaction_value
                );
        }


        if (potentialRecoverableValue) {

            potentialRecoverableValue.textContent =
                formatCurrency(
                    stats.potential_recoverable_value
                );
        }

    } catch (error) {

        console.error(
            "Failed to load dashboard statistics:",
            error
        );
    }
}


// ============================================================
// LOAD RECENT TRANSACTIONS
// ============================================================

async function loadRecentTransactions() {

    try {

        const response =
            await fetch(
                `${API_BASE_URL}/transactions/recent`
            );

        if (!response.ok) {

            throw new Error(
                "Failed to load recent transactions"
            );
        }

        const data =
            await response.json();


        console.log(
            "Recent transactions:",
            data
        );


        const transactions =
            Array.isArray(data)
                ? data
                : data.transactions || [];


        renderRecentTransactions(
            transactions
        );

    } catch (error) {

        console.error(
            "Failed to load recent transactions:",
            error
        );


        if (recentTransactions) {

            recentTransactions.innerHTML = `
                <tr>
                    <td
                        colspan="6"
                        class="error-cell"
                    >
                        Unable to load recent transactions
                    </td>
                </tr>
            `;
        }
    }
}


// ============================================================
// RENDER RECENT TRANSACTIONS
// ============================================================

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
            <tr>
                <td
                    colspan="6"
                    class="empty-cell"
                >
                    No transactions available
                </td>
            </tr>
        `;

        return;
    }


    recentTransactions.innerHTML =
        transactions.map(
            transaction => {

                const transactionDecision =
                    transaction.decision ||
                    "UNKNOWN";


                const probability =
                    Number(
                        transaction.recovery_probability ?? 0
                    );


                return `
                    <tr>

                        <td>
                            ${escapeHTML(
                                transaction.transaction_id ||
                                "-"
                            )}
                        </td>

                        <td>
                            ${escapeHTML(
                                transaction.payment_method ||
                                "-"
                            )}
                        </td>

                        <td>
                            ${escapeHTML(
                                transaction.bank ||
                                "-"
                            )}
                        </td>

                        <td>
                            ${formatCurrency(
                                transaction.amount
                            )}
                        </td>

                        <td>
                            ${(probability * 100).toFixed(2)}%
                        </td>

                        <td>

                            <span
                                class="decision-badge
                                ${getDecisionClass(
                                    transactionDecision
                                )}"
                            >
                                ${escapeHTML(
                                    transactionDecision
                                )}
                            </span>

                        </td>

                    </tr>
                `;
            }
        ).join("");
}


// ============================================================
// TRANSACTION FORM
// ============================================================

if (transactionForm) {

    transactionForm.addEventListener(
        "submit",
        analyzeTransaction
    );
}


// ============================================================
// ANALYZE TRANSACTION
// ============================================================

async function analyzeTransaction(
    event
) {

    event.preventDefault();


    clearFormError();


    if (analyzeButton) {

        analyzeButton.disabled = true;

        analyzeButton.textContent =
            "Analyzing...";
    }


    try {

        const formData =
            new FormData(
                transactionForm
            );


        // ----------------------------------------------------
        // Build transaction
        // ----------------------------------------------------

        const transaction = {

            merchant_id:
                formData.get(
                    "merchant_id"
                ) || "",

            customer_id:
                formData.get(
                    "customer_id"
                ) || "",

            payment_method:
                formData.get(
                    "payment_method"
                ),

            bank:
                formData.get(
                    "bank"
                ),

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
                    formData.get(
                        "amount"
                    )
                ),

            retry_count:
                Number(
                    formData.get(
                        "retry_count"
                    )
                ),

            is_recurring:
                formData.has(
                    "is_recurring"
                )
        };


        console.log(
            "Sending transaction:",
            transaction
        );


        // ----------------------------------------------------
        // API REQUEST
        // ----------------------------------------------------

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


        const data =
            await response.json();


        console.log(
            "Prediction response:",
            data
        );


        if (!response.ok) {

            throw new Error(
                data.error ||
                "Prediction failed"
            );
        }


        // ----------------------------------------------------
        // EXTRACT API RESULT
        // ----------------------------------------------------

        const prediction =
            data.prediction || data;


        const input =
            data.input || {};


        const finalDecision =
            prediction.decision ||
            input.decision ||
            "UNKNOWN";


        const probability =
            Number(
                prediction.recovery_probability ??
                input.recovery_probability ??
                0
            );


        const reason =
            prediction.reason ||
            input.reason ||
            "No decision reason provided";


        // IMPORTANT:
        // Backend is the source of truth for risk level.

        const riskLevel =
            prediction.risk_level ||
            input.risk_level ||
            "";


        // IMPORTANT:
        // Backend is the source of truth for policy rule.

        const policyRule =
            prediction.policy_rule ||
            input.policy_rule ||
            "";


        // Backend explanation

        const backendExplanation =
            Array.isArray(
                prediction.explanation
            )
                ? prediction.explanation
                : [];


        const transactionId =
            input.transaction_id ||
            prediction.transaction_id ||
            "Generated automatically";


        // ----------------------------------------------------
        // UPDATE FINAL DECISION
        // ----------------------------------------------------

        if (decision) {

            decision.textContent =
                formatDecision(
                    finalDecision
                );


            decision.className =
                `decision-value ${
                    getDecisionClass(
                        finalDecision
                    )
                }`;
        }


        // ----------------------------------------------------
        // UPDATE ML PROBABILITY
        // ----------------------------------------------------

        if (recoveryProbability) {

            recoveryProbability.textContent =
                `${(
                    probability * 100
                ).toFixed(2)}%`;
        }


        if (recoveryProbabilityBar) {

            recoveryProbabilityBar.style.width =
                `${Math.min(
                    probability * 100,
                    100
                )}%`;
        }


        // ----------------------------------------------------
        // UPDATE POLICY EVALUATION
        // ----------------------------------------------------

        updatePolicyEvaluation(
            finalDecision,
            probability,
            reason,
            transaction,
            riskLevel,
            policyRule
        );


        // ----------------------------------------------------
        // UPDATE EXPLANATION
        // ----------------------------------------------------

        updateDecisionExplanation(
            finalDecision,
            probability,
            reason,
            transaction,
            backendExplanation
        );


        // ----------------------------------------------------
        // UPDATE DECISION REASON
        // ----------------------------------------------------

        if (decisionReason) {

            decisionReason.textContent =
                reason;
        }


        // ----------------------------------------------------
        // UPDATE TRANSACTION ID
        // ----------------------------------------------------

        if (transactionResult) {

            transactionResult.classList.remove(
                "hidden"
            );
        }


        if (resultTransactionId) {

            resultTransactionId.textContent =
                transactionId;
        }


        // ----------------------------------------------------
        // REFRESH DASHBOARD
        // ----------------------------------------------------

        await loadDashboardStats();

        await loadRecentTransactions();


    } catch (error) {

        console.error(
            "Transaction analysis failed:",
            error
        );


        showFormError(
            error.message
        );


    } finally {

        if (analyzeButton) {

            analyzeButton.disabled = false;

            analyzeButton.textContent =
                "Analyze Transaction";
        }
    }
}


// ============================================================
// POLICY & RISK EVALUATION
// ============================================================

function updatePolicyEvaluation(
    decisionValue,
    probability,
    reason,
    transaction,
    riskLevel,
    policyRule
) {

    if (!policyEvaluation) {
        return;
    }


    // --------------------------------------------------------
    // Use backend risk level
    // --------------------------------------------------------

    const displayedRisk =
        riskLevel
            ? riskLevel.toUpperCase()
            : "UNKNOWN";


    let evaluation = "";


    if (
        displayedRisk ===
        "LOW"
    ) {

        evaluation =
            "LOW RISK — ";

    } else if (
        displayedRisk ===
        "MEDIUM"
    ) {

        evaluation =
            "MEDIUM RISK — ";

    } else if (
        displayedRisk ===
        "HIGH"
    ) {

        evaluation =
            "HIGH RISK — ";

    } else {

        evaluation =
            "RISK LEVEL UNKNOWN — ";
    }


    // --------------------------------------------------------
    // Decision-specific message
    // --------------------------------------------------------

    if (
        decisionValue ===
        "AUTOMATE"
    ) {

        evaluation +=
            `Recovery probability is ` +
            `${(
                probability * 100
            ).toFixed(2)}%. ` +
            `Policy permits automated recovery.`;

    } else if (
        decisionValue ===
        "REVIEW"
    ) {

        evaluation +=
            `Recovery may be possible, ` +
            `but policy requires additional review ` +
            `before recovery.`;

    } else if (
        decisionValue ===
        "DO_NOT_RECOVER"
    ) {

        evaluation +=
            `Policy does not permit ` +
            `automated recovery for this transaction.`;

    } else {

        evaluation +=
            "Policy evaluation unavailable.";
    }


    // --------------------------------------------------------
    // Policy rule
    // --------------------------------------------------------

    if (policyRule) {

        evaluation +=
            ` Policy rule: ${policyRule}.`;
    }


    // --------------------------------------------------------
    // Backend reason
    // --------------------------------------------------------

    if (reason) {

        evaluation +=
            ` ${reason}`;
    }


    policyEvaluation.textContent =
        evaluation;


    // --------------------------------------------------------
    // CSS class
    // --------------------------------------------------------

    policyEvaluation.classList.remove(
        "policy-automate",
        "policy-review",
        "policy-block"
    );


    if (
        decisionValue ===
        "AUTOMATE"
    ) {

        policyEvaluation.classList.add(
            "policy-automate"
        );

    } else if (
        decisionValue ===
        "REVIEW"
    ) {

        policyEvaluation.classList.add(
            "policy-review"
        );

    } else if (
        decisionValue ===
        "DO_NOT_RECOVER"
    ) {

        policyEvaluation.classList.add(
            "policy-block"
        );
    }
}


// ============================================================
// EXPLAINABLE AI DECISION
// ============================================================

function updateDecisionExplanation(
    decisionValue,
    probability,
    reason,
    transaction,
    backendExplanation = []
) {

    if (!decisionExplanation) {
        return;
    }


    // --------------------------------------------------------
    // Prefer backend explanation
    // --------------------------------------------------------

    if (
        Array.isArray(backendExplanation) &&
        backendExplanation.length > 0
    ) {

        decisionExplanation.innerHTML =
            backendExplanation.map(
                item => `
                    <li>
                        <span class="explanation-icon">
                            ✓
                        </span>
                        <span>
                            ${escapeHTML(item)}
                        </span>
                    </li>
                `
            ).join("");

        return;
    }


    // --------------------------------------------------------
    // Fallback explanation
    // --------------------------------------------------------

    const percentage =
        (
            probability * 100
        ).toFixed(2);


    const amount =
        Number(
            transaction.amount || 0
        );


    const retryCount =
        Number(
            transaction.retry_count || 0
        );


    const failureCode =
        transaction.failure_code ||
        "Unknown";


    const explanation =
        [];


    // --------------------------------------------------------
    // ML PROBABILITY
    // --------------------------------------------------------

    explanation.push(
        `ML model estimated a ${percentage}% ` +
        `recovery probability.`
    );


    // --------------------------------------------------------
    // DECISION-SPECIFIC POLICY EXPLANATION
    // --------------------------------------------------------

    if (
        decisionValue ===
        "AUTOMATE"
    ) {

        explanation.push(
            `Probability is at or above the ` +
            `70% automation threshold.`
        );

        explanation.push(
            `The transaction passed the current ` +
            `policy safety checks.`
        );

        explanation.push(
            `Automatic recovery is permitted.`
        );

    } else if (
        decisionValue ===
        "REVIEW"
    ) {

        explanation.push(
            `Recovery probability is within the ` +
            `review range of 40%–69.99%.`
        );

        explanation.push(
            `The transaction should receive ` +
            `additional human review before recovery.`
        );

    } else if (
        decisionValue ===
        "DO_NOT_RECOVER"
    ) {

        if (
            failureCode ===
            "CARD_BLOCKED"
        ) {

            explanation.push(
                `The failure code is CARD_BLOCKED, ` +
                `so automated recovery is considered unsafe.`
            );

        } else if (
            retryCount >= 3
        ) {

            explanation.push(
                `The transaction has reached the ` +
                `maximum retry limit of 3.`
            );

        } else if (
            probability < 0.40
        ) {

            explanation.push(
                `Recovery probability is below the ` +
                `40% review threshold.`
            );

        } else {

            explanation.push(
                `Current policy does not permit ` +
                `automated recovery.`
            );
        }
    }


    // --------------------------------------------------------
    // HIGH-VALUE TRANSACTION
    // --------------------------------------------------------

    if (
        amount >= 7500
    ) {

        explanation.push(
            `Transaction value is ${formatCurrency(
                amount
            )}, so high-value transactions require review.`
        );
    }


    // --------------------------------------------------------
    // RETRY INFORMATION
    // --------------------------------------------------------

    explanation.push(
        `Current retry count: ${retryCount}.`
    );


    // --------------------------------------------------------
    // RENDER
    // --------------------------------------------------------

    decisionExplanation.innerHTML =
        explanation.map(
            item => `
                <li>
                    <span class="explanation-icon">
                        ✓
                    </span>
                    <span>
                        ${escapeHTML(item)}
                    </span>
                </li>
            `
        ).join("");
}


// ============================================================
// DECISION CSS CLASS
// ============================================================

function getDecisionClass(
    decisionValue
) {

    switch (decisionValue) {

        case "AUTOMATE":

            return "decision-automate";

        case "REVIEW":

            return "decision-review";

        case "DO_NOT_RECOVER":

            return "decision-do-not-recover";

        default:

            return "";
    }
}


// ============================================================
// FORMAT DECISION FOR DISPLAY
// ============================================================

function formatDecision(
    decisionValue
) {

    if (
        decisionValue ===
        "DO_NOT_RECOVER"
    ) {

        return "DO NOT RECOVER";
    }


    return decisionValue;
}


// ============================================================
// CURRENCY FORMATTER
// ============================================================

function formatCurrency(
    value
) {

    const amount =
        Number(
            value ?? 0
        );


    return amount.toLocaleString(
        "en-IN",
        {
            style: "currency",
            currency: "INR",
            maximumFractionDigits: 2
        }
    );
}


// ============================================================
// HTML ESCAPE
// ============================================================

function escapeHTML(
    value
) {

    return String(value)
        .replace(
            /&/g,
            "&amp;"
        )
        .replace(
            /</g,
            "&lt;"
        )
        .replace(
            />/g,
            "&gt;"
        )
        .replace(
            /"/g,
            "&quot;"
        )
        .replace(
            /'/g,
            "&#039;"
        );
}


// ============================================================
// FORM ERROR
// ============================================================

function showFormError(
    message
) {

    if (!formError) {
        return;
    }


    formError.textContent =
        message ||
        "An unexpected error occurred.";


    formError.classList.remove(
        "hidden"
    );
}


function clearFormError() {

    if (!formError) {
        return;
    }


    formError.textContent = "";

    formError.classList.add(
        "hidden"
    );
}