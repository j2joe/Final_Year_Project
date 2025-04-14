document.addEventListener('DOMContentLoaded', function() {
    // Initialize modals
    const incomeModal = document.getElementById('incomeModal');
    const expenseModal = document.getElementById('expenseModal');
    const reportModal = document.getElementById('reportModal');
    const incomeBtn = document.getElementById('addIncomeBtn');
    const expenseBtn = document.getElementById('addExpenseBtn');
    const reportBtn = document.getElementById('generateReportBtn');
    const closeButtons = document.querySelectorAll('.close');

    // Open modals
    if (incomeBtn) {
        incomeBtn.addEventListener('click', () => {
            fetchCategories('INCOME');
            incomeModal.style.display = 'block';
            document.body.style.overflow = 'hidden';
            document.getElementById('incomeDate').valueAsDate = new Date();
        });
    }

    if (expenseBtn) {
        expenseBtn.addEventListener('click', () => {
            fetchCategories('EXPENSE');
            expenseModal.style.display = 'block';
            document.body.style.overflow = 'hidden';
            document.getElementById('expenseDate').valueAsDate = new Date();
        });
    }

    if (reportBtn) {
        reportBtn.addEventListener('click', () => {
            reportModal.style.display = 'block';
            document.body.style.overflow = 'hidden';
            const today = new Date().toISOString().split('T')[0];
            document.getElementById('startDate').value = today;
            document.getElementById('endDate').value = today;
        });
    }

    // Close modals
    closeButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.modal').forEach(modal => {
                modal.style.display = 'none';
            });
            document.body.style.overflow = 'auto';
        });
    });

    // Close modal when clicking outside
    window.addEventListener('click', (event) => {
        if (event.target.classList.contains('modal')) {
            event.target.style.display = 'none';
            document.body.style.overflow = 'auto';
        }
    });

    // Load recent transactions
    loadRecentTransactions();
});

function fetchCategories(type) {
    const selectId = type === 'INCOME' ? 'incomeCategory' : 'expenseCategory';
    const select = document.getElementById(selectId);
    
    fetch(`/api/categories?type=${type}`)
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        select.innerHTML = '<option value="">Select category</option>';
        data.forEach(category => {
            const option = document.createElement('option');
            option.value = category.id;
            option.textContent = category.name;
            select.appendChild(option);
        });
    })
    .catch(error => {
        console.error('Error fetching categories:', error);
        showAlert('Error loading categories. Please try again.', 'error');
    });
}

function loadRecentTransactions() {
    fetch('/api/transactions/recent')
    .then(response => response.json())
    .then(data => {
        const container = document.getElementById('transactions-container');
        if (data.length > 0) {
            let html = '<table><tr><th>Date</th><th>Description</th><th>Amount</th><th>Type</th></tr>';
            data.forEach(transaction => {
                const amountClass = transaction.type === 'INCOME' ? 'text-success' : 'text-danger';
                html += `
                    <tr>
                        <td>${new Date(transaction.date).toLocaleDateString()}</td>
                        <td>${transaction.description || 'N/A'}</td>
                        <td class="${amountClass}">${transaction.type === 'INCOME' ? '+' : '-'}$${transaction.amount.toFixed(2)}</td>
                        <td>${transaction.type}</td>
                    </tr>
                `;
            });
            html += '</table>';
            container.innerHTML = html;
        } else {
            container.innerHTML = '<p>No recent transactions found</p>';
        }
    })
    .catch(error => {
        console.error('Error loading transactions:', error);
        document.getElementById('transactions-container').innerHTML = 
            '<p class="text-error">Error loading transactions. Please try again.</p>';
    });
}

// Form submissions
document.getElementById('incomeForm')?.addEventListener('submit', function(e) {
    e.preventDefault();
    submitTransaction('INCOME');
});

document.getElementById('expenseForm')?.addEventListener('submit', function(e) {
    e.preventDefault();
    submitTransaction('EXPENSE');
});

document.getElementById('reportForm')?.addEventListener('submit', function(e) {
    e.preventDefault();
    generateReport();
});

