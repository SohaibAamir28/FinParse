// Global application state
let state = {
    filename: "",
    transactions: [],
    summary: {}
};

// Available categories for manual selection dropdown
const CATEGORIES = [
    "Income/Salary",
    "Groceries",
    "Restaurants/Dining",
    "Utilities",
    "Housing/Rent",
    "Transfers/Investing",
    "Transportation/Auto",
    "Shopping/Retail",
    "Insurance/Medical",
    "Miscellaneous"
];

document.addEventListener("DOMContentLoaded", () => {
    initDragAndDrop();
    initToolbarActions();
});

// Initialize Drag & Drop Events for Ingesting Statements
function initDragAndDrop() {
    const dropZone = document.getElementById("drop-zone");
    const fileInput = document.getElementById("file-input");
    const cancelBtn = document.getElementById("cancel-file-btn");

    // Click to select
    dropZone.addEventListener("click", () => fileInput.click());

    fileInput.addEventListener("change", (e) => {
        if (e.target.files.length > 0) {
            handleFileSelection(e.target.files[0]);
        }
    });

    // Drag-over styling classes
    dropZone.addEventListener("dragover", (e) => {
        e.preventDefault();
        dropZone.classList.add("drag-over");
    });

    dropZone.addEventListener("dragleave", () => {
        dropZone.classList.remove("drag-over");
    });

    dropZone.addEventListener("drop", (e) => {
        e.preventDefault();
        dropZone.classList.remove("drag-over");
        if (e.dataTransfer.files.length > 0) {
            handleFileSelection(e.dataTransfer.files[0]);
        }
    });

    // Remove file selection button
    cancelBtn.addEventListener("click", () => {
        resetAppUI();
    });
}

// Display selected file details and initiate backend parsing
async function handleFileSelection(file) {
    const dropZone = document.getElementById("drop-zone");
    const fileInfo = document.getElementById("file-info-container");
    const fileNameEl = document.getElementById("file-name");
    const fileSizeEl = document.getElementById("file-size");
    const loading = document.getElementById("loading-container");

    // Check extensions
    const ext = file.name.split('.').pop().toLowerCase();
    if (ext !== 'pdf' && ext !== 'csv' && ext !== 'xlsx') {
        alert("Incorrect format! Please upload only bank statement PDF, CSV, or XLSX spreadsheets.");
        return;
    }

    // Update upload UI cards
    dropZone.style.display = "none";
    fileInfo.style.display = "flex";
    fileNameEl.textContent = file.name;
    fileSizeEl.textContent = formatBytes(file.size);

    // Show loading spinner
    loading.style.display = "block";
    hideResultsSections();

    // Prepare upload payload
    const formData = new FormData();
    formData.append("file", file);

    try {
        const response = await fetch("/api/upload", {
            method: "POST",
            body: formData
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || "Server error while parsing the statement file.");
        }

        const data = await response.json();
        state.filename = data.filename;
        state.transactions = data.transactions;
        state.summary = data.summary;

        // Render sections
        renderAppSummary();
        renderTransactionsTable();
        renderCategoriesSummary();
        
        // Unhide elements
        document.getElementById("kpi-section").style.display = "grid";
        document.getElementById("data-section").style.display = "flex";
    } catch (e) {
        alert("Upload Failed: " + e.message);
        resetAppUI();
    } finally {
        loading.style.display = "none";
    }
}

