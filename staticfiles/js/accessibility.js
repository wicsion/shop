// main.js
// Search Autocomplete
const searchInput = document.getElementById('globalSearch');
new Autocomplete(searchInput, {
    threshold: 2,
    maximumItems: 5,
    onSelectItem: ({ value }) => {
        window.location.href = `/search/?q=${value}`;
    }
});

// Cart Functionality
document.querySelectorAll('.add-to-cart').forEach(button => {
    button.addEventListener('click', async () => {
        const productId = button.dataset.productId;
        try {
            const response = await fetch(`/cart/add/${productId}/`);
            if (response.ok) {
                showToast('Товар добавлен в корзину');
            }
        } catch (error) {
            console.error('Error:', error);
        }
    });
});

function showToast(message) {
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.textContent = message;
    document.body.appendChild(toast);

    setTimeout(() => {
        toast.remove();
    }, 3000);
}