function submitTransaction(type) {
    const form = document.getElementById(`${type.toLowerCase()}Form`);
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalBtnText = submitBtn.textContent;
    
    // Show loading state
    submitBtn.disabled = true;
    submitBtn.textContent = 'Processing...';
    
    const formData = {
        amount: document.getElementById(`${type.toLowerCase()}Amount`).value,
        category_id: document.getElementById(`${type.toLowerCase()}Category`).value,
        date: document.getElementById(`${type.toLowerCase()}Date`).value,
        description: document.getElementById(`${type.toLowerCase()}Description`).value,
        type: type
    };
    
    // Add expense-specific fields
    if (type === 'EXPENSE') {
        formData.payment_method = document.getElementById('expensePayment').value;
        formData.is_recurring = document.getElementById('expenseRecurring').checked;
    }
    
    fetch('/api/transactions', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(err => { throw err; });
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            showAlert(`${type} added successfully!`, 'success');
            document.getElementById(`${type.toLowerCase()}Modal`).style.display = 'none';
            document.body.style.overflow = 'auto';
            form.reset();
            loadRecentTransactions();
        } else {
            throw new Error(data.message || 'Unknown error occurred');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert(`Error: ${error.message}`, 'error');
    })
    .finally(() => {
        submitBtn.disabled = false;
        submitBtn.textContent = originalBtnText;
    });
}

function generateReport() {
    const form = document.getElementById('reportForm');
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalBtnText = submitBtn.textContent;
    
    submitBtn.disabled = true;
    submitBtn.textContent = 'Generating...';
    
    const formData = {
        type: document.getElementById('reportType').value,
        start_date: document.getElementById('startDate').value,
        end_date: document.getElementById('endDate').value,
        format: document.getElementById('reportFormat').value
    };
    
    fetch('/api/reports', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(err => { throw err; });
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            showAlert('Report generated successfully!', 'success');
            document.getElementById('reportModal').style.display = 'none';
            document.body.style.overflow = 'auto';
            form.reset();
            
            // Handle report download/view based on format
            if (formData.format === 'csv' || formData.format === 'pdf') {
                window.location.href = data.download_url;
            }
        } else {
            throw new Error(data.message || 'Unknown error occurred');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert(`Error: ${error.message}`, 'error');
    })
    .finally(() => {
        submitBtn.disabled = false;
        submitBtn.textContent = originalBtnText;
    });
}

function showAlert(message, type) {
    const notificationArea = document.getElementById('notification-area');
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    notificationArea.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 5000);
}

// Add these functions to dashboard.js after the existing code

function generateReport() {
    const form = document.getElementById('reportForm');
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalBtnText = document.getElementById('reportSubmitText').textContent;
    const spinner = document.getElementById('reportSpinner');
    
    // Show loading state
    submitBtn.disabled = true;
    document.getElementById('reportSubmitText').style.display = 'none';
    spinner.style.display = 'inline-block';
    
    const formData = {
        type: document.getElementById('reportType').value,
        start_date: document.getElementById('startDate').value,
        end_date: document.getElementById('endDate').value,
        format: document.getElementById('reportFormat').value
    };
    
    fetch('/api/reports', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(err => { throw err; });
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            showAlert('Report generated successfully!', 'success');
            document.getElementById('reportModal').style.display = 'none';
            document.body.style.overflow = 'auto';
            
            // Handle report display or download based on format
            if (data.format === 'html') {
                displayReportInOverview(data);
            } else if (data.format === 'csv' || data.format === 'pdf') {
                window.location.href = data.download_url;
            }
        } else {
            throw new Error(data.message || 'Unknown error occurred');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert(`Error: ${error.message || 'Unknown error occurred'}`, 'error');
    })
    .finally(() => {
        submitBtn.disabled = false;
        document.getElementById('reportSubmitText').style.display = 'inline';
        spinner.style.display = 'none';
    });
}

