// JavaScript for client-side interactions
document.addEventListener('DOMContentLoaded', function() {
    // Example: Add confirmation for delete buttons
    document.querySelectorAll('.delete-btn').forEach(button => {
        button.addEventListener('click', function(event) {
            if (!confirm('Are you sure you want to delete this item?')) {
                event.preventDefault();
            }
        });
    });
});