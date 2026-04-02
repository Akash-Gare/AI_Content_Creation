const API_BASE = 'http://127.0.0.1:8000';

// State Management
const state = {
    currentView: 'dashboard',
    posts: [],
    stats: { total: 0, scheduled: 0, posted: 0 }
};

// DOM Elements
let viewport, viewTitle, navItems;

// --- Templates ---
const templates = {
    dashboard: () => `
        <div class="stats-grid animate-in">
            <div class="stat-card glass">
                <div class="stat-icon purple"><i data-lucide="send"></i></div>
                <div class="stat-content">
                    <h3>Total Posts</h3>
                    <p class="stat-value">${state.stats.total}</p>
                </div>
            </div>
            <div class="stat-card glass">
                <div class="stat-icon blue"><i data-lucide="clock"></i></div>
                <div class="stat-content">
                    <h3>Scheduled</h3>
                    <p class="stat-value">${state.stats.scheduled}</p>
                </div>
            </div>
            <div class="stat-card glass">
                <div class="stat-icon green"><i data-lucide="check-circle"></i></div>
                <div class="stat-content">
                    <h3>Posted</h3>
                    <p class="stat-value">${state.stats.posted}</p>
                </div>
            </div>
        </div>
        <div class="recent-section animate-in" style="animation-delay: 0.1s">
            <div class="section-header">
                <h2>Recent Requests</h2>
                <button class="btn btn-link" id="refresh-posts">Refresh</button>
            </div>
            <div class="post-grid" id="recent-posts-grid">
                ${renderRecentPostsList()}
            </div>
        </div>
    `,
    create: () => `
        <div class="form-container glass animate-in">
            <h2>Create AI Poster</h2>
            <p class="form-subtitle">Let AI generate your next viral post</p>
            <form id="create-post-form">
                <div class="form-group">
                    <label>Post Topic</label>
                    <input type="text" id="topic" placeholder="e.g. 5 Morning Habits for Success" required>
                </div>
                <div class="form-group">
                    <label>Visual Style</label>
                    <select id="style">
                        <option value="Minimalist">Minimalist</option>
                        <option value="Vibrant">Vibrant</option>
                        <option value="Vintage">Vintage</option>
                        <option value="3D Cartoon">3D Cartoon</option>
                        <option value="Futuristic">Futuristic</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Scheduled Time</label>
                    <input type="datetime-local" id="post_time">
                    <p class="helper-text">Leave blank for AI-optimized smart timing</p>
                </div>
                <button type="submit" class="btn btn-primary btn-large">
                    Generate Poster <i data-lucide="sparkles"></i>
                </button>
            </form>
            <div id="generation-result" class="result-area hidden">
                <div class="divider"></div>
                <div class="result-card glass">
                    <div id="loader" class="loader-container">
                        <div class="spinner"></div>
                        <p>AI is crafting your poster...</p>
                    </div>
                    <div id="result-display" class="hidden">
                        <h3>Your Poster is Ready!</h3>
                        <div class="image-preview">
                            <img id="generated-image" src="" alt="Generated Poster">
                        </div>
                        <div class="result-details">
                            <p id="result-caption"></p>
                            <div class="result-actions">
                                <button class="btn btn-secondary" id="btn-download">Download</button>
                                <button class="btn btn-primary" id="btn-post-now">Post to IG</button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `,
    gallery: () => `
        <div class="section-header animate-in">
            <h2>Generated Creations</h2>
            <button class="btn btn-link" id="refresh-gallery">Refresh</button>
        </div>
        <div class="image-grid animate-in" id="gallery-grid" style="animation-delay: 0.1s">
            ${renderGalleryList()}
        </div>
    `,
    calendar: () => `
        <div class="calendar-list glass animate-in">
            <div class="section-header">
                <h2>Full Posting Schedule</h2>
            </div>
            <div id="calendar-items">
                ${renderCalendarList()}
            </div>
        </div>
    `,
    profile: () => {
        const name  = localStorage.getItem('userName')  || 'Admin User';
        const email = localStorage.getItem('userEmail') || 'admin@aiposter.com';
        const init  = name.charAt(0).toUpperCase();
        return `
        <div class="pv-container animate-in">
            <div class="pv-card glass">
                <div class="pv-header">
                    <div class="pv-avatar-ring">
                        <div class="pv-avatar">${init}</div>
                    </div>
                    <div class="pv-header-text">
                        <h2>${name}</h2>
                        <p class="pv-role"><i data-lucide="shield-check"></i> System Administrator</p>
                        <span class="pv-badge">Pro Plan</span>
                    </div>
                </div>
                <div class="pv-divider"></div>
                <div class="pv-details-grid">
                    <div class="pv-detail">
                        <div class="pv-detail-icon purple"><i data-lucide="mail"></i></div>
                        <div>
                            <label>Email Address</label>
                            <p>${email}</p>
                        </div>
                    </div>
                    <div class="pv-detail">
                        <div class="pv-detail-icon blue"><i data-lucide="calendar-days"></i></div>
                        <div>
                            <label>Member Since</label>
                            <p>March 2026</p>
                        </div>
                    </div>
                    <div class="pv-detail">
                        <div class="pv-detail-icon green"><i data-lucide="instagram"></i></div>
                        <div>
                            <label>Integration</label>
                            <p>Instagram Connected</p>
                        </div>
                    </div>
                    <div class="pv-detail">
                        <div class="pv-detail-icon orange"><i data-lucide="zap"></i></div>
                        <div>
                            <label>AI Credits</label>
                            <p>Unlimited</p>
                        </div>
                    </div>
                </div>
                <div class="pv-actions">
                    <button class="btn btn-primary" onclick="showToast('Edit feature coming soon!')">
                        <i data-lucide="pencil"></i> Edit Profile
                    </button>
                    <button class="btn btn-secondary" onclick="switchView('dashboard')">
                        <i data-lucide="arrow-left"></i> Back to Dashboard
                    </button>
                </div>
            </div>
        </div>
        `;
    }


};

