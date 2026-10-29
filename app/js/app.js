/**
 * HSH Sales Pro - app.js v3
 * Hệ Thống Tra Cứu Thiết Bị Nhà Tắm & Nhà Bếp Toàn Diện
 */

const PRICE_LABELS = {
    gia_ban_le:     'Giá bán lẻ (Có VAT)',
    gia_niem_yet:   'Giá niêm yết (Có VAT)',
    gia_cong_bo:    'Giá công bố (Chưa VAT)',
    gia_thau_tho:   'Giá thầu thợ (CK 10%)',
    than_thiet_c1:  'Thân thiết C1 (CK 20%)',
    than_thiet_c2:  'Thân thiết C2 (CK 20%)',
    dai_ly_c1:      'Đại lý C1 (CK 20%)',
    dai_ly_c2:      'Đại lý C2 (CK 20%)',
    dai_ly_c3:      'Đại lý C3 (CK 20%)',
    dai_ly_c4:      'Đại lý C4 (CK 20%)',
    npp_c1:         'NPP C1 (CK 22%)',
    npp_c2:         'NPP C2 (CK 22%)',
    npp_c3:         'NPP C3 (CK 25%)',
    gia_ban_mau:    'Chính sách bán mẫu',
    gia_catalogue:  'Giá Catalogue',
    gia_nhan_vien:  'Giá nhân viên HSH (BCL)',
};

const BRAND_ICONS = {
    'INAX': '🔵', 'TOTO': '🟢', 'American Standard': '🇺🇸',
    'CAESAR': '⚜️', 'ROCA': '🟤', 'ARROW': '🏹',
    'TUSLO': '✨', 'LUSHINE': '💎', 'HAFELE': '🔧',
    'TEKA': '🍳', 'KITTO': '🌟', 'Sơn Hà': '🔴',
    'VIGLACERA': '🟡', 'Toàn Mỹ': '🇻🇳', 'Hùng Anh': '🦅', 'Tân An Vinh': '💫',
};

const PAGE_SIZE = 24;
const TABLE_PAGE_SIZE = 40;

// ======================== STATE ========================
let allProducts = [];
let filteredProducts = [];
let extrasData = null;
let currentTab = 'catalog';
let currentPage = 1;
let currentTablePage = 1;
let currentView = localStorage.getItem('hsh_view') || 'grid';
let selectedPriceType = localStorage.getItem('hsh_price_type') || 'gia_ban_le';
let favorites   = JSON.parse(localStorage.getItem('hsh_fav')     || '[]');
let compareList = JSON.parse(localStorage.getItem('hsh_compare') || '[]');
let quoteList   = JSON.parse(localStorage.getItem('hsh_quote')   || '[]');
let fuse = null;
let searchTimer = null;

// ======================== INIT ========================
async function init() {
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('./sw.js').catch(() => {});
    }

    const updateOfflineBanner = () => {
        document.getElementById('offline-banner').style.display = navigator.onLine ? 'none' : 'block';
    };
    window.addEventListener('online',  updateOfflineBanner);
    window.addEventListener('offline', updateOfflineBanner);
    updateOfflineBanner();

    document.getElementById('filter-price-type').value = selectedPriceType;
    setView(currentView, false);

    try {
        const [prodRes, extRes] = await Promise.all([
            fetch('data/products.json'),
            fetch('data/extras.json').catch(() => null)
        ]);
        allProducts = await prodRes.json();
        if (extRes && extRes.ok) {
            extrasData = await extRes.json();
        }

        fuse = new Fuse(allProducts, {
            keys: [
                { name: 'ten_sp',      weight: 0.40 },
                { name: 'ma_sp',       weight: 0.30 },
                { name: 'ma_item',     weight: 0.12 },
                { name: 'ma_phu',      weight: 0.08 },
                { name: 'thuong_hieu', weight: 0.05 },
                { name: 'nhom_sp',     weight: 0.05 },
            ],
            threshold: 0.32,
            includeScore: true,
            minMatchCharLength: 1,
            ignoreLocation: true,
        });

        populateFilters();
        buildBrandStrip();
        filteredProducts = [...allProducts];
        renderProducts();
        renderMasterTable();
        if (extrasData) {
            renderPromosTab();
            renderPoliciesTab();
            renderKnowledgeTab();
            renderStoresTab();
        }
        updateBadges();
        showStats();
        setupEvents();
        handleDeepLink();

    } catch (err) {
        console.error(err);
        document.getElementById('products-container').innerHTML = `
        <div class="empty-state">
            <div class="empty-icon">⚠️</div>
            <div class="empty-title">Không tải được dữ liệu sản phẩm</div>
            <div class="empty-sub">Vui lòng chạy file <strong>start_server.bat</strong> để mở ứng dụng</div>
        </div>`;
    }
}

function showStats() {
    const brands  = new Set(allProducts.map(p => p.thuong_hieu)).size;
    const withImg = allProducts.filter(p => p.hinh_anh).length;
    const inStock = allProducts.filter(p => getStockTotal(p) > 0).length;
    const hot     = allProducts.filter(p => p.hang_ban_chay).length;
    document.getElementById('stat-total').innerHTML =
        `📦 <strong>${allProducts.length.toLocaleString('vi-VN')}</strong> sản phẩm &nbsp;|&nbsp; ` +
        `🖼️ <strong>${withImg.toLocaleString('vi-VN')}</strong> có ảnh thật &nbsp;|&nbsp; ` +
        `🏷️ <strong>${brands}</strong> thương hiệu &nbsp;|&nbsp; ` +
        `✅ <strong>${inStock.toLocaleString('vi-VN')}</strong> mã còn tồn kho &nbsp;|&nbsp; ` +
        `🔥 <strong>${hot}</strong> SP Hot`;
}

function populateFilters() {
    // Brands with count
    const brandCounts = {};
    allProducts.forEach(p => {
        if (p.thuong_hieu) brandCounts[p.thuong_hieu] = (brandCounts[p.thuong_hieu] || 0) + 1;
    });
    const brands = Object.keys(brandCounts).sort();
    const bSel = document.getElementById('filter-brand');
    brands.forEach(b => {
        const o = document.createElement('option');
        o.value = b;
        o.textContent = `${BRAND_ICONS[b] || '🏷️'} ${b} (${brandCounts[b]})`;
        bSel.appendChild(o);
    });

    // Groups with count
    const groupCounts = {};
    allProducts.forEach(p => {
        if (p.nhom_sp) groupCounts[p.nhom_sp] = (groupCounts[p.nhom_sp] || 0) + 1;
    });
    const groups = Object.keys(groupCounts).sort();
    const gSel = document.getElementById('filter-group');
    groups.forEach(g => {
        const o = document.createElement('option');
        o.value = g;
        o.textContent = `${g} (${groupCounts[g]})`;
        gSel.appendChild(o);
    });

    // Warehouses
    const whSel = document.getElementById('filter-warehouse');
    const sampleTon = allProducts.find(p => p.ton_kho && Object.keys(p.ton_kho).length > 0)?.ton_kho || {};
    Object.keys(sampleTon).filter(k => !k.includes('Tổng')).forEach(kho => {
        const o = document.createElement('option');
        o.value = kho;
        o.textContent = `🏭 Kho: ${kho}`;
        whSel.appendChild(o);
    });
}

function buildBrandStrip() {
    const brandCounts = {};
    allProducts.forEach(p => {
        if (p.thuong_hieu) brandCounts[p.thuong_hieu] = (brandCounts[p.thuong_hieu] || 0) + 1;
    });
    const brands = Object.keys(brandCounts).sort((a, b) => brandCounts[b] - brandCounts[a]);
    const strip = document.getElementById('brand-strip');
    strip.innerHTML = '';

    const allChip = document.createElement('button');
    allChip.className = 'brand-chip active';
    allChip.textContent = `🏷️ Tất cả (${allProducts.length})`;
    allChip.dataset.brand = '';
    allChip.onclick = () => filterByBrandChip('', allChip);
    strip.appendChild(allChip);

    brands.forEach(b => {
        const chip = document.createElement('button');
        chip.className = 'brand-chip';
        chip.textContent = `${BRAND_ICONS[b] || ''} ${b} (${brandCounts[b]})`;
        chip.dataset.brand = b;
        chip.onclick = () => filterByBrandChip(b, chip);
        strip.appendChild(chip);
    });
}

function filterByBrandChip(brand, el) {
    document.querySelectorAll('.brand-chip').forEach(c => c.classList.remove('active'));
    el.classList.add('active');
    document.getElementById('filter-brand').value = brand;
    applyFilters();
}

function setupEvents() {
    const inp = document.getElementById('search-input');
    inp.addEventListener('input', () => {
        document.getElementById('search-clear').style.display = inp.value ? 'flex' : 'none';
        clearTimeout(searchTimer);
        searchTimer = setTimeout(applyFilters, 220);
    });
    inp.addEventListener('keydown', e => { if (e.key === 'Escape') clearSearch(); });

    document.addEventListener('keydown', e => {
        if (e.key === '/' && document.activeElement.tagName !== 'INPUT' && document.activeElement.tagName !== 'SELECT') {
            e.preventDefault();
            inp.focus();
        }
        if (e.key === 'Escape') {
            closeLightbox();
        }
    });

    window.addEventListener('scroll', () => {
        document.getElementById('fab-scroll-top').style.display = window.scrollY > 450 ? 'flex' : 'none';
    });

    document.getElementById('filter-brand').addEventListener('change', function() {
        document.querySelectorAll('.brand-chip').forEach(c => {
            c.classList.toggle('active', c.dataset.brand === this.value);
        });
    });
}

// ======================== TAB NAVIGATION & MOBILE MENU ========================
function toggleMobileMenu() {
    const d = document.getElementById('mobile-drawer');
    const b = document.getElementById('drawer-backdrop');
    if (!d || !b) return;
    const isOpen = d.classList.contains('active');
    if (isOpen) {
        closeMobileMenu();
    } else {
        d.classList.add('active');
        b.classList.add('active');
        document.body.style.overflow = 'hidden';
    }
}

function closeMobileMenu() {
    const d = document.getElementById('mobile-drawer');
    const b = document.getElementById('drawer-backdrop');
    if (d) d.classList.remove('active');
    if (b) b.classList.remove('active');
    document.body.style.overflow = '';
}

function switchTab(tabId) {
    currentTab = tabId;
    document.querySelectorAll('.nav-tab').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tab === tabId);
    });
    document.querySelectorAll('.drawer-item').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tab === tabId);
    });
    document.querySelectorAll('.bottom-nav-item').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tab === tabId);
    });
    document.querySelectorAll('.tab-panel').forEach(panel => {
        panel.style.display = panel.id === `tab-${tabId}` ? 'block' : 'none';
    });
    // Show search wrapper only on catalog & pricelist tabs
    const showSearch = (tabId === 'catalog' || tabId === 'pricelist');
    document.getElementById('catalog-search-wrapper').style.display = showSearch ? 'block' : 'none';
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// ======================== FILTER & SORT ========================
function getStockTotal(p, warehouse = '') {
    if (!p.ton_kho) return 0;
    if (warehouse) return p.ton_kho[warehouse] || 0;
    if (p.ton_kho['Tổng tồn kho'] !== undefined) return p.ton_kho['Tổng tồn kho'];
    return Object.entries(p.ton_kho)
        .filter(([k]) => !k.includes('Tổng'))
        .reduce((s, [, v]) => s + (v || 0), 0);
}

function getDisplayPrice(p, pt = selectedPriceType) {
    return p[pt] || p.gia_ban_le || p.gia_niem_yet || p.gia_catalogue || 0;
}