function displayReportInOverview(reportData) {
    const overviewBox = document.querySelector('.dashboard-card:nth-child(2)');
    if (!overviewBox) return;
    
    // Clear previous content
    overviewBox.innerHTML = '';
    
    // Create report header
    const header = document.createElement('div');
    header.className = 'report-header';
    header.innerHTML = `
        <h2>${reportData.title}</h2>
        <p class="report-period">Period: ${formatDate(reportData.start_date)} - ${formatDate(reportData.end_date)}</p>
        <button class="close-report-btn">Back to Overview</button>
    `;
    overviewBox.appendChild(header);
    
    // Add event listener to close report button
    const closeBtn = header.querySelector('.close-report-btn');
    closeBtn.addEventListener('click', resetFinancialOverview);
    
    // Create report content based on type
    const content = document.createElement('div');
    content.className = 'report-content';
    
    if (reportData.report_type === 'monthly_summary') {
        renderMonthlySummaryReport(content, reportData.data);
    } else if (reportData.report_type === 'category_breakdown') {
        renderCategoryBreakdownReport(content, reportData.data);
    } else if (reportData.report_type === 'income_vs_expense') {
        renderIncomeVsExpenseReport(content, reportData.data);
    }
    
    overviewBox.appendChild(content);
    
    // Add styles for the report
    addReportStyles();
}

function renderMonthlySummaryReport(container, data) {
    if (!data || data.length === 0) {
        container.innerHTML = '<p class="no-data">No data available for the selected period.</p>';
        return;
    }
    
    let tableHtml = `
        <table class="report-table">
            <thead>
                <tr>
                    <th>Month</th>
                    <th>Income</th>
                    <th>Expenses</th>
                    <th>Net</th>
                </tr>
            </thead>
            <tbody>
    `;
    
    let totalIncome = 0;
    let totalExpenses = 0;
    let totalNet = 0;
    
    data.forEach(month => {
        totalIncome += month.income;
        totalExpenses += month.expense;
        totalNet += month.net;
        
        tableHtml += `
            <tr>
                <td>${month.month_formatted || month.month}</td>
                <td class="text-success">$${month.income.toFixed(2)}</td>
                <td class="text-danger">$${month.expense.toFixed(2)}</td>
                <td class="${month.net >= 0 ? 'text-success' : 'text-danger'}">
                    $${month.net.toFixed(2)}
                </td>
            </tr>
        `;
    });
    
    tableHtml += `
            <tr class="total-row">
                <td><strong>Total</strong></td>
                <td class="text-success"><strong>$${totalIncome.toFixed(2)}</strong></td>
                <td class="text-danger"><strong>$${totalExpenses.toFixed(2)}</strong></td>
                <td class="${totalNet >= 0 ? 'text-success' : 'text-danger'}">
                    <strong>$${totalNet.toFixed(2)}</strong>
                </td>
            </tr>
        </tbody>
    </table>
    `;
    
    container.innerHTML = tableHtml;
    
    // Add chart visualization
    const chartContainer = document.createElement('div');
    chartContainer.className = 'chart-container';
    chartContainer.style.height = '250px';
    chartContainer.style.marginTop = '20px';
    container.appendChild(chartContainer);
    
    // In a real app, you would render a chart here using a library like Chart.js
    chartContainer.innerHTML = `
        <div style="width: 100%; height: 100%; background: #f8f9fa; border-radius: 8px; 
                    display: flex; align-items: center; justify-content: center;">
            <p style="color: #7f8c8d;">Chart visualization would appear here</p>
        </div>
    `;
}

