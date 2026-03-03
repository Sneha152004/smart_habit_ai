const API_URL = window.location.origin.includes('localhost') || window.location.origin.includes('127.0.0.1') 
    ? (window.location.origin.includes('5000') ? '/api' : 'http://127.0.0.1:5000/api') 
    : window.location.origin + '/api';
let token = localStorage.getItem('token');
let selectedMood = 3;
let currentTimerSeconds = 0;
let timerInterval = null;
let habitCompletedMap = {}; // Use a map to track completion per habit

const MOTIVATIONAL_MESSAGES = {
    on_track: [
        "You’re showing up consistently, and that’s what builds real transformation. Keep stacking these small wins — they are shaping the person you’re becoming.",
        "Your habits are aligned with your goals right now. Stay steady, stay disciplined, and don’t let comfort slow your momentum.",
        "You’re in control. Every healthy choice you’re making today is compounding into long-term success.",
        "Consistency beats motivation every time — and right now, you’re consistent. Protect this streak.",
        "You’re not relying on luck. You’re relying on discipline. That’s powerful.",
        "The version of you that you want to become You’re already acting like them."
    ],
    moderate: [
        "You’re not off track — but you’re drifting slightly. A small correction today can prevent a bigger struggle tomorrow.",
        "This is your reminder to refocus. You don’t need perfection — just effort.",
        "Momentum can be lost quietly. Protect it before it slips further.",
        "You’ve worked too hard to let small distractions undo your progress.",
        "Today is a decision point. Choose discipline over delay.",
        "You don’t need to restart. You just need to realign.",
        "Progress isn’t about never slipping — it’s about noticing early and adjusting."
    ],
    high_risk: [
        "You’re entering dangerous territory. This is where habits break — or strengthen. Choose wisely.",
        "Your goals don’t disappear when effort does. Step back up.",
        "Discipline feels heavy now, but regret feels heavier later.",
        "You’re capable of more than this. Act like it.",
        "The difference between success and setback is one decisive action.",
        "This is the moment most people quit. Be the one who doesn’t.",
        "Future you is either proud or disappointed. Decide which one you’re creating.",
        "You don’t need motivation. You need commitment."
    ],
    very_high_risk: [
        "Right now, your habits are moving you away from the life you want. Pause. Reset. Take control.",
        "This isn’t failure — this is feedback. Use it.",
        "You can either continue this pattern or interrupt it right now. One strong decision changes everything.",
        "No one is coming to fix this for you. You are responsible. And you are capable.",
        "Comfort is pulling you down. Discipline will lift you up.",
        "You are not stuck. You are undisciplined right now. And that can change immediately.",
        "The longer you wait, the harder it becomes. Act now.",
        "This is your wake-up signal. Don’t ignore it.",
        "Your goals require effort. The time to recommit is now."
    ],
    reset_mode: "Stop. Breathe. This is not the end of your progress — but it can become the start of decline if ignored. Reset your habits today. Even one disciplined action right now shifts your direction.",
    habit_personalization: {
        sleep: "Your recovery is suffering.",
        study: "Your focus is slipping.",
        workout: "Energy follows movement.",
        journal: "Your reflection is missing.",
        reading: "Your growth is slowing.",
        mood: "Your mental clarity is clouded."
    }
};

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
    if (viewId === 'history-list') { loadHistory(); }
}

