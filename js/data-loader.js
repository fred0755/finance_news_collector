// ==================== 加载单日数据 ====================
async function loadDateData(dateStr) {
    if (loadedDates.has(dateStr)) return null;
    try {
        const response = await fetch(`/data/archive/${dateStr}.json?t=${Date.now()}`);
        if (!response.ok) return null;
        const data = await response.json();
        loadedDates.add(dateStr);
        return data;
    } catch (e) {
        console.error(`加载 ${dateStr} 失败:`, e);
        return null;
    }
}

// ==================== 加载所有未加载的历史数据 ====================
async function loadAllRemainingArchiveData() {
    const today = new Date();
    const maxDaysToTry = 90;
    let consecutiveFailures = 0;
    const maxConsecutiveFailures = 5;

    for (let i = 0; i < maxDaysToTry; i++) {
        const date = new Date(today);
        date.setDate(date.getDate() - i);
        const dateStr = date.toISOString().split('T')[0];

        if (loadedDates.has(dateStr)) {
            consecutiveFailures = 0;
            continue;
        }

        try {
            showSearchLoading(`正在加载历史数据 (${dateStr})...`);
            const response = await fetch(`/data/archive/${dateStr}.json?t=${Date.now()}`);

            if (!response.ok) {
                consecutiveFailures++;
                if (consecutiveFailures >= maxConsecutiveFailures) {
                    console.log(`⏹️ 连续${maxConsecutiveFailures}天没有数据，停止加载`);
                    break;
                }
                continue;
            }

            const data = await response.json();
            if (data && data.length > 0) {
                console.log(`  ✅ 加载 ${dateStr} 成功: ${data.length} 条`);
                loadedDates.add(dateStr);
                const merged = mergeNews(data);
                allNews = mergeNews([...allNews, ...merged]);
                consecutiveFailures = 0;
            }
        } catch (e) {
            console.error(`加载 ${dateStr} 失败:`, e);
            consecutiveFailures++;
            if (consecutiveFailures >= maxConsecutiveFailures) {
                break;
            }
        }
    }

    allNews = sortByTime(allNews);
}

// ==================== 初始化加载 ====================
async function loadInitialData() {
    try {
        console.log('🔄 开始加载初始数据...');
        const timeRes = await fetch('/data/last_update.txt?t=' + Date.now());
        const updateTime = await timeRes.text();
        lastUpdateTime = updateTime;
        document.getElementById('update-time').textContent = updateTime.trim().slice(5, 16) || '--:--';

        const now = new Date();
        const startTime = new Date(now);
        startTime.setHours(startTime.getHours() - 12);

        const datesToLoad = [];
        let currentDate = new Date(startTime);

        while (currentDate <= now) {
            const dateStr = currentDate.toISOString().split('T')[0];
            if (!loadedDates.has(dateStr)) {
                datesToLoad.push(dateStr);
            }
            currentDate.setDate(currentDate.getDate() + 1);
        }

        if (datesToLoad.length > 0) {
            console.log(`🔄 加载初始数据: ${datesToLoad.join(', ')}`);

            const loadPromises = datesToLoad.map(dateStr => loadDateData(dateStr));
            const results = await Promise.all(loadPromises);

            allNews = [];
            results.forEach((data, index) => {
                if (data && data.length > 0) {
                    const dateStr = datesToLoad[index];
                    console.log(`  ✅ 加载 ${dateStr} 成功: ${data.length} 条`);
                    const merged = mergeNews(data);
                    allNews = mergeNews([...allNews, ...merged]);
                }
            });
        }

        const todayStr = now.toISOString().split('T')[0];
        if (!loadedDates.has(todayStr)) {
            const todayData = await loadDateData(todayStr);
            if (todayData && todayData.length > 0) {
                const merged = mergeNews(todayData);
                allNews = mergeNews([...allNews, ...merged]);
            }
        }

        applyFilters();
        console.log(`✅ 初始化完成: 总计 ${allNews.length} 条新闻`);

    } catch (e) {
        console.error('❌ 加载初始数据失败:', e);
        document.getElementById('news-list').innerHTML = `
            <div class="error">
                <span>⚠️</span>
                <h3>加载失败</h3>
                <p>${e.message}</p>
                <button onclick="location.reload()" class="retry-btn">重试</button>
            </div>
        `;
    }
}

// ==================== 按需加载历史数据（用于24h/3d）====================
async function loadHistoricalData(range) {
    if (isLoading) return;
    isLoading = true;

    const loadBtn = document.getElementById('load-more-btn');
    loadBtn.style.display = 'block';
    loadBtn.textContent = '📅 正在加载历史数据...';
    loadBtn.classList.add('disabled');

    try {
        const now = new Date();
        const days = range === '24h' ? 1 : 2;
        const datesToLoad = [];

        for (let i = 1; i <= days; i++) {
            const date = new Date(now);
            date.setDate(date.getDate() - i);
            const dateStr = date.toISOString().split('T')[0];
            if (!loadedDates.has(dateStr)) {
                datesToLoad.push(dateStr);
            }
        }

        if (datesToLoad.length > 0) {
            const loadPromises = datesToLoad.map(dateStr => loadDateData(dateStr));
            const results = await Promise.all(loadPromises);

            results.forEach((data) => {
                if (data && data.length > 0) {
                    const merged = mergeNews(data);
                    allNews = mergeNews([...allNews, ...merged]);
                }
            });
        }

        applyFilters();

    } catch (error) {
        console.error('加载历史数据失败:', error);
    } finally {
        loadBtn.style.display = 'none';
        isLoading = false;
    }
}