// --- Rendering Logic ---
function switchView(viewName) {
    try {
        state.currentView = viewName;
        
        // Update Sidebar
        if (navItems) {
            navItems.forEach(item => {
                item.classList.toggle('active', item.getAttribute('data-view') === viewName);
            });
        }

        // Update Title
        if (viewTitle) viewTitle.textContent = viewName.charAt(0).toUpperCase() + viewName.slice(1);

        // Render Template
        const template = templates[viewName] || templates.dashboard;
        viewport.innerHTML = template();
        
        // Re-initialize Lucide icons
        if (window.lucide) lucide.createIcons();
        
        // Bind View-Specific Events
        bindViewEvents(viewName);
    } catch (e) {
        console.error('Error switching view:', e);
    }
}

function bindViewEvents(viewName) {
    if (viewName === 'dashboard') {
        document.getElementById('refresh-posts')?.addEventListener('click', () => fetchData());
    } else if (viewName === 'create') {
        document.getElementById('create-post-form')?.addEventListener('submit', handleCreateSubmit);
    } else if (viewName === 'gallery') {
        document.getElementById('refresh-gallery')?.addEventListener('click', () => fetchData());
    }
}

// --- Data & Helpers ---
async function fetchData() {
    try {
        const response = await fetch(`${API_BASE}/calendar`);
        const data = await response.json();
        state.posts = data.schedule;
        updateStats();
        switchView(state.currentView); // Re-render current view with new data
    } catch (e) {
        showToast('Error fetching data', true);
    }
}

function updateStats() {
    state.stats.total = state.posts.length;
    state.stats.scheduled = state.posts.filter(p => !p.posted_at && p.status !== 'Failed').length;
    state.stats.posted = state.posts.filter(p => p.status === 'Posted').length;
}

function renderRecentPostsList() {
    const latest = [...state.posts].sort((a, b) => b.id - a.id).slice(0, 6);
    if (latest.length === 0) return '<p class="meta">No posts yet.</p>';
    
    return latest.map(post => `
        <div class="post-card glass">
            <div class="post-card-header">
                <span class="status-badge status-${post.status.toLowerCase().replace(' ', '-')}">${post.status}</span>
                <span class="meta">ID: ${post.id}</span>
            </div>
            <h4>${post.topic}</h4>
            <div class="meta"><i data-lucide="clock"></i> ${new Date(post.post_time).toLocaleString()}</div>
        </div>
    `).join('');
}

