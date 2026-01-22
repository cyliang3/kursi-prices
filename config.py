# Kursi Trades - 矿石价格抓取系统配置
# ==========================================
import os

# Manus API 配置 (从环境变量读取，保护密钥安全)
# 在本地运行时，请设置环境变量: export MANUS_API_KEY="your-api-key"
# 在 GitHub Actions 中，请在仓库 Settings > Secrets 中添加 MANUS_API_KEY
MANUS_API_KEY = os.environ.get("MANUS_API_KEY", "")
MANUS_API_BASE = "https://api.manus.im"

# ==========================================
# 数据源配置
# ==========================================

# SMM (上海金属网) 数据源
SMM_SOURCES = {
    # --- 稀土/独居石 ---
    "monazite": {
        "name_cn": "独居石精矿",
        "name_en": "Monazite Concentrate",
        "url": "https://www.metal.com/price/Rare-Earth/Concentrate",
        "field": "Monazite Concentrate (USD/mt)",
        "unit": "USD/mt",
    },
    
    # --- 锂矿 ---
    "spodumene": {
        "name_cn": "锂辉石精矿 (CIF中国)",
        "name_en": "Spodumene Concentrate",
        "url": "https://www.metal.com/price/New-Energy/Lithium",
        "field": "Spodumene Concentrate Index (CIF China) (USD/mt)",
        "unit": "USD/mt",
    },
    "lithium_carbonate": {
        "name_cn": "电池级碳酸锂",
        "name_en": "Battery-Grade Lithium Carbonate",
        "url": "https://www.metal.com/price/New-Energy/Lithium",
        "field": "Battery-Grade Lithium Carbonate (USD/mt)",
        "unit": "USD/mt",
    },
    
    # --- 钛铁矿 ---
    "titanium_nigeria": {
        "name_cn": "钛精矿 (尼日利亚, TiO2≥50%)",
        "name_en": "Titanium Concentrate (Nigeria)",
        "url": "https://www.metal.com/price/Minor-Metals/Titanium",
        "field": "Titanium Concentrate (Nigeria origin, TiO2 content ≥50%) (yuan/mt)",
        "unit": "CNY/mt",
    },
    
    # --- 钽铌矿 ---
    "tantalum_ore": {
        "name_cn": "钽矿 (Ta≥30%, CIF中国)",
        "name_en": "Tantalum Ore",
        "url": "https://www.metal.com/price/Minor-Metals/Niobium-Tantalum",
        "field": "Tantalum Ore (Ta2O5 ≥30%) CIF China",
        "unit": "USD/lb",
    },
    "tantalum_oxide": {
        "name_cn": "钽氧化物 (Ta₂O₅ 99.5%)",
        "name_en": "Tantalum Oxide",
        "url": "https://www.metal.com/price/Minor-Metals/Niobium-Tantalum",
        "field": "Tantalum Oxide (Ta2O5 99.5%)",
        "unit": "USD/kg",
    },
    "niobium_oxide": {
        "name_cn": "铌氧化物 (Nb₂O₅ 99.5%)",
        "name_en": "Niobium Oxide",
        "url": "https://www.metal.com/price/Minor-Metals/Niobium-Tantalum",
        "field": "Niobium Oxide (Nb2O5 99.5%)",
        "unit": "USD/kg",
    },
    
    # --- 锆英砂 ---
    "zircon_sand": {
        "name_cn": "锆英砂",
        "name_en": "Zircon Sand",
        "url": "https://www.metal.com/price/Minor-Metals/Other-Minor-Metals",
        "field": "Zircon Sand",
        "unit": "USD/mt",
    },
    
    # --- 基本金属 (SMM) ---
    "smm_tin": {
        "name_cn": "锡 (SMM)",
        "name_en": "Tin (SMM)",
        "url": "https://www.metal.com/price/Base-Metals/Tin",
        "field": "SMM 1# Tin Ingot",
        "unit": "USD/mt",
    },
    "smm_lead": {
        "name_cn": "铅 (SMM)",
        "name_en": "Lead (SMM)",
        "url": "https://www.metal.com/price/Base-Metals/Lead",
        "field": "SMM 1# Lead Ingot",
        "unit": "USD/mt",
    },
    "smm_zinc": {
        "name_cn": "锌 (SMM)",
        "name_en": "Zinc (SMM)",
        "url": "https://www.metal.com/price/Base-Metals/Zinc",
        "field": "SMM 0# Zinc Ingot",
        "unit": "USD/mt",
    },
    
    # --- 贵金属 (SMM) ---
    "smm_gold": {
        "name_cn": "黄金 (SMM)",
        "name_en": "Gold (SMM)",
        "url": "https://www.metal.com/price/Precious-Metals/Gold",
        "field": "Au99.99",
        "unit": "CNY/g",
    },
    "smm_silver": {
        "name_cn": "白银 (SMM)",
        "name_en": "Silver (SMM)",
        "url": "https://www.metal.com/price/Precious-Metals/Silver",
        "field": "Ag99.99",
        "unit": "CNY/kg",
    },
}

# LME / 国际市场数据源 (通过 Investing.com)
LME_SOURCES = {
    "lme_tin": {
        "name_cn": "锡 (LME)",
        "name_en": "Tin (LME)",
        "url": "https://www.investing.com/commodities/tin",
        "unit": "USD/mt",
    },
    "lme_lead": {
        "name_cn": "铅 (LME)",
        "name_en": "Lead (LME)",
        "url": "https://www.investing.com/commodities/lead",
        "unit": "USD/mt",
    },
    "lme_zinc": {
        "name_cn": "锌 (LME)",
        "name_en": "Zinc (LME)",
        "url": "https://www.investing.com/commodities/zinc",
        "unit": "USD/mt",
    },
    "lme_gold": {
        "name_cn": "黄金 (国际)",
        "name_en": "Gold (International)",
        "url": "https://www.investing.com/commodities/gold",
        "unit": "USD/oz",
    },
    "lme_silver": {
        "name_cn": "白银 (国际)",
        "name_en": "Silver (International)",
        "url": "https://www.investing.com/commodities/silver",
        "unit": "USD/oz",
    },
}

# 汇率数据源
EXCHANGE_RATE_SOURCE = {
    "name": "环非平行市场",
    "url": "https://mp.weixin.qq.com/s/rxk1MaKpRMME8HJpSbxX0A",
    "note": "需要访问最新文章获取 USD/CNY/NGN 汇率",
    "currencies": ["USD", "CNY", "NGN"],
}

# ==========================================
# 系统配置
# ==========================================

# 数据存储路径
DATA_DIR = "data"
PRICE_JSON_FILE = "data/price_history.json"  # 历史价格汇总

# 任务超时设置（秒）
TASK_TIMEOUT = 600  # 10分钟，Manus访问多个网站需要时间
TASK_CHECK_INTERVAL = 15

# 需要对比价差的矿种配对 (SMM vs LME)
PRICE_COMPARISON_PAIRS = [
    ("smm_tin", "lme_tin", "锡"),
    ("smm_lead", "lme_lead", "铅"),
    ("smm_zinc", "lme_zinc", "锌"),
    ("smm_gold", "lme_gold", "黄金"),
    ("smm_silver", "lme_silver", "白银"),
]
