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
                
                // Определяем классы для строки
                var rowClass = 'product-row';
                if (p.stock_quantity === 0) {
                    rowClass += ' out-of-stock';
                } else if (p.discount > 17) {
                    rowClass += ' high-discount';
                }

                // Блок с ценой
                var priceHtml = '';
                if (p.discount > 0) {
                    priceHtml = '<span class="product-row-old-price">' + p.price + ' \u20BD</span>' +
                                '<span class="product-row-final-price">' + p.discounted_price + ' \u20BD</span>' +
                                '<span class="product-row-discount">Скидка: ' + p.discount + '%</span>';
                } else {
                    priceHtml = '<span class="product-row-final-price">' + p.price + ' \u20BD</span>';
                }

                // Текст о наличии
                var stockHtml = 'Количество на складе: ' + p.stock_quantity + ' ' + p.unit;

                // Кнопки действий
                var actionsHtml = '<a href="/catalog/product/' + p.id + '/" class="btn btn-details">Подробнее</a>';
                if (userRole === 'admin') {
                    actionsHtml += '<a href="/catalog/product/' + p.id + '/update/" class="btn btn-edit">Редактировать</a>' +
                                   '<a href="/catalog/product/' + p.id + '/delete/" class="btn btn-delete">Удалить</a>';
                }

                // Описание (обрезаем если больше 100 символов)
                var descriptionHtml = '';
                if (p.description && p.description.trim() !== '') {
                    var desc = p.description;
                    if (desc.length > 100) {
                        desc = desc.substring(0, 100) + '...';
                    }
                    descriptionHtml = '<p class="product-row-description" title="' + p.description.replace(/"/g, '"') + '">' + desc.replace(/"/g, '"') + '</p>';
                }

                html += '<div class="' + rowClass + '" data-product-id="' + p.id + '">' +
                            '<div class="product-row-image">' +
                                '<img src="' + p.image_url + '" alt="' + p.name.replace(/"/g, '"') + '">' +
                            '</div>' +
                            '<div class="product-row-content">' +
                                '<div class="product-row-info">' +
                                    '<div>' +
                                        '<span class="product-row-category">' + p.category + '</span>' +
                                        '<h3 class="product-row-name">' + p.name + '</h3>' +
                                    '</div>' +
                                    descriptionHtml +
                                    '<p class="product-row-manufacturer">Производитель: ' + p.manufacturer + '</p>' +
                                    '<p class="product-row-supplier">Поставщик: ' + p.supplier + '</p>' +
                                    '<p class="product-row-stock">' + stockHtml + '</p>' +
                                '</div>' +
                                '<div class="product-row-price-block">' +
                                    priceHtml +
                                '</div>' +
                            '</div>' +
                            '<div class="product-row-actions">' +
                                actionsHtml +
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