function renderCalendarList() {
    if (state.posts.length === 0) return '<p style="padding: 1rem; color: var(--text-muted);">No posts scheduled.</p>';
    
    return state.posts.map(post => `
        <div style="padding: 1rem; border-bottom: 1px solid var(--glass-border); display: flex; justify-content: space-between; align-items: center;">
            <div>
                <strong>${post.topic}</strong>
                <p style="font-size: 0.8rem; color: var(--text-muted);">${new Date(post.post_time).toLocaleString()}</p>
            </div>
            <span class="status-badge status-${post.status.toLowerCase().replace(' ', '-')}">${post.status}</span>
        </div>
    `).join('');
}

function renderGalleryList() {
    const generated = state.posts.filter(p => p.image_ready === true || p.status === 'Generated');
    if (generated.length === 0) return '<p style="grid-column: 1/-1; text-align: center; padding: 2rem; color: var(--text-muted);">No images generated yet.</p>';
    
    return generated.map(post => {
        const url = getImageUrlById(post.id);
        return `
            <div class="gallery-item glass" onclick="openPreview(${post.id})">
                <img src="${url}" alt="${post.topic}" onerror="this.src='https://placehold.co/400x400/1e293b/f8fafc?text=Error'">
                <div class="overlay"><span>${post.topic}</span></div>
            </div>
        `;
    }).join('');
}

function openPreview(id) {
    const post = state.posts.find(p => p.id === id);
    if (!post) return;
    
    showToast(`Viewing: ${post.topic}`);
    // Open image in new tab as a simple preview/lightbox
    const url = getImageUrlById(id);
    if (url) window.open(url, '_blank');
}

function getImageUrlById(id) {
    const post = state.posts.find(p => p.id === id);
    if (!post || !post.id) return '';
    
    // Check if the calendar response already has the full/relative path
    // Based on app/main.py, it doesn't currently return image_url in /calendar.
    // However, I can fetch it from the /status endpoint or update /calendar.
    // For now, I'll update /calendar in main.py to include image_url.
    return getImageUrl(post.image_url);
}

// --- Image URL Helper (Fixed) ---
function getImageUrl(rawPath) {
    if (!rawPath) return '';
    let filename = rawPath.split(/[/\\]/).pop();
    return `${API_BASE}/images/${filename}`;
}

// --- Create Flow ---
async function handleCreateSubmit(e) {
    e.preventDefault();
    const topic = document.getElementById('topic').value;
    const style = document.getElementById('style').value;
    const postTimeInput = document.getElementById('post_time').value;
    const post_time = postTimeInput ? new Date(postTimeInput).toISOString() : new Date().toISOString();

    const resultArea = document.getElementById('generation-result');
    const loader = document.getElementById('loader');
    resultArea.classList.remove('hidden');
    loader.classList.remove('hidden');

    try {
        const response = await fetch(`${API_BASE}/request-poster`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ topic, style, post_time })
        });
        const result = await response.json();
        if (result.request_id) {
            showToast('AI is generating...');
            pollForStatus(result.request_id);
        }
    } catch (e) {
        showToast('Error starting generation', true);
    }
}

async function pollForStatus(requestId) {
    const interval = setInterval(async () => {
        try {
            const res = await fetch(`${API_BASE}/status/${requestId}`);
            const data = await res.json();
            if (['image_ready', 'Generated', 'Posted'].includes(data.status)) {
                clearInterval(interval);
                showLiveResult(data);
            } else if (data.status === 'Failed') {
                clearInterval(interval);
                showToast('Generation failed', true);
            }
        } catch (e) {}
    }, 5000);
}

function showLiveResult(data) {
    const loader = document.getElementById('loader');
    const display = document.getElementById('result-display');
    const img = document.getElementById('generated-image');
    const caption = document.getElementById('result-caption');
    
    loader.classList.add('hidden');
    display.classList.remove('hidden');
    
    const imgPath = getImageUrl(data.image_url);
    img.src = imgPath;
    caption.textContent = data.title || 'Ready to post!';
    
    document.getElementById('btn-download').onclick = () => {
        const link = document.createElement('a');
        link.href = imgPath;
        link.download = `ai_poster_${data.id}.png`;
        link.click();
    };

    document.getElementById('btn-post-now').onclick = () => {
        fetch(`${API_BASE}/post-to-instagram/${data.id}`, { method: 'POST' });
        showToast('Posting started!');
    };
}

