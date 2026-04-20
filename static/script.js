const daysOfWeek = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];


const DAY_START_HOUR = 8;      // 8:00 AM
const DAY_END_HOUR = 22;       // 10:00 PM
const SLOT_INTERVAL_MINUTES = 15;

function generateTimeSlots() {
    const slots = [];
    const startMinutes = DAY_START_HOUR * 60;
    const endMinutes = DAY_END_HOUR * 60;

    for (let minutes = startMinutes; minutes < endMinutes; minutes += SLOT_INTERVAL_MINUTES) {
        const hour24 = Math.floor(minutes / 60);
        const mins = minutes % 60;

        const period = hour24 >= 12 ? 'PM' : 'AM';
        let hour12 = hour24 % 12;
        if (hour12 === 0) hour12 = 12;

        const minsStr = mins.toString().padStart(2, '0');
        slots.push(`${hour12}:${minsStr} ${period}`);
    }

    return slots;
}

const timeSlots = generateTimeSlots();

let currentWeekStart = getCurrentWeekStart();

function getCurrentWeekStart() {
    const today = new Date();
    const day = today.getDay();
    const diff = today.getDate() - day + (day === 0 ? -6 : 1);
    const monday = new Date(today.setDate(diff));
    monday.setHours(0, 0, 0, 0);
    return monday;
}

function getWeekDates(weekStart) {
    const dates = [];
    for (let i = 0; i < 7; i++) {
        const date = new Date(weekStart);
        date.setDate(weekStart.getDate() + i);
        dates.push(date);
    }
    return dates;
}

function formatDate(date) {
    const day = date.getDate();
    const suffix = getDaySuffix(day);
    return `${day}${suffix}`;
}

function getDaySuffix(day) {
    if (day > 3 && day < 21) return 'th';
    switch (day % 10) {
        case 1: return 'st';
        case 2: return 'nd';
        case 3: return 'rd';
        default: return 'th';
    }
}

function formatMonthYear(weekStart) {
    const months = ['January', 'February', 'March', 'April', 'May', 'June', 
                   'July', 'August', 'September', 'October', 'November', 'December'];
    const month = months[weekStart.getMonth()];
    const year = weekStart.getFullYear();
    return `${month} ${year}`;
}

function parseTime(timeStr) {
    const [time, period] = timeStr.split(' ');
    const [hours, minutes] = time.split(':').map(Number);
    let hour24 = hours;
    if (period === 'PM' && hours !== 12) hour24 = hours + 12;
    if (period === 'AM' && hours === 12) hour24 = 0;
    return { hours: hour24, minutes: minutes || 0 };
}

/** API times are 24h "HH:MM" or "HH:MM:SS"; calendar cells use "h:mm AM/PM". */
function parseTime24h(hhmm) {
    if (hhmm == null || hhmm === '') {
        return { hours: 0, minutes: 0 };
    }
    const parts = String(hhmm).trim().split(':');
    const hours = parseInt(parts[0], 10) || 0;
    const minutes = parseInt(parts[1], 10) || 0;
    return { hours, minutes };
}

function isPastSlot(date, timeStr) {
    const now = new Date();
    const slotTime = parseTime(timeStr);
    const slotDate = new Date(date);
    slotDate.setHours(slotTime.hours, slotTime.minutes, 0, 0);
    return slotDate < now;
}

