let token = localStorage.getItem('booking_token') || '';
let currentUser = null;
let services = [];
let therapists = [];

const authSection = document.getElementById('authSection');
const appSection = document.getElementById('appSection');
const logoutButton = document.getElementById('logoutButton');
const message = document.getElementById('message');

function escapeHtml(value) {
    return String(value)
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll("'", '&#039;');
}

function showMessage(text) {
    message.textContent = text;
    message.classList.remove('hidden');
    setTimeout(() => message.classList.add('hidden'), 3500);
}

async function api(path, options = {}) {
    const headers = {'Content-Type': 'application/json', ...(options.headers || {})};

    if (token) {
        headers.Authorization = `Bearer ${token}`;
    }

    const response = await fetch(path, {...options, headers});
    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
        throw new Error(data.detail || 'Request failed');
    }

    return data;
}

function saveLogin(data) {
    token = data.token;
    currentUser = data.user;
    localStorage.setItem('booking_token', token);
    showDashboard();
}

function showDashboard() {
    authSection.classList.add('hidden');
    appSection.classList.remove('hidden');
    logoutButton.classList.remove('hidden');
    document.getElementById('welcomeText').textContent = `Welcome, ${currentUser.name}`;
    loadDashboard();
}

function showLogin() {
    authSection.classList.remove('hidden');
    appSection.classList.add('hidden');
    logoutButton.classList.add('hidden');
}

async function loadUser() {
    if (!token) {
        showLogin();
        return;
    }

    try {
        currentUser = await api('/api/auth/me');
        showDashboard();
    } catch (error) {
        token = '';
        localStorage.removeItem('booking_token');
        showLogin();
    }
}

async function loadDashboard() {
    try {
        [services, therapists] = await Promise.all([
            api('/api/services'),
            api('/api/therapists')
        ]);

        renderServices();
        renderTherapists();
        fillBookingSelects();

        const bookingPanel = document.getElementById('bookingForm').closest('.panel');
        const availabilityPanel = document.getElementById('availabilityFormPanel');

        bookingPanel.classList.toggle('hidden', currentUser.role !== 'client');
        availabilityPanel.classList.toggle('hidden', currentUser.role !== 'therapist');

        await Promise.all([loadAvailability(), loadBookings()]);
    } catch (error) {
        showMessage(error.message);
    }
}

function renderServices() {
    const container = document.getElementById('servicesList');
    container.innerHTML = services.map(service => `
        <article class="card">
            <h3>${escapeHtml(service.name)}</h3>
            <p>${escapeHtml(service.description)}</p>
            <p>${service.duration_minutes} minutes · €${(service.price_cents / 100).toFixed(2)}</p>
        </article>
    `).join('');
}

function renderTherapists() {
    const container = document.getElementById('therapistsList');
    container.innerHTML = therapists.map(therapist => `
        <article class="card">
            <h3>${escapeHtml(therapist.name)}</h3>
            <p>${escapeHtml(therapist.bio)}</p>
            <p>${therapist.service_ids.length} services</p>
        </article>
    `).join('');
}

function fillBookingSelects() {
    const therapistSelect = document.getElementById('bookingTherapist');
    const serviceSelect = document.getElementById('bookingService');

    therapistSelect.innerHTML = therapists.map(item =>
        `<option value="${item.id}">${escapeHtml(item.name)}</option>`
    ).join('');

    serviceSelect.innerHTML = services.map(item =>
        `<option value="${item.id}">${escapeHtml(item.name)}</option>`
    ).join('');
}

async function loadAvailability() {
    const availability = await api('/api/availability');
    const container = document.getElementById('availabilityList');

    if (availability.length === 0) {
        container.innerHTML = '<p>No available slots.</p>';
        return;
    }

    container.innerHTML = availability.map(slot => `
        <article class="card">
            <h3>${new Date(slot.start_time).toLocaleString()}</h3>
            <p>Until ${new Date(slot.end_time).toLocaleString()}</p>
            ${currentUser.role === 'client' ? `
                <button data-start="${slot.start_time}" data-therapist="${slot.therapist_id}" class="choose-slot">Choose this slot</button>
            ` : ''}
        </article>
    `).join('');

    document.querySelectorAll('.choose-slot').forEach(button => {
        button.addEventListener('click', () => {
            document.getElementById('bookingTherapist').value = button.dataset.therapist;
            document.getElementById('bookingStart').value = button.dataset.start.slice(0, 16);
            document.getElementById('bookingStart').scrollIntoView({behavior: 'smooth'});
        });
    });
}