// Format file size utilities
function formatBytes(bytes, decimals = 2) {
    if (!+bytes) return '0 Bytes';
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(dm))} ${sizes[i]}`;
}

// Reset entire state and clear data grids
function resetAppUI() {
    state = { filename: "", transactions: [], summary: {} };
    document.getElementById("file-input").value = "";
    document.getElementById("drop-zone").style.display = "block";
    document.getElementById("file-info-container").style.display = "none";
    hideResultsSections();
}

function hideResultsSections() {
    document.getElementById("kpi-section").style.display = "none";
    document.getElementById("data-section").style.display = "none";
    document.getElementById("discrepancy-warning").style.display = "none";
}

// Update Top KPI Metric widgets
function renderAppSummary() {
    const s = state.summary;
    
    document.getElementById("kpi-starting").querySelector(".kpi-val").textContent = formatCurrency(s.starting_balance);
    document.getElementById("kpi-credits").querySelector(".kpi-val").textContent = formatCurrency(s.total_credits);
    document.getElementById("kpi-debits").querySelector(".kpi-val").textContent = formatCurrency(s.total_debits);
    
    // Net Flow card formatting
    const netEl = document.getElementById("kpi-net").querySelector(".kpi-val");
    netEl.textContent = formatCurrency(s.net_cash_flow);
    if (s.net_cash_flow > 0) {
        netEl.className = "kpi-val credit-color";
    } else if (s.net_cash_flow < 0) {
        netEl.className = "kpi-val debit-color";
    } else {
        netEl.className = "kpi-val";
    }

    document.getElementById("kpi-ending").querySelector(".kpi-val").textContent = formatCurrency(s.ending_balance);

    // Status widget state
    const statusCard = document.getElementById("kpi-status");
    const statusText = statusCard.querySelector(".status-text");
    const statusIcon = statusCard.querySelector(".status-icon");
    const pill = document.getElementById("reconciled-message");
    const warning = document.getElementById("discrepancy-warning");

    if (s.is_reconciled) {
        statusCard.className = "kpi-card status-card";
        statusText.textContent = "VERIFIED";
        statusIcon.className = "fa-solid fa-check-circle kpi-icon status-icon credit-color";
        
        pill.className = "reconciled-status-pill";
        pill.innerHTML = `<i class="fa-solid fa-circle-check"></i> Reconciled & Math-Verified`;
        warning.style.display = "none";
    } else {
        statusCard.className = "kpi-card status-card mismatch-status";
        statusText.textContent = `${s.discrepancies_count} DRIFTS`;
        statusIcon.className = "fa-solid fa-circle-exclamation kpi-icon status-icon debit-color";
        
        pill.className = "reconciled-status-pill mismatch-pill";
        pill.innerHTML = `<i class="fa-solid fa-triangle-exclamation"></i> Reconciliation Discrepancy`;
        
        document.getElementById("error-count").textContent = s.discrepancies_count;
        warning.style.display = "flex";
    }
}

// Render dynamic interactive data table
function renderTransactionsTable() {
    const tbody = document.getElementById("table-body");
    tbody.innerHTML = "";

    state.transactions.forEach((tx, index) => {
        const tr = document.createElement("tr");
        if (!tx.reconciled) {
            tr.classList.add("row-mismatch");
        }

        // Action column delete button
        const actionHtml = `<button class="icon-btn danger-btn" onclick="deleteRow(${index})" title="Delete row"><i class="fa-solid fa-trash-can"></i></button>`;

        // Construct category dropdown options selector
        let catOptions = "";
        CATEGORIES.forEach(c => {
            // Apply category matcher logic
            const currentCat = tx.category || categorizeLocal(tx.description);
            const selected = (c === currentCat) ? "selected" : "";
            catOptions += `<option value="${c}" ${selected}>${c}</option>`;
        });
        const categoryDropdownHtml = `
            <select class="category-dropdown" onchange="updateRowCategory(${index}, this.value)">
                ${catOptions}
            </select>
        `;

        tr.innerHTML = `
            <td contenteditable="true" onblur="updateRowField(${index}, 'date', this.innerText)">${tx.date}</td>
            <td contenteditable="true" onblur="updateRowField(${index}, 'description', this.innerText)">${tx.description}</td>
            <td>${categoryDropdownHtml}</td>
            <td contenteditable="true" class="text-right debit-color" onblur="updateRowField(${index}, 'debit', this.innerText)">${tx.debit.toFixed(2)}</td>
            <td contenteditable="true" class="text-right credit-color" onblur="updateRowField(${index}, 'credit', this.innerText)">${tx.credit.toFixed(2)}</td>
            <td contenteditable="true" class="text-right" onblur="updateRowField(${index}, 'balance', this.innerText)">${tx.balance.toFixed(2)}</td>
            <td class="text-right font-semibold">${tx.expected_balance.toFixed(2)}</td>
            <td class="text-right ${tx.discrepancy !== 0 ? 'debit-color font-semibold' : ''}">${tx.discrepancy.toFixed(2)}</td>
            <td class="text-center">
                <span class="badge ${tx.reconciled ? 'ok' : 'err'}">${tx.reconciled ? 'OK' : 'MISMATCH'}</span>
            </td>
            <td class="text-center">${actionHtml}</td>
        `;
        tbody.appendChild(tr);
    });
}

// Ingest local classification keywords (syncs with Python logic)
function categorizeLocal(desc) {
    desc = String(desc).toLowerCase();
    const map = {
        'Income/Salary': ['payroll', 'salary', 'deposit', 'direct dep', 'transfer in', 'wire in', 'refund', 'interest payment', 'dividends'],
        'Groceries': ['grocery', 'safeway', 'kroger', 'whole foods', 'trader joe', 'supermarket', 'walmart', 'target', 'costco', 'heeb', 'aldi'],
        'Restaurants/Dining': ['restaurant', 'cafe', 'starbucks', 'coffee', 'mcdonald', 'grubhub', 'ubereats', 'pizza', 'diner', 'bar', 'pub', 'grill', 'bistro'],
        'Utilities': ['electric', 'water', 'gas', 'power', 'comcast', 'verizon', 'att', 'internet', 'utility', 'trash', 'sewer', 'heating', 'netflix', 'spotify', 'hulu', 'subscriptions'],
        'Housing/Rent': ['rent', 'mortgage', 'housing', 'landlord', 'hoa', 'lease'],
        'Transfers/Investing': ['transfer', 'venmo', 'paypal', 'zelle', 'schwab', 'fidelity', 'vanguard', 'robinhood', 'atm withdrawal', 'cash withdrawal'],
        'Transportation/Auto': ['gasoline', 'chevron', 'shell', 'exxon', 'mobil', 'uber', 'lyft', 'subway', 'transit', 'auto', 'car wash', 'parking', 'toll'],
        'Shopping/Retail': ['amazon', 'ebay', 'macys', 'nordstrom', 'clothing', 'retail', 'electronics', 'apple', 'best buy', 'nike'],
        'Insurance/Medical': ['insurance', 'geico', 'progressive', 'medical', 'doctor', 'copay', 'pharmacy', 'cvs', 'walgreens', 'dentist', 'hospital'],
    };
    for (let key in map) {
        if (map[key].some(kw => desc.includes(kw))) {
            return key;
        }
    }
    return 'Miscellaneous';
}

// Render the category widgets breakdown list
function renderCategoriesSummary() {
    const list = document.getElementById("category-list");
    list.innerHTML = "";

    // Aggregate values
    const breakdown = {};
    CATEGORIES.forEach(c => {
        breakdown[c] = { count: 0, debits: 0, credits: 0 };
    });

    state.transactions.forEach(tx => {
        const cat = tx.category || categorizeLocal(tx.description);
        if (!breakdown[cat]) {
            breakdown[cat] = { count: 0, debits: 0, credits: 0 };
        }
        breakdown[cat].count++;
        breakdown[cat].debits += tx.debit;
        breakdown[cat].credits += tx.credit;
    });

    // Create entries for categories that have at least 1 item
    Object.keys(breakdown).forEach(cat => {
        const data = breakdown[cat];
        if (data.count === 0) return;

        const net = data.credits - data.debits;
        const netFormatted = formatCurrency(net);
        const netClass = net > 0 ? "credit-color" : net < 0 ? "debit-color" : "";

        const item = document.createElement("div");
        item.className = "category-item";
        item.innerHTML = `
            <div class="cat-details">
                <span class="cat-name">${cat}</span>
                <span class="cat-count">${data.count} transaction${data.count > 1 ? 's' : ''}</span>
            </div>
            <div class="cat-amounts">
                <span class="cat-net ${netClass}">${netFormatted}</span>
                <div class="cat-breakdown">
                    In: ${formatCurrency(data.credits)} | Out: ${formatCurrency(data.debits)}
                </div>
            </div>
        `;
        list.appendChild(item);
    });
}

// Local State Mutators
function updateRowField(index, field, value) {
    let cleanVal = value.trim();
    
    if (field === 'debit' || field === 'credit' || field === 'balance') {
        // Strip symbols and parse float
        cleanVal = parseFloat(cleanVal.replace(/[^\d.-]/g, "")) || 0.0;
    }

    state.transactions[index][field] = cleanVal;
    
    // Auto sync category if description changes
    if (field === 'description') {
        state.transactions[index].category = categorizeLocal(cleanVal);
    }
}

function updateRowCategory(index, category) {
    state.transactions[index].category = category;
    renderCategoriesSummary();
}

function deleteRow(index) {
    state.transactions.splice(index, 1);
    
    // Automatically re-calculate after deletes
    recalculateReconciliation();
}

// Toolbar action clicks
function initToolbarActions() {
    document.getElementById("reconcile-btn").addEventListener("click", () => {
        recalculateReconciliation();
    });

    document.getElementById("add-row-btn").addEventListener("click", () => {
        addNewRow();
    });

    document.getElementById("export-btn").addEventListener("click", () => {
        exportToExcelFile();
    });
}

// Insert new row helper
function addNewRow() {
    const today = new Date().toISOString().split('T')[0];
    
    // Establish default starting balance based on last row or 0.0
    let lastBal = 0.0;
    if (state.transactions.length > 0) {
        lastBal = state.transactions[state.transactions.length - 1].balance;
    }

    const newTx = {
        date: today,
        description: "Manual Transaction Entry",
        category: "Miscellaneous",
        debit: 0.0,
        credit: 0.0,
        balance: lastBal,
        expected_balance: lastBal,
        discrepancy: 0.0,
        reconciled: true,
        raw_row_idx: state.transactions.length
    };

    state.transactions.push(newTx);
    
    // Instantly update table view and recalculate
    renderTransactionsTable();
    recalculateReconciliation();
}

// Post current client states to backend recalculation API
async function recalculateReconciliation() {
    const loading = document.getElementById("loading-container");
    loading.style.display = "block";

    try {
        const response = await fetch("/api/reconcile", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                transactions: state.transactions
            })
        });

        if (!response.ok) {
            throw new Error("Mathematical reconciliation request failed on server.");
        }

        const data = await response.json();
        state.transactions = data.transactions;
        state.summary = data.summary;

        // Refresh views
        renderAppSummary();
        renderTransactionsTable();
        renderCategoriesSummary();
    } catch (e) {
        alert("Calculation Error: " + e.message);
    } finally {
        loading.style.display = "none";
    }
}

// Submit transaction payload to generate and download Excel
async function exportToExcelFile() {
    try {
        const response = await fetch("/api/export", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                transactions: state.transactions,
                summary: state.summary
            })
        });

        if (!response.ok) {
            throw new Error("Excel compilation request failed on server.");
        }

        const blob = await response.blob();
        
        // Trigger client browser download
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.style.display = "none";
        a.href = url;
        a.download = `${state.filename.split('.')[0]}_reconciled.xlsx`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    } catch (e) {
        alert("Export Failure: " + e.message);
    }
}

// Currency format helper
function formatCurrency(val) {
    const absVal = Math.abs(val).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    return val < 0 ? `-$${absVal}` : `$${absVal}`;
}