function renderCalendar() {
    const weekDates = getWeekDates(currentWeekStart);
    const headerRow = document.getElementById('calendar-header');
    const calendarBody = document.getElementById('calendar-body');
    
    headerRow.innerHTML = '';
    calendarBody.innerHTML = '';
    
    const emptyHeader = document.createElement('th');
    headerRow.appendChild(emptyHeader);
    
    weekDates.forEach((date, index) => {
        const dayName = daysOfWeek[index];
        const dateStr = formatDate(date);
        const headerCell = document.createElement('th');
        headerCell.textContent = `${dayName} - ${dateStr}`;
        headerRow.appendChild(headerCell);
    });
    
    timeSlots.forEach(time => {
        const timeRow = document.createElement('tr');
        
        const timeCell = document.createElement('th');
        timeCell.setAttribute('scope', 'row');
        timeCell.textContent = time;
        timeRow.appendChild(timeCell);
        
        weekDates.forEach((date, dayIndex) => {
            const dayCell = document.createElement('td');
            const dayName = daysOfWeek[dayIndex];
            const dateStr = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
            
            dayCell.setAttribute('data-day', dayName);
            dayCell.setAttribute('data-time', time);
            dayCell.setAttribute('data-date', dateStr);
            
            if (isPastSlot(date, time)) {
                dayCell.classList.add('past-slot');
                dayCell.style.cursor = 'not-allowed';
            }
            
            timeRow.appendChild(dayCell);
        });
        
        calendarBody.appendChild(timeRow);
    });
    
    document.getElementById('week-display').textContent = formatMonthYear(currentWeekStart);
    
    // slot states are handled in applyBookingColors()
    loadBookingColors();
}

function checkPastSlots() {
    loadBookingColors();
}

async function loadBookingColors() {
    const weekStartISO = currentWeekStart.toISOString();
    const isPublic = document.body.classList.contains('public-calendar');
    const localDemo = Array.isArray(window.__localDemoUnavailability)
        ? window.__localDemoUnavailability
        : [];
    const onAdminCalendar = Boolean(document.getElementById('add-block-btn'));

    function mergeAndApply(bookings, blocks) {
        const b = Array.isArray(bookings) ? bookings : [];
        const bl = Array.isArray(blocks) ? blocks : [];
        const mergedBlocks = onAdminCalendar ? [...bl, ...localDemo] : bl;
        applyBookingColors(b, mergedBlocks);
    }

    try {
        const url = isPublic
            ? `/api/public/calendar/bookings?week_start=${weekStartISO}`
            : `/api/calendar/bookings?week_start=${weekStartISO}`;
        const response = await fetch(url, { credentials: 'same-origin' });

        if (!response.ok) {
            console.warn('loadBookingColors: HTTP', response.status);
            mergeAndApply([], []);
            return;
        }

        const data = await response.json();

        if (!data || !data.success) {
            mergeAndApply([], []);
            return;
        }

        const bookings = Array.isArray(data.bookings) ? data.bookings : [];
        const blocks = Array.isArray(data.unavailability_blocks)
            ? data.unavailability_blocks
            : [];
        mergeAndApply(bookings, blocks);
    } catch (error) {
        console.error('Error loading booking colors:', error);
        mergeAndApply([], []);
    }
}