function bookingActions(booking) {
    if (currentUser.role === 'client' && ['pending', 'confirmed'].includes(booking.status)) {
        return `<button class="booking-action" data-id="${booking.id}" data-status="cancelled">Cancel</button>`;
    }

    if (currentUser.role === 'therapist' && booking.status === 'pending') {
        return `
            <div class="action-row">
                <button class="booking-action" data-id="${booking.id}" data-status="confirmed">Confirm</button>
                <button class="booking-action secondary" data-id="${booking.id}" data-status="rejected">Reject</button>
            </div>
        `;
    }

    return '';
}

async function loadBookings() {
    const bookings = await api('/api/bookings');
    const container = document.getElementById('bookingsList');

    if (bookings.length === 0) {
        container.innerHTML = '<p>No bookings yet.</p>';
        return;
    }

    container.innerHTML = bookings.map(booking => `
        <article class="card">
            <h3>${escapeHtml(booking.service_name)}</h3>
            <p>${escapeHtml(booking.therapist_name)} · ${new Date(booking.start_time).toLocaleString()}</p>
            <p>${escapeHtml(booking.note || 'No note')}</p>
            <span class="status">${escapeHtml(booking.status)}</span>
            ${bookingActions(booking)}
        </article>
    `).join('');

    document.querySelectorAll('.booking-action').forEach(button => {
        button.addEventListener('click', async () => {
            try {
                await api(`/api/bookings/${button.dataset.id}/status`, {
                    method: 'PATCH',
                    body: JSON.stringify({status: button.dataset.status})
                });
                showMessage('Booking updated');
                await loadBookings();
            } catch (error) {
                showMessage(error.message);
            }
        });
    });
}

document.getElementById('loginForm').addEventListener('submit', async event => {
    event.preventDefault();

    try {
        const data = await api('/api/auth/login', {
            method: 'POST',
            body: JSON.stringify({
                email: document.getElementById('loginEmail').value,
                password: document.getElementById('loginPassword').value
            })
        });
        saveLogin(data);
    } catch (error) {
        showMessage(error.message);
    }
});

document.getElementById('registerForm').addEventListener('submit', async event => {
    event.preventDefault();

    try {
        const data = await api('/api/auth/register', {
            method: 'POST',
            body: JSON.stringify({
                name: document.getElementById('registerName').value,
                email: document.getElementById('registerEmail').value,
                password: document.getElementById('registerPassword').value
            })
        });
        saveLogin(data);
    } catch (error) {
        showMessage(error.message);
    }
});

document.getElementById('bookingForm').addEventListener('submit', async event => {
    event.preventDefault();

    try {
        await api('/api/bookings', {
            method: 'POST',
            body: JSON.stringify({
                therapist_id: Number(document.getElementById('bookingTherapist').value),
                service_id: Number(document.getElementById('bookingService').value),
                start_time: new Date(document.getElementById('bookingStart').value).toISOString(),
                note: document.getElementById('bookingNote').value
            })
        });
        showMessage('Booking request created');
        event.target.reset();
        await loadBookings();
    } catch (error) {
        showMessage(error.message);
    }
});

document.getElementById('availabilityForm').addEventListener('submit', async event => {
    event.preventDefault();

    try {
        await api('/api/availability', {
            method: 'POST',
            body: JSON.stringify({
                start_time: new Date(document.getElementById('availabilityStart').value).toISOString(),
                end_time: new Date(document.getElementById('availabilityEnd').value).toISOString()
            })
        });
        showMessage('Availability added');
        event.target.reset();
        await loadAvailability();
    } catch (error) {
        showMessage(error.message);
    }
});

document.getElementById('refreshButton').addEventListener('click', loadDashboard);

logoutButton.addEventListener('click', () => {
    token = '';
    currentUser = null;
    localStorage.removeItem('booking_token');
    showLogin();
});

loadUser();
