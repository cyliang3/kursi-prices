# Kursi Trades - 矿石价格抓取器
# ==========================================

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional

from config import SMM_SOURCES, LME_SOURCES, DATA_DIR, PRICE_JSON_FILE
from manus_client import ManusClient


class PriceScraper:
    """矿石价格抓取器"""
    
    def __init__(self):
        self.client = ManusClient()
        self._ensure_data_dir()
    
    def _ensure_data_dir(self):
        """确保数据目录存在"""
        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR)
    
    def build_scraping_prompt(self) -> str:
        """构建完整的价格抓取 Prompt - 优化版"""
        today = datetime.now().strftime("%Y-%m-%d")
        current_time = datetime.now().strftime("%H:%M")
        
        prompt = f"""
你是一个专业的矿石和金属价格数据收集助手。请像正常用户一样浏览以下网站，提取今日（{today}）的价格数据。

## 操作说明
- 像普通用户一样访问每个页面
- 等待页面完全加载后再提取数据
- 从页面表格中读取 Price Range、Avg、Change 等数据
- 最后将所有数据整理成 JSON 格式返回

---

## 一、SMM 数据 (metal.com) - 共7个页面

### 1. 独居石精矿
访问: https://www.metal.com/price/Rare-Earth/Concentrate
在 "Concentrate prices" 表格中找到 "Monazite Concentrate (USD/mt)" 这一行
读取: Price Range (如 7,440.97-7,567.73), Avg (如 7,504.35), Change (如 -42.24)

### 2. 锂矿
访问: https://www.metal.com/price/New-Energy/Lithium
在价格表格中找到:
- "Spodumene Concentrate" 相关价格 (CIF China, USD/mt)
- "Lithium Carbonate, Battery Grade" 价格 (USD/mt)

### 3. 钛精矿
访问: https://www.metal.com/price/Minor-Metals/Titanium
找到 "Titanium Concentrate" 相关价格，优先找尼日利亚来源的 (Nigeria origin)

### 4. 钽铌矿
访问: https://www.metal.com/price/Minor-Metals/Niobium-Tantalum
在表格中找到:
- Tantalum Ore (Ta2O5 含量 ≥30%) 的价格
- Tantalum Oxide (Ta2O5 99.5%) 的价格
- Niobium Oxide (Nb2O5 99.5%) 的价格

### 5. 锆英砂
访问: https://www.metal.com/price/Minor-Metals/Zirconium
或者: https://www.metal.com/price/Minor-Metals/Other-Minor-Metals
找到 "Zircon Sand" 或 "Zircon" 相关价格

### 6. 基本金属 (SMM)
- 锡: https://www.metal.com/price/Base-Metals/Tin → 找 "SMM Tin" 价格
- 铅: https://www.metal.com/price/Base-Metals/Lead → 找 "SMM Lead" 价格
- 锌: https://www.metal.com/price/Base-Metals/Zinc → 找 "SMM Zinc" 价格

### 7. 贵金属 (SMM)
- 黄金: https://www.metal.com/price/Precious-Metals/Gold → 找 "Au99.99" 价格
- 白银: https://www.metal.com/price/Precious-Metals/Silver → 找 "Ag99.99" 价格

---

## 二、LME/国际市场 (Investing.com)

访问以下页面，提取当前价格和涨跌幅:
1. 锡: https://www.investing.com/commodities/tin
2. 铅: https://www.investing.com/commodities/lead
3. 锌: https://www.investing.com/commodities/zinc
4. 黄金: https://www.investing.com/commodities/gold
5. 白银: https://www.investing.com/commodities/silver

---

## 三、汇率 (重要！)

**首选来源：环非平行市场公众号**
尝试访问: https://mp.weixin.qq.com/s?__biz=Mzg5NDc0NTIwNA==&mid=2247491931&idx=1&sn=1c01f98e4a6c2d1dd59455e590c9917f

如果上述链接无法访问（需要验证），请使用以下方法：

**方法1**: 在微信公众号平台搜索"环非平行市场"，找到最新一篇文章，获取汇率

**方法2**: 在搜索引擎搜索以下关键词获取最新平行市场汇率:
- "环非平行市场 今日汇率"
- "Nigeria Naira parallel market rate today"
- "USD NGN black market rate"
- "人民币 奈拉 平行市场"

需要获取的汇率:
- USD/CNY (美元对人民币) - 中国银行或央行汇率
- USD/NGN (美元对奈拉) - **平行市场汇率，不是官方汇率**
- CNY/NGN (人民币对奈拉) - 平行市场汇率

**注意**: 尼日利亚有官方汇率和平行市场(黑市)汇率，我们需要的是**平行市场汇率**，通常比官方汇率高很多。目前平行市场汇率大约在 1 USD = 1500-1700 NGN 左右。

---

## 输出要求

请将收集到的数据整理成以下 JSON 格式（只返回JSON，不要其他文字）:

```json
{{
    "date": "{today}",
    "fetch_time": "{current_time}",
    "smm_prices": {{
        "monazite": {{"price_low": 7440.97, "price_high": 7567.73, "price_avg": 7504.35, "unit": "USD/mt", "change": "-42.24"}},
        "spodumene": {{"price_low": null, "price_high": null, "price_avg": null, "unit": "USD/mt", "change": null}},
        "lithium_carbonate": {{"price_low": null, "price_high": null, "price_avg": null, "unit": "USD/mt", "change": null}},
        "titanium": {{"price_low": null, "price_high": null, "price_avg": null, "unit": "CNY/mt", "change": null}},
        "tantalum_ore": {{"price_low": null, "price_high": null, "price_avg": null, "unit": "USD/lb", "change": null}},
        "tantalum_oxide": {{"price_low": null, "price_high": null, "price_avg": null, "unit": "USD/kg", "change": null}},
        "niobium_oxide": {{"price_low": null, "price_high": null, "price_avg": null, "unit": "USD/kg", "change": null}},
        "zircon_sand": {{"price_low": null, "price_high": null, "price_avg": null, "unit": "USD/mt", "change": null}},
        "tin": {{"price_low": null, "price_high": null, "price_avg": null, "unit": "CNY/mt", "change": null}},
        "lead": {{"price_low": null, "price_high": null, "price_avg": null, "unit": "CNY/mt", "change": null}},
        "zinc": {{"price_low": null, "price_high": null, "price_avg": null, "unit": "CNY/mt", "change": null}},
        "gold": {{"price_avg": null, "unit": "CNY/g", "change": null}},
        "silver": {{"price_avg": null, "unit": "CNY/kg", "change": null}}
    }},
    "lme_prices": {{
        "tin": {{"price": null, "unit": "USD/mt", "change": null}},
        "lead": {{"price": null, "unit": "USD/mt", "change": null}},
        "zinc": {{"price": null, "unit": "USD/mt", "change": null}},
        "gold": {{"price": null, "unit": "USD/oz", "change": null}},
        "silver": {{"price": null, "unit": "USD/oz", "change": null}}
    }},
    "exchange_rates": {{
        "usd_cny": null,
        "usd_ngn": null,
        "cny_ngn": null,
        "source": "环非平行市场 或 其他来源",
        "rate_type": "parallel_market"
    }},
    "data_issues": {{
        "unavailable": [],
        "reasons": ""
    }}
}}
```

**说明**: 上面的 null 值都需要替换为你实际从网页获取的数据。如果某个数据确实无法获取，保留 null 并在 data_issues 中说明原因。
"""
        return prompt
    
    def fetch_prices(self) -> Dict[str, Any]:
        """执行价格抓取"""
        print("=" * 60)
        print("🚀 开始抓取今日矿石价格")
        print("=" * 60)
        print("📋 抓取内容:")
        print("   - SMM: 独居石、锂矿、钛矿、钽铌、锆砂、锡铅锌、金银")
        print("   - LME: 锡、铅、锌、黄金、白银")
        print("   - 汇率: USD/CNY/NGN")
        print("=" * 60)
        
        prompt = self.build_scraping_prompt()
        
        try:
            result = self.client.run_task(prompt)
            
            print(f"\n📋 返回数据类型: {type(result)}")
            
            # 处理返回结果
            text_content = self._extract_text_content(result)
            
            if text_content:
                print(f"📋 提取的文本长度: {len(str(text_content))} 字符")
                price_data = self._parse_json_from_text(text_content)
                
                if price_data and "error" not in price_data:
                    print("\n✅ 价格数据抓取成功!")
                    return price_data
            
            return {"error": "无法解析返回数据", "raw": str(result)[:1000]}
            
        except Exception as e:
            print(f"❌ 抓取失败: {e}")
            import traceback
            traceback.print_exc()
            return {"error": str(e)}
    
    def _extract_text_content(self, result) -> Optional[str]:
        """从各种格式的结果中提取文本内容"""
        if isinstance(result, str):
            return result
        elif isinstance(result, dict):
            if "smm_prices" in result or "lme_prices" in result or "date" in result:
                return json.dumps(result)
            return (result.get("text") or result.get("content") or 
                   result.get("message") or result.get("output") or
                   json.dumps(result))
        elif isinstance(result, list):
            for item in result:
                if isinstance(item, dict):
                    if "smm_prices" in item or "lme_prices" in item:
                        return json.dumps(item)
                    text = item.get("text") or item.get("content") or item.get("message")
                    if text and isinstance(text, str) and "{" in text:
                        return text
                elif isinstance(item, str) and "{" in item:
                    return item
            return json.dumps(result)
        return str(result) if result else None
    
    def _parse_json_from_text(self, text) -> Dict[str, Any]:
        """从文本中解析JSON"""
        try:
            if isinstance(text, dict):
                return text
            
            if isinstance(text, list):
                debug_file = os.path.join(DATA_DIR, "debug_last_response.txt")
                with open(debug_file, "w", encoding="utf-8") as f:
                    f.write(str(text))
                return {"error": "返回格式为list", "raw": str(text)[:500]}
            
            if not isinstance(text, str):
                text = str(text)
            
            # 提取 JSON 部分
            if "```json" in text:
                json_str = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                parts = text.split("```")
                json_str = None
                for part in parts:
                    if "{" in part and "prices" in part:
                        json_str = part
                        break
                if not json_str:
                    json_str = text
            else:
                start = text.find("{")
                end = text.rfind("}") + 1
                if start != -1 and end > start:
                    json_str = text[start:end]
                else:
                    json_str = text
            
            return json.loads(json_str.strip())
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON 解析失败: {e}")
            debug_file = os.path.join(DATA_DIR, "debug_last_response.txt")
            with open(debug_file, "w", encoding="utf-8") as f:
                f.write(str(text))
            print(f"💾 原始响应已保存到: {debug_file}")
            return {"error": "JSON解析失败", "raw": str(text)[:500]}
    
    def save_prices(self, price_data: Dict[str, Any]):
        """保存价格数据到 JSON 文件"""
        date = price_data.get("date", datetime.now().strftime("%Y-%m-%d"))
        
        # 1. 保存当日文件
        daily_file = os.path.join(DATA_DIR, f"prices_{date}.json")
        with open(daily_file, "w", encoding="utf-8") as f:
            json.dump(price_data, f, ensure_ascii=False, indent=2)
        print(f"💾 当日数据保存到: {daily_file}")
        
        # 2. 更新历史记录
        history = {}
        if os.path.exists(PRICE_JSON_FILE):
            with open(PRICE_JSON_FILE, "r", encoding="utf-8") as f:
                history = json.load(f)
        
        history[date] = price_data
        
        with open(PRICE_JSON_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
        print(f"💾 历史记录更新: {PRICE_JSON_FILE}")
    
    def print_prices(self, price_data: Dict[str, Any]):
        """打印价格数据"""
        print("\n" + "=" * 80)
        print(f"📊 今日矿石价格汇总 ({price_data.get('date', 'N/A')})")
        print("=" * 80)
        
        # SMM 价格
        print("\n【SMM 上海金属网】")
        print("-" * 80)
        smm_prices = price_data.get("smm_prices", {})
        
        # 支持多种字段名格式 (monazite 或 monazite_concentrate)
        smm_names = {
            ("monazite", "monazite_concentrate"): "独居石精矿",
            ("spodumene", "spodumene_concentrate"): "锂辉石精矿",
            ("lithium_carbonate",): "电池级碳酸锂",
            ("titanium", "titanium_concentrate"): "钛精矿",
            ("tantalum_ore",): "钽矿(Ta≥30%)",
            ("tantalum_oxide",): "钽氧化物",
            ("niobium_oxide",): "铌氧化物",
            ("zircon_sand", "zircon"): "锆英砂",
            ("tin",): "锡",
            ("lead",): "铅",
            ("zinc",): "锌",
            ("gold",): "黄金",
            ("silver",): "白银",
        }
        
        for keys, name in smm_names.items():
            data = None
            for key in keys:
                if key in smm_prices:
                    data = smm_prices[key]
                    break
            
            if data and data is not None:
                price = data.get("price_avg") or data.get("price", "N/A")
                unit = data.get("unit", "")
                change = data.get("change", "")
                print(f"  {name:<18} | {str(price):>12} {unit:<10} | {change}")
            else:
                print(f"  {name:<18} | {'未获取':>12} {'':<10} | ")
        
        # LME 价格
        print("\n【LME 国际市场】")
        print("-" * 80)
        lme_prices = price_data.get("lme_prices", {})
        
        lme_names = {"tin": "锡", "lead": "铅", "zinc": "锌", "gold": "黄金", "silver": "白银"}
        
        for key, name in lme_names.items():
            data = lme_prices.get(key)
            if data and data is not None:
                price = data.get("price", "N/A")
                unit = data.get("unit", "")
                change = data.get("change", "")
                print(f"  {name:<18} | {str(price):>12} {unit:<10} | {change}")
        
        # 价差对比
        print("\n【SMM vs LME 价差】")
        print("-" * 80)
        for key in ["tin", "lead", "zinc"]:
            smm = smm_prices.get(key, {})
            lme = lme_prices.get(key, {})
            if smm and lme:
                smm_p = smm.get("price_avg") or smm.get("price")
                lme_p = lme.get("price")
                
                if smm_p and lme_p:
                    try:
                        diff = float(smm_p) - float(lme_p)
                        pct = (diff / float(lme_p)) * 100
                        print(f"  {lme_names[key]:<6} | SMM: {float(smm_p):>10,.0f} | LME: {float(lme_p):>10,.0f} | 价差: {diff:>+8,.0f} ({pct:>+5.2f}%)")
                    except:
                        pass
        
        # 汇率
        print("\n【汇率】")
        print("-" * 80)
        rates = price_data.get("exchange_rates", {})
        if rates:
            print(f"  USD/CNY: {rates.get('usd_cny', 'N/A')}")
            print(f"  USD/NGN: {rates.get('usd_ngn', 'N/A')}")
            print(f"  CNY/NGN: {rates.get('cny_ngn', 'N/A')}")
        
        # 数据问题
        issues = price_data.get("data_issues", {})
        if issues:
            unavailable = issues.get("unavailable", [])
            if unavailable:
                print(f"\n⚠️ 未获取的数据: {', '.join(unavailable)}")
            if issues.get("reasons"):
                print(f"   原因: {issues.get('reasons')}")
        
        print("=" * 80)
    
    def run(self):
        """执行完整流程"""
        price_data = self.fetch_prices()
        
        if "error" not in price_data:
            self.save_prices(price_data)
            self.print_prices(price_data)
        else:
            print(f"❌ 抓取出错: {price_data.get('error')}")
        
        return price_data


if __name__ == "__main__":
    scraper = PriceScraper()
    scraper.run()
