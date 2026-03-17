// ==================== 获取来源配置 ====================
function getSourceConfig(source) {
    const defaultConfig = SOURCE_CONFIG['默认'];
    if (!source) return defaultConfig;
    return SOURCE_CONFIG[source] || defaultConfig;
}

// ==================== 获取新闻链接 ====================
function getNewsUrl(item) {
    if (item && item.code) {
        return `https://finance.eastmoney.com/a/${item.code}.html`;
    }
    return 'https://finance.eastmoney.com/';
}

// ==================== 按时间排序 ====================
function sortByTime(newsArray) {
    return newsArray.sort((a, b) => {
        if (a.time === '未知时间' && b.time === '未知时间') return 0;
        if (a.time === '未知时间') return 1;
        if (b.time === '未知时间') return -1;
        return b.time.localeCompare(a.time);
    });
}

// ==================== 格式化时间显示 ====================
function formatNewsTime(timeStr) {
    if (!timeStr) return '未知时间';
    if (/^\d{2}-\d{2} \d{2}:\d{2}$/.test(timeStr)) {
        return timeStr;
    }
    const match = timeStr.match(/(\d{4}-\d{2}-\d{2}) (\d{2}:\d{2})/);
    if (match) {
        return `${match[1].slice(5)} ${match[2]}`;
    }
    return timeStr;
}

// ==================== 获取新闻时间 ====================
function getFullNewsTime(item) {
    if (!item) return null;
    return item.showTime || item.time || item.publish_time || item.pubDate || item.raw_data?.showTime || null;
}

// ==================== 渲染标签 ====================
function renderTags(tags) {
    if (!tags) return '';
    let html = '';
    if (tags.concepts && tags.concepts.length > 0) {
        tags.concepts.forEach(concept => {
            const matched = concept.matched_keyword ? ` (${concept.matched_keyword})` : '';
            html += `<span class="tag tag-concept" title="概念: ${concept.name}${matched}">🏷️ ${concept.name}</span>`;
        });
    }
    if (tags.industries && tags.industries.length > 0) {
        tags.industries.forEach(industry => {
            const levelInfo = `行业: ${industry.level1 || ''} > ${industry.level2 || ''} > ${industry.name}`;
            html += `<span class="tag tag-industry" title="${levelInfo}">🏭 ${industry.name}</span>`;
        });
    }
    return html;
}

// ==================== HTML转义 ====================
function escapeHtml(unsafe) {
    if (!unsafe) return '';
    return String(unsafe)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

// ==================== 显示/隐藏搜索加载提示 ====================
function showSearchLoading(message) {
    let loadingDiv = document.getElementById('search-loading');
    if (!loadingDiv) {
        loadingDiv = document.createElement('div');
        loadingDiv.id = 'search-loading';
        loadingDiv.className = 'search-loading';
        document.body.appendChild(loadingDiv);
    }
    loadingDiv.innerHTML = `<span>⏳</span> ${message}`;
    loadingDiv.style.display = 'flex';
}

function hideSearchLoading() {
    const loadingDiv = document.getElementById('search-loading');
    if (loadingDiv) {
        loadingDiv.style.display = 'none';
    }
}