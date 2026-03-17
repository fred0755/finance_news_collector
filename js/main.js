// ==================== 渲染新闻列表 ====================
function renderNews(newsArray) {
    const container = document.getElementById('news-list');
    if (!newsArray || newsArray.length === 0) {
        container.innerHTML = '<div class="empty"><span>📭</span><h3>暂无新闻</h3></div>';
        document.getElementById('news-count').textContent = '0';
        return;
    }

    let html = '';
    newsArray.forEach((item, index) => {
        const displayTime = item.displayTime || (item.time ? item.time.slice(5, 16) : '未知时间');

        let sourcesHtml = '';
        if (item.sources && item.sources.length > 0) {
            item.sources.forEach(source => {
                sourcesHtml += `
                    <a href="${escapeHtml(source.url)}" target="_blank" class="source-icon" title="查看${source.name}原文">
                        <span class="emoji">${source.config.emoji}</span> ${source.config.name}
                    </a>
                `;
            });
        }

        const tagsHtml = renderTags(item.tags);
        const hasFullContent = item.full_content &&
                              item.full_content !== item.title &&
                              item.full_content.length > 30;
        const detailId = `detail-${index}-${Date.now()}`;

        html += `
            <div class="news-card" id="card-${detailId}">
                <div class="news-title">${escapeHtml(item.title)}</div>
                <div class="sources-bar">${sourcesHtml}</div>
                ${hasFullContent ? `
                    <div class="news-detail" id="${detailId}" style="display: none;">
                        ${escapeHtml(item.full_content)}
                    </div>
                    <button class="toggle-detail-btn" data-target="${detailId}">
                        <span>🔽</span> 查看详情
                    </button>
                ` : ''}
                <div class="news-time">
                    <span class="time-icon">🕐</span>
                    <span>${displayTime}</span>
                </div>
                ${tagsHtml ? `<div class="news-tags">${tagsHtml}</div>` : ''}
            </div>
        `;
    });

    container.innerHTML = html;
    document.getElementById('news-count').textContent = newsArray.length;

    document.querySelectorAll('.toggle-detail-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            const targetId = this.getAttribute('data-target');
            const detailDiv = document.getElementById(targetId);
            if (detailDiv) {
                if (detailDiv.style.display === 'none') {
                    detailDiv.style.display = 'block';
                    this.innerHTML = '<span>🔼</span> 收起详情';
                } else {
                    detailDiv.style.display = 'none';
                    this.innerHTML = '<span>🔽</span> 查看详情';
                }
            }
        });
    });
}

// ==================== 应用所有过滤条件 ====================
function applyFilters() {
    // 如果正在搜索，显示提示
    if (currentSearchTerm) {
        document.getElementById('news-list').innerHTML = `
            <div class="loading">
                <span>🔍</span>
                正在搜索 "${currentSearchTerm}"...
            </div>
        `;
    }

    // 关键修改：如果有搜索词，就不按时间范围过滤
    let filtered;
    if (currentSearchTerm) {
        filtered = filterNews(allNews, currentSearchTerm);
    } else {
        filtered = filterByTimeRange(allNews, currentTimeRange);
        filtered = filterNews(filtered, currentSearchTerm);
    }

    renderNews(filtered);
}

// ==================== 改变时间范围 ====================
async function setTimeRange(range) {
    currentTimeRange = range;

    document.querySelectorAll('.time-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.range === range) {
            btn.classList.add('active');
        }
    });

    if (range === '12h') {
        applyFilters();
        return;
    }

    await loadHistoricalData(range);
}

// ==================== 搜索处理 ====================
async function handleSearch() {
    const searchInput = document.getElementById('search-input');
    const term = searchInput.value.trim();
    currentSearchTerm = term;

    const searchAll = document.getElementById('search-all')?.checked || false;

    document.getElementById('clear-search').style.display = term ? 'inline' : 'none';

    if (searchAll && term) {
        try {
            await loadAllRemainingArchiveData();
        } catch (e) {
            console.error('全库搜索失败:', e);
        } finally {
            hideSearchLoading();
        }
    }

    applyFilters(); // 直接调用，让 applyFilters 处理是否有搜索词的情况
}

// ==================== 清除搜索 ====================
function clearSearch() {
    document.getElementById('search-input').value = '';
    currentSearchTerm = '';
    document.getElementById('search-all').checked = false;
    document.getElementById('clear-search').style.display = 'none';
    applyFilters();
}

// ==================== 初始化 ====================
window.addEventListener('DOMContentLoaded', () => {
    loadInitialData();

    document.querySelectorAll('.time-btn').forEach(btn => {
        btn.addEventListener('click', () => setTimeRange(btn.dataset.range));
    });

    document.getElementById('search-btn').addEventListener('click', handleSearch);
    document.getElementById('clear-search').addEventListener('click', clearSearch);
    document.getElementById('search-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleSearch();
    });
});