function applyFilters() {
    const q        = document.getElementById('search-input').value.trim();
    const brand    = document.getElementById('filter-brand').value;
    const group    = document.getElementById('filter-group').value;
    const wh       = document.getElementById('filter-warehouse').value;
    const sortMode = document.getElementById('filter-sort').value;
    const hasImg   = document.getElementById('filter-has-img').checked;
    const instock  = document.getElementById('filter-instock').checked;
    const hotOnly  = document.getElementById('filter-hot').checked;
    const promoOnly= document.getElementById('filter-promo').checked;
    const onlineOnly= document.getElementById('filter-online').checked;

    let results = allProducts;

    if (q.length >= 1) {
        const qUpper = q.toUpperCase();
        // Exact substring match boost + Fuse fuzzy search
        const directMatches = allProducts.filter(p =>
            p.ma_sp.toUpperCase().includes(qUpper) ||
            (p.ma_item && p.ma_item.toUpperCase().includes(qUpper)) ||
            (p.ma_phu && p.ma_phu.toUpperCase().includes(qUpper)) ||
            p.ten_sp.toUpperCase().includes(qUpper) ||
            (p.kich_thuoc && p.kich_thuoc.toUpperCase().includes(qUpper))
        );
        const fuseMatches = fuse.search(q).map(r => r.item);
        const seen = new Set(directMatches.map(p => p.id));
        results = [...directMatches, ...fuseMatches.filter(p => !seen.has(p.id))];
    }

    if (brand)      results = results.filter(p => p.thuong_hieu === brand);
    if (group)      results = results.filter(p => p.nhom_sp === group);
    if (wh)         results = results.filter(p => (p.ton_kho?.[wh] || 0) > 0);
    if (hasImg)     results = results.filter(p => !!p.hinh_anh);
    if (instock)    results = results.filter(p => getStockTotal(p, wh) > 0);
    if (hotOnly)    results = results.filter(p => p.hang_ban_chay);
    if (promoOnly)  results = results.filter(p => p.xa_kho || p.ctkm_tuslo);
    if (onlineOnly) results = results.filter(p => p.uu_tien_online);

    // Sorting
    if (sortMode === 'img_first') {
        results = [...results].sort((a, b) => (b.hinh_anh ? 1 : 0) - (a.hinh_anh ? 1 : 0));
    } else if (sortMode === 'price_asc') {
        results = [...results].sort((a, b) => (getDisplayPrice(a) || 999999999) - (getDisplayPrice(b) || 999999999));
    } else if (sortMode === 'price_desc') {
        results = [...results].sort((a, b) => getDisplayPrice(b) - getDisplayPrice(a));
    } else if (sortMode === 'stock_desc') {
        results = [...results].sort((a, b) => getStockTotal(b, wh) - getStockTotal(a, wh));
    }

    filteredProducts = results;
    currentPage = 1;
    currentTablePage = 1;
    renderProducts();
    renderMasterTable();
}

function clearSearch() {
    document.getElementById('search-input').value = '';
    document.getElementById('search-clear').style.display = 'none';
    applyFilters();
    document.getElementById('search-input').focus();
}

function resetFilters() {
    document.getElementById('search-input').value = '';
    document.getElementById('search-clear').style.display = 'none';
    document.getElementById('filter-brand').value = '';
    document.getElementById('filter-group').value = '';
    document.getElementById('filter-warehouse').value = '';
    document.getElementById('filter-sort').value = 'default';
    document.getElementById('filter-has-img').checked = false;
    document.getElementById('filter-instock').checked = false;
    document.getElementById('filter-hot').checked = false;
    document.getElementById('filter-promo').checked = false;
    document.getElementById('filter-online').checked = false;
    document.querySelectorAll('.brand-chip').forEach((c, i) => c.classList.toggle('active', i === 0));
    applyFilters();
}

function changePriceType(val) {
    selectedPriceType = val;
    localStorage.setItem('hsh_price_type', val);
    renderProducts();
    renderMasterTable();
}

// ======================== RENDER CATALOG (GRID & LIST) ========================
function renderProducts() {
    const container = document.getElementById('products-container');
    const start = (currentPage - 1) * PAGE_SIZE;
    const page  = filteredProducts.slice(start, start + PAGE_SIZE);
    const wh    = document.getElementById('filter-warehouse').value;

    const withImgCnt = filteredProducts.filter(p => p.hinh_anh).length;
    document.getElementById('results-count').innerHTML =
        `Hiển thị <strong>${filteredProducts.length.toLocaleString('vi-VN')}</strong> sản phẩm ` +
        `<span style="color:var(--text-muted)">(${withImgCnt.toLocaleString('vi-VN')} SP có ảnh)</span>`;

    if (page.length === 0) {
        container.className = 'products-grid';
        container.innerHTML = `<div class="empty-state">
            <div class="empty-icon">🔍</div>
            <div class="empty-title">Không tìm thấy sản phẩm phù hợp</div>
            <div class="empty-sub">Thử từ khóa khác hoặc <button class="btn btn-sm btn-outline" onclick="resetFilters()">↺ Xóa bộ lọc</button></div>
        </div>`;
        document.getElementById('pagination').innerHTML = '';
        return;
    }

    container.className = currentView === 'grid' ? 'products-grid' : 'products-list';
    container.innerHTML = page.map(p =>
        currentView === 'grid' ? renderGridCard(p, wh) : renderListCard(p, wh)
    ).join('');

    renderPagination('pagination', filteredProducts.length, PAGE_SIZE, currentPage, 'goPage');
}

function getStockBadgeInfo(p, wh = '') {
    if (!p.ton_kho || Object.keys(p.ton_kho).length === 0) return { total: -1, label: '', cls: '' };
    const total = getStockTotal(p, wh);
    const prefix = wh ? `${wh}: ` : 'Tồn: ';
    if (total <= 0) return { total: 0, label: wh ? `${wh}: 0` : 'Hết tồn', cls: 'badge-out' };
    if (total < 10) return { total, label: `${prefix}${total}`, cls: 'badge-low' };
    return { total, label: `${prefix}${total.toLocaleString('vi-VN')}`, cls: 'badge-in' };
}

function renderGridCard(p, wh = '') {
    const price   = getDisplayPrice(p);
    const nyPrice = p.gia_niem_yet || 0;
    const stock   = getStockBadgeInfo(p, wh);
    const isFav   = favorites.includes(p.ma_sp);
    const isCmp   = compareList.includes(p.ma_sp);
    const isQuote = !!quoteList.find(q => q.ma_sp === p.ma_sp);
    const isStudioImg = p.hinh_anh && p.hinh_anh.includes('album_');
    const pctSave = (nyPrice > price && price > 0) ? Math.round((nyPrice - price) * 100 / nyPrice) : 0;

    const imgHtml = p.hinh_anh
        ? `<img class="card-image" src="${escHtml(p.hinh_anh)}" alt="${escHtml(p.ten_sp)}" loading="lazy" onerror="this.parentElement.innerHTML='<div class=card-no-image>${BRAND_ICONS[p.thuong_hieu]||'🛁'}<span>Chưa có ảnh</span></div>'">`
        : `<div class="card-no-image">${BRAND_ICONS[p.thuong_hieu] || '🛁'}<span>${escHtml(p.nhom_sp || 'TBVS')}</span></div>`;

    return `<div class="product-card" onclick="openDetail(${p.id})">
        <div class="card-badges">
            ${isStudioImg ? '<span class="badge-studio">📸 STUDIO HD</span>' : ''}
            ${p.hang_ban_chay ? '<span class="badge-hot">🔥 HOT</span>' : ''}
            ${p.xa_kho ? '<span class="badge-promo">🏷️ XẢ KHO</span>' : ''}
            ${p.ctkm_tuslo ? '<span class="badge-promo">🎁 TẶNG QUÀ</span>' : ''}
            ${p.uu_tien_online ? '<span class="badge-online">🌐 ONLINE</span>' : ''}
            ${p.ngung_nhap ? '<span class="badge-discont">⛔ NGƯNG NHẬP</span>' : ''}
            ${stock.total >= 0 ? `<span class="badge-stock ${stock.cls}">${stock.label}</span>` : ''}
        </div>
        <div class="card-image-wrap">${imgHtml}</div>
        <div class="card-body">
            <div class="card-meta-top">
                <span class="card-brand">${BRAND_ICONS[p.thuong_hieu]||''} ${escHtml(p.thuong_hieu)}</span>
                ${p.nhom_sp ? `<span class="card-group-tag" title="${escHtml(p.nhom_sp)}">${escHtml(p.nhom_sp)}</span>` : ''}
            </div>
            <div class="card-title" title="${escHtml(p.ten_sp)}">${escHtml(p.ten_sp)}</div>
            <div class="card-code">📌 ${escHtml(p.ma_sp)} ${p.ma_item ? `<span style="color:var(--text-muted);font-weight:400">· ${escHtml(p.ma_item)}</span>` : ''}</div>
            ${p.kich_thuoc ? `<div class="card-spec-mini">📏 ${escHtml(p.kich_thuoc)}</div>` : ''}
            <div class="card-price-block">
                <div>
                    <div class="card-price">${formatPrice(price)}</div>
                    <div class="card-price-label">${(PRICE_LABELS[selectedPriceType] || '').split(' (')[0]}</div>
                </div>
                ${nyPrice > price && price > 0 ? `<div style="text-align:right">
                    <span class="card-price-sub" title="Giá niêm yết">${formatPrice(nyPrice)}</span>
                    ${pctSave >= 5 ? `<span style="display:inline-block;background:#16a34a;color:#fff;font-size:9.5px;font-weight:800;padding:1px 5px;border-radius:4px;margin-left:3px">-${pctSave}%</span>` : ''}
                </div>` : ''}
            </div>
            <div class="card-actions">
                <button class="btn-detail" onclick="event.stopPropagation();openDetail(${p.id})">Chi tiết ▸</button>
                <button class="btn-action-sm ${isFav?'active':''}" onclick="event.stopPropagation();toggleFav('${escJs(p.ma_sp)}')" title="Lưu yêu thích">❤️</button>
                <button class="btn-action-sm ${isCmp?'active':''}" onclick="event.stopPropagation();toggleCompare('${escJs(p.ma_sp)}')" title="So sánh">⚖️</button>
                <button class="btn-action-sm ${isQuote?'active':''}" onclick="event.stopPropagation();addToQuote(${p.id})" title="Thêm vào báo giá">📋</button>
            </div>
        </div>
    </div>`;
}

