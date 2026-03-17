// ==================== 合并新闻（核心逻辑）====================
function mergeNews(newsList) {
    const newsMap = new Map();

    newsList.forEach(item => {
        let rawTitle = item.title || '无标题';
        let cleanTitle = rawTitle
            .replace(/^(【.*?】)?(财联社.*?日电\s*)?/g, '')
            .replace(/^\s*|\s*$/g, '');
        if (!cleanTitle) cleanTitle = rawTitle;

        const key = cleanTitle;

        // ===== 推断来源（因为数据中没有 source 字段）=====
        let sourceName = '默认';

        // 1. 根据标题特征推断东方财富
        if (item.title.includes('快讯') ||
            item.title.includes('行情') ||
            item.title.includes('公告') ||
            item.title.includes('业绩') ||
            item.title.includes('涨停') ||
            item.title.includes('跌停')) {
            sourceName = '东方财富快讯';
        }

        // 2. 根据 code 特征（东方财富的 code 是纯数字）
        if (item.code && /^\d+$/.test(item.code)) {
            sourceName = '东方财富快讯';
        }

        // 3. 财联社来源推断
        if (item.title.includes('财联社') || item.title.includes('科创板')) {
            sourceName = '财联社';
        }

        const url = getNewsUrl(item);
        const time = getFullNewsTime(item) || '未知时间';
        const displayTime = formatNewsTime(time);

        if (!newsMap.has(key)) {
            // 首次出现，必须保存 code
            newsMap.set(key, {
                title: rawTitle,
                cleanTitle: cleanTitle,
                code: item.code,
                time: time,
                displayTime: displayTime,
                full_content: item.full_content || item.content || '',
                tags: item.tags || { industries: [], concepts: [] },
                sources: [{
                    name: sourceName,
                    url: url,
                    config: getSourceConfig(sourceName)
                }]
            });
        } else {
            const existing = newsMap.get(key);

            const existingSource = existing.sources.find(s => s.name === sourceName);
            if (!existingSource) {
                existing.sources.push({
                    name: sourceName,
                    url: url,
                    config: getSourceConfig(sourceName)
                });
            } else {
                existingSource.url = url;
            }

            if (time !== '未知时间' && (existing.time === '未知时间' || time > existing.time)) {
                existing.time = time;
                existing.displayTime = displayTime;
                existing.code = item.code;
                if (item.full_content) {
                    existing.full_content = item.full_content;
                }
            } else {
                if (!existing.code && item.code) {
                    existing.code = item.code;
                }
            }
        }
    });

    return Array.from(newsMap.values()).sort((a, b) => (b.time || '').localeCompare(a.time || ''));
}

// ==================== 过滤新闻（根据搜索词）====================
function filterNews(newsArray, searchTerm) {
    if (!searchTerm) return newsArray;
    const term = searchTerm.toLowerCase();
    return newsArray.filter(item =>
        item.title.toLowerCase().includes(term)
    );
}

// ==================== 根据时间范围过滤 ====================
function filterByTimeRange(newsArray, range) {
    const now = new Date();
    let cutoffTime = new Date();

    switch(range) {
        case '12h':
            cutoffTime = new Date(now - 12 * 60 * 60 * 1000);
            break;
        case '24h':
            cutoffTime = new Date(now - 24 * 60 * 60 * 1000);
            break;
        case '3d':
            cutoffTime = new Date(now - 3 * 24 * 60 * 60 * 1000);
            break;
        default:
            return newsArray;
    }

    return newsArray.filter(item => {
        if (item.time === '未知时间') return false;
        const itemDate = new Date(item.time);
        return itemDate >= cutoffTime;
    });
}