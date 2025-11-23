
const today = new Date();
const currentYear = today.getFullYear();
const currentMonth = today.getMonth() + 1; // January is 0

const daysOfWeek = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
const timeSlots = [ '9:00 AM', '10:00 AM', '11:00 AM', '12:00 PM', '13:00 PM', '14:00 PM', '15:00 PM', '16:00 PM', '17:00 PM', '18:00 PM', '19:00 PM', '20:00 PM' ];

doccument.addEventListener("DOMContentLoaded", function() {

    const calendarTable = document.getElementById("calendar");

    daysOfWeek.forEach(function(day) {
        const headerCell = document.createElement("th");
        headerCell.innerText = day;
        headerRow.appendChild(headerCell);
    });     

    calendarTable.appendChild(headerRow);
});