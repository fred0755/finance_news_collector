// ==================== 全局变量 ====================
let allNews = [];
let displayedNews = [];
let currentTimeRange = '12h';
let currentSearchTerm = '';
let loadedDates = new Set();
let isLoading = false;
let lastUpdateTime = '';

// ==================== 来源图标配置（包含所有可能值）====================
const SOURCE_CONFIG = {
    '东方财富': { emoji: '📈', name: '东方财富' },
    '东方财富快讯': { emoji: '📈', name: '东方财富' },
    '东方财富网': { emoji: '📈', name: '东方财富' },
    '财联社': { emoji: '📡', name: '财联社' },
    '新浪财经': { emoji: '🐦', name: '新浪财经' },
    '华尔街见闻': { emoji: '📰', name: '华尔街见闻' },
    '证券时报': { emoji: '📊', name: '证券时报' },
    '第一财经': { emoji: '📺', name: '第一财经' },
    '默认': { emoji: '🔗', name: '原文' }
};