function applyBookingColors(bookings, unavailabilityBlocks = []) {
    const cells = document.querySelectorAll('#calendar td[data-date][data-time]');
    const now = new Date();
    const minAllowedTime = new Date(now.getTime() + 3 * 60 * 60 * 1000); // 3 hours from now
    
    cells.forEach(cell => {
        const dateStr = cell.getAttribute('data-date');
        const timeStr = cell.getAttribute('data-time');
        
        if (!dateStr || !timeStr) {
            return;
        }
        
        const slotTime = parseTime(timeStr);
        const [year, month, day] = dateStr.split('-').map(Number);
        const slotStart = new Date(year, month - 1, day, slotTime.hours, slotTime.minutes, 0, 0);
        const slotEnd = new Date(slotStart);
        slotEnd.setMinutes(slotEnd.getMinutes() + 15); // 15-minute slot

        cell.classList.remove(
            'slot-available',
            'slot-pending',
            'slot-accepted',
            'slot-unavailable',
            'slot-advance-limit',
            'past-slot'
        );
        cell.style.cursor = 'pointer';
        
        // Check if slot is in the past
        if (slotStart < now) {
            cell.classList.add('past-slot');
            cell.style.cursor = 'not-allowed';
            return;
        }

        // Tutor unavailability — before 3-hour rule so blocked slots still get slot-unavailable (grey).
        let isUnavailable = false;
        for (const block of unavailabilityBlocks) {
            if (block.repeat_until) {
                const until = new Date(block.repeat_until);
                const untilDay = new Date(until.getFullYear(), until.getMonth(), until.getDate());
                const slotDay = new Date(year, month - 1, day);
                if (slotDay > untilDay) {
                    continue;
                }
            }

            const blockStart = parseTime24h(block.start_time);
            const blockEnd = parseTime24h(block.end_time);

            const blockStartDate = new Date(year, month - 1, day, blockStart.hours, blockStart.minutes, 0, 0);
            const blockEndDate = new Date(year, month - 1, day, blockEnd.hours, blockEnd.minutes, 0, 0);

            if (blockEndDate <= blockStartDate) {
                blockEndDate.setDate(blockEndDate.getDate() + 1);
            } else if (blockEnd.hours < blockStart.hours) {
                blockEndDate.setDate(blockEndDate.getDate() + 1);
            }

            if (slotStart < blockEndDate && slotEnd > blockStartDate) {
                isUnavailable = true;
                break;
            }
        }

        if (isUnavailable) {
            cell.classList.add('slot-unavailable');
            cell.style.cursor = 'not-allowed';
            return;
        }

        // Check if slot is less than 3 hours from now - make it unavailable
        if (slotStart < minAllowedTime) {
            cell.classList.add('slot-advance-limit');
            cell.style.cursor = 'not-allowed';
            return;
        }
        
        // Check if this slot overlaps with any booking
        let slotStatus = 'available';
        
        for (const booking of bookings) {
            const bookingStart = new Date(booking.start_time);
            const bookingEnd = new Date(booking.end_time);
            
            // Check if slot overlaps with booking
            if (slotStart < bookingEnd && slotEnd > bookingStart) {
                if (booking.status === 'accepted') {
                    slotStatus = 'accepted';
                    break; // Accepted takes priority
                } else if (booking.status === 'pending' && slotStatus !== 'accepted') {
                    slotStatus = 'pending';
                }
            }
        }
        

        if (slotStatus === 'available') {
            cell.classList.add('slot-available');
        } else if (slotStatus === 'pending') {
            cell.classList.add('slot-pending');
        } else if (slotStatus === 'accepted') {
            cell.classList.add('slot-accepted');
        }
    });
}



let currentBookingSlot = null;
let currentDuration = 120; // minutes, default 2 hours
const MIN_DURATION = 120; // 2 hours minimum
const MAX_DURATION = 240; // 4 hours maximum
const BASE_PRICE = 100; // euros for 2 hours
const PRICE_PER_HOUR = 50; // euros per additional hour

// Calculate price based on duration in minutes
function calculatePrice(minutes) {
    if (minutes < MIN_DURATION) return BASE_PRICE;
    const extraHours = (minutes - MIN_DURATION) / 60;
    return BASE_PRICE + (PRICE_PER_HOUR * extraHours);
}

// Format time for display (e.g., "11:00 AM - 1:00 PM")
function formatTimeRange(startTimeStr, durationMinutes) {
    const start = parseTime(startTimeStr);
    const startDate = new Date();
    startDate.setHours(start.hours, start.minutes, 0, 0);
    
    const endDate = new Date(startDate);
    endDate.setMinutes(endDate.getMinutes() + durationMinutes);
    
    const formatTime = (date) => {
        let hours = date.getHours();
        const minutes = date.getMinutes();
        const period = hours >= 12 ? 'PM' : 'AM';
        hours = hours % 12;
        if (hours === 0) hours = 12;
        const minsStr = minutes.toString().padStart(2, '0');
        return `${hours}:${minsStr} ${period}`;
    };
    
    return `${formatTime(startDate)} - ${formatTime(endDate)}`;
}