function renderListCard(p, wh = '') {
    const price   = getDisplayPrice(p);
    const stock   = getStockBadgeInfo(p, wh);
    const isFav   = favorites.includes(p.ma_sp);
    const isQuote = !!quoteList.find(q => q.ma_sp === p.ma_sp);

    const topKho = p.ton_kho
        ? Object.entries(p.ton_kho).filter(([k,v]) => !k.includes('Tổng') && v > 0).slice(0, 5)
        : [];

    const imgHtml = p.hinh_anh
        ? `<img class="list-thumb" src="${escHtml(p.hinh_anh)}" alt="" loading="lazy" onerror="this.outerHTML='<div class=list-thumb-placeholder>${BRAND_ICONS[p.thuong_hieu]||'🛁'}</div>'">`
        : `<div class="list-thumb-placeholder">${BRAND_ICONS[p.thuong_hieu] || '🛁'}</div>`;

    return `<div class="product-list-card" onclick="openDetail(${p.id})">
        ${imgHtml}
        <div class="list-info">
            <div class="list-title">
                ${p.hang_ban_chay ? '🔥 ' : ''}${escHtml(p.ten_sp)}
                ${p.xa_kho ? '<span class="badge-promo" style="margin-left:6px">🏷️ XẢ KHO</span>' : ''}
                ${p.ctkm_tuslo ? '<span class="badge-promo" style="margin-left:6px">🎁 TẶNG QUÀ</span>' : ''}
            </div>
            <div class="list-meta">
                <span class="list-meta-brand">${BRAND_ICONS[p.thuong_hieu]||''} ${escHtml(p.thuong_hieu)}</span>
                <span>📌 <strong>${escHtml(p.ma_sp)}</strong></span>
                ${p.ma_item ? `<span>🔢 ${escHtml(p.ma_item)}</span>` : ''}
                ${p.nhom_sp ? `<span>🗂️ ${escHtml(p.nhom_sp)}</span>` : ''}
                ${p.kich_thuoc ? `<span>📏 ${escHtml(p.kich_thuoc)}</span>` : ''}
                ${stock.total >= 0 ? `<span class="badge-stock ${stock.cls}">${stock.label}</span>` : ''}
            </div>
            ${topKho.length ? `<div class="list-stock">
                ${topKho.map(([k,v]) => `<span class="list-stock-item ${v<10?'badge-low':'badge-in'}">${escHtml(k)}: ${v}</span>`).join('')}
            </div>` : ''}
        </div>
        <div class="list-price-col">
            <div class="list-price">${formatPrice(price)}</div>
            <div class="list-price-label">${(PRICE_LABELS[selectedPriceType]||'').split(' (')[0]}</div>
        </div>
        <div class="list-actions">
            <button class="btn-action-sm" onclick="event.stopPropagation();openDetail(${p.id})" title="Chi tiết">🔍</button>
            <button class="btn-action-sm ${isFav?'active':''}" onclick="event.stopPropagation();toggleFav('${escJs(p.ma_sp)}')" title="Yêu thích">❤️</button>
            <button class="btn-action-sm ${isQuote?'active':''}" onclick="event.stopPropagation();addToQuote(${p.id})" title="Báo giá">📋</button>
        </div>
    </div>`;
}

// ======================== TAB 2: MASTER EXCEL PRICE & INVENTORY TABLE ========================
function renderMasterTable() {
    const container = document.getElementById('pricelist-table-container');
    if (!container) return;

    const start = (currentTablePage - 1) * TABLE_PAGE_SIZE;
    const page  = filteredProducts.slice(start, start + TABLE_PAGE_SIZE);
    const wh    = document.getElementById('filter-warehouse').value;

    document.getElementById('table-results-count').textContent =
        `Đang lọc ${filteredProducts.length.toLocaleString('vi-VN')} sản phẩm — Bấm vào bất kỳ dòng nào để xem chi tiết đầy đủ`;

    const rowsHtml = page.map((p, idx) => {
        const imgThumb = p.hinh_anh
            ? `<img src="${escHtml(p.hinh_anh)}" style="width:42px;height:42px;object-fit:contain;border-radius:4px;background:#fff;border:1px solid var(--border-light)" loading="lazy">`
            : `<span style="font-size:20px">${BRAND_ICONS[p.thuong_hieu]||'🛁'}</span>`;
        const totalStock = getStockTotal(p, wh);
        const mtStock = p.ton_kho?.['HTPP MT'] || 0;
        const khStock = p.ton_kho?.['Khánh Hòa'] || 0;
        const dlStock = p.ton_kho?.['Đắk Lắk'] || 0;
        const glStock = p.ton_kho?.['Gia Lai'] || 0;

        return `<tr onclick="openDetail(${p.id})">
            <td style="text-align:center">${start + idx + 1}</td>
            <td style="text-align:center">${imgThumb}</td>
            <td><strong>${escHtml(p.thuong_hieu)}</strong><br><small style="color:var(--text-muted)">${escHtml(p.nhom_sp)}</small></td>
            <td><code style="font-weight:700;color:var(--primary)">${escHtml(p.ma_sp)}</code><br><small style="color:var(--text-muted)">${escHtml(p.ma_item)}</small></td>
            <td style="max-width:260px;white-space:normal;font-weight:600">${p.hang_ban_chay?'🔥 ':''}${escHtml(p.ten_sp)}</td>
            <td style="text-align:center">${escHtml(p.dvt)}</td>
            <td class="num">${p.gia_cong_bo ? p.gia_cong_bo.toLocaleString('vi-VN') : '-'}</td>
            <td class="num">${p.gia_niem_yet ? p.gia_niem_yet.toLocaleString('vi-VN') : '-'}</td>
            <td class="num hi-price">${p.gia_ban_le ? p.gia_ban_le.toLocaleString('vi-VN') : '-'}</td>
            <td class="num">${p.gia_thau_tho ? p.gia_thau_tho.toLocaleString('vi-VN') : '-'}</td>
            <td class="num">${p.dai_ly_c1 ? p.dai_ly_c1.toLocaleString('vi-VN') : '-'}</td>
            <td class="num">${p.dai_ly_c4 ? p.dai_ly_c4.toLocaleString('vi-VN') : '-'}</td>
            <td class="num">${p.npp_c1 ? p.npp_c1.toLocaleString('vi-VN') : '-'}</td>
            <td class="num">${p.npp_c3 ? p.npp_c3.toLocaleString('vi-VN') : '-'}</td>
            <td class="num">${p.gia_ban_mau ? p.gia_ban_mau.toLocaleString('vi-VN') : '-'}</td>
            <td class="num" style="font-weight:800;color:${totalStock>0?'var(--success)':'var(--text-muted)'}">${totalStock.toLocaleString('vi-VN')}</td>
            <td class="num">${mtStock || '-'}</td>
            <td class="num">${khStock || '-'}</td>
            <td class="num">${dlStock || '-'}</td>
            <td class="num">${glStock || '-'}</td>
            <td><button class="btn btn-sm btn-outline" onclick="event.stopPropagation();addToQuote(${p.id})">+Báo giá</button></td>
        </tr>`;
    }).join('');

    container.innerHTML = `<table class="excel-table">
        <thead>
            <tr>
                <th>#</th>
                <th>Ảnh</th>
                <th>Thương hiệu / Nhóm</th>
                <th>Mã SP / Mã Item</th>
                <th>Tên sản phẩm</th>
                <th>ĐVT</th>
                <th class="num">Giá Công Bố<br><small>(Chưa VAT)</small></th>
                <th class="num">Giá Niêm Yết<br><small>(Có VAT)</small></th>
                <th class="num">Giá Bán Lẻ</th>
                <th class="num">Giá Thầu Thợ<br><small>(CK 10%)</small></th>
                <th class="num">Đại Lý C1-C3<br><small>(CK 20%)</small></th>
                <th class="num">Đại Lý C4</th>
                <th class="num">NPP C1-C2<br><small>(CK 22%)</small></th>
                <th class="num">NPP C3<br><small>(CK 25%)</small></th>
                <th class="num">Giá Bán Mẫu</th>
                <th class="num">${wh ? `Tồn ${wh}` : 'Tổng Tồn'}</th>
                <th class="num">HTPP MT</th>
                <th class="num">Khánh Hòa</th>
                <th class="num">Đắk Lắk</th>
                <th class="num">Gia Lai</th>
                <th>Thao tác</th>
            </tr>
        </thead>
        <tbody>${rowsHtml}</tbody>
    </table>`;

    renderPagination('table-pagination', filteredProducts.length, TABLE_PAGE_SIZE, currentTablePage, 'goTablePage');
}

