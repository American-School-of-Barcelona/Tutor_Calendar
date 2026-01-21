const daysOfWeek = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];


const DAY_START_HOUR = 8;      // 8:00 AM
const DAY_END_HOUR = 20;       // 8:00 PM
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
            const dateStr = date.toISOString().split('T')[0];
            
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
    checkPastSlots();
}

function checkPastSlots() {
    const now = new Date();
    const cells = document.querySelectorAll('#calendar td');
    
    cells.forEach(cell => {
        const dateStr = cell.getAttribute('data-date');
        const timeStr = cell.getAttribute('data-time');
        
        if (dateStr && timeStr) {
            const [year, month, day] = dateStr.split('-').map(Number);
            const slotTime = parseTime(timeStr);
            const slotDate = new Date(year, month - 1, day, slotTime.hours, slotTime.minutes, 0, 0);
            
            if (slotDate < now) {
                cell.classList.add('past-slot');
                cell.style.cursor = 'not-allowed';
            }
        }
    });
}

document.addEventListener('DOMContentLoaded', function() {
    renderCalendar();
    
    document.getElementById('prev-week').addEventListener('click', function() {
        currentWeekStart.setDate(currentWeekStart.getDate() - 7);
        renderCalendar();
    });
    
    document.getElementById('next-week').addEventListener('click', function() {
        currentWeekStart.setDate(currentWeekStart.getDate() + 7);
        renderCalendar();
    });
    
    const calendarTable = document.getElementById('calendar');
    calendarTable.addEventListener('click', function(event) {
        const clickedCell = event.target;
        
        if (clickedCell.tagName === 'TD' && !clickedCell.classList.contains('past-slot')) {
            clickedCell.classList.toggle('selected');
            
            const day = clickedCell.getAttribute('data-day');
            const time = clickedCell.getAttribute('data-time');
            const date = clickedCell.getAttribute('data-date');
            const isSelected = clickedCell.classList.contains('selected');
            
            fetch('/select_date', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    day: day,
                    time: time,
                    date: date,
                    selected: isSelected
                })
            })
            .then(response => response.json())
            .then(data => {
                console.log('Success:', data);
            })
            .catch((error) => {
                console.error('Error:', error);
            });
        }
    });
    
    setInterval(checkPastSlots, 60000);
});