// Open booking modal with selected slot
function openBookingModal(dateStr, timeStr, dayName) {
    const modal = document.getElementById('booking-modal');
    if (!modal) {
        return;
    }
    currentBookingSlot = { dateStr, timeStr, dayName };
    currentDuration = MIN_DURATION;

    const slotDisplay = formatTimeRange(timeStr, currentDuration);
    document.getElementById('booking-slot-time').textContent = slotDisplay;
    document.getElementById('duration-display').textContent = '2h';
    document.getElementById('price-display').textContent = `${calculatePrice(currentDuration)}€`;

    modal.classList.add('active');
}

// Close booking modal
function closeBookingModal() {
    const modal = document.getElementById('booking-modal');
    if (!modal) {
        return;
    }
    modal.classList.remove('active');
    const bookingError = document.getElementById('booking-error');
    if (bookingError) {
        bookingError.style.display = 'none';
    }
    currentBookingSlot = null;
    currentDuration = MIN_DURATION;
}

// Update duration display and price
function updateDurationDisplay() {
    const hours = Math.floor(currentDuration / 60);
    document.getElementById('duration-display').textContent = `${hours}h`;
    document.getElementById('price-display').textContent = `${calculatePrice(currentDuration)}€`;
    
    if (currentBookingSlot) {
        const slotDisplay = formatTimeRange(currentBookingSlot.timeStr, currentDuration);
        document.getElementById('booking-slot-time').textContent = slotDisplay;
    }
}

// Submit booking request
function submitBooking() {
    if (!currentBookingSlot) {
        console.error('No booking slot selected');
        return;
    }
    
    console.log('submitBooking called');
    showLoading('Submitting booking request...');
    
    const { dateStr, timeStr } = currentBookingSlot;
    const slotTime = parseTime(timeStr);
    const [year, month, day] = dateStr.split('-').map(Number);
    
    const startDateTime = new Date(year, month - 1, day, slotTime.hours, slotTime.minutes, 0, 0);
    const endDateTime = new Date(startDateTime);
    endDateTime.setMinutes(endDateTime.getMinutes() + currentDuration);
    
    const localStartTime = `${startDateTime.getFullYear()}-${String(startDateTime.getMonth() + 1).padStart(2, '0')}-${String(startDateTime.getDate()).padStart(2, '0')}T${String(startDateTime.getHours()).padStart(2, '0')}:${String(startDateTime.getMinutes()).padStart(2, '0')}:00`;

    const bookingData = {
        start_time: localStartTime,
        lesson_minutes: currentDuration
    };
    
    console.log('Sending booking request:', bookingData);
    
    fetch('/api/book-slot', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(bookingData)
    })
    .then(response => {
        console.log('Response status:', response.status);
        console.log('Response headers:', response.headers.get('content-type'));
        
        // Check if response is HTML (error page)
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('text/html')) {
            return response.text().then(html => {
                console.error('Received HTML instead of JSON:', html.substring(0, 200));
                throw new Error('Server returned HTML error page instead of JSON');
            });
        }
        
        if (!response.ok) {
            return response.json().then(err => Promise.reject(err));
        }
        return response.json();
    })
    .then(data => {
        console.log('Booking success:', data);
        hideLoading();
        if (data.success) {
            closeBookingModal();
            renderCalendar();
            showToast('Booking request submitted! Check your email for an approval notification.', 'success');
        } else {
            showToast(data.error || 'Failed to submit booking', 'error');
            document.getElementById('booking-error').textContent = data.error || 'Failed to submit booking';
            document.getElementById('booking-error').style.display = 'block';
        }
    })
    .catch(error => {
        console.error('Booking error:', error);
        hideLoading();
        const errorMsg = error.error || error.message || 'Network error. Please try again.';
        showToast(errorMsg, 'error');
        document.getElementById('booking-error').textContent = errorMsg;
        document.getElementById('booking-error').style.display = 'block';
    });
}

