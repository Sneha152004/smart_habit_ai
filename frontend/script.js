const API_URL = window.location.origin.includes('127.0.0.1:5000') ? '/api' : 'http://127.0.0.1:5000/api';
let token = localStorage.getItem('token');
let selectedMood = 3;
let currentTimerSeconds = 0;
let timerInterval = null;
let habitCompletedMap = {}; // Use a map to track completion per habit

// Initial UI Check
if (token) { showMain(); }

function toggleAuth() {
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');
    if (loginForm.style.display === 'none') {
        loginForm.style.display = 'block';
        registerForm.style.display = 'none';
    } else {
        loginForm.style.display = 'none';
        registerForm.style.display = 'block';
    }
}

async function register() {
    const username = document.getElementById('reg-username').value;
    const password = document.getElementById('reg-password').value;
    if (!username || !password) return alert("Please fill all fields");
    try {
        const res = await fetch(`${API_URL}/auth/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        if (res.ok) {
            alert('Registration successful! Please login.');
            toggleAuth();
        } else {
            const data = await res.json();
            alert("Error: " + (data.msg || "Registration failed"));
        }
    } catch (e) { alert("Server connection error."); }
}

async function login() {
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    try {
        const res = await fetch(`${API_URL}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        if (res.ok) {
            const data = await res.json();
            token = data.access_token;
            localStorage.setItem('token', token);
            localStorage.setItem('username', username);
            showMain();
        } else { alert('Login failed. Check username/password.'); }
    } catch (e) { alert("Server connection error."); }
}

function toggleTheme() {
    const body = document.body;
    const isLight = body.classList.toggle('light-theme');
    const themeText = document.getElementById('theme-text');
    const themeIcon = document.querySelector('.theme-toggle i');

    if (isLight) {
        themeText.innerText = "Light Mode";
        themeIcon.className = "fas fa-sun";
    } else {
        themeText.innerText = "Dark Mode";
        themeIcon.className = "fas fa-moon";
    }
}

function showView(viewId) {
    document.querySelectorAll('.view').forEach(v => v.style.display = 'none');
    document.getElementById(`${viewId}-view`).style.display = 'block';
    document.querySelectorAll('.nav-item').forEach(nav => nav.classList.remove('active'));
    if (event && event.currentTarget) {
        event.currentTarget.classList.add('active');
    } else {
        const nav = document.querySelector(`.nav-item[onclick*="${viewId}"]`);
        if (nav) nav.classList.add('active');
    }
    if (viewId === 'breakdown') { loadBreakdown(); }
}

function updateSliderVal(id, val) {
    document.getElementById(`${id}-val`).innerText = val;
}

function selectMood(val) {
    selectedMood = val;
    document.querySelectorAll('.mood-opt').forEach((opt, idx) => {
        opt.classList.toggle('active', idx + 1 === val);
    });
}

function logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('username');
    location.reload();
}

function showMain() {
    document.getElementById('auth-container').style.display = 'none';
    document.getElementById('main-container').style.display = 'flex';
    const username = localStorage.getItem('username') || "User";
    document.getElementById('display-username').innerText = username;
    document.getElementById('welcome-msg').innerText = `Good Evening, ${username}`;
    loadDashboard();
}

async function loadDashboard() {
    const res = await fetch(`${API_URL}/history`, {
        headers: { 'Authorization': `Bearer ${token}` }
    });
    if (res.ok) {
        const history = await res.json();
        if (history.length > 0) { 
            // Re-fetch insights if we don't have recommendations in history
            // Actually, let's just use the displayInsights which handles the rendering
            displayInsights(history[0]); 
        }
    }
}

async function submitLog() {
    const data = {
        sleep_hours: parseFloat(document.getElementById('sleep').value),
        study_hours: parseFloat(document.getElementById('study').value),
        workout_minutes: parseFloat(document.getElementById('workout').value),
        journal_minutes: parseFloat(document.getElementById('journal').value),
        reading_minutes: parseFloat(document.getElementById('reading').value),
        mood: selectedMood
    };
    try {
        const res = await fetch(`${API_URL}/log`, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(data)
        });
        if (res.ok) {
            const insights = await res.json();
            habitCompletedMap = {}; // Reset on new entry
            displayInsights(insights);
            showView('dashboard');
        }
    } catch (e) { alert("Error connecting to server."); }
}

