/**
 * HSH Sales Pro v4 — Module mở rộng
 *  - Tab "📦 Combo & Báo Giá Mẫu":
 *    + Combo soạn sẵn (thêm trọn bộ vào báo giá 1 chạm)
 *    + 📖 THƯ VIỆN SẢN PHẨM HSH MIỀN TRUNG 2026 (ALBUM GỐC) với 142 sản phẩm chụp studio cực nét, đầy đủ thông số & bảo hành
 *    + Top 10 SKU đề xuất
 *    + Bồn cầu thông minh TOTO/INAX (TCG)
 *    + Bảng giá thiết bị bếp TEKA/HAFELE/TOÀN MỸ/INOX
 *  - CTKM đang chạy (tab CTKM) + Ma trận chiết khấu & CK trả sau/tháng/quý (tab Chính sách)
 *  - Giỏ báo giá nâng cấp: giá combo, hàng tặng, chi phí lắp đặt
 */

let quoteInstall = JSON.parse(localStorage.getItem('hsh_install') || '{}'); // { stt: qty }
let currentComboSubTab = 'combos'; // 'combos' | 'album' | 'top' | 'tcg' | 'bep'
let selectedAlbumCategory = 'all';
let albumSearchQuery = '';

const pctFmt = v => (v === undefined || v === null || v === '') ? '—' : String(v);
const imgOrIcon = (src, size = 54) => src
    ? `<img src="${escHtml(src)}" loading="lazy" onclick="event.stopPropagation();openLightbox('${escJs(src)}')" style="width:${size}px;height:${size}px;object-fit:contain;cursor:zoom-in;background:#fff;border-radius:8px;border:1px solid var(--border-light)">`
    : `<div style="width:${size}px;height:${size}px;display:flex;align-items:center;justify-content:center;font-size:${Math.round(size/2)}px;background:var(--bg-subtle,#f5f5f5);border-radius:8px">🛁</div>`;
const openIfId = id => id ? `onclick="openDetail(${id})" style="cursor:pointer"` : '';