function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container') || createToastContainer();
    
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    const messageEl = document.createElement('div');
    messageEl.className = 'toast-message';
    messageEl.textContent = message;
    
    const closeBtn = document.createElement('button');
    closeBtn.className = 'toast-close';
    closeBtn.innerHTML = '×';
    closeBtn.onclick = () => removeToast(toast);
    
    toast.appendChild(messageEl);
    toast.appendChild(closeBtn);
    container.appendChild(toast);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        removeToast(toast);
    }, 5000);
}

function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container';
    document.body.appendChild(container);
    return container;
}

function removeToast(toast) {
    toast.classList.add('fade-out');
    setTimeout(() => {
        if (toast.parentNode) {
            toast.parentNode.removeChild(toast);
        }
    }, 300);
}

document.addEventListener('DOMContentLoaded', function() {
    renderCalendar();

    const prevWeek = document.getElementById('prev-week');
    const nextWeek = document.getElementById('next-week');
    if (prevWeek) {
        prevWeek.addEventListener('click', function() {
            currentWeekStart.setDate(currentWeekStart.getDate() - 7);
            renderCalendar();
        });
    }
    if (nextWeek) {
        nextWeek.addEventListener('click', function() {
            currentWeekStart.setDate(currentWeekStart.getDate() + 7);
            renderCalendar();
        });
    }

    const calendarTable = document.getElementById('calendar');
    if (calendarTable) {
        calendarTable.addEventListener('click', function(event) {
            const clickedCell = event.target;

            if (
                clickedCell.tagName === 'TD' &&
                !clickedCell.classList.contains('past-slot') &&
                !clickedCell.classList.contains('slot-accepted') &&
                !clickedCell.classList.contains('slot-unavailable')
            ) {
                const day = clickedCell.getAttribute('data-day');
                const time = clickedCell.getAttribute('data-time');
                const date = clickedCell.getAttribute('data-date');

                if (day && time && date) {
                    openBookingModal(date, time, day);
                }
            }
        });
    }

    const durationDecrease = document.getElementById('duration-decrease');
    const durationIncrease = document.getElementById('duration-increase');
    const bookingCancel = document.getElementById('booking-cancel');
    const bookingConfirm = document.getElementById('booking-confirm');
    const bookingOverlay = document.querySelector('.booking-modal-overlay');

    if (durationDecrease && durationIncrease) {
        durationDecrease.addEventListener('click', function() {
            if (currentDuration > MIN_DURATION) {
                currentDuration -= 60;
                updateDurationDisplay();
            }
        });
        durationIncrease.addEventListener('click', function() {
            if (currentDuration < MAX_DURATION) {
                currentDuration += 60;
                updateDurationDisplay();
            }
        });
    }

    if (bookingCancel) {
        bookingCancel.addEventListener('click', closeBookingModal);
    }
    if (bookingConfirm) {
        bookingConfirm.addEventListener('click', submitBooking);
    }
    if (bookingOverlay) {
        bookingOverlay.addEventListener('click', closeBookingModal);
    }

    setInterval(checkPastSlots, 60000);
});

let loadingOverlay = null;

function showLoading(message = 'Loading...') {
    if (loadingOverlay) return;
    
    loadingOverlay = document.createElement('div');
    loadingOverlay.className = 'loading-overlay';
    
    const content = document.createElement('div');
    content.className = 'loading-content';
    
    const spinner = document.createElement('div');
    spinner.className = 'loading-spinner';
    
    const text = document.createElement('div');
    text.className = 'loading-text';
    text.textContent = message;
    
    content.appendChild(spinner);
    content.appendChild(text);
    loadingOverlay.appendChild(content);
    document.body.appendChild(loadingOverlay);
}

function hideLoading() {
    if (loadingOverlay) {
        loadingOverlay.remove();
        loadingOverlay = null;
    }
}

window.addEventListener('storage', function (e) {
    if (e.key === 'tutor_calendar_invalidate' && typeof loadBookingColors === 'function') {
        loadBookingColors();
    }
});