function renderCategoryBreakdownReport(container, data) {
    if (!data || (!data.expenses.length && !data.income.length)) {
        container.innerHTML = '<p class="no-data">No data available for the selected period.</p>';
        return;
    }
    
    // Create tabs for expenses and income
    const tabsHtml = `
        <div class="report-tabs">
            <button class="tab-btn active" data-tab="expenses">Expenses</button>
            <button class="tab-btn" data-tab="income">Income</button>
        </div>
        <div class="tab-content">
            <div id="expenses-tab" class="tab-pane active"></div>
            <div id="income-tab" class="tab-pane"></div>
        </div>
    `;
    
    container.innerHTML = tabsHtml;
    
    // Render expenses table
    const expensesTab = container.querySelector('#expenses-tab');
    if (data.expenses.length > 0) {
        let expensesHtml = `
            <table class="report-table">
                <thead>
                    <tr>
                        <th>Category</th>
                        <th>Amount</th>
                        <th>Count</th>
                        <th>% of Total</th>
                    </tr>
                </thead>
                <tbody>
        `;
        
        let totalExpenses = data.expenses.reduce((sum, cat) => sum + cat.total, 0);
        
        data.expenses.forEach(category => {
            const percentage = (category.total / totalExpenses * 100).toFixed(1);
            expensesHtml += `
                <tr>
                    <td>${category.category}</td>
                    <td class="text-danger">$${category.total.toFixed(2)}</td>
                    <td>${category.count}</td>
                    <td>
                        <div class="percentage-bar">
                            <div class="bar" style="width: ${percentage}%"></div>
                            <span>${percentage}%</span>
                        </div>
                    </td>
                </tr>
            `;
        });
        
        expensesHtml += `
                <tr class="total-row">
                    <td><strong>Total</strong></td>
                    <td class="text-danger"><strong>$${totalExpenses.toFixed(2)}</strong></td>
                    <td>${data.expenses.reduce((sum, cat) => sum + cat.count, 0)}</td>
                    <td>100%</td>
                </tr>
            </tbody>
        </table>
        `;
        
        expensesTab.innerHTML = expensesHtml;
    } else {
        expensesTab.innerHTML = '<p class="no-data">No expense data available.</p>';
    }
    
    // Render income table
    const incomeTab = container.querySelector('#income-tab');
    if (data.income.length > 0) {
        let incomeHtml = `
            <table class="report-table">
                <thead>
                    <tr>
                        <th>Category</th>
                        <th>Amount</th>
                        <th>Count</th>
                        <th>% of Total</th>
                    </tr>
                </thead>
                <tbody>
        `;
        
        let totalIncome = data.income.reduce((sum, cat) => sum + cat.total, 0);
        
        data.income.forEach(category => {
            const percentage = (category.total / totalIncome * 100).toFixed(1);
            incomeHtml += `
                <tr>
                    <td>${category.category}</td>
                    <td class="text-success">$${category.total.toFixed(2)}</td>
                    <td>${category.count}</td>
                    <td>
                        <div class="percentage-bar">
                            <div class="bar" style="width: ${percentage}%"></div>
                            <span>${percentage}%</span>
                        </div>
                    </td>
                </tr>
            `;
        });
        
        incomeHtml += `
                <tr class="total-row">
                    <td><strong>Total</strong></td>
                    <td class="text-success"><strong>$${totalIncome.toFixed(2)}</strong></td>
                    <td>${data.income.reduce((sum, cat) => sum + cat.count, 0)}</td>
                    <td>100%</td>
                </tr>
            </tbody>
        </table>
        `;
        
        incomeTab.innerHTML = incomeHtml;
    } else {
        incomeTab.innerHTML = '<p class="no-data">No income data available.</p>';
    }
    
    // Add tab switching functionality
    container.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            // Remove active class from all tabs and panes
            container.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            container.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
            
            // Add active class to current tab and pane
            this.classList.add('active');
            const tabId = this.dataset.tab + '-tab';
            document.getElementById(tabId).classList.add('active');
        });
    });
}

