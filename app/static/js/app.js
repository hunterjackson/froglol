// Handle delete bookmark
document.addEventListener('DOMContentLoaded', () => {
    // Delete bookmark buttons
    const deleteButtons = document.querySelectorAll('.delete-btn');
    deleteButtons.forEach(btn => {
        btn.addEventListener('click', async () => {
            const bookmarkId = btn.dataset.bookmarkId;
            if (!confirm('Are you sure you want to delete this bookmark?')) {
                return;
            }

            try {
                const response = await fetch(`/api/bookmarks/${bookmarkId}`, {
                    method: 'DELETE'
                });

                if (response.ok) {
                    window.location.reload();
                } else {
                    alert('Failed to delete bookmark');
                }
            } catch (error) {
                alert('Error: ' + error.message);
            }
        });
    });

    // Delete alias buttons
    const deleteAliasButtons = document.querySelectorAll('.delete-alias-btn');
    deleteAliasButtons.forEach(btn => {
        btn.addEventListener('click', async () => {
            const aliasId = btn.dataset.aliasId;

            try {
                const response = await fetch(`/api/aliases/${aliasId}`, {
                    method: 'DELETE'
                });

                if (response.ok) {
                    window.location.reload();
                } else {
                    alert('Failed to delete alias');
                }
            } catch (error) {
                alert('Error: ' + error.message);
            }
        });
    });

    // Add alias buttons
    const addAliasButtons = document.querySelectorAll('.add-alias-btn');
    addAliasButtons.forEach(btn => {
        btn.addEventListener('click', async () => {
            const bookmarkId = btn.dataset.bookmarkId;
            const alias = prompt('Enter alias name:');

            if (!alias || !alias.trim()) {
                return;
            }

            try {
                const response = await fetch(`/api/bookmarks/${bookmarkId}/aliases`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ alias: alias.trim() })
                });

                if (response.ok) {
                    window.location.reload();
                } else {
                    const error = await response.json();
                    alert('Error: ' + (error.error || 'Failed to add alias'));
                }
            } catch (error) {
                alert('Error: ' + error.message);
            }
        });
    });
});