function displayInsights(data) {
    if (!data) return;
    const isBadDay = data.bad_day || false;
    const badge = document.getElementById('gentle-mode-badge');
    if (badge) badge.style.display = isBadDay ? 'flex' : 'none';
    const welcome = document.getElementById('welcome-msg');
    const username = localStorage.getItem('username') || "Alex";
    if (welcome) welcome.innerText = isBadDay ? `Deep Breath, ${username}.` : `Good Evening, ${username}`;
    
    // Slip Chance
    const prob = data.p_slip_prob !== undefined ? data.p_slip_prob : 0;
    const slipChance = Math.round(prob * 100);
    const slipEl = document.getElementById('p-slip-prob');
    slipEl.innerText = `${slipChance}%`;
    
    // Custom Slip Status and Message Logic
    let statusText = "Stable";
    let statusMsg = "You're on track, but stay consistent. Small lapses can increase risk.";
    let statusColor = "var(--primary)"; // Teal/Blue

    if (slipChance <= 20) {
        statusText = "Very Safe";
        statusMsg = "You’re doing great! Very low risk of slipping. Keep the momentum going.";
        statusColor = "var(--primary)"; // Green/Teal
    } else if (slipChance <= 40) {
        statusText = "Stable";
        statusMsg = "You’re on track, but stay consistent. Small lapses can increase risk.";
        statusColor = "var(--primary)"; // Green/Teal
    } else if (slipChance <= 60) {
        statusText = "Moderate Risk";
        const lowHabit = data.weakest_habit ? data.weakest_habit : "your routine";
        statusMsg = `Warning: Your consistency is dropping. Try to improve ${lowHabit} today.`;
        statusColor = "var(--warning)"; // Yellow
    } else if (slipChance <= 80) {
        statusText = "High Risk";
        statusMsg = "High risk of slipping! Take corrective action today. Focus on your weakest habit.";
        statusColor = "var(--warning)"; // Orange (mapped to warning)
    } else {
        statusText = "Critical";
        statusMsg = "Critical slip risk! Immediate action needed. Reset your routine today.";
        statusColor = "var(--danger)"; // Red
    }

    const riskBadge = document.getElementById('risk-badge');
    riskBadge.innerText = statusText;
    riskBadge.style.background = statusColor;
    
    const msgEl = document.getElementById('consistency-msg');
    if (msgEl) msgEl.innerText = statusMsg;

    // Slip Color Logic (Bad thing: High = Danger)
    slipEl.className = prob > 0.6 ? 'text-danger' : (prob > 0.3 ? 'text-warning' : 'text-primary');

    // Motivation Gauge
    const score = Math.round(data.motivation_score || 0);
    const scoreEl = document.getElementById('motivation-score');
    scoreEl.innerText = score;
    const gauge = document.querySelector('.circular-progress');
    gauge.style.setProperty('--progress', score);
    
    // Motivation Color Logic (Good thing: Low = Danger)
    gauge.className = 'circular-progress ' + (score < 40 ? 'low' : (score < 70 ? 'moderate' : 'high'));
    
    const adjCard = document.getElementById('daily-adj-card');
    const restCard = document.getElementById('rest-recover-card');
    if (adjCard) adjCard.style.display = isBadDay ? 'none' : 'flex';
    if (restCard) restCard.style.display = isBadDay ? 'flex' : 'none';
    const diffAdj = document.getElementById('difficulty-adjustment');
    if (diffAdj) diffAdj.innerText = data.difficulty_adjustment || "Maintain current level.";
    
    // Recommendations Rendering
    const recList = document.getElementById('rec-list');
    recList.innerHTML = ''; 
    
    const recs = data.recommendations || [{
        habit: data.weakest_habit || "STUDY",
        text: data.recommendation || "Maintain your routine for better insights.",
        duration: data.timer_seconds || 0
    }];

    recs.forEach(rec => {
        const habitKey = rec.habit.toUpperCase();
        const isCompleted = habitCompletedMap[habitKey] || false;
        const tickHtml = isCompleted ? '<i class="fas fa-check-circle text-primary" style="margin-left: auto; font-size: 1.5rem;"></i>' : '';
        const timerBtnHtml = !isCompleted && rec.duration > 0 ? `<button class="timer-btn" onclick="openTimerModal(${rec.duration}, '${habitKey}')"><i class="fas fa-play-circle"></i></button>` : tickHtml;

        recList.innerHTML += `
            <div class="rec-item">
                <div class="item-icon"><i class="fas fa-bolt"></i></div>
                <div class="item-content">
                    <span class="label">${habitKey}</span>
                    <p>"${rec.text}"</p>
                </div>
                ${timerBtnHtml}
            </div>
        `;
    });

    // Burnout
    const burnoutValue = data.burnout_risk !== undefined ? data.burnout_risk : 0;
    const burnout = Math.round(burnoutValue * 100);
    const burnoutEl = document.getElementById('burnout-risk-val');
    burnoutEl.innerText = `${burnout}%`;
    const burnoutBar = document.getElementById('burnout-bar');
    burnoutBar.style.width = `${burnout}%`;
    
    // Burnout Color Logic (Bad thing: High = Danger)
    const burnoutClass = burnoutValue > 0.6 ? 'low' : (burnoutValue > 0.3 ? 'moderate' : 'high'); // Inverted class naming for bar color (low=red)
    burnoutBar.className = 'fill ' + (burnoutValue > 0.6 ? 'low' : (burnoutValue > 0.3 ? 'moderate' : 'high'));
    burnoutEl.className = burnoutValue > 0.6 ? 'text-danger' : (burnoutValue > 0.3 ? 'text-warning' : 'text-primary');

    const icons = { 1: "😢", 2: "😕", 3: "😐", 4: "😊", 5: "🤩" };
    const moodStatusMap = {
        1: "Feeling Down",
        2: "Low Energy",
        3: "Stable & Balanced",
        4: "Feeling Good",
        5: "Ready to Conquer"
    };
    const moodVal = data.mood || 3;
    document.getElementById('mood-icon').innerText = isBadDay ? "🌧️" : (icons[moodVal] || "✨");
    document.getElementById('mood-status').innerText = isBadDay ? "Low Energy Mode" : (moodStatusMap[moodVal] || "Balanced & Ready.");
}

