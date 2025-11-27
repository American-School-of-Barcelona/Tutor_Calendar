
const today = new Date();
const currentYear = today.getFullYear();
const currentMonth = today.getMonth() + 1; // January is 0

const daysOfWeek = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
const timeSlots = [ '9:00 AM', '10:00 AM', '11:00 AM', '12:00 PM', '13:00 PM', '14:00 PM', '15:00 PM', '16:00 PM', '17:00 PM', '18:00 PM', '19:00 PM', '20:00 PM' ];

document.addEventListener("DOMContentLoaded", function() {

    const calendarTable = document.getElementById("calendar");
    const headerRow = document.createElement("tr");
    
    // create header row
    const emptyHeaderCell = document.createElement("th");
    emptyHeaderCell.innerText = "";
    headerRow.appendChild(emptyHeaderCell);

    daysOfWeek.forEach(function(day) {
        const headerCell = document.createElement("th");
        headerCell.innerText = day;
        headerRow.appendChild(headerCell);
    });     

    calendarTable.appendChild(headerRow);

    // create time slots rows
    timeSlots.forEach(function(time) {
        const timeRow = document.createElement("tr");

        //create the time table cell
        const timeCell = document.createElement("th");
        timeCell.setAttribute('scope', 'row');
        timeCell.innerText = time;
        timeRow.appendChild(timeCell);

        // create a cell for each day of the week
        daysOfWeek.forEach(function(day) {
            const dayCell = document.createElement('td');
            dayCell.setAttribute('data-day', day);
            dayCell.setAttribute('data-time', time);
            timeRow.appendChild(dayCell);
            });

    //append the time row to the calendar table
    calendarTable.appendChild(timeRow);
    });

    //add click event listener to the table
    calendarTable.addEventListener('click', function(event) {

        const clickedCell = event.target;

        // handle clicks only on day cells
        if (clickedCell.tagName === 'TD') {

            clickedCell.classList.toggle('selected');

            // get the day and time from data attributes
            const day = clickedCell.getAttribute('data-day');
            const time = clickedCell.getAttribute('data-time');
            const isSelected = clickedCell.classList.contains('selected');


        //send data to Flask
        fetch('/select_date', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                day: day,
                time: time,
                selected: isSelected,
                month: currentMonth,
                year: currentYear,
                selected_date: `${currentYear}-${currentMonth}-${day} ${time}`
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
    })    
});