// --- Initialization & Global Events ---
document.addEventListener('DOMContentLoaded', () => {
    // 0. Check Authentication
    if (localStorage.getItem('isLoggedIn') !== 'true' && !window.location.pathname.includes('login.html')) {
        window.location.href = 'login.html';
        return;
    }

    viewport = document.getElementById('main-viewport');
    viewTitle = document.getElementById('view-title');
    navItems = document.querySelectorAll('.nav-item');

    // ── Profile System ──────────────────────────────────────────
    const userName  = localStorage.getItem('userName')  || 'Admin User';
    const userEmail = localStorage.getItem('userEmail') || 'admin@aiposter.com';
    const initial   = userName.charAt(0).toUpperCase();

    // Hydrate all avatar/name/email elements
    ['profile-avatar', 'dropdown-avatar'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.textContent = initial;
    });
    const nameHeader = document.getElementById('profile-name-header');
    if (nameHeader) nameHeader.textContent = userName;
    const dropdownName = document.getElementById('dropdown-user-name');
    if (dropdownName) dropdownName.textContent = userName;
    const dropdownEmail = document.getElementById('dropdown-user-email');
    if (dropdownEmail) dropdownEmail.textContent = userEmail;

    // Dropdown toggle
    const profileBtn      = document.getElementById('profile-btn');
    const profileDropdown = document.getElementById('profile-dropdown');
    const profileChevron  = document.getElementById('profile-chevron');

    function openDropdown() {
        profileDropdown.classList.add('open');
        profileChevron.style.transform = 'rotate(180deg)';
    }
    function closeDropdown() {
        profileDropdown.classList.remove('open');
        profileChevron.style.transform = 'rotate(0deg)';
    }

    if (profileBtn && profileDropdown) {
        profileBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            profileDropdown.classList.contains('open') ? closeDropdown() : openDropdown();
        });
        document.addEventListener('click', closeDropdown);
        profileDropdown.addEventListener('click', (e) => e.stopPropagation());
    }

    // View Profile
    const viewProfileBtn = document.getElementById('view-profile-btn');
    if (viewProfileBtn) {
        viewProfileBtn.addEventListener('click', () => {
            closeDropdown();
            switchView('profile');
        });
    }

    // Logout – show confirmation modal
    const logoutBtn    = document.getElementById('logout-btn');
    const logoutModal  = document.getElementById('logout-modal');
    const modalCancel  = document.getElementById('modal-cancel');
    const modalConfirm = document.getElementById('modal-confirm');

    function openModal()  { logoutModal.classList.remove('hidden'); logoutModal.classList.add('open'); }
    function closeModal() { logoutModal.classList.remove('open'); setTimeout(() => logoutModal.classList.add('hidden'), 250); }

    if (logoutBtn) {
        logoutBtn.addEventListener('click', () => {
            closeDropdown();
            openModal();
        });
    }
    if (modalCancel)  modalCancel.addEventListener('click', closeModal);
    if (logoutModal)  logoutModal.addEventListener('click', (e) => { if (e.target === logoutModal) closeModal(); });
    if (modalConfirm) {
        modalConfirm.addEventListener('click', () => {
            closeModal();
            localStorage.removeItem('isLoggedIn');
            localStorage.removeItem('userEmail');
            localStorage.removeItem('userName');
            showToast('Logged out successfully', false);
            setTimeout(() => { window.location.href = 'login.html'; }, 1200);
        });
    }

    // ── Navigation Events ───────────────────────────────────────
    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const view = item.getAttribute('data-view');
            if (view === 'settings') return showToast('Settings coming soon!');
            switchView(view);
        });
    });

    const createBtnHeader = document.getElementById('btn-create-header');
    if (createBtnHeader) createBtnHeader.onclick = () => switchView('create');

    fetchData().then(() => {
        if (!state.currentView) switchView('dashboard');
        else switchView(state.currentView);
    });

    setInterval(fetchData, 30000);
});



function showToast(message, isError = false) {
    const container = document.getElementById('toast-container') || document.body;
    const toast = document.createElement('div');
    toast.className = `toast${isError ? ' error' : ''}`;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(30px)';
        toast.style.transition = 'all 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