async function loadBreakdown() {
    const res = await fetch(`${API_URL}/history`, {
        headers: { 'Authorization': `Bearer ${token}` }
    });
    if (res.ok) {
        const history = await res.json();
        if (history.length > 0) {
            const last = history[0];
            const norms = last.norms;
            if (norms) {
                const habits = ['sleep', 'study', 'workout', 'journal', 'reading', 'mood'];
                habits.forEach(h => {
                    const val = norms[h] || 0;
                    const bar = document.getElementById(`bar-${h}`);
                    
                    // Cap width at 100% and show a minimum of 5% for visibility
                    const percentage = Math.round(val * 100);
                    const displayWidth = val > 0 ? Math.min(100, Math.max(5, percentage)) : 0;
                    bar.style.width = `${displayWidth}%`;
                    
                    // Clear and re-apply color classes
                    bar.classList.remove('low', 'moderate', 'high');
                    if (val < 0.4) {
                        bar.classList.add('low');
                    } else if (val < 0.7) {
                        bar.classList.add('moderate');
                    } else {
                        bar.classList.add('high');
                    }
                });
            }
        }
    }
}

let activeHabit = ""; // Track which habit timer is running

function openTimerModal(seconds, habit) {
    if (seconds <= 0) return;
    currentTimerSeconds = seconds;
    activeHabit = habit;
    const modal = document.getElementById('timer-modal');
    document.getElementById('timer-habit-name').innerText = habit.toUpperCase() + " SPRINT";
    document.getElementById('timer-start-btn').style.display = 'inline-block';
    modal.style.display = 'flex';
    updateTimerDisplay();
}

function runTimer() {
    document.getElementById('timer-start-btn').style.display = 'none';
    timerInterval = setInterval(() => {
        currentTimerSeconds--;
        updateTimerDisplay();
        if (currentTimerSeconds <= 0) {
            clearInterval(timerInterval);
            habitCompletedMap[activeHabit] = true;
            document.getElementById('timer-modal').style.display = 'none';
            
            // Fun Confetti Effect
            confetti({
                particleCount: 150,
                spread: 70,
                origin: { y: 0.6 },
                colors: ['#2dd4bf', '#6366f1', '#f59e0b']
            });

            alert("Session complete! Reward earned.");
            // Refresh dashboard locally to show tick
            loadDashboard(); 
        }
    }, 1000);
}

function updateTimerDisplay() {
    const mins = Math.floor(currentTimerSeconds / 60);
    const secs = currentTimerSeconds % 60;
    document.getElementById('countdown-display').innerText = `${mins}:${secs < 10 ? '0' : ''}${secs}`;
}

function stopTimer() {
    clearInterval(timerInterval);
    document.getElementById('timer-modal').style.display = 'none';
}
