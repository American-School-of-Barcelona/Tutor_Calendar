// Format time for display
function formatTime(timeStr) {
    const [hours, minutes] = timeStr.split(':').map(Number);
    const period = hours >= 12 ? 'PM' : 'AM';
    const hour12 = hours % 12 || 12;
    return `${hour12}:${minutes.toString().padStart(2, '0')} ${period}`;
}

// Render unavailability blocks list
function renderBlocks(blocks) {
    const container = document.getElementById('blocks-list');
    const loading = document.getElementById('blocks-loading');
    const empty = document.getElementById('blocks-empty');
    
    loading.style.display = 'none';
    
    if (blocks.length === 0) {
        empty.style.display = 'block';
        container.innerHTML = '';
        return;
    }
    
    empty.style.display = 'none';
    
    container.innerHTML = blocks.map(block => {
        const repeatText = block.repeat_rule === 'daily' ? 'Daily' :
                          block.repeat_rule === 'weekly' ? 'Weekly' :
                          block.repeat_rule === 'none' ? 'One-time' : block.repeat_rule;
        
        return `
            <div class="unavailability-block-item">
                <div class="unavailability-block-info">
                    <div class="unavailability-block-time">
                        ${formatTime(block.start_time)} - ${formatTime(block.end_time)}
                    </div>
                    <div class="unavailability-block-repeat">${repeatText}</div>
                </div>
                <button class="unavailability-block-delete" data-id="${block.id}">Delete</button>
            </div>
        `;
    }).join('');
    
    // Attach delete event listeners
    container.querySelectorAll('.unavailability-block-delete').forEach(btn => {
        btn.addEventListener('click', handleDeleteBlock);
    });
}

// Handle add block form
document.addEventListener('DOMContentLoaded', function() {
    const addBlockBtn = document.getElementById('add-block-btn');
    if (addBlockBtn) {
        addBlockBtn.addEventListener('click', function() {
            const startTime = document.getElementById('block-start-time').value;
            const endTime = document.getElementById('block-end-time').value;
            const repeatRule = document.getElementById('block-repeat').value;
            
            if (!startTime || !endTime) {
                alert('Please fill in both start and end times');
                return;
            }
            
            fetch('/api/admin/unavailability', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    start_time: startTime,
                    end_time: endTime,
                    repeat_rule: repeatRule
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    document.getElementById('block-start-time').value = '';
                    document.getElementById('block-end-time').value = '';
                    document.getElementById('block-repeat').value = 'none';
                    loadBlocks();
                    // Reload calendar to show new block
                    if (typeof loadBookingColors === 'function') {
                        loadBookingColors();
                    }
                } else {
                    alert(data.error || 'Failed to create block');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Network error. Please try again.');
            });
        });
    }
    
    loadBlocks();
});

// Handle delete block
function handleDeleteBlock(event) {
    const blockId = event.target.getAttribute('data-id');
    
    if (!confirm('Are you sure you want to delete this unavailability block?')) {
        return;
    }
    
    fetch(`/api/admin/unavailability/${blockId}`, {
        method: 'DELETE',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            loadBlocks();
        } else {
            alert(data.error || 'Failed to delete block');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Network error. Please try again.');
    });
}

// Load blocks from API
function loadBlocks() {
    fetch('/api/admin/unavailability')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                renderBlocks(data.blocks);
            } else {
                console.error('Failed to load blocks:', data.error);
            }
        })
        .catch(error => {
            console.error('Error loading blocks:', error);
            document.getElementById('blocks-loading').textContent = 'Error loading blocks. Please refresh.';
        });
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    loadBlocks();
});