function goTablePage(p) {
    const max = Math.ceil(filteredProducts.length / TABLE_PAGE_SIZE);
    if (p < 1 || p > max) return;
    currentTablePage = p;
    renderMasterTable();
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function exportFilteredTableCSV() {
    let csv = '\uFEFFSTT,Thương hiệu,Nhóm SP,Mã Item,Mã SP,Tên sản phẩm,ĐVT,Thuế VAT,Giá Công Bố (Chưa VAT),Giá Niêm Yết (Có VAT),Giá Bán Lẻ,Giá Thầu Thợ,Đại Lý C1,Đại Lý C4,NPP C1,NPP C3,Giá Bán Mẫu,Tổng Tồn Kho,HTPP MT,Khánh Hòa,Đắk Lắk,Gia Lai,Kích thước,Bảo hành\n';
    filteredProducts.forEach((p, i) => {
        const totalStock = getStockTotal(p);
        csv += `${i+1},"${p.thuong_hieu}","${p.nhom_sp}","${p.ma_item}","${p.ma_sp}","${p.ten_sp.replace(/"/g,'""')}","${p.dvt}",${p.thue},${p.gia_cong_bo},${p.gia_niem_yet},${p.gia_ban_le},${p.gia_thau_tho},${p.dai_ly_c1},${p.dai_ly_c4},${p.npp_c1},${p.npp_c3},${p.gia_ban_mau},${totalStock},${p.ton_kho?.['HTPP MT']||0},${p.ton_kho?.['Khánh Hòa']||0},${p.ton_kho?.['Đắk Lắk']||0},${p.ton_kho?.['Gia Lai']||0},"${(p.kich_thuoc||'').replace(/"/g,'""')}","${(p.bao_hanh||'').replace(/"/g,'""')}"\n`;
    });
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `BangGia_HSH_${filteredProducts.length}SP.csv`;
    a.click();
    showToast(`✅ Đã xuất ${filteredProducts.length} sản phẩm ra file Excel CSV!`, 'success');
}

// ======================== TAB 3: PROMOTIONS, CLEARANCE & NEW LAUNCH ========================
function renderPromosTab() {
    if (!extrasData) return;
    const xk = extrasData.xa_kho_2026 || [];
    const rm = extrasData.ra_mat_tuslo || [];
    const pt = extrasData.pt_ctkm || [];

    const xkRows = xk.map((item, i) => {
        const prod = allProducts.find(p => p.ma_item === item.ma_item);
        return `<tr ${prod ? `onclick="openDetail(${prod.id})" style="cursor:pointer"` : ''}>
            <td>${i+1}</td>
            <td><span class="badge-promo">${escHtml(item.nhom_uu_dai.split('-')[0])}</span></td>
            <td><code>${escHtml(item.ma_item)}</code></td>
            <td><strong>${escHtml(item.ten_sp)}</strong></td>
            <td class="num">${formatPrice(item.gia_niem_yet)}</td>
            <td class="num" style="color:var(--primary);font-weight:700">${formatPrice(item.gia_new_0_60)}</td>
            <td class="num">${formatPrice(item.gia_60_90)}</td>
            <td class="num">${formatPrice(item.gia_90_180)}</td>
            <td class="num">${formatPrice(item.gia_180_360)}</td>
            <td class="num" style="color:var(--success);font-weight:800">${formatPrice(item.gia_tren_360)}</td>
            <td class="num">${formatPrice(item.gia_thau_tho)}</td>
            <td class="num">${formatPrice(item.gia_dai_ly)}</td>
        </tr>`;
    }).join('');

    const rmRows = rm.map((item, i) => {
        const prod = allProducts.find(p => p.ma_item === item.ma_item);
        return `<tr ${prod ? `onclick="openDetail(${prod.id})" style="cursor:pointer"` : ''}>
            <td>${i+1}</td>
            <td><code>${escHtml(item.ma_item)}</code></td>
            <td><strong>${escHtml(item.ten_sp)}</strong></td>
            <td class="num">${formatPrice(item.gia_niem_yet)}</td>
            <td class="num" style="color:var(--primary);font-weight:700">${formatPrice(item.gia_ban_le)}</td>
            <td class="num">${formatPrice(item.gia_dai_ly)}</td>
            <td><span class="badge-hot">${escHtml(item.ctkm)}</span></td>
            <td style="color:var(--success);font-weight:700">🎁 ${escHtml(item.qua_tang)}<br><small style="color:var(--text-muted)">Tổng gói quà lên đến: ${formatPrice(item.tong_qua_tang)}</small></td>
        </tr>`;
    }).join('');

    const ptRows = pt.map(item => `<tr>
        <td>${item.stt}</td>
        <td><code>${escHtml(item.ma_item)}</code></td>
        <td><strong>${escHtml(item.ten_sp)}</strong></td>
        <td>${escHtml(item.dvt)}</td>
        <td style="text-align:center;font-weight:700">${item.so_luong}</td>
        <td class="num">${formatPrice(item.gia_niem_yet)}</td>
        <td class="num" style="color:var(--primary);font-weight:700">${formatPrice(item.gia_km)}</td>
        <td class="num" style="font-weight:700">${item.thanh_tien_km > 0 ? formatPrice(item.thanh_tien_km) : '🎁 Tặng 0đ'}</td>
        <td class="num">${formatPrice(item.thanh_tien_sau_km)}</td>
        <td class="num" style="color:var(--success);font-weight:800">+${formatPrice(item.chenh_lech)}</td>
    </tr>`).join('');

    document.getElementById('promos-container').innerHTML = `
        <div class="hb-card" style="margin-bottom:22px">
            <div class="hb-card-title">
                <span>🏷️ Chương Trình “Xả Kho Đón Mẫu Mới 2026” (Sheet: XẢ KHO ĐÓN MẪU MỚI 2026)</span>
                <span class="badge-promo">Bồn cầu CK thêm 12% | Sen tắm CK thêm 15%</span>
            </div>
            <p style="font-size:13px;color:var(--text-secondary);margin-bottom:12px">
                Áp dụng chính sách thanh lý hàng trưng bày &amp; xả kho theo độ tuổi tồn kho (0-60 ngày, 60-90 ngày, 90-180 ngày, 180-360 ngày, &gt;360 ngày). Bấm vào sản phẩm để xem chi tiết &amp; hình ảnh.
            </p>
            <div style="overflow-x:auto">
                <table class="hb-table">
                    <thead>
                        <tr>
                            <th>#</th><th>Nhóm ưu đãi</th><th>Mã Item</th><th>Tên sản phẩm</th>
                            <th class="num">Giá Niêm Yết</th><th class="num">NEW (0-60N)</th>
                            <th class="num">60-90N</th><th class="num">90-180N</th>
                            <th class="num">180-360N</th><th class="num">&gt;360N</th>
                            <th class="num">Thầu Thợ</th><th class="num">Đại Lý</th>
                        </tr>
                    </thead>
                    <tbody>${xkRows}</tbody>
                </table>
            </div>
        </div>

        <div class="hb-card" style="margin-bottom:22px">
            <div class="hb-card-title">
                <span>🎁 Chương Trình “Ra Mắt Sản Phẩm Mới - Bộ Sưu Tập TUSLO”</span>
                <span class="badge-hot">Mua 1 Tặng Quà Lên Đến 7.1 Triệu</span>
            </div>
            <p style="font-size:13px;color:var(--text-secondary);margin-bottom:12px">
                Lưu ý: Chương trình tặng quà không áp dụng đồng thời với chính sách bán mẫu.
            </p>
            <div style="overflow-x:auto">
                <table class="hb-table">
                    <thead>
                        <tr>
                            <th>#</th><th>Mã Item</th><th>Tên sản phẩm chính</th>
                            <th class="num">Giá Niêm Yết</th><th class="num">Giá Bán Lẻ</th>
                            <th class="num">Giá Đại Lý (CK 20%)</th><th>Chương trình</th><th>Chi tiết quà tặng đi kèm</th>
                        </tr>
                    </thead>
                    <tbody>${rmRows}</tbody>
                </table>
            </div>
        </div>

        <div class="hb-card">
            <div class="hb-card-title">
                <span>📈 Phân Tích Gói Combo Khuyến Mãi Đại Lý (Sheet: PT - CTKM)</span>
                <span style="font-size:12px;color:var(--success);font-weight:700">Lợi nhuận chênh lệch: +4.078.080 ₫</span>
            </div>
            <div style="overflow-x:auto">
                <table class="hb-table">
                    <thead>
                        <tr>
                            <th>#</th><th>Mã Item</th><th>Tên sản phẩm</th><th>ĐVT</th><th>SL</th>
                            <th class="num">Đơn Giá NY</th><th class="num">Đơn Giá ĐL</th>
                            <th class="num">Thành Tiền Trong KM</th><th class="num">Sau KM</th>
                            <th class="num">Chênh Lệch Lợi Nhuận</th>
                        </tr>
                    </thead>
                    <tbody>${ptRows}</tbody>
                </table>
            </div>
        </div>
    `;
}

// ======================== TAB 4: INSTALLATION COSTS & SALES POLICIES ========================
function renderPoliciesTab() {
    if (!extrasData) return;
    const cpld = extrasData.chi_phi_lap_dat;
    const cs   = extrasData.chinh_sach_chiet_khau;
    const links= extrasData.thu_vien_links || [];

    const lapDatRows = cpld.bang_gia.map(r => `<tr>
        <td style="text-align:center;font-weight:700">${r.stt}</td>
        <td><strong>${escHtml(r.mat_hang)}</strong></td>
        <td class="num" style="font-weight:600">${formatPrice(r.chua_vat)}</td>
        <td class="num" style="color:var(--primary);font-weight:800;font-size:14px">${formatPrice(r.co_vat)}</td>
    </tr>`).join('');

    document.getElementById('policies-container').innerHTML = `
        <div class="hb-grid">
            <!-- BẢNG CHI PHÍ LẮP ĐẶT -->
            <div class="hb-card">
                <div class="hb-card-title">
                    <span>🛠️ Chính Sách Chi Phí Lắp Đặt (Sheet: CHI PHÍ LẮP ĐẶT)</span>
                    <span class="chip">${escHtml(cpld.so_van_ban)}</span>
                </div>
                <p style="font-size:12.5px;color:var(--text-secondary);margin-bottom:10px">
                    <strong>Ngày áp dụng:</strong> ${escHtml(cpld.ngay_ban_hanh)}<br>
                    <strong>Phạm vi:</strong> ${escHtml(cpld.pham_vi)}
                </p>
                <table class="hb-table" style="margin-bottom:12px">
                    <thead>
                        <tr><th style="width:45px">STT</th><th>Tên mặt hàng lắp đặt</th><th class="num">Chưa VAT (đ/bộ)</th><th class="num">Có VAT 8-10% (đ/bộ)</th></tr>
                    </thead>
                    <tbody>${lapDatRows}</tbody>
                </table>
                <div class="note-box" style="font-size:12px">
                    ${cpld.luu_y.map(l => `• ${escHtml(l)}`).join('\n')}
                </div>
            </div>

            <!-- THƯ VIỆN LINK GỐC GOOGLE DRIVE / LIVE SHEET -->
            <div class="hb-card">
                <div class="hb-card-title">
                    <span>📂 Thư Viện Tài Liệu, Catalogue &amp; Live Sheet (Sheet: Thư viện có gì)</span>
                </div>
                <p style="font-size:12.5px;color:var(--text-secondary);margin-bottom:12px">
                    Truy cập trực tiếp kho Google Drive Catalogue, Video, File in Tem/Tab giá A5-A7 và bảng Tồn kho Live của ngành hàng:
                </p>
                <div>
                    ${links.map(l => `
                        <a class="hb-link-card" href="${escHtml(l.url)}" target="_blank" rel="noopener">
                            <div>
                                <div style="font-size:11px;color:var(--text-muted);text-transform:uppercase">${escHtml(l.nhom)}</div>
                                <div>${escHtml(l.ten)}</div>
                            </div>
                            <span>↗️ Mở link</span>
                        </a>
                    `).join('')}
                </div>
            </div>
        </div>

        <div class="hb-grid">
            <!-- CHÍNH SÁCH KHÁCH HÀNG CÔNG TRÌNH -->
            <div class="hb-card">
                <div class="hb-card-title"><span>🏗️ Chính Sách Chiết Khấu Khách Hàng Công Trình</span></div>
                <table class="hb-table">
                    <thead><tr><th>Hạng mục / Doanh số đơn hàng</th><th class="num">Mức chiết khấu</th></tr></thead>
                    <tbody>
                        ${cs.cong_trinh.map(r => `<tr><td>${escHtml(r.hang_muc)}</td><td class="num" style="color:var(--primary);font-weight:800">${escHtml(r.muc_ck)}</td></tr>`).join('')}
                    </tbody>
                </table>
            </div>

            <!-- CHÍNH SÁCH ĐƠN HÀNG KHÁCH LẺ & THẦU THỢ + CHUYÊN NGÀNH -->
            <div class="hb-card">
                <div class="hb-card-title"><span>💼 Chiết Khấu Đơn Hàng Lẻ/Thầu Thợ &amp; Chuyên Ngành HSH</span></div>
                <h4 style="font-size:12.5px;margin:8px 0;color:var(--text-secondary)">1. Khung doanh số đơn hàng Khách lẻ &amp; Thầu thợ (Chưa VAT):</h4>
                <table class="hb-table" style="margin-bottom:14px">
                    <thead><tr><th>Doanh số đơn hàng</th><th class="num">Chiết khấu</th></tr></thead>
                    <tbody>
                        ${cs.khach_le_thau_tho.map(r => `<tr><td>${escHtml(r.doanh_so)}</td><td class="num" style="color:var(--primary);font-weight:800">${escHtml(r.muc_ck)}</td></tr>`).join('')}
                    </tbody>
                </table>

                <h4 style="font-size:12.5px;margin:8px 0;color:var(--text-secondary)">2. Chính sách chuyên ngành thương hiệu Hoa Sen Home (NPP / Đại lý / KHTT):</h4>
                <table class="hb-table" style="margin-bottom:14px">
                    <thead><tr><th>Doanh số mua hàng tháng theo thương hiệu</th><th class="num">Chiết khấu</th></tr></thead>
                    <tbody>
                        ${cs.chuyen_nganh_hsh.map(r => `<tr><td>${escHtml(r.doanh_so_thang)}</td><td class="num" style="color:var(--success);font-weight:800">${escHtml(r.muc_ck)}</td></tr>`).join('')}
                    </tbody>
                </table>

                <h4 style="font-size:12.5px;margin:8px 0;color:var(--text-secondary)">3. Chính sách nhận hàng tại kho:</h4>
                <table class="hb-table">
                    <tbody>
                        ${cs.nhan_hang_tai_kho.map(r => `<tr><td>${escHtml(r.dia_diem)}</td><td class="num" style="font-weight:800">${escHtml(r.muc_ck)}</td></tr>`).join('')}
                    </tbody>
                </table>
            </div>
        </div>
    `;
}

// ======================== TAB 5: PRODUCT KNOWLEDGE, CODE CONVERSION & WARRANTY ========================
function renderKnowledgeTab() {
    if (!extrasData) return;
    const kt = extrasData.kien_thuc_sp || [];
    const cd = extrasData.bang_chuyen_doi_ma || {};
    const bh = extrasData.bao_hanh_va_khieu_nai || {};

    const ktRows = kt.map(r => `<tr>
        <td><strong style="color:var(--primary)">${escHtml(r.thuong_hieu)}</strong></td>
        <td><strong>${escHtml(r.san_pham)}</strong><br><small style="color:var(--text-secondary)">${escHtml(r.chi_tiet)}</small></td>
        <td>${escHtml(r.chat_lieu)}</td>
        <td style="white-space:pre-line;font-size:12px">${escHtml(r.cong_nghe)}</td>
        <td style="white-space:pre-line;font-size:12px">${escHtml(r.cong_dung)}</td>
        <td><span class="badge-in" style="padding:2px 7px;border-radius:6px;font-size:11px">${escHtml(r.bao_hanh)}</span></td>
        <td style="white-space:pre-line;font-size:12px;color:#92400E">${escHtml(r.phu_kien_di_kem)}</td>
        <td style="font-weight:700;color:var(--success)">${escHtml(r.tu_van_mua_them)}</td>
    </tr>`).join('');

    const tusloMapRows = (cd.tuslo_cu_moi || []).map(r => `<tr>
        <td><code>${escHtml(r.ma_cu)}</code></td>
        <td style="text-align:center">➔</td>
        <td><code style="color:var(--primary);font-weight:800">${escHtml(r.ma_moi)}</code></td>
    </tr>`).join('');

    const napMapRows = (cd.nap_bon_cau || []).map(r => `<tr>
        <td><code style="color:var(--info);font-weight:800">${escHtml(r.ma_nap)}</code></td>
        <td style="text-align:center">dùng cho</td>
        <td><code style="font-weight:700">${escHtml(r.bon_cau)}</code></td>
    </tr>`).join('');

    const arrowMapRows = (cd.arrow_trung_anh || []).map((r, i) => `<tr>
        <td>${i+1}</td>
        <td><code>${escHtml(r.item_cn)}</code></td>
        <td><strong style="color:var(--warning)">${escHtml(r.ma_cn)}</strong></td>
        <td style="text-align:center">⇄</td>
        <td><code>${escHtml(r.item_en)}</code></td>
        <td><strong style="color:var(--success)">${escHtml(r.ma_en)}</strong></td>
        <td style="font-size:11.5px">${escHtml(r.ten_en || r.ten_cn)}</td>
    </tr>`).join('');

    document.getElementById('knowledge-container').innerHTML = `
        <!-- KIẾN THỨC SẢN PHẨM & PHỤ KIỆN ĐI KÈM -->
        <div class="hb-card" style="margin-bottom:22px">
            <div class="hb-card-title">
                <span>📚 Kiến Thức Sản Phẩm, Phụ Kiện Đi Kèm &amp; Tư Vấn Mua Thêm (Sheet: PHỤ KIỆN ĐI KÈM)</span>
            </div>
            <div style="overflow-x:auto">
                <table class="hb-table">
                    <thead>
                        <tr>
                            <th>Hãng</th><th>Sản phẩm / Phân loại</th><th>Chất liệu</th>
                            <th>Công nghệ</th><th>Công dụng / Nhận biết</th><th>Bảo hành</th>
                            <th>Phụ kiện đi kèm trong thùng</th><th>Cần tư vấn mua thêm</th>
                        </tr>
                    </thead>
                    <tbody>${ktRows}</tbody>
                </table>
            </div>
        </div>

        <!-- BẢNG TRA CỨU MÃ CŨ <-> MỚI & NẮP BỒN CẦU & BẢO HÀNH -->
        <div class="hb-grid">
            <div class="hb-card">
                <div class="hb-card-title"><span>🔄 Bảng Đổi Mã Cũ ➔ Mới TUSLO &amp; Nắp Bồn Cầu Phù Hợp (Sheet: LƯU Ý)</span></div>
                <div style="display:grid;grid-template-columns:1fr 1fr;gap:14px">
                    <div>
                        <h4 style="font-size:12.5px;margin-bottom:6px;color:var(--text-secondary)">Mã cũ ➔ Mã mới TUSLO:</h4>
                        <table class="hb-table">
                            <thead><tr><th>Mã cũ</th><th></th><th>Mã mới</th></tr></thead>
                            <tbody>${tusloMapRows}</tbody>
                        </table>
                    </div>
                    <div>
                        <h4 style="font-size:12.5px;margin-bottom:6px;color:var(--text-secondary)">Mã nắp bồn cầu thay thế:</h4>
                        <table class="hb-table">
                            <thead><tr><th>Mã nắp</th><th></th><th>Mã bồn cầu</th></tr></thead>
                            <tbody>${napMapRows}</tbody>
                        </table>
                    </div>
                </div>
            </div>

            <div class="hb-card">
                <div class="hb-card-title"><span>🛡️ Quy Trình Xử Lý Khiếu Nại &amp; Hotline Bảo Hành Các Hãng</span></div>
                <div class="desc-box" style="margin-bottom:12px;font-size:12.5px">
                    <strong>1. Thương hiệu OEM Hoa Sen (TUSLO &amp; LUSHINE):</strong><br>
                    • Gửi <em>BM01 (Phiếu TNKN)</em> + <em>BM02 (Biên bản kiểm tra)</em> kèm hình ảnh/video và hóa đơn về email: <strong style="color:var(--primary)">${escHtml(bh.email_ktcl)}</strong>.<br>
                    <strong>2. Thương hiệu nội địa (TOTO, INAX, VIGLACERA, KITTO):</strong><br>
                    • Gửi thông tin (Tên chủ nhà, SĐT, Địa chỉ, Mã SP, Hình ảnh/Video lỗi) về ngành hàng hoặc liên hệ tổng đài hãng xử lý trong 24h:
                </div>
                <table class="hb-table" style="margin-bottom:12px">
                    <thead><tr><th>Thương hiệu</th><th>Tổng đài bảo hành</th><th>Chính sách hãng</th></tr></thead>
                    <tbody>
                        ${(bh.hang_noi_dia || []).map(h => `<tr>
                            <td><strong>${escHtml(h.thuong_hieu)}</strong></td>
                            <td><strong style="color:var(--primary)">📞 ${escHtml(h.hotline)}</strong></td>
                            <td><a href="${escHtml(h.link)}" target="_blank" style="color:var(--info)">Xem web hãng ↗️</a></td>
                        </tr>`).join('')}
                    </tbody>
                </table>
                <h4 style="font-size:12px;margin-bottom:6px;color:var(--text-secondary)">Thời hạn bảo hành TUSLO &amp; LUSHINE:</h4>
                <table class="hb-table">
                    <tbody>
                        ${(bh.bao_hanh_tuslo || []).map(b => `<tr><td>${escHtml(b.danh_muc)}</td><td class="num" style="font-weight:700;color:var(--success)">${escHtml(b.thoi_gian)}</td></tr>`).join('')}
                    </tbody>
                </table>
            </div>
        </div>

        <!-- BẢNG MÃ BAO BÌ TIẾNG TRUNG <-> TIẾNG ANH ARROW -->
        <div class="hb-card">
            <div class="hb-card-title">
                <span>🏹 Bảng Đối Chiếu Mã Bao Bì Tiếng Trung ⇄ Tiếng Anh Thương Hiệu ARROW (31 Mã)</span>
            </div>
            <div style="overflow-x:auto">
                <table class="hb-table">
                    <thead>
                        <tr>
                            <th>#</th><th>Mã Item (Bao bì Trung)</th><th>Mã NCC (Bao bì Trung)</th><th></th>
                            <th>Mã Item (Bao bì Anh)</th><th>Mã NCC (Bao bì Anh)</th><th>Tên sản phẩm Hoa Sen Home</th>
                        </tr>
                    </thead>
                    <tbody>${arrowMapRows}</tbody>
                </table>
            </div>
        </div>
    `;
}

// ======================== TAB 6: STORE DIRECTORY (DSCH) ========================
function renderStoresTab(filterText = '') {
    if (!extrasData) return;
    const stores = extrasData.danh_sach_cua_hang || [];
    const q = filterText.trim().toLowerCase();
    const filtered = q
        ? stores.filter(s =>
            s.tinh_moi.toLowerCase().includes(q) ||
            s.ma_ch.toLowerCase().includes(q) ||
            s.ten_ch.toLowerCase().includes(q) ||
            (s.tinh_cu && s.tinh_cu.toLowerCase().includes(q)) ||
            (s.ma_ch_cu && s.ma_ch_cu.toLowerCase().includes(q)) ||
            (s.ten_ch_cu && s.ten_ch_cu.toLowerCase().includes(q))
          )
        : stores;

    const rows = filtered.map((s, i) => `<tr>
        <td>${i+1}</td>
        <td><strong>${escHtml(s.tinh_moi)}</strong></td>
        <td><code style="color:var(--primary);font-weight:800">${escHtml(s.ma_ch)}</code></td>
        <td><strong>${escHtml(s.ten_ch)}</strong></td>
        <td><span class="chip">${escHtml(s.mo_hinh)}</span></td>
        <td style="color:var(--text-secondary)">${escHtml(s.tinh_cu)}</td>
        <td><code>${escHtml(s.ma_ch_cu)}</code></td>
        <td style="color:var(--text-secondary)">${escHtml(s.ten_ch_cu)}</td>
    </tr>`).join('');

    const container = document.getElementById('stores-container');
    if (!document.getElementById('store-search-inp')) {
        container.innerHTML = `
            <div class="hb-card">
                <div class="hb-card-title">
                    <span>🏪 Danh Sách Cửa Hàng Hoa Sen Home &amp; Chuyển Đổi Mã Cũ/Mới (Sheet: DSCH — ${stores.length} CH)</span>
                </div>
                <div style="margin-bottom:14px;max-width:460px">
                    <input id="store-search-inp" type="text" placeholder="🔍 Tìm tỉnh, mã cửa hàng mới/cũ, tên cửa hàng (VD: Khánh Hòa, KHH.07, L56...)"
                        style="width:100%;padding:9px 14px;border:1.5px solid var(--border);border-radius:8px;font-family:var(--font);font-size:13.5px"
                        oninput="renderStoresTableBody(this.value)">
                </div>
                <div style="overflow-x:auto" id="stores-table-wrap"></div>
            </div>
        `;
    }
    renderStoresTableBody(filterText);
}

function renderStoresTableBody(filterText = '') {
    const stores = extrasData?.danh_sach_cua_hang || [];
    const q = filterText.trim().toLowerCase();
    const filtered = q
        ? stores.filter(s =>
            s.tinh_moi.toLowerCase().includes(q) ||
            s.ma_ch.toLowerCase().includes(q) ||
            s.ten_ch.toLowerCase().includes(q) ||
            (s.tinh_cu && s.tinh_cu.toLowerCase().includes(q)) ||
            (s.ma_ch_cu && s.ma_ch_cu.toLowerCase().includes(q)) ||
            (s.ten_ch_cu && s.ten_ch_cu.toLowerCase().includes(q))
          )
        : stores;

    document.getElementById('stores-table-wrap').innerHTML = `
        <table class="hb-table">
            <thead>
                <tr>
                    <th>#</th><th>Tỉnh Mới</th><th>Mã CH Mới</th><th>Tên Cửa Hàng Mới</th><th>Mô Hình</th>
                    <th>Tỉnh Cũ</th><th>Mã CH Cũ</th><th>Tên Cửa Hàng Cũ</th>
                </tr>
            </thead>
            <tbody>
                ${filtered.map((s, i) => `<tr>
                    <td>${i+1}</td>
                    <td><strong>${escHtml(s.tinh_moi)}</strong></td>
                    <td><code style="color:var(--primary);font-weight:800">${escHtml(s.ma_ch)}</code></td>
                    <td><strong>${escHtml(s.ten_ch)}</strong></td>
                    <td><span class="chip">${escHtml(s.mo_hinh)}</span></td>
                    <td style="color:var(--text-secondary)">${escHtml(s.tinh_cu)}</td>
                    <td><code>${escHtml(s.ma_ch_cu)}</code></td>
                    <td style="color:var(--text-secondary)">${escHtml(s.ten_ch_cu)}</td>
                </tr>`).join('')}
            </tbody>
        </table>
    `;
}

// ======================== PAGINATION HELPER ========================
function renderPagination(elId, totalItems, pageSize, curPage, fnName) {
    const total = Math.ceil(totalItems / pageSize);
    const el = document.getElementById(elId);
    if (!el) return;
    if (total <= 1) { el.innerHTML = ''; return; }

    const range = buildPageRange(curPage, total);
    let html = `<button class="page-btn" onclick="${fnName}(${curPage-1})" ${curPage===1?'disabled':''}>◀</button>`;
    range.forEach(p => {
        if (p === '…') html += `<span style="padding:0 4px;color:var(--text-muted)">…</span>`;
        else html += `<button class="page-btn ${p===curPage?'active':''}" onclick="${fnName}(${p})">${p}</button>`;
    });
    html += `<button class="page-btn" onclick="${fnName}(${curPage+1})" ${curPage===total?'disabled':''}>▶</button>`;
    el.innerHTML = html;
}

function buildPageRange(cur, total) {
    if (total <= 7) return Array.from({length:total},(_,i)=>i+1);
    if (cur <= 4)   return [1,2,3,4,5,'…',total];
    if (cur >= total-3) return [1,'…',total-4,total-3,total-2,total-1,total];
    return [1,'…',cur-1,cur,cur+1,'…',total];
}

function goPage(p) {
    const max = Math.ceil(filteredProducts.length / PAGE_SIZE);
    if (p < 1 || p > max) return;
    currentPage = p;
    renderProducts();
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// ======================== DETAIL MODAL ========================
function openDetail(id) {
    const p = allProducts.find(x => x.id === id);
    if (!p) return;

    const isFav = favorites.includes(p.ma_sp);
    const isCmp = compareList.includes(p.ma_sp);

    // 1. Build current price rows
    const priceRows = Object.entries(PRICE_LABELS)
        .filter(([k]) => p[k] > 0)
        .map(([k, label]) => {
            const hi = k === selectedPriceType || k === 'gia_ban_le';
            const pct = (p.gia_niem_yet > 0 && p[k] < p.gia_niem_yet)
                ? `(-${Math.round((1 - p[k] / p.gia_niem_yet) * 100)}%)`
                : '';
            return `<tr class="${hi?'price-row-primary':''}">
                <td>${label}</td>
                <td class="${hi?'price-highlight':''}">${formatPrice(p[k])}</td>
                <td style="color:var(--success);font-weight:600;font-size:11.5px">${pct}</td>
            </tr>`;
        }).join('');

    // 2. Historical prices
    const histEntries = Object.entries(p.lich_su_gia || {});
    const histHtml = histEntries.length ? `
        <div class="modal-section">
            <div class="sec-title">🕰️ Lịch Sử Giá Các Kỳ Trước (Sheet: DATA GIÁ)</div>
            <table class="spec-table">
                ${histEntries.map(([k, v]) => `<tr><td style="width:240px">${escHtml(k)}</td><td>${formatPrice(v)}</td></tr>`).join('')}
            </table>
        </div>` : '';

    // 3. Stock breakdown
    const mainKhos = p.ton_kho
        ? Object.entries(p.ton_kho).filter(([k]) => !k.includes('Tổng'))
        : [];
    const stockHtml = mainKhos.map(([kho, qty]) => {
        const cls = qty === 0 ? 's-out' : qty < 10 ? 's-low' : 's-in';
        return `<div class="stock-item ${cls}">
            <div class="stock-name">${escHtml(kho)}</div>
            <div class="stock-qty">${qty.toLocaleString('vi-VN')}</div>
        </div>`;
    }).join('');

    const tongTon = getStockTotal(p);

    // 4. Image + Technical Drawing
    const imgHtml = p.hinh_anh
        ? `<img class="modal-img" id="detail-main-img" src="${escHtml(p.hinh_anh)}" alt="${escHtml(p.ten_sp)}" onclick="openLightbox(this.src)" title="Bấm để phóng to ảnh">
           <div style="font-size:11px;color:var(--text-muted);margin-top:6px">🔍 Bấm vào ảnh để phóng to</div>
           ${p.hinh_ban_ve ? `<div style="display:flex;gap:6px;margin-top:8px">
               <button class="btn btn-sm btn-outline" onclick="document.getElementById('detail-main-img').src='${escJs(p.hinh_anh)}'">📷 Ảnh SP</button>
               <button class="btn btn-sm btn-outline" onclick="document.getElementById('detail-main-img').src='${escJs(p.hinh_ban_ve)}'">📐 Bản vẽ kỹ thuật</button>
           </div>` : ''}`
        : `<div class="modal-img-icon">${BRAND_ICONS[p.thuong_hieu] || '🛁'}</div>`;

    // 5. Promo banners inside modal
    let promoBannerHtml = '';
    if (p.xa_kho) {
        promoBannerHtml += `<div class="suggest-box" style="margin-bottom:14px;border-left-color:#7C3AED;background:#F5F3FF;color:#4C1D95">
            <strong>🏷️ SẢN PHẨM NẰM TRONG CTKM XẢ KHO 2026:</strong> ${escHtml(p.xa_kho.nhom_uu_dai)}<br>
            • Giá NEW (0-60N): <strong>${formatPrice(p.xa_kho.gia_new_0_60)}</strong> | 60-90N: <strong>${formatPrice(p.xa_kho.gia_60_90)}</strong> | 90-180N: <strong>${formatPrice(p.xa_kho.gia_90_180)}</strong> | &gt;360N: <strong>${formatPrice(p.xa_kho.gia_tren_360)}</strong>
        </div>`;
    }
    if (p.ctkm_tuslo) {
        promoBannerHtml += `<div class="suggest-box" style="margin-bottom:14px">
            <strong>🎁 CTKM RA MẮT SẢN PHẨM MỚI TUSLO (${escHtml(p.ctkm_tuslo.ctkm)}):</strong><br>
            • Quà tặng kèm: <strong>${escHtml(p.ctkm_tuslo.qua_tang)}</strong> (Tổng gói quà lên đến ${formatPrice(p.ctkm_tuslo.tong_qua_tang)})
        </div>`;
    }

    document.getElementById('modal-content').innerHTML = `
    <div class="modal-product">
        <div class="modal-top">
            <div class="modal-img-box">${imgHtml}</div>
            <div>
                <div style="display:flex;gap:6px;flex-wrap:wrap;align-items:center;margin-bottom:8px">
                    <span class="modal-brand-chip" style="margin-bottom:0">${BRAND_ICONS[p.thuong_hieu]||''} ${escHtml(p.thuong_hieu)}</span>
                    ${p.hang_ban_chay ? '<span class="badge-hot">🔥 HÀNG BÁN CHẠY</span>' : ''}
                    ${p.uu_tien_online ? '<span class="badge-online">🌐 ƯU TIÊN ONLINE / TMĐT</span>' : ''}
                    ${p.ngung_nhap ? '<span class="badge-discont">⛔ NGƯNG NHẬP HÀNG</span>' : ''}
                </div>
                <div class="modal-title">${escHtml(p.ten_sp)}</div>
                <div class="chips-row">
                    <span class="chip">📌 Mã SP: <strong>${escHtml(p.ma_sp)}</strong></span>
                    ${p.ma_item ? `<span class="chip">🔢 Mã Item: <strong>${escHtml(p.ma_item)}</strong></span>` : ''}
                    ${p.dvt    ? `<span class="chip">📦 ĐVT: ${escHtml(p.dvt)}</span>`    : ''}
                    ${p.nhom_sp ? `<span class="chip">🗂️ ${escHtml(p.nhom_sp)}</span>` : ''}
                    ${p.thue > 0 ? `<span class="chip">🧾 VAT ${Math.round(p.thue*100)}%</span>` : ''}
                </div>
                ${p.ma_phu ? `<div style="margin-bottom:12px;font-size:12px;color:var(--info);font-weight:700;background:#EFF6FF;padding:8px 12px;border-radius:6px;border:1px solid #BFDBFE">🔄 ${escHtml(p.ma_phu)}</div>` : ''}
                ${promoBannerHtml}

                <div class="modal-section" style="margin-bottom:0">
                    <div class="sec-title">💰 Bảng Giá Chi Tiết Đa Cấp</div>
                    <table class="price-table">
                        <thead><tr><th>Cấp giá khách hàng</th><th>Đơn giá</th><th>Chiết khấu so với NY</th></tr></thead>
                        <tbody>${priceRows || '<tr><td colspan="3">Liên hệ</td></tr>'}</tbody>
                    </table>
                </div>
            </div>
        </div>

        <div class="modal-section">
            <div class="sec-title">📏 Thông Số Kỹ Thuật &amp; Bảo Hành</div>
            <table class="spec-table">
                ${p.kich_thuoc ? `<tr><td>Kích thước / Quy cách</td><td>${escHtml(p.kich_thuoc)}</td></tr>` : ''}
                ${p.bao_hanh   ? `<tr><td>Chính sách bảo hành</td><td style="color:var(--success)">🛡️ ${escHtml(p.bao_hanh)}</td></tr>` : ''}
                ${p.diem_trung_bay ? `<tr><td>Quy hoạch trưng bày</td><td>🏪 ${escHtml(p.diem_trung_bay)}</td></tr>` : ''}
                <tr><td>Nguồn danh mục</td><td>${escHtml(p.nguon || 'Bảng giá chính')}</td></tr>
            </table>
        </div>

        ${p.thong_tin ? `
        <div class="modal-section">
            <div class="sec-title">📝 Mô Tả &amp; Tính Năng Sản Phẩm</div>
            <div class="desc-box">${escHtml(p.thong_tin)}</div>
        </div>` : ''}

        ${p.khac ? `
        <div class="modal-section">
            <div class="sec-title">⚠️ Lưu Ý &amp; Linh Kiện Đi Kèm Trong Thùng</div>
            <div class="note-box">${escHtml(p.khac)}</div>
        </div>` : ''}

        ${p.goi_y_mua_kem ? `
        <div class="modal-section">
            <div class="sec-title">🛒 Gợi Ý Tư Vấn Sản Phẩm Mua Kèm</div>
            <div class="suggest-box">${escHtml(p.goi_y_mua_kem)}</div>
        </div>` : ''}

        ${stockHtml ? `
        <div class="modal-section">
            <div class="sec-title">
                <span>📦 Tồn Kho Theo Khu Vực &amp; Nhà Máy</span>
                <span style="margin-left:auto;color:${tongTon>0?'var(--success)':'var(--danger)'}">Tổng tồn: ${tongTon.toLocaleString('vi-VN')} ${escHtml(p.dvt)}</span>
            </div>
            <div class="stock-grid">${stockHtml}</div>
        </div>` : ''}

        ${histHtml}

        <div class="modal-actions">
            <button class="btn btn-primary" onclick="addToQuote(${p.id})">📋 Thêm vào báo giá</button>
            <button class="btn btn-success" onclick="copyProductZalo(${p.id})">📱 Copy gửi Zalo</button>
            <button class="btn btn-outline" id="modal-fav-btn" onclick="toggleFav('${escJs(p.ma_sp)}');updateModalFavBtn('${escJs(p.ma_sp)}')">
                ${isFav ? '❤️ Đã lưu yêu thích' : '🤍 Lưu yêu thích'}
            </button>
            <button class="btn btn-outline" id="modal-cmp-btn" onclick="toggleCompare('${escJs(p.ma_sp)}');updateModalCmpBtn('${escJs(p.ma_sp)}')">
                ${isCmp ? '⚖️ Đang so sánh' : '⚖️ So sánh'}
            </button>
            <button class="btn btn-outline" onclick="shareProduct('${escJs(p.ma_sp)}','${encodeURIComponent(p.ten_sp)}')">📤 Copy link SP</button>
            <button class="btn btn-outline" onclick="window.print()">🖨️ In phiếu SP</button>
        </div>
    </div>`;

    document.getElementById('modal-overlay').classList.add('active');
    document.body.style.overflow = 'hidden';
    history.pushState({}, '', `?sp=${encodeURIComponent(p.ma_sp)}`);
}

function openLightbox(src) {
    if (!src) return;
    document.getElementById('lightbox-img').src = src;
    document.getElementById('lightbox-overlay').classList.add('active');
}
function closeLightbox() {
    document.getElementById('lightbox-overlay').classList.remove('active');
}

function updateModalFavBtn(maSp) {
    const btn = document.getElementById('modal-fav-btn');
    if (btn) btn.innerHTML = favorites.includes(maSp) ? '❤️ Đã lưu yêu thích' : '🤍 Lưu yêu thích';
}
function updateModalCmpBtn(maSp) {
    const btn = document.getElementById('modal-cmp-btn');
    if (btn) btn.innerHTML = compareList.includes(maSp) ? '⚖️ Đang so sánh' : '⚖️ So sánh';
}

function closeModal(e) {
    if (e.target.id === 'modal-overlay') closeDetailModal();
}
function closeDetailModal() {
    document.getElementById('modal-overlay').classList.remove('active');
    document.body.style.overflow = '';
    history.pushState({}, '', location.pathname);
}

// ======================== FAVORITES ========================
function toggleFav(maSp) {
    const idx = favorites.indexOf(maSp);
    if (idx > -1) { favorites.splice(idx, 1); showToast('Đã bỏ khỏi danh sách yêu thích', 'warning'); }
    else          { favorites.push(maSp);      showToast('❤️ Đã lưu sản phẩm yêu thích!', 'success'); }
    localStorage.setItem('hsh_fav', JSON.stringify(favorites));
    updateBadges();
    renderProducts();
}

function showFavorites() {
    const prods = allProducts.filter(p => favorites.includes(p.ma_sp));
    let html = `<div class="quote-wrap">
        <div class="modal-page-title">❤️ Sản Phẩm Đã Lưu <small style="font-size:13px;color:var(--text-muted)">(${prods.length} SP)</small></div>`;
    if (!prods.length) {
        html += `<div class="empty-state" style="padding:40px"><div class="empty-icon">🤍</div><div class="empty-title">Chưa có sản phẩm yêu thích</div></div>`;
    } else {
        html += `<div style="overflow-x:auto"><table class="quote-table">
            <thead><tr><th>Ảnh</th><th>Sản phẩm</th><th>Mã SP</th><th>Thương hiệu</th><th>Giá bán lẻ</th><th></th></tr></thead>
            <tbody>${prods.map(p => `<tr>
                <td>${p.hinh_anh ? `<img src="${escHtml(p.hinh_anh)}" style="width:40px;height:40px;object-fit:contain">` : '🛁'}</td>
                <td><strong>${escHtml(p.ten_sp)}</strong></td>
                <td><code>${escHtml(p.ma_sp)}</code></td>
                <td>${escHtml(p.thuong_hieu)}</td>
                <td style="color:var(--primary);font-weight:700">${formatPrice(p.gia_ban_le)}</td>
                <td style="white-space:nowrap">
                    <button class="btn btn-sm btn-outline" onclick="closeFavModal();openDetail(${p.id})">Chi tiết</button>
                    <button class="btn btn-sm btn-primary" onclick="addToQuote(${p.id})" style="margin-left:4px">+Báo giá</button>
                </td>
            </tr>`).join('')}</tbody>
        </table></div>
        <div style="margin-top:16px;display:flex;gap:8px">
            <button class="btn btn-primary" onclick="addAllFavToQuote()">📋 Thêm tất cả vào báo giá</button>
            <button class="btn btn-outline" onclick="favorites=[];localStorage.removeItem('hsh_fav');updateBadges();renderProducts();closeFavModal()">🗑️ Xóa tất cả</button>
        </div>`;
    }
    html += `</div>`;
    document.getElementById('fav-content').innerHTML = html;
    document.getElementById('fav-modal-overlay').classList.add('active');
    document.body.style.overflow = 'hidden';
}

function addAllFavToQuote() {
    favorites.forEach(maSp => {
        const p = allProducts.find(x => x.ma_sp === maSp);
        if (p && !quoteList.find(q => q.ma_sp === maSp)) {
            quoteList.push({ ma_sp: maSp, id: p.id, qty: 1 });
        }
    });
    localStorage.setItem('hsh_quote', JSON.stringify(quoteList));
    updateBadges();
    showToast(`📋 Đã thêm ${favorites.length} SP vào báo giá!`, 'success');
    closeFavModal();
}

function closeFavModal(e) {
    if (!e || e.target.id === 'fav-modal-overlay') {
        document.getElementById('fav-modal-overlay').classList.remove('active');
        document.body.style.overflow = '';
    }
}

// ======================== COMPARE ========================
function toggleCompare(maSp) {
    const idx = compareList.indexOf(maSp);
    if (idx > -1) { compareList.splice(idx, 1); showToast('Đã bỏ khỏi so sánh'); }
    else {
        if (compareList.length >= 4) { showToast('⚠️ Chỉ so sánh tối đa 4 sản phẩm', 'warning'); return; }
        compareList.push(maSp);
        showToast('⚖️ Đã thêm vào so sánh!', 'success');
    }
    localStorage.setItem('hsh_compare', JSON.stringify(compareList));
    updateBadges();
    renderProducts();
}

function showCompare() {
    const prods = allProducts.filter(p => compareList.includes(p.ma_sp));
    if (!prods.length) { showToast('Chưa có sản phẩm nào để so sánh', 'warning'); return; }

    const priceKeys = Object.keys(PRICE_LABELS).filter(k => prods.some(p => p[k] > 0));

    const html = `<div class="cmp-wrap">
        <div class="modal-page-title">⚖️ So Sánh Sản Phẩm <small style="font-size:13px;color:var(--text-muted)">(${prods.length} SP)</small></div>
        <div style="overflow-x:auto">
        <table class="cmp-table">
            <thead><tr>
                <th style="min-width:150px">Tiêu chí</th>
                ${prods.map(p => `<th style="text-align:center">
                    <div>${escHtml(p.thuong_hieu)}</div>
                    <div style="font-size:11px;opacity:.85">${escHtml(p.ma_sp)}</div>
                </th>`).join('')}
            </tr></thead>
            <tbody>
                <tr>
                    <td><strong>Hình ảnh</strong></td>
                    ${prods.map(p => `<td style="text-align:center">${p.hinh_anh ? `<img src="${escHtml(p.hinh_anh)}" style="width:90px;height:90px;object-fit:contain">` : '🛁'}</td>`).join('')}
                </tr>
                <tr>
                    <td><strong>Tên sản phẩm</strong></td>
                    ${prods.map(p => `<td style="font-weight:700">${escHtml(p.ten_sp)}</td>`).join('')}
                </tr>
                <tr>
                    <td><strong>Nhóm hàng</strong></td>
                    ${prods.map(p => `<td>${escHtml(p.nhom_sp||'-')}</td>`).join('')}
                </tr>
                <tr>
                    <td><strong>Kích thước</strong></td>
                    ${prods.map(p => `<td>${escHtml(p.kich_thuoc||'-')}</td>`).join('')}
                </tr>
                <tr>
                    <td><strong>Bảo hành</strong></td>
                    ${prods.map(p => `<td>${escHtml(p.bao_hanh||'-')}</td>`).join('')}
                </tr>
                ${priceKeys.map(k => `<tr>
                    <td><strong>${PRICE_LABELS[k]}</strong></td>
                    ${prods.map(p => `<td style="${k==='gia_ban_le'?'color:var(--primary);font-weight:800':''}">${p[k]>0?formatPrice(p[k]):'-'}</td>`).join('')}
                </tr>`).join('')}
                <tr>
                    <td><strong>Tổng tồn kho</strong></td>
                    ${prods.map(p => {
                        const t = getStockTotal(p);
                        return `<td style="font-weight:800;color:${t>0?'var(--success)':'var(--danger)'}">${t.toLocaleString('vi-VN')}</td>`;
                    }).join('')}
                </tr>
            </tbody>
        </table>
        </div>
        <div style="margin-top:16px;display:flex;gap:8px;flex-wrap:wrap">
            <button class="btn btn-outline" onclick="compareList=[];localStorage.removeItem('hsh_compare');updateBadges();closeCompareModal();renderProducts()">🗑️ Xóa danh sách so sánh</button>
        </div>
    </div>`;

    document.getElementById('compare-content').innerHTML = html;
    document.getElementById('compare-modal-overlay').classList.add('active');
    document.body.style.overflow = 'hidden';
}

function closeCompareModal(e) {
    if (!e || e.target.id === 'compare-modal-overlay') {
        document.getElementById('compare-modal-overlay').classList.remove('active');
        document.body.style.overflow = '';
    }
}

// ======================== QUOTE ========================
function addToQuote(id) {
    const p = allProducts.find(x => x.id === id);
    if (!p) return;
    const ex = quoteList.find(q => q.ma_sp === p.ma_sp);
    if (ex) { ex.qty = (ex.qty||1) + 1; showToast(`+1 SL ➔ ${p.ten_sp.substring(0,28)}…`); }
    else    { quoteList.push({ ma_sp: p.ma_sp, id: p.id, qty: 1 }); showToast('📋 Đã thêm vào giỏ báo giá!', 'success'); }
    localStorage.setItem('hsh_quote', JSON.stringify(quoteList));
    updateBadges();
    renderProducts();
}

function showQuote() {
    if (!quoteList.length) { showToast('Chưa có sản phẩm nào trong báo giá', 'warning'); return; }
    renderQuoteContent();
    document.getElementById('quote-modal-overlay').classList.add('active');
    document.body.style.overflow = 'hidden';
}

function renderQuoteContent() {
    const pt = selectedPriceType;
    let total = 0;
    const rows = quoteList.map((q, i) => {
        const p = allProducts.find(x => x.ma_sp === q.ma_sp);
        if (!p) return '';
        const price = getDisplayPrice(p, pt);
        const sub   = price * (q.qty || 1);
        total += sub;
        return `<tr>
            <td style="text-align:center">${i+1}</td>
            <td>${p.hinh_anh ? `<img src="${escHtml(p.hinh_anh)}" style="width:40px;height:40px;object-fit:contain">` : '🛁'}</td>
            <td>
                <div style="font-weight:700">${escHtml(p.ten_sp)}</div>
                <div style="font-size:11px;color:var(--text-muted)">📌 ${escHtml(p.ma_sp)} | ${escHtml(p.thuong_hieu)}</div>
            </td>
            <td style="text-align:center">${escHtml(p.dvt||'')}</td>
            <td style="text-align:center">
                <input type="number" class="qty-input" value="${q.qty||1}" min="1"
                    onchange="updateQty('${escJs(q.ma_sp)}',+this.value)">
            </td>
            <td style="color:var(--primary);font-weight:600;text-align:right">${formatPrice(price)}</td>
            <td style="color:var(--primary);font-weight:800;text-align:right">${formatPrice(sub)}</td>
            <td style="text-align:center">
                <button onclick="removeFromQuote('${escJs(q.ma_sp)}')" style="border:none;background:none;color:var(--danger);cursor:pointer;font-size:16px" title="Xóa">🗑️</button>
            </td>
        </tr>`;
    }).join('');

    document.getElementById('quote-content').innerHTML = `<div class="quote-wrap">
        <div class="modal-page-title">📋 Bảng Báo Giá Khách Hàng <small style="font-size:13px;color:var(--text-muted)">(${quoteList.length} sản phẩm)</small></div>

        <div style="display:flex;align-items:center;gap:10px;margin-bottom:16px;flex-wrap:wrap">
            <label style="font-size:13px;font-weight:700;color:var(--text-secondary)">Áp dụng cấp giá:</label>
            <select onchange="selectedPriceType=this.value;localStorage.setItem('hsh_price_type',this.value);renderQuoteContent()"
                style="padding:7px 12px;border:1.5px solid var(--border);border-radius:8px;font-family:var(--font);font-size:12.5px;font-weight:600">
                ${Object.entries(PRICE_LABELS).map(([k,v]) => `<option value="${k}" ${k===pt?'selected':''}>${v}</option>`).join('')}
            </select>
            <span style="margin-left:auto;font-size:14px">Tổng cộng: <strong style="color:var(--primary);font-size:17px">${formatPrice(total)}</strong></span>
        </div>

        <div style="overflow-x:auto">
        <table class="quote-table">
            <thead><tr><th>#</th><th>Ảnh</th><th>Sản phẩm</th><th>ĐVT</th><th>SL</th><th style="text-align:right">${PRICE_LABELS[pt]||pt}</th><th style="text-align:right">Thành tiền</th><th></th></tr></thead>
            <tbody>${rows}</tbody>
            <tfoot><tr class="total-row">
                <td colspan="6" style="text-align:right">TỔNG CỘNG THANH TOÁN:</td>
                <td style="text-align:right">${formatPrice(total)}</td>
                <td></td>
            </tr></tfoot>
        </table>
        </div>

        <div style="margin-top:20px;display:flex;gap:8px;flex-wrap:wrap">
            <button class="btn btn-primary"  onclick="window.print()">📄 In / Xuất PDF</button>
            <button class="btn btn-success"  onclick="copyQuote()">📱 Copy gửi Zalo</button>
            <button class="btn btn-warning"  onclick="exportExcel()">📊 Xuất File Excel (.CSV)</button>
            <button class="btn btn-outline"  onclick="clearQuote()">🗑️ Xóa giỏ báo giá</button>
        </div>
    </div>`;
}

function updateQty(maSp, val) {
    const q = quoteList.find(x => x.ma_sp === maSp);
    if (q) { q.qty = Math.max(1, val); localStorage.setItem('hsh_quote', JSON.stringify(quoteList)); renderQuoteContent(); }
}
function removeFromQuote(maSp) {
    quoteList = quoteList.filter(q => q.ma_sp !== maSp);
    localStorage.setItem('hsh_quote', JSON.stringify(quoteList));
    updateBadges(); renderProducts();
    if (!quoteList.length) { closeQuoteModal(); return; }
    renderQuoteContent();
}
function clearQuote() {
    quoteList = []; localStorage.removeItem('hsh_quote');
    updateBadges(); renderProducts(); closeQuoteModal();
}
function closeQuoteModal(e) {
    if (!e || e.target.id === 'quote-modal-overlay') {
        document.getElementById('quote-modal-overlay').classList.remove('active');
        document.body.style.overflow = '';
    }
}

function copyQuote() {
    let txt = `📋 BÁO GIÁ THIẾT BỊ NHÀ TẮM & NHÀ BẾP — HOA SEN HOME\n🗓️ Ngày: ${new Date().toLocaleDateString('vi-VN')}\n💰 Bảng giá: ${PRICE_LABELS[selectedPriceType]}\n${'─'.repeat(42)}\n`;
    let total = 0;
    quoteList.forEach((q, i) => {
        const p = allProducts.find(x => x.ma_sp === q.ma_sp);
        if (!p) return;
        const price = getDisplayPrice(p, selectedPriceType);
        const sub   = price * q.qty;
        total += sub;
        txt += `${i+1}. ${p.ten_sp}\n   📌 Mã: ${p.ma_sp} | SL: ${q.qty} ${p.dvt||''} × ${formatPrice(price)} = ${formatPrice(sub)}\n`;
    });
    txt += `${'─'.repeat(42)}\n💵 TỔNG CỘNG: ${formatPrice(total)}\n📞 Liên hệ Hoa Sen Home để được tư vấn & giao hàng tận nơi!`;
    navigator.clipboard.writeText(txt).then(() => showToast('✅ Đã copy nội dung báo giá để dán vào Zalo!', 'success'));
}

function exportExcel() {
    const pt = selectedPriceType;
    let csv = '\uFEFFBÁO GIÁ HOA SEN HOME\n';
    csv += `Ngày,${new Date().toLocaleDateString('vi-VN')}\n`;
    csv += `Loại giá,${PRICE_LABELS[pt]}\n\n`;
    csv += `STT,Mã SP,Mã Item,Tên sản phẩm,Thương hiệu,ĐVT,Số lượng,Đơn giá,Thành tiền,Bảo hành\n`;
    let total = 0;
    quoteList.forEach((q, i) => {
        const p = allProducts.find(x => x.ma_sp === q.ma_sp);
        if (!p) return;
        const price = getDisplayPrice(p, pt);
        const sub   = price * q.qty;
        total += sub;
        csv += `${i+1},"${p.ma_sp}","${p.ma_item}","${p.ten_sp.replace(/"/g,'""')}","${p.thuong_hieu}","${p.dvt||''}",${q.qty},${price},${sub},"${(p.bao_hanh||'').replace(/"/g,'""')}"\n`;
    });
    csv += `,,,,,,,TỔNG CỘNG,${total},\n`;

    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const a    = document.createElement('a');
    a.href     = URL.createObjectURL(blob);
    a.download = `BaoGia_HSH_${new Date().toLocaleDateString('vi-VN').replace(/\//g,'-')}.csv`;
    a.click();
    showToast('✅ Đã tải xuống file Excel báo giá!', 'success');
}

// ======================== SHARE & UTILS ========================
function shareProduct(maSp, tenSpEncoded) {
    const tenSp = decodeURIComponent(tenSpEncoded);
    const url   = `${location.origin}${location.pathname}?sp=${encodeURIComponent(maSp)}`;
    if (navigator.share) {
        navigator.share({ title: tenSp, url }).catch(() => {});
    } else {
        navigator.clipboard.writeText(url).then(() => showToast('✅ Đã copy đường dẫn sản phẩm!', 'success'));
    }
}

function formatPrice(n) {
    if (!n || n <= 0) return 'Liên hệ';
    return Math.round(n).toLocaleString('vi-VN') + ' ₫';
}

function escHtml(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

function escJs(str) {
    if (!str) return '';
    return String(str).replace(/\\/g, '\\\\').replace(/'/g, "\\'");
}

function showToast(msg, type = '') {
    const t = document.getElementById('toast');
    t.textContent = msg;
    t.className = `toast ${type} show`;
    clearTimeout(t._timer);
    t._timer = setTimeout(() => { t.className = 'toast'; }, 2600);
}

function copyProductZalo(id) {
    const p = allProducts.find(x => x.id === id);
    if (!p) return;
    const price = getDisplayPrice(p);
    const nyPrice = p.gia_niem_yet || 0;
    let txt = `🛁 HOA SEN HOME — SẢN PHẨM: ${p.ten_sp}\n`;
    txt += `📌 Mã SP: ${p.ma_sp}${p.ma_item ? ` | Item: ${p.ma_item}` : ''}\n`;
    txt += `🏷️ Thương hiệu: ${p.thuong_hieu}${p.nhom_sp ? ` (${p.nhom_sp})` : ''}\n`;
    txt += `💰 Giá ưu đãi: ${formatPrice(price)}${nyPrice > price && price > 0 ? ` (Niêm yết: ${formatPrice(nyPrice)})` : ''}\n`;
    if (p.kich_thuoc) txt += `📏 Kích thước: ${p.kich_thuoc}\n`;
    if (p.bao_hanh)   txt += `🛡️ Bảo hành: ${p.bao_hanh}\n`;
    if (p.cong_nghe_xa) txt += `💧 Công nghệ xả: ${p.cong_nghe_xa}\n`;
    txt += `🔗 Xem chi tiết & đặt hàng: ${location.origin}${location.pathname}?sp=${encodeURIComponent(p.ma_sp)}\n`;
    txt += `📞 Hoa Sen Home Miền Trung — Cam kết chính hãng 100%`;
    
    if (navigator.clipboard) {
        navigator.clipboard.writeText(txt).then(() => showToast('✅ Đã copy thông tin sản phẩm để dán vào Zalo!', 'success'));
    } else {
        showToast('⚠️ Không thể tự động copy, vui lòng chọn văn bản thủ công', 'warning');
    }
}

function clearCompareList() {
    compareList = [];
    localStorage.removeItem('hsh_compare');
    updateBadges();
    renderProducts();
    showToast('Đã xóa danh sách so sánh');
}

function updateBadges() {
    const upd = (id, count) => {
        const el = document.getElementById(id);
        if (!el) return;
        el.textContent = count;
        el.style.display = count ? 'flex' : 'none';
    };
    upd('fav-badge',          favorites.length);
    upd('compare-badge',      compareList.length);
    upd('quote-badge',        quoteList.length);
    upd('bottom-quote-badge', quoteList.length);

    // Floating Compare Dock ở góc dưới màn hình
    const dock = document.getElementById('floating-compare-dock');
    const dockCount = document.getElementById('compare-dock-count');
    if (dock) {
        dock.style.display = compareList.length > 0 ? 'flex' : 'none';
        if (dockCount) dockCount.textContent = compareList.length;
    }

    const setText = (id, count) => {
        const el = document.getElementById(id);
        if (el) el.textContent = count;
    };
    setText('drawer-quote-count',   quoteList.length);
    setText('drawer-fav-count',     favorites.length);
    setText('drawer-compare-count', compareList.length);
}

function setView(v, save = true) {
    currentView = v;
    if (save) localStorage.setItem('hsh_view', v);
    document.getElementById('btn-grid').className = `view-btn ${v==='grid'?'active':''}`;
    document.getElementById('btn-list').className = `view-btn ${v==='list'?'active':''}`;
    if (allProducts.length) renderProducts();
}

function scrollToTop() { window.scrollTo({ top: 0, behavior: 'smooth' }); }

function handleDeepLink() {
    const params = new URLSearchParams(location.search);
    const tab = params.get('tab');
    if (tab) {
        setTimeout(() => switchTab(tab), 150);
    }
    const sub = params.get('sub');
    if (sub) {
        setTimeout(() => { if (typeof setComboSubTab === 'function') setComboSubTab(sub); }, 280);
    }
    const maSp = params.get('sp');
    if (maSp) {
        const p = allProducts.find(x => x.ma_sp === maSp);
        if (p) setTimeout(() => openDetail(p.id), 380);
    }
}

init();