function setComboSubTab(tab) {
    currentComboSubTab = tab;
    renderCombosTab();
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function onAlbumSearch(val) {
    albumSearchQuery = (val || '').trim().toLowerCase();
    renderCombosTab();
}

function filterAlbumCategory(cat) {
    selectedAlbumCategory = cat;
    renderCombosTab();
}

// ======================== WRAP CÁC HÀM RENDER GỐC ========================
const _v3RenderPromos   = renderPromosTab;
const _v3RenderPolicies = renderPoliciesTab;
const _v3RenderKnowledge= renderKnowledgeTab;

renderPromosTab = function () {
    _v3RenderPromos();
    renderCtkmDangChay();
    renderCombosTab();
};
renderPoliciesTab = function () {
    _v3RenderPolicies();
    renderChinhSachKinhDoanh();
};
renderKnowledgeTab = function () {
    _v3RenderKnowledge();
    renderAlbumWarrantyTables();
};

// ======================== TAB COMBO & BÁO GIÁ MẪU (V5 REDESIGN) ========================
function renderCombosTab() {
    const el = document.getElementById('combos-container');
    if (!el || !extrasData) return;

    const combos = extrasData.combo_ban_hang || [];
    const top    = extrasData.top_de_xuat || [];
    const tcg    = (extrasData.tcg_thong_minh || {}).items || [];
    const bep    = extrasData.bang_gia_bep || {};
    const album  = extrasData.album_hsh_2026 || {};

    // 1. SUB-TAB SWITCHER NAVIGATION BAR
    const switcherHtml = `
        <div class="combo-switcher-wrap">
            <button class="combo-switch-btn ${currentComboSubTab==='combos'?'active':''}" onclick="setComboSubTab('combos')">
                <span>🔥</span> <span>Combo Trọn Bộ HOT</span>
                <span class="combo-switch-badge">${combos.length} Gói</span>
            </button>
            <button class="combo-switch-btn ${currentComboSubTab==='album'?'active':''}" onclick="setComboSubTab('album')">
                <span>📖</span> <span>Thư Viện Album 2026</span>
                <span class="combo-switch-badge">${album.tong_so_sp || 142} SP</span>
            </button>
            <button class="combo-switch-btn ${currentComboSubTab==='top'?'active':''}" onclick="setComboSubTab('top')">
                <span>🏆</span> <span>Top 10 Bán Chạy</span>
                <span class="combo-switch-badge">10 SKU</span>
            </button>
            <button class="combo-switch-btn ${currentComboSubTab==='tcg'?'active':''}" onclick="setComboSubTab('tcg')">
                <span>🚽</span> <span>Bồn Cầu Thông Minh TCG</span>
                <span class="combo-switch-badge">${tcg.length}</span>
            </button>
            <button class="combo-switch-btn ${currentComboSubTab==='bep'?'active':''}" onclick="setComboSubTab('bep')">
                <span>🍳</span> <span>Thiết Bị Bếp &amp; INOX</span>
                <span class="combo-switch-badge">Teka/Hafele</span>
            </button>
        </div>
    `;

    // 2. VIEW 1: COMBOS TRỌN BỘ (HOT)
    let bodyHtml = '';
    if (currentComboSubTab === 'combos') {
        const comboCardsHtml = combos.map((c, ci) => {
            const previewThumbs = c.items.map(it => `
                <div class="combo-preview-item" title="${escHtml(it.ten_sp)}">
                    ${it.hinh_anh ? `<img class="combo-preview-thumb" src="${escHtml(it.hinh_anh)}" loading="lazy" onclick="openLightbox('${escJs(it.hinh_anh)}')">` : '<div class="combo-preview-thumb" style="display:flex;align-items:center;justify-content:center;font-size:22px">🛁</div>'}
                    <span class="combo-preview-code">${escHtml(it.ma_sp)}</span>
                    <span style="font-size:9.5px;color:var(--text-muted)">SL: ${it.so_luong}</span>
                </div>
            `).join('');

            const rows = c.items.map((it, i) => `
                <tr ${openIfId(it.id)}>
                    <td style="text-align:center">${i + 1}</td>
                    <td>${imgOrIcon(it.hinh_anh, 44)}</td>
                    <td>
                        <div style="font-weight:700;font-size:13px">${escHtml(it.ten_sp)}</div>
                        <div style="font-size:11px;color:var(--text-muted)">📌 <strong>${escHtml(it.ma_sp)}</strong> · ${escHtml(it.thuong_hieu)}${it.id ? '' : ' · <em>(Ngoài DM bảng giá)</em>'}</div>
                    </td>
                    <td style="text-align:center"><strong>${it.so_luong}</strong> ${escHtml(it.dvt || '')}</td>
                    <td class="num" style="color:var(--text-muted);${it.tang || it.gia_combo < it.gia_niem_yet ? 'text-decoration:line-through' : ''}">${formatPrice(it.gia_niem_yet)}</td>
                    <td class="num" style="font-weight:800;color:${it.tang ? 'var(--success,#16a34a)' : 'var(--hsh-red)'}">
                        ${it.tang ? '🎁 TẶNG MIỄN PHÍ' : formatPrice(it.gia_combo)}
                    </td>
                </tr>
            `).join('');

            const pctSave = c.tong_niem_yet > 0 && c.tiet_kiem > 0 ? Math.round(c.tiet_kiem * 100 / c.tong_niem_yet) : 0;

            return `
            <div class="combo-hero-card">
                <div class="combo-hero-header">
                    <div class="combo-hero-title">
                        <span>📦 ${escHtml(c.ten_combo)}</span>
                        <span class="chip" style="font-size:11px;font-weight:700;background:var(--hsh-red-subtle);color:var(--hsh-red)">Trọn bộ ${c.items.length} món</span>
                    </div>
                    ${c.tiet_kiem > 0 ? `<div class="combo-badge-hot">🔥 TIẾT KIỆM ${formatPrice(c.tiet_kiem)} (-${pctSave}%)</div>` : '<div class="combo-badge-hot">🔥 GÓI COMBO HOT</div>'}
                </div>

                ${c.mo_ta ? `<p style="padding:10px 20px 0;font-size:13px;color:var(--text-secondary);margin:0">${escHtml(c.mo_ta)}</p>` : ''}

                <!-- THUMBNAIL GALLERY STRIP -->
                <div class="combo-preview-bar">
                    <div style="font-size:11px;font-weight:800;color:var(--text-muted);writing-mode:vertical-lr;transform:rotate(180deg);padding:0 4px">TRỌN BỘ</div>
                    ${previewThumbs}
                </div>

                <!-- DETAILED ITEMS TABLE -->
                <div class="combo-table-wrap">
                    <table class="hb-table" style="margin-top:10px">
                        <thead>
                            <tr><th>#</th><th>Ảnh</th><th>Sản phẩm trong gói</th><th style="text-align:center">SL</th><th class="num">Giá Niêm Yết</th><th class="num">Đơn Giá Combo</th></tr>
                        </thead>
                        <tbody>${rows}</tbody>
                    </table>
                </div>

                <!-- FINANCIAL FOOTER -->
                <div class="combo-footer-box">
                    <div class="combo-price-summary">
                        <div>
                            <div class="combo-old-price">Tổng niêm yết: ${formatPrice(c.tong_niem_yet)}</div>
                            <div class="combo-final-price">${formatPrice(c.tong_combo)}</div>
                        </div>
                        ${c.tiet_kiem > 0 ? `<div class="combo-save-pill">💰 Tiết kiệm ${formatPrice(c.tiet_kiem)} (-${pctSave}%)</div>` : ''}
                    </div>
                    <div style="display:flex;gap:8px;flex-wrap:wrap">
                        <button class="btn btn-primary" onclick="addComboToQuote(${ci})">➕ Thêm Trọn Bộ Vào Báo Giá</button>
                        <button class="btn btn-success" onclick="copyCombo(${ci})">📱 Copy Gửi Zalo</button>
                    </div>
                </div>
            </div>`;
        }).join('');

        bodyHtml = `
            <div style="margin-bottom:14px">
                <h2 style="font-size:18px;font-weight:800;color:var(--text-primary);margin-bottom:4px">🔥 GÓI COMBO BÁN HÀNG ƯU ĐÃI (SẴN SÀNG BÁO GIÁ)</h2>
                <p style="font-size:13px;color:var(--text-secondary)">Các gói thiết bị phòng tắm &amp; nhà bếp đồng bộ đã được tính toán chiết khấu tối đa, có thể đưa trọn bộ vào giỏ báo giá hoặc gửi tư vấn khách hàng chỉ với 1 click.</p>
            </div>
            ${comboCardsHtml}
        `;

    // 3. VIEW 2: THƯ VIỆN ALBUM 2026 (142 SP STUDIO)
    } else if (currentComboSubTab === 'album') {
        // Parent Category Mapping
        const PARENT_GROUPS = [
            { id: 'all',      label: '🌟 Tất cả', icon: '🌟' },
            { id: 'bon_cau',  label: '🚽 Bồn Cầu & Bồn Tiểu', keywords: ['bồn cầu', 'bàn cầu', 'bồn tiểu'] },
            { id: 'lavabo',   label: '🥣 Chậu Lavabo', keywords: ['lavabo', 'chậu'] },
            { id: 'sen_voi',  label: '🚿 Sen Tắm & Vòi Nước', keywords: ['sen', 'vòi'] },
            { id: 'bon_tam',  label: '🛁 Bồn Tắm & Vách Kính', keywords: ['bồn tắm', 'vách kính'] },
            { id: 'phu_kien', label: '🪞 Gương Đèn & Phụ Kiện', keywords: ['gương', 'khăn', 'phụ kiện', 'kệ', 'thoát sàn'] },
        ];

        // Gather all items
        let allAlbumItems = [];
        Object.values(album.danh_muc || {}).forEach(arr => allAlbumItems.push(...arr));

        // Filter by parent group
        let filteredItems = allAlbumItems;
        if (selectedAlbumCategory !== 'all') {
            const grp = PARENT_GROUPS.find(g => g.id === selectedAlbumCategory);
            if (grp && grp.keywords) {
                filteredItems = allAlbumItems.filter(item => {
                    const str = ((item.nhom_sp || '') + ' ' + (item.ten_sp || '')).toLowerCase();
                    return grp.keywords.some(kw => str.includes(kw));
                });
            }
        }

        // Filter by search query
        if (albumSearchQuery) {
            filteredItems = filteredItems.filter(item =>
                (item.ten_sp || '').toLowerCase().includes(albumSearchQuery) ||
                (item.ma_sp || '').toLowerCase().includes(albumSearchQuery) ||
                (item.ma_cu || '').toLowerCase().includes(albumSearchQuery) ||
                (item.kich_thuoc || '').toLowerCase().includes(albumSearchQuery)
            );
        }

        const parentTabsHtml = PARENT_GROUPS.map(grp => {
            let count = allAlbumItems.length;
            if (grp.id !== 'all' && grp.keywords) {
                count = allAlbumItems.filter(item => {
                    const str = ((item.nhom_sp || '') + ' ' + (item.ten_sp || '')).toLowerCase();
                    return grp.keywords.some(kw => str.includes(kw));
                }).length;
            }
            return `<button class="album-ptab ${selectedAlbumCategory===grp.id?'active':''}" onclick="filterAlbumCategory('${grp.id}')">${grp.label} (${count})</button>`;
        }).join('');

        const albumCardsHtml = filteredItems.map(item => {
            const p = allProducts.find(x => x.ma_sp === item.ma_sp) || (item.ma_cu ? allProducts.find(x => x.ma_sp === item.ma_cu) : null);
            const pid = p ? p.id : null;
            return `
            <div class="album-card-v5" ${openIfId(pid)}>
                <div style="display:flex;justify-content:space-between;align-items:center">
                    <span class="card-brand" style="font-size:9.5px">${escHtml(item.thuong_hieu)}</span>
                    <span class="badge-studio" style="font-size:8.5px">📸 STUDIO HD</span>
                </div>
                <div class="album-img-wrap">
                    ${item.hinh_anh ? `<img src="${escHtml(item.hinh_anh)}" loading="lazy" onclick="event.stopPropagation();openLightbox('${escJs(item.hinh_anh)}')">` : '<div style="font-size:36px">🛁</div>'}
                </div>
                <div style="font-size:10.5px;color:var(--text-muted);text-transform:uppercase;font-weight:700">${escHtml(item.nhom_sp)}</div>
                <div style="font-size:13px;font-weight:700;line-height:1.35;min-height:36px;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden">${escHtml(item.ten_sp)}</div>
                <div style="font-size:11.5px;color:var(--text-secondary);font-family:monospace">
                    📌 <strong>${escHtml(item.ma_sp)}</strong>
                    ${item.ma_cu ? `<span style="color:#b45309;font-size:10.5px"> (cũ: ${escHtml(item.ma_cu)})</span>` : ''}
                </div>
                ${item.kich_thuoc ? `<div style="font-size:11px;color:var(--text-secondary);white-space:nowrap;overflow:hidden;text-overflow:ellipsis">📐 ${escHtml(item.kich_thuoc)}</div>` : ''}
                ${item.bao_hanh ? `<div style="font-size:11px;color:#15803d;font-weight:600">🛡️ ${escHtml(item.bao_hanh)}</div>` : ''}
                <div style="margin-top:auto;padding-top:6px;border-top:1px dashed var(--border-subtle);display:flex;align-items:baseline;justify-content:space-between">
                    <div style="font-size:15px;font-weight:800;color:var(--hsh-red)">${item.gia_niem_yet > 0 ? formatPrice(item.gia_niem_yet) : 'Liên hệ'}</div>
                </div>
                <div style="display:flex;gap:6px;margin-top:6px">
                    ${pid ? `<button class="btn btn-sm btn-outline" style="flex:1" onclick="event.stopPropagation();openDetail(${pid})">Chi tiết ▸</button>` : ''}
                    ${pid ? `<button class="btn btn-sm btn-primary" onclick="event.stopPropagation();addToQuote(${pid})">+ Báo giá</button>` : ''}
                </div>
            </div>`;
        }).join('');

        bodyHtml = `
            <div class="album-hero-banner">
                <div class="album-hero-title">
                    <span>📖 THƯ VIỆN ALBUM THIẾT BỊ HSH MIỀN TRUNG 2026</span>
                    <span class="badge-studio" style="font-size:11px;padding:3px 10px">142 SP STUDIO NÉT CHUẨN</span>
                </div>
                <p class="album-hero-sub">
                    Trích xuất và chuẩn hoá 100% hình ảnh chụp Studio độ phân giải cao từ Album Catalogue chính thức của Tập đoàn Hoa Sen Home — Đầy đủ thông số kích thước, công nghệ xả men CeFiONtect, hệ thống phụ kiện và bảo hành chính hãng.
                </p>
            </div>

            <div class="album-filter-controls">
                <input type="text" class="album-search-input" placeholder="🔍 Tìm nhanh trong 142 SP Album (gõ tên, mã SP, mã cũ, kích thước...)" value="${escHtml(albumSearchQuery)}" oninput="onAlbumSearch(this.value)">
                <div class="album-parent-tabs">${parentTabsHtml}</div>
            </div>

            <div style="font-size:13px;color:var(--text-secondary);margin-bottom:12px">
                Hiển thị <strong>${filteredItems.length}</strong> sản phẩm ${albumSearchQuery ? `cho từ khóa "<em>${escHtml(albumSearchQuery)}</em>"` : ''}
            </div>

            <div class="products-grid" style="grid-template-columns:repeat(auto-fill, minmax(225px, 1fr));gap:14px">
                ${albumCardsHtml || '<div class="empty-state">Không tìm thấy sản phẩm nào trong danh mục này</div>'}
            </div>
        `;

    // 4. VIEW 3: TOP 10 SKU ĐỀ XUẤT
    } else if (currentComboSubTab === 'top') {
        const topCards = top.map((t, i) => {
            const p = t.id ? allProducts.find(x => x.id === t.id) : null;
            const tk = Object.entries(t.ton_kho || {}).map(([k, v]) => `<span class="mini-stock ${v > 0 ? 'in' : 'out'}">${escHtml(k)}: <b>${v}</b></span>`).join('');
            const cup = i === 0 ? '🥇' : (i === 1 ? '🥈' : (i === 2 ? '🥉' : '⭐'));
            return `<div class="v4-card" ${openIfId(t.id)}>
                <div class="v4-rank" style="background:${i<3?'#b45309':'var(--hsh-red)'}">${cup} TOP ${i + 1}</div>
                <div class="v4-img">${imgOrIcon(t.hinh_anh, 140)}</div>
                <div class="v4-cat">${escHtml(t.phan_loai)}</div>
                <div class="v4-name">${escHtml(t.ten_sp)}</div>
                <div class="v4-code">📌 <strong>${escHtml(t.ma_sp)}</strong></div>
                <div class="v4-price">${formatPrice(p ? getDisplayPrice(p) : t.gia_niem_yet)}</div>
                <div class="v4-stock">${tk}</div>
                ${p ? `<button class="btn btn-sm btn-primary" onclick="event.stopPropagation();addToQuote(${p.id})">+ Báo giá</button>` : ''}
            </div>`;
        }).join('');

        bodyHtml = `
            <div style="margin-bottom:16px">
                <h2 style="font-size:18px;font-weight:800;color:var(--text-primary);margin-bottom:4px">🏆 TOP 10 SKU ĐỀ XUẤT BÁN CHẠY NHẤT THÁNG</h2>
                <p style="font-size:13px;color:var(--text-secondary)">Danh mục 10 mặt hàng chủ lực dựa trên 3 tiêu chí: Doanh số cao + Tồn kho dồi dào tại 17 kho Miền Trung + Biên lợi nhuận và chiết khấu hấp dẫn.</p>
            </div>
            <div class="v4-grid">${topCards}</div>
        `;

    // 5. VIEW 4: BỒN CẦU THÔNG MINH TCG
    } else if (currentComboSubTab === 'tcg') {
        const tcgCards = tcg.map((t, i) => `
            <div class="v4-card" ${openIfId(t.id)}>
                <div class="v4-rank" style="background:${t.thuong_hieu === 'TOTO' ? '#0f4c81' : '#1f7a4d'}">${escHtml(t.thuong_hieu)}</div>
                <div class="v4-img">${imgOrIcon(t.hinh_anh, 130)}</div>
                <div class="v4-cat">${escHtml(t.loai)}</div>
                <div class="v4-name">${escHtml(t.ten_sp)}</div>
                <div class="v4-code">📌 ${escHtml(t.ma_sp)}</div>
                <div style="font-size:12px;color:var(--text-muted);text-decoration:line-through">${formatPrice(t.gia_niem_yet)}</div>
                <div class="v4-price">${formatPrice(t.gia_ban)} <small class="chip" style="background:#16a34a;color:#fff">-${Math.round(t.chiet_khau * 100)}%</small></div>
                <button class="btn btn-sm btn-primary" onclick="event.stopPropagation();addCustomToQuote('tcg',${i})">+ Báo giá</button>
            </div>`).join('');

        bodyHtml = `
            <div style="margin-bottom:16px">
                <h2 style="font-size:18px;font-weight:800;color:var(--text-primary);margin-bottom:4px">🚽 BỒN CẦU THÔNG MINH TOTO &amp; INAX (THƯ CHÀO GIÁ TCG)</h2>
                <p style="font-size:13px;color:var(--text-secondary)">Dòng sản phẩm nắp rửa điện tử cao cấp với mức giá ưu đãi đặc biệt cho công trình &amp; biệt thự.</p>
            </div>
            <div class="v4-grid">${tcgCards}</div>
            ${((extrasData.tcg_thong_minh || {}).ghi_chu || []).length ? `<div class="note-box" style="font-size:12.5px;margin-top:16px">${extrasData.tcg_thong_minh.ghi_chu.map(g => '• ' + escHtml(g)).join('<br>')}</div>` : ''}
        `;

    // 6. VIEW 5: BẾP & CHẬU INOX
    } else if (currentComboSubTab === 'bep') {
        const simpleTable = (title, chip, head, rows) => `
            <div class="hb-card" style="margin-bottom:20px">
                <div class="hb-card-title"><span>${title}</span>${chip ? `<span class="chip">${chip}</span>` : ''}</div>
                <div style="overflow-x:auto"><table class="hb-table"><thead><tr>${head}</tr></thead><tbody>${rows}</tbody></table></div>
            </div>`;

        const tekaRows = (bep.teka || []).map(t => `<tr ${openIfId(t.id)}>
            <td>${imgOrIcon(t.hinh_anh, 40)}</td><td><b>${escHtml(t.ten_sp)}</b><div style="font-size:11px;color:var(--text-muted)">${escHtml(t.ma_item)}</div></td>
            <td class="num"><s>${formatPrice(t.gia_niem_yet)}</s></td>
            <td class="num" style="color:var(--hsh-red);font-weight:800">${formatPrice(t.gia_uu_dai)}</td>
            <td style="text-align:center"><span class="chip" style="background:#16a34a;color:#fff">-${Math.round(t.muc_uu_dai * 100)}%</span></td>
            <td style="font-size:11px">${Object.entries(t.ton_kho).filter(([, v]) => v > 0).map(([k, v]) => `${escHtml(k)}: <b>${v}</b>`).join(' · ') || '<span style="color:var(--text-muted)">Hết hàng</span>'}</td>
        </tr>`).join('');

        const ck3Rows = list => list.map(t => `<tr ${openIfId(t.id)}>
            <td>${imgOrIcon(t.hinh_anh, 40)}</td><td><b>${escHtml(t.ten_sp)}</b><div style="font-size:11px;color:var(--text-muted)">${escHtml(t.ma_item)}${t.quy_cach ? ' · ' + escHtml(t.quy_cach) : ''}</div></td>
            <td class="num" style="font-weight:700">${formatPrice(t.gia_niem_yet)}</td>
            <td class="num">${formatPrice(t.gia_ck10)}</td><td class="num">${formatPrice(t.gia_ck15)}</td>
            <td class="num" style="color:var(--hsh-red);font-weight:800">${formatPrice(t.gia_ck20)}</td>
        </tr>`).join('');
        const ck3Head = '<th>Ảnh</th><th>Sản phẩm</th><th class="num">Niêm yết</th><th class="num">CK 10%</th><th class="num">CK 15%</th><th class="num">CK 20%</th>';

        const inoxBlocks = (bep.inox_khu_vuc || []).map(kv => simpleTable(
            `🚰 ${escHtml(kv.khu_vuc.replace(/\n/g, ' — '))}`,
            `Lẻ -${Math.round(kv.ck_le * 100)}% · Sỉ -${Math.round(kv.ck_si * 100)}%`,
            '<th>Mã Item</th><th>Sản phẩm</th><th class="num">NY chưa VAT</th><th class="num">NY có VAT</th><th class="num">Giá bán lẻ</th><th class="num">Giá bán sỉ</th>',
            kv.items.map(it => `<tr ${openIfId(it.id)}><td>${escHtml(it.ma_item)}</td><td><b>${escHtml(it.ten_sp)}</b></td>
                <td class="num">${formatPrice(it.ny_chua_vat)}</td><td class="num">${formatPrice(it.ny_co_vat)}</td>
                <td class="num" style="color:var(--hsh-red);font-weight:700">${formatPrice(it.gia_le)}</td>
                <td class="num" style="font-weight:700">${formatPrice(it.gia_si)}</td></tr>`).join('')
        )).join('');

        bodyHtml = `
            <div style="margin-bottom:16px">
                <h2 style="font-size:18px;font-weight:800;color:var(--text-primary);margin-bottom:4px">🍳 BẢNG GIÁ THIẾT BỊ BẾP &amp; CHẬU RỬA INOX</h2>
                <p style="font-size:13px;color:var(--text-secondary)">Chính sách giá thiết bị nhà bếp TEKA, HAFELE và chậu rửa Inox TOÀN MỸ chính hãng.</p>
            </div>
            ${simpleTable('🔥 HOA SEN HOME “HÀNG HIỆU TEKA – GIÁ HỜI”', `${(bep.teka || []).length} mã`, '<th>Ảnh</th><th>Sản phẩm</th><th class="num">Niêm yết</th><th class="num">Giá ưu đãi</th><th>Ưu đãi</th><th>Tồn kho</th>', tekaRows)}
            ${simpleTable('🏷️ BẢNG GIÁ THIẾT BỊ HAFELE', `${(bep.hafele || []).length} mã`, ck3Head, ck3Rows(bep.hafele || []))}
            ${simpleTable('🚰 BẢNG GIÁ CHẬU RỬA INOX TOÀN MỸ (XẢ TỒN KHO)', `${(bep.toan_my || []).length} mã`, ck3Head, ck3Rows(bep.toan_my || []))}
            ${inoxBlocks}
            ${bep.inox_info ? `<div class="note-box" style="font-size:12.5px;margin-top:10px">📄 ${escHtml(bep.inox_info)}</div>` : ''}
        `;
    }

    el.innerHTML = switcherHtml + bodyHtml;
}

// ======================== ALBUM WARRANTY TABLES (TAB KIẾN THỨC) ========================
function renderAlbumWarrantyTables() {
    const box = document.getElementById('knowledge-container');
    if (!box) return;
    const wrap = document.createElement('div');
    wrap.innerHTML = `
        <div class="v4-section-title">🛡️ Chính Sách Bảo Hành Chính Thức (Theo Album HSH 2026)</div>
        <div class="hb-grid" style="margin-bottom:20px">
            <div class="hb-card">
                <div class="hb-card-title"><span>🚿 TUSLO &amp; TUSLO PRO</span><span class="chip">Album Trang 1</span></div>
                <table class="hb-table">
                    <thead><tr><th>Danh mục</th><th>Thời gian bảo hành</th></tr></thead>
                    <tbody>
                        <tr><td><b>Bồn cầu sứ</b></td><td style="color:#15803d;font-weight:700">10 năm</td></tr>
                        <tr><td><b>Lavabo sứ</b></td><td style="color:#15803d;font-weight:700">10 năm</td></tr>
                        <tr><td><b>Vòi Lavabo</b></td><td style="color:#15803d;font-weight:700">3 năm</td></tr>
                        <tr><td><b>Sen tắm</b></td><td style="color:#15803d;font-weight:700">3 năm</td></tr>
                        <tr><td><b>Gương soi</b></td><td style="color:#15803d;font-weight:700">2 năm</td></tr>
                        <tr><td><b>Giá treo khăn điện</b></td><td style="color:#15803d;font-weight:700">2 năm</td></tr>
                        <tr><td><b>Phụ kiện nhà tắm</b></td><td style="color:#15803d;font-weight:700">3 năm</td></tr>
                    </tbody>
                </table>
            </div>

            <div class="hb-card">
                <div class="hb-card-title"><span>💎 TUSLO LUXURY</span><span class="chip">Album Trang 1</span></div>
                <table class="hb-table">
                    <thead><tr><th>Danh mục cao cấp</th><th>Thời gian bảo hành</th></tr></thead>
                    <tbody>
                        <tr><td><b>Bồn cầu thông minh</b></td><td style="color:#0f766e;font-weight:700">2 năm điện tử (10 năm sứ)</td></tr>
                        <tr><td><b>Bồn cầu 1 khối Luxury</b></td><td style="color:#0f766e;font-weight:700">10 năm sứ</td></tr>
                        <tr><td><b>Lavabo Luxury</b></td><td style="color:#0f766e;font-weight:700">10 năm sứ</td></tr>
                        <tr><td><b>Bồn tiểu nam cảm ứng</b></td><td style="color:#0f766e;font-weight:700">10 năm</td></tr>
                        <tr><td><b>Vòi Lavabo cảm ứng</b></td><td style="color:#0f766e;font-weight:700">3 năm</td></tr>
                        <tr><td><b>Vòi Lavabo Luxury</b></td><td style="color:#0f766e;font-weight:700">5 năm</td></tr>
                        <tr><td><b>Vòi bếp Luxury</b></td><td style="color:#0f766e;font-weight:700">5 năm</td></tr>
                        <tr><td><b>Sen tắm Luxury</b></td><td style="color:#0f766e;font-weight:700">5 năm</td></tr>
                        <tr><td><b>Tủ Lavabo / Tủ gương</b></td><td style="color:#0f766e;font-weight:700">2 năm</td></tr>
                        <tr><td><b>Vách kính tắm</b></td><td style="color:#0f766e;font-weight:700">3 năm</td></tr>
                        <tr><td><b>Bồn tắm</b></td><td style="color:#0f766e;font-weight:700">2 năm</td></tr>
                    </tbody>
                </table>
            </div>

            <div class="hb-card">
                <div class="hb-card-title"><span>🍳 THƯƠNG HIỆU LUSHINE</span><span class="chip">Album Trang 1 &amp; 5</span></div>
                <table class="hb-table">
                    <thead><tr><th>Sản phẩm nhà bếp</th><th>Thời gian bảo hành</th></tr></thead>
                    <tbody>
                        <tr><td><b>Chậu rửa Inox 304 dập liền khối</b></td><td style="color:#b45309;font-weight:700">10 năm</td></tr>
                        <tr><td><b>Chậu rửa đá nhân tạo</b></td><td style="color:#b45309;font-weight:700">7 năm</td></tr>
                        <tr><td><b>Vòi rửa chén &amp; Vòi cảm ứng</b></td><td style="color:#b45309;font-weight:700">3 năm</td></tr>
                        <tr><td><b>Phụ kiện xi phông &amp; ống xả</b></td><td style="color:#b45309;font-weight:700">2 - 3 năm</td></tr>
                    </tbody>
                </table>
            </div>
        </div>`;
    box.prepend(wrap);
}

// ======================== CTKM ĐANG CHẠY ========================
function renderCtkmDangChay() {
    const box = document.getElementById('promos-container');
    const cs = extrasData && extrasData.chinh_sach_kinh_doanh;
    if (!box || !cs || !(cs.ctkm_dang_chay || []).length) return;
    const cards = cs.ctkm_dang_chay.map(k => `
        <div class="ctkm-card">
            <div class="ctkm-title">🎉 ${escHtml(k.ten)}</div>
            ${k.loai_hang ? `<div class="chip" style="margin-bottom:6px">${escHtml(k.loai_hang)}</div>` : ''}
            <div class="ctkm-body">${escHtml(k.noi_dung).replace(/\n/g, '<br>')}</div>
            <div class="ctkm-time">⏰ Thời hạn: <b>${escHtml(k.thoi_han)}</b></div>
        </div>`).join('');
    const wrap = document.createElement('div');
    wrap.innerHTML = `
        <div class="v4-section-title">🎁 Các Chương Trình Khuyến Mãi Đang Chạy <small>(${cs.ctkm_dang_chay.length} chương trình — sheet “Thư viện có gì”)</small></div>
        <div class="ctkm-grid">${cards}</div>`;
    box.prepend(wrap);
}

// ======================== CHÍNH SÁCH KINH DOANH ========================
function renderChinhSachKinhDoanh() {
    const box = document.getElementById('policies-container');
    const cs = extrasData && extrasData.chinh_sach_kinh_doanh;
    if (!box || !cs) return;
    const mt = (cs.ma_tran_ck || []).map(r => `<tr><td><b>${escHtml(r.loai_hang)}</b></td>
        <td style="text-align:center">${escHtml(r.vang_lai)}</td><td style="text-align:center;font-weight:700">${escHtml(r.thau_tho)}</td>
        <td style="text-align:center;font-weight:700">${escHtml(r.si_thuong_mai)}</td><td style="text-align:center;color:var(--primary);font-weight:800">${escHtml(r.ban_mau)}</td></tr>`).join('');
    const ts = (cs.ck_tra_sau || []).map((r, i) => `<tr><td style="text-align:center">${i + 1}</td><td>${escHtml(r.khung)}</td>
        <td style="text-align:center">${pctFmt(r.ck_thang)}</td><td style="text-align:center">${pctFmt(r.ck_quy)}</td>
        <td style="text-align:center">${pctFmt(r.ck_chuyen_nganh)}</td><td style="text-align:center;color:var(--primary);font-weight:800">${pctFmt(r.tong)}</td></tr>`).join('');
    const simple = list => list.map((r, i) => `<tr><td style="text-align:center">${i + 1}</td><td>${escHtml(r.khung)}</td><td style="text-align:center;font-weight:800;color:var(--primary)">${pctFmt(r.muc_ck)}</td></tr>`).join('');
    const lich = (cs.lich_can_tru_quy || []).map(r => `<tr><td style="text-align:center">Q${escHtml(r.quy)}</td><td>${escHtml(r.thoi_gian)}</td><td>${escHtml(r.can_tru)}</td></tr>`).join('');

    const wrap = document.createElement('div');
    wrap.innerHTML = `
        <div class="v4-section-title">💼 Chính Sách Kinh Doanh &amp; Chiết Khấu Theo Nhóm Khách Hàng</div>
        <div class="hb-grid" style="margin-bottom:18px">
            <div class="hb-card" style="grid-column:1/-1">
                <div class="hb-card-title"><span>🎯 Ma trận mức chiết khấu trên giá niêm yết</span><span class="chip">Thư viện có gì</span></div>
                <div style="overflow-x:auto"><table class="hb-table">
                    <thead><tr><th>Loại hàng</th><th>Khách vãng lai</th><th>Khách thầu thợ</th><th>Khách sỉ / thương mại</th><th>Chính sách bán mẫu</th></tr></thead>
                    <tbody>${mt}</tbody></table></div>
            </div>
            <div class="hb-card">
                <div class="hb-card-title"><span>📈 Tổng hợp CK trả sau — KH thân thiết / Đại lý / NPP</span></div>
                <div style="overflow-x:auto"><table class="hb-table">
                    <thead><tr><th>#</th><th>Doanh số mua hàng tháng</th><th>CK Tháng</th><th>CK Quý</th><th>CK Chuyên ngành</th><th>Tổng CK</th></tr></thead>
                    <tbody>${ts}</tbody></table></div>
            </div>
            <div class="hb-card">
                <div class="hb-card-title"><span>🗓️ Chiết khấu Tháng</span></div>
                <table class="hb-table"><thead><tr><th>#</th><th>Doanh số tháng</th><th>Mức CK</th></tr></thead><tbody>${simple(cs.ck_thang || [])}</tbody></table>
                <div class="note-box" style="font-size:12px;margin-top:8px">Tháng N: từ 25 tháng N-1 đến hết 24 tháng N · Cấn trừ từ 05 đến cuối tháng N+1.</div>
            </div>
            <div class="hb-card">
                <div class="hb-card-title"><span>📅 Chiết khấu Quý</span></div>
                <table class="hb-table"><thead><tr><th>#</th><th>Doanh số quý</th><th>Mức CK</th></tr></thead><tbody>${simple(cs.ck_quy || [])}</tbody></table>
                ${lich ? `<table class="hb-table" style="margin-top:10px"><thead><tr><th>Quý</th><th>Thời gian quý</th><th>Thời gian cấn trừ</th></tr></thead><tbody>${lich}</tbody></table>` : ''}
            </div>
        </div>`;
    box.prepend(wrap);
}

// ======================== GIỎ BÁO GIÁ NÂNG CẤP ========================
function saveQuote() {
    localStorage.setItem('hsh_quote', JSON.stringify(quoteList));
    localStorage.setItem('hsh_install', JSON.stringify(quoteInstall));
    updateBadges();
}

function pushQuoteItem(item) {
    const ex = quoteList.find(q => q.ma_sp === item.ma_sp);
    if (ex) { ex.qty = (ex.qty || 1) + (item.qty || 1); return; }
    quoteList.push(item);
}

function addComboToQuote(ci) {
    const c = (extrasData.combo_ban_hang || [])[ci];
    if (!c) return;
    c.items.forEach(it => {
        const base = { ma_sp: it.ma_sp, id: it.id, qty: it.so_luong, gia: it.gia_combo, tang: !!it.tang, combo: c.ten_combo };
        if (!it.id) base.custom = { ten_sp: it.ten_sp, dvt: it.dvt, thuong_hieu: it.thuong_hieu, hinh_anh: it.hinh_anh, gia_niem_yet: it.gia_niem_yet };
        pushQuoteItem(base);
    });
    saveQuote();
    renderProducts();
    showToast(`📦 Đã thêm ${c.items.length} SP của “${c.ten_combo.substring(0, 30)}…” vào báo giá!`, 'success');
}

function addCustomToQuote(src, i) {
    if (src === 'tcg') {
        const t = extrasData.tcg_thong_minh.items[i];
        pushQuoteItem({ ma_sp: t.ma_sp, id: t.id, qty: 1, gia: t.gia_ban,
            custom: t.id ? undefined : { ten_sp: t.ten_sp, dvt: t.dvt, thuong_hieu: t.thuong_hieu, hinh_anh: t.hinh_anh, gia_niem_yet: t.gia_niem_yet } });
        saveQuote();
        showToast('📋 Đã thêm vào giỏ báo giá!', 'success');
    }
}

function copyCombo(ci) {
    const c = (extrasData.combo_ban_hang || [])[ci];
    if (!c) return;
    let txt = `📦 ${c.ten_combo} — HOA SEN HOME\n${'─'.repeat(40)}\n`;
    c.items.forEach((it, i) => {
        txt += `${i + 1}. ${it.ten_sp}\n   📌 ${it.ma_sp} | SL: ${it.so_luong} | ${it.tang ? '🎁 TẶNG (NY ' + formatPrice(it.gia_niem_yet) + ')' : formatPrice(it.gia_combo)}\n`;
    });
    txt += `${'─'.repeat(40)}\n💵 Tổng niêm yết: ${formatPrice(c.tong_niem_yet)}\n🔥 GIÁ COMBO: ${formatPrice(c.tong_combo)}`;
    if (c.tiet_kiem > 0) txt += `\n💰 Tiết kiệm: ${formatPrice(c.tiet_kiem)}`;
    txt += `\n📞 Liên hệ Hoa Sen Home để được tư vấn & giao hàng tận nơi!`;
    navigator.clipboard.writeText(txt).then(() => showToast('✅ Đã copy combo để gửi Zalo!', 'success'));
}

function resolveQuoteItem(q) {
    const p = q.id ? allProducts.find(x => x.id === q.id) : allProducts.find(x => x.ma_sp === q.ma_sp);
    const info = p || (q.custom ? { ...q.custom, ma_sp: q.ma_sp, ma_item: '', bao_hanh: '' } : null);
    if (!info) return null;
    let price;
    if (q.tang) price = 0;
    else if (typeof q.gia === 'number' && q.gia > 0) price = q.gia;
    else price = p ? getDisplayPrice(p, selectedPriceType) : (q.custom?.gia_niem_yet || 0);
    return { info, price, isFixed: q.tang || (typeof q.gia === 'number' && q.gia > 0) };
}

function installRows() { return (extrasData?.chi_phi_lap_dat?.bang_gia) || []; }

function installTotal() {
    return installRows().reduce((s, r) => s + (quoteInstall[r.stt] || 0) * r.co_vat, 0);
}

function setInstallQty(stt, val) {
    const v = Math.max(0, parseInt(val) || 0);
    if (v) quoteInstall[stt] = v; else delete quoteInstall[stt];
    saveQuote(); renderQuoteContent();
}

function suggestInstall() {
    const map = { 1: 0, 2: 0, 3: 0, 4: 0, 6: 0, 7: 0, 8: 0 };
    quoteList.forEach(q => {
        const r = resolveQuoteItem(q); if (!r || q.tang) return;
        const t = ((r.info.nhom_sp || '') + ' ' + (r.info.ten_sp || '')).toLowerCase();
        const n = q.qty || 1;
        if (/thông minh|điện tử|washlet/.test(t) && /cầu/.test(t)) map[2] += n;
        else if (/bồn cầu|bàn cầu|bồn tiểu/.test(t) && !/nắp|van|dây|phụ kiện/.test(t)) map[1] += n;
        else if (/bồn tắm|vách kính/.test(t)) map[3] += n;
        else if (/^lavabo|lavabo (đặt|treo|âm|bán)/.test(t) || /chậu lavabo/.test(t)) map[4] += n;
        else if (/tủ gương|tủ lavabo|bộ tủ/.test(t)) map[6] += n;
        else if (/sen (cây|tắm)|bộ sen/.test(t)) map[7] += n;
        else if (/chậu rửa (chén|bát)|chậu rửa inox/.test(t)) map[8] += n;
    });
    quoteInstall = {};
    Object.entries(map).forEach(([k, v]) => { if (v) quoteInstall[k] = v; });
    saveQuote(); renderQuoteContent();
    showToast('🔧 Đã gợi ý chi phí lắp đặt theo giỏ hàng', 'success');
}

renderQuoteContent = function () {
    const pt = selectedPriceType;
    let total = 0;
    const rows = quoteList.map((q, i) => {
        const r = resolveQuoteItem(q);
        if (!r) return '';
        const { info, price, isFixed } = r;
        const sub = price * (q.qty || 1);
        total += sub;
        return `<tr>
            <td style="text-align:center">${i + 1}</td>
            <td>${info.hinh_anh ? `<img src="${escHtml(info.hinh_anh)}" style="width:40px;height:40px;object-fit:contain">` : '🛁'}</td>
            <td>
                <div style="font-weight:700">${escHtml(info.ten_sp)}</div>
                <div style="font-size:11px;color:var(--text-muted)">📌 ${escHtml(q.ma_sp)} | ${escHtml(info.thuong_hieu || '')}${q.combo ? ` | <span class="chip" style="font-size:10px">📦 ${escHtml(q.combo.substring(0, 32))}</span>` : ''}</div>
            </td>
            <td style="text-align:center">${escHtml(info.dvt || '')}</td>
            <td style="text-align:center"><input type="number" class="qty-input" value="${q.qty || 1}" min="1" onchange="updateQty('${escJs(q.ma_sp)}',+this.value)"></td>
            <td style="color:${q.tang ? 'var(--success,#16a34a)' : 'var(--primary)'};font-weight:600;text-align:right">${q.tang ? '🎁 Tặng' : formatPrice(price)}${isFixed && !q.tang ? '<div style="font-size:10px;color:var(--text-muted)">giá combo</div>' : ''}</td>
            <td style="color:var(--primary);font-weight:800;text-align:right">${q.tang ? '0 ₫' : formatPrice(sub)}</td>
            <td style="text-align:center"><button onclick="removeFromQuote('${escJs(q.ma_sp)}')" style="border:none;background:none;color:var(--danger);cursor:pointer;font-size:16px" title="Xóa">🗑️</button></td>
        </tr>`;
    }).join('');

    const inst = installRows();
    const instTotal = installTotal();
    const grand = total + instTotal;
    const instHtml = inst.length ? `
        <details class="install-box" ${instTotal ? 'open' : ''}>
            <summary>🔧 Chi phí lắp đặt (tùy chọn) ${instTotal ? `— <b style="color:var(--primary)">${formatPrice(instTotal)}</b>` : ''}</summary>
            <div style="display:flex;gap:8px;margin:8px 0;flex-wrap:wrap">
                <button class="btn btn-sm btn-outline" onclick="suggestInstall()">✨ Gợi ý theo giỏ hàng</button>
                <button class="btn btn-sm btn-outline" onclick="quoteInstall={};saveQuote();renderQuoteContent()">↺ Bỏ lắp đặt</button>
            </div>
            <table class="quote-table"><thead><tr><th>Hạng mục lắp đặt</th><th style="text-align:right">Đơn giá (có VAT)</th><th style="text-align:center">SL</th><th style="text-align:right">Thành tiền</th></tr></thead>
            <tbody>${inst.map(r => `<tr><td>${escHtml(r.mat_hang)}</td><td style="text-align:right">${formatPrice(r.co_vat)}</td>
                <td style="text-align:center"><input type="number" class="qty-input" min="0" value="${quoteInstall[r.stt] || 0}" onchange="setInstallQty(${r.stt},this.value)"></td>
                <td style="text-align:right;font-weight:700">${quoteInstall[r.stt] ? formatPrice(quoteInstall[r.stt] * r.co_vat) : '—'}</td></tr>`).join('')}</tbody></table>
            <div style="font-size:11px;color:var(--text-muted);margin-top:6px">Theo CS ${escHtml(extrasData.chi_phi_lap_dat.so_van_ban)} — chưa gồm vật tư phát sinh.</div>
        </details>` : '';

    document.getElementById('quote-content').innerHTML = `<div class="quote-wrap">
        <div class="modal-page-title">📋 Bảng Báo Giá Khách Hàng <small style="font-size:13px;color:var(--text-muted)">(${quoteList.length} sản phẩm)</small></div>
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:16px;flex-wrap:wrap">
            <label style="font-size:13px;font-weight:700;color:var(--text-secondary)">Áp dụng cấp giá:</label>
            <select onchange="selectedPriceType=this.value;localStorage.setItem('hsh_price_type',this.value);renderQuoteContent()"
                style="padding:7px 12px;border:1.5px solid var(--border);border-radius:8px;font-family:var(--font);font-size:12.5px;font-weight:600">
                ${Object.entries(PRICE_LABELS).map(([k, v]) => `<option value="${k}" ${k === pt ? 'selected' : ''}>${v}</option>`).join('')}
            </select>
            <span style="margin-left:auto;font-size:14px">Tổng cộng: <strong style="color:var(--primary);font-size:17px">${formatPrice(grand)}</strong></span>
        </div>
        <div style="overflow-x:auto">
        <table class="quote-table">
            <thead><tr><th>#</th><th>Ảnh</th><th>Sản phẩm</th><th>ĐVT</th><th>SL</th><th style="text-align:right">${PRICE_LABELS[pt] || pt}</th><th style="text-align:right">Thành tiền</th><th></th></tr></thead>
            <tbody>${rows}</tbody>
            <tfoot>
                <tr><td colspan="6" style="text-align:right">Tiền hàng:</td><td style="text-align:right;font-weight:700">${formatPrice(total)}</td><td></td></tr>
                ${instTotal ? `<tr><td colspan="6" style="text-align:right">Chi phí lắp đặt:</td><td style="text-align:right;font-weight:700">${formatPrice(instTotal)}</td><td></td></tr>` : ''}
                <tr class="total-row"><td colspan="6" style="text-align:right">TỔNG CỘNG THANH TOÁN:</td><td style="text-align:right">${formatPrice(grand)}</td><td></td></tr>
            </tfoot>
        </table>
        </div>
        ${instHtml}
        <div style="margin-top:20px;display:flex;gap:8px;flex-wrap:wrap">
            <button class="btn btn-primary" onclick="window.print()">📄 In / Xuất PDF</button>
            <button class="btn btn-success" onclick="copyQuote()">📱 Copy gửi Zalo</button>
            <button class="btn btn-warning" onclick="exportExcel()">📊 Xuất File Excel (.CSV)</button>
            <button class="btn btn-outline" onclick="clearQuote()">🗑️ Xóa giỏ báo giá</button>
        </div>
    </div>`;
};

showQuote = function () {
    if (!quoteList.length) { showToast('Chưa có sản phẩm nào trong báo giá', 'warning'); return; }
    renderQuoteContent();
    document.getElementById('quote-modal-overlay').classList.add('active');
    document.body.style.overflow = 'hidden';
};

clearQuote = function () {
    quoteList = []; quoteInstall = {};
    localStorage.removeItem('hsh_quote'); localStorage.removeItem('hsh_install');
    updateBadges(); renderProducts(); closeQuoteModal();
};

copyQuote = function () {
    let txt = `📋 BÁO GIÁ THIẾT BỊ NHÀ TẮM & NHÀ BẾP — HOA SEN HOME\n🗓️ Ngày: ${new Date().toLocaleDateString('vi-VN')}\n💰 Bảng giá: ${PRICE_LABELS[selectedPriceType]}\n${'─'.repeat(42)}\n`;
    let total = 0, i = 0;
    quoteList.forEach(q => {
        const r = resolveQuoteItem(q); if (!r) return;
        const sub = r.price * q.qty; total += sub; i++;
        txt += `${i}. ${r.info.ten_sp}\n   📌 Mã: ${q.ma_sp} | SL: ${q.qty} ${r.info.dvt || ''} × ${q.tang ? '🎁 TẶNG' : formatPrice(r.price)}${q.tang ? '' : ' = ' + formatPrice(sub)}\n`;
    });
    const it = installTotal();
    txt += `${'─'.repeat(42)}\n💵 Tiền hàng: ${formatPrice(total)}\n`;
    if (it) {
        installRows().forEach(r => { if (quoteInstall[r.stt]) txt += `🔧 Lắp đặt ${r.mat_hang}: ${quoteInstall[r.stt]} × ${formatPrice(r.co_vat)}\n`; });
        txt += `🔧 Chi phí lắp đặt: ${formatPrice(it)}\n`;
    }
    txt += `✅ TỔNG CỘNG: ${formatPrice(total + it)}\n📞 Liên hệ Hoa Sen Home để được tư vấn & giao hàng tận nơi!`;
    navigator.clipboard.writeText(txt).then(() => showToast('✅ Đã copy nội dung báo giá để dán vào Zalo!', 'success'));
};

exportExcel = function () {
    const pt = selectedPriceType;
    const q2 = s => `"${String(s || '').replace(/"/g, '""')}"`;
    let csv = '\uFEFFBÁO GIÁ HOA SEN HOME\n';
    csv += `Ngày,${new Date().toLocaleDateString('vi-VN')}\nLoại giá,${PRICE_LABELS[pt]}\n\n`;
    csv += `STT,Mã SP,Mã Item,Tên sản phẩm,Thương hiệu,ĐVT,Số lượng,Đơn giá,Thành tiền,Ghi chú,Bảo hành\n`;
    let total = 0, i = 0;
    quoteList.forEach(q => {
        const r = resolveQuoteItem(q); if (!r) return;
        const sub = r.price * q.qty; total += sub; i++;
        csv += `${i},${q2(q.ma_sp)},${q2(r.info.ma_item)},${q2(r.info.ten_sp)},${q2(r.info.thuong_hieu)},${q2(r.info.dvt)},${q.qty},${r.price},${sub},${q2(q.tang ? 'Hàng tặng' : (q.combo ? 'Combo: ' + q.combo : ''))},${q2(r.info.bao_hanh)}\n`;
    });
    installRows().forEach(r => {
        if (!quoteInstall[r.stt]) return;
        const sub = quoteInstall[r.stt] * r.co_vat; i++;
        csv += `${i},"LAP-DAT","",${q2('Chi phí lắp đặt: ' + r.mat_hang)},"","Bộ",${quoteInstall[r.stt]},${r.co_vat},${sub},"",""\n`;
    });
    csv += `,,,,,,,TỔNG CỘNG,${total + installTotal()},,\n`;
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `BaoGia_HSH_${new Date().toLocaleDateString('vi-VN').replace(/\//g, '-')}.csv`;
    a.click();
    showToast('✅ Đã tải xuống file Excel báo giá!', 'success');
};

// Render if extrasData is already loaded
if (typeof extrasData !== 'undefined' && extrasData) {
    renderCtkmDangChay();
    renderCombosTab();
    renderChinhSachKinhDoanh();
    renderAlbumWarrantyTables();
}