function renderIncomeVsExpenseReport(container, data) {
    if (!data || data.length === 0) {
        container.innerHTML = '<p class="no-data">No data available for the selected period.</p>';
        return;
    }
    
    let tableHtml = `
        <table class="report-table">
            <thead>
                <tr>
                    <th>Date</th>
                    <th>Income</th>
                    <th>Expenses</th>
                    <th>Balance</th>
                </tr>
            </thead>
            <tbody>
    `;
    
    let totalIncome = 0;
    let totalExpenses = 0;
    
    data.forEach(day => {
        totalIncome += day.income;
        totalExpenses += day.expense;
        const balance = day.income - day.expense;
        
        tableHtml += `
            <tr>
                <td>${day.date_formatted || day.date}</td>
                <td class="text-success">$${day.income.toFixed(2)}</td>
                <td class="text-danger">$${day.expense.toFixed(2)}</td>
                <td class="${balance >= 0 ? 'text-success' : 'text-danger'}">
                    $${balance.toFixed(2)}
                </td>
            </tr>
        `;
    });
    
    const totalBalance = totalIncome - totalExpenses;
    
    tableHtml += `
            <tr class="total-row">
                <td><strong>Total</strong></td>
                <td class="text-success"><strong>$${totalIncome.toFixed(2)}</strong></td>
                <td class="text-danger"><strong>$${totalExpenses.toFixed(2)}</strong></td>
                <td class="${totalBalance >= 0 ? 'text-success' : 'text-danger'}">
                    <strong>$${totalBalance.toFixed(2)}</strong>
                </td>
            </tr>
        </tbody>
    </table>
    `;
    
    container.innerHTML = tableHtml;
    
    // Add chart visualization
    const chartContainer = document.createElement('div');
    chartContainer.className = 'chart-container';
    chartContainer.style.height = '250px';
    chartContainer.style.marginTop = '20px';
    container.appendChild(chartContainer);
    
    // In a real app, you would render a chart here using a library like Chart.js
    chartContainer.innerHTML = `
        <div style="width: 100%; height: 100%; background: #f8f9fa; border-radius: 8px; 
                    display: flex; align-items: center; justify-content: center;">
            <p style="color: #7f8c8d;">Income vs Expense chart would appear here</p>
        </div>
    `;
}

function resetFinancialOverview() {
    const overviewBox = document.querySelector('.dashboard-card:nth-child(2)');
    if (!overviewBox) return;
    
    overviewBox.innerHTML = `
        <h2>Financial Overview</h2>
        <p>Your current financial summary will appear here</p>
        <div style="height: 200px; background: #f8f9fa; border-radius: 8px; display: flex; align-items: center; justify-content: center; color: #7f8c8d;">
            Financial Charts Coming Soon
        </div>
    `;
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
        year: 'numeric', 
        month: 'short', 
        day: 'numeric' 
    });
}

function addReportStyles() {
    // Check if styles already exist
    if (document.getElementById('report-styles')) return;
    
    const styleSheet = document.createElement('style');
    styleSheet.id = 'report-styles';
    styleSheet.innerHTML = `
        .report-header {
            display: flex;
            flex-direction: column;
            margin-bottom: 20px;
        }
        
        .report-period {
            color: #7f8c8d;
            margin-top: 5px;
        }
        
        .close-report-btn {
            align-self: flex-start;
            background: #3498db;
            color: white;
            border: none;
            padding: 8px 12px;
            border-radius: 4px;
            cursor: pointer;
            margin-top: 10px;
        }
        
        .close-report-btn:hover {
            background: #2980b9;
        }
        
        .report-content {
            overflow-x: auto;
        }
        
        .report-table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }
        
        .report-table th,
        .report-table td {
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid #e0e0e0;
        }
        
        .report-table th {
            background-color: #f8f9fa;
            font-weight: bold;
        }
        
        .report-table .total-row {
            background-color: #f8f9fa;
        }
        
        .text-success {
            color: #2ecc71;
        }
        
        .text-danger {
            color: #e74c3c;
        }
        
        .no-data {
            text-align: center;
            color: #7f8c8d;
            padding: 20px;
        }
        
        .report-tabs {
            display: flex;
            border-bottom: 1px solid #e0e0e0;
            margin-bottom: 15px;
        }
        
        .tab-btn {
            padding: 10px 15px;
            border: none;
            background: none;
            cursor: pointer;
            opacity: 0.7;
            font-weight: bold;
        }
        
        .tab-btn.active {
            opacity: 1;
            border-bottom: 3px solid #3498db;
        }
        
        .tab-pane {
            display: none;
        }
        
        .tab-pane.active {
            display: block;
        }
        
        .percentage-bar {
            position: relative;
            width: 100%;
            height: 20px;
            background: #f1f1f1;
            border-radius: 10px;
            overflow: hidden;
        }
        
        .percentage-bar .bar {
            position: absolute;
            height: 100%;
            background: #3498db;
            left: 0;
            top: 0;
        }
        
        .percentage-bar span {
            position: relative;
            display: block;
            text-align: center;
            line-height: 20px;
            font-size: 0.8em;
            color: #333;
        }
    `;
    
    document.head.appendChild(styleSheet);
}