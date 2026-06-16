document.addEventListener('DOMContentLoaded', function () {
    var searchInput = document.getElementById('search-input');
    var categoryFilter = document.getElementById('category-filter');
    var supplierFilter = document.getElementById('supplier-filter');
    var manufacturerFilter = document.getElementById('manufacturer-filter');
    var sortSelect = document.getElementById('sort-select');
    var productGrid = document.getElementById('product-grid');

    if (!searchInput && !categoryFilter && !supplierFilter && !manufacturerFilter && !sortSelect) {
        return;
    }

    var debounceTimer;

    function fetchProducts() {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(function () {
            var params = new URLSearchParams();
            if (searchInput) params.set('search', searchInput.value);
            if (categoryFilter && categoryFilter.value) params.set('category', categoryFilter.value);
            if (supplierFilter && supplierFilter.value) params.set('supplier', supplierFilter.value);
            if (manufacturerFilter && manufacturerFilter.value) params.set('manufacturer', manufacturerFilter.value);
            if (sortSelect && sortSelect.value) params.set('sort', sortSelect.value);
            var url = '/catalog/ajax/?' + params.toString();

            fetch(url, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(function (response) { return response.json(); })
            .then(function (data) {
                renderProducts(data.products, data.user_role);
            })
            .catch(function (err) {
                console.error('Ошибка при загрузке:', err);
            });
        }, 400);
    }

    function renderProducts(products, userRole) {
        if (!productGrid) return;
        var html = '';
        if (products.length === 0) {
            html = '<p class="no-products">Товары не найдены.</p>';
        } else {
            for (var i = 0; i < products.length; i++) {
                var p = products[i];
                var cardClass = 'product-card';
                if (p.stock_quantity === 0) cardClass += ' out-of-stock';
                if (p.discount > 17) cardClass += ' high-discount';

                var priceHtml = '';
                if (p.discount > 0) {
                    priceHtml = '<p class="product-price old-price">' + p.price + ' \u20BD</p>' +
                                '<p class="product-price discounted-price">' + p.discounted_price + ' \u20BD</p>' +
                                '<p class="product-discount">Скидка: ' + p.discount + '%</p>';
                } else {
                    priceHtml = '<p class="product-price">' + p.price + ' \u20BD</p>';
                }

                var stockHtml = p.stock_quantity === 0
                    ? 'Нет в наличии'
                    : 'В наличии: ' + p.stock_quantity + ' ' + p.unit;

                var actionsHtml = '';
                if (userRole === 'admin') {
                    actionsHtml = '<a href="/catalog/product/' + p.id + '/update/" class="btn btn-edit">Редактировать</a>' +
                                  '<a href="/catalog/product/' + p.id + '/delete/" class="btn btn-delete">Удалить</a>';
                }

                html += '<div class="' + cardClass + '">' +
                            '<div class="product-image">' +
                                '<img src="' + p.image_url + '" alt="' + p.name.replace(/"/g, '&quot;') + '">' +
                            '</div>' +
                            '<div class="product-info">' +
                                '<h3 class="product-name">' + p.name + '</h3>' +
                                '<p class="product-article">Артикул: ' + p.article + '</p>' +
                                '<p class="product-category">' + p.category + '</p>' +
                                priceHtml +
                                '<p class="product-stock">' + stockHtml + '</p>' +
                                '<div class="product-actions">' +
                                    '<a href="/catalog/product/' + p.id + '/" class="btn btn-details">Подробнее</a>' +
                                    actionsHtml +
                                '</div>' +
                            '</div>' +
                        '</div>';
            }
        }
        productGrid.innerHTML = html;
    }

    if (searchInput) searchInput.addEventListener('input', fetchProducts);
    if (categoryFilter) categoryFilter.addEventListener('change', fetchProducts);
    if (supplierFilter) supplierFilter.addEventListener('change', fetchProducts);
    if (manufacturerFilter) manufacturerFilter.addEventListener('change', fetchProducts);
    if (sortSelect) sortSelect.addEventListener('change', fetchProducts);
});