async function loadHistory() {
    const res = await fetch(`${API_URL}/history`, {
        headers: { 'Authorization': `Bearer ${token}` }
    });
    if (res.ok) {
        const history = await res.json();
        const tableBody = document.getElementById('history-table-body');
        tableBody.innerHTML = '';
        
        // Group by date to ensure "day-wise" view (latest entry per day)
        const dayWise = {};
        history.forEach(entry => {
            if (!dayWise[entry.date]) {
                dayWise[entry.date] = entry;
            }
        });

        const sortedDates = Object.keys(dayWise).sort((a, b) => new Date(b) - new Date(a));
        
        const moodIcons = { 1: "😢", 2: "😕", 3: "😐", 4: "😊", 5: "🤩" };

        sortedDates.forEach(date => {
            const entry = dayWise[date];
            const prob = entry.p_slip_prob || 0;
            const slipPercentage = Math.round(prob * 100);
            
            // Re-calculate category if not present in history entry
            let category = "On Track";
            let colorClass = "text-primary";
            if (slipPercentage > 80) { category = "Critical"; colorClass = "text-danger"; }
            else if (slipPercentage > 60) { category = "High Risk"; colorClass = "text-warning"; }
            else if (slipPercentage > 30) { category = "Moderate"; colorClass = "text-warning"; }

            const row = `
                <tr>
                    <td>${entry.date}</td>
                    <td class="${colorClass}">${slipPercentage}%</td>
                    <td>${Math.round(entry.motivation_score)}</td>
                    <td>${moodIcons[entry.mood] || "😐"}</td>
                    <td style="text-transform: capitalize;">${entry.weakest_habit}</td>
                    <td><span class="badge" style="background: ${colorClass === 'text-danger' ? 'var(--danger)' : (colorClass === 'text-warning' ? 'var(--warning)' : 'var(--primary)')}">${category}</span></td>
                </tr>
            `;
            tableBody.innerHTML += row;
        });
    }
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
    const slipChance = data.slip_percentage !== undefined ? data.slip_percentage : Math.round(prob * 100);
    const slipEl = document.getElementById('p-slip-prob');
    slipEl.innerText = `${slipChance}%`;
    
    // Task 2: Use Category from Backend if available
    let statusText = data.category || "Stable";
    let statusMsg = "You're on track, but stay consistent. Small lapses can increase risk.";
    let statusColor = "var(--primary)"; // Teal/Blue

    // Map categories to colors
    if (statusText === "On Track") {
        statusMsg = "You’re doing great! Very low risk of slipping. Keep the momentum going.";
        statusColor = "var(--primary)";
    } else if (statusText === "Moderate Risk") {
        const lowHabit = data.weakest_habit ? data.weakest_habit : "your routine";
        statusMsg = `Warning: Your consistency is dropping. Try to improve ${lowHabit} today.`;
        statusColor = "var(--warning)";
    } else if (statusText === "High Risk") {
        statusMsg = "High risk of slipping! Take corrective action today. Focus on your weakest habit.";
        statusColor = "#f59e0b"; // Orange
    } else if (statusText === "Very High Risk") {
        statusText = "Critical";
        statusMsg = "Critical slip risk! Immediate action needed. Reset your routine today.";
        statusColor = "var(--danger)";
    }

    const riskBadge = document.getElementById('risk-badge');
    riskBadge.innerText = statusText;
    riskBadge.style.background = statusColor;
    
    // Dynamic Motivation Selection
    const momentumCard = document.getElementById('ai-momentum-card');
    const motivationEl = document.getElementById('dynamic-motivation');
    const personalEl = document.getElementById('habit-personal-msg');
    
    let pool = [];
    momentumCard.classList.remove('reset-mode');

    if (slipChance > 90) {
        motivationEl.innerText = MOTIVATIONAL_MESSAGES.reset_mode;
        momentumCard.classList.add('reset-mode');
    } else {
        if (slipChance <= 30) pool = MOTIVATIONAL_MESSAGES.on_track;
        else if (slipChance <= 60) pool = MOTIVATIONAL_MESSAGES.moderate;
        else if (slipChance <= 80) pool = MOTIVATIONAL_MESSAGES.high_risk;
        else pool = MOTIVATIONAL_MESSAGES.very_high_risk;

        const randomMsg = pool[Math.floor(Math.random() * pool.length)];
        motivationEl.innerText = randomMsg;
    }

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
    const mStatus = (score < 40 ? 'low' : (score < 70 ? 'moderate' : 'high'));
    gauge.className = 'circular-progress ' + mStatus;
    scoreEl.className = 'status-' + mStatus; // New class for number color
    
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
                    <p>${rec.text}</p>
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
    
    // Dynamic classes for Burnout card
    const burnoutCard = document.querySelector('.burnout-risk');
    if (burnoutCard) {
        burnoutCard.classList.remove('status-good', 'status-warning', 'status-danger');
        if (burnoutValue < 0.3) burnoutCard.classList.add('status-good');
        else if (burnoutValue < 0.6) burnoutCard.classList.add('status-warning');
        else burnoutCard.classList.add('status-danger');
    }

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

    // Dynamic classes for Emotional State card
    const moodCard = document.querySelector('.emotional-state');
    if (moodCard) {
        moodCard.classList.remove('status-good', 'status-warning', 'status-danger');
        if (isBadDay || moodVal <= 2) moodCard.classList.add('status-danger');
        else if (moodVal === 3) moodCard.classList.add('status-warning');
        else moodCard.classList.add('status-good');
    }
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
