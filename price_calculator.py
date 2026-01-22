# Kursi Trades - 尼日利亚矿产品采购价格倒推系统
# ================================================
# 从JSON文件读取SMM/LME实时价格，计算各矿种的最高可接受采购价（0利润基准）

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional, List

# ==================== 全局参数 ====================

# 增值税
VAT_RATE = 1.13  # 13%中国进口增值税

# 奈拉汇率修正参数（系统获取的汇率通常偏高，需要向上修正）
# 设置为 None 则使用系统获取的汇率，设置具体数值则覆盖
CNY_NGN_OVERRIDE = 216  # 人民币/奈拉 手动覆盖值，设为 None 使用自动获取

# 海运物流成本（NGN/吨）- 从码头开始，不含内陆运输
LOGISTICS_COST_SEA = 80309  # 出口报关 + 海运 + 中国清关 + 场站拖车

# 物流成本明细（供参考）
LOGISTICS_BREAKDOWN = {
    "export_clearance": 32143,   # 出口报关: 900,000 ÷ 28吨
    "sea_freight": 21243,        # 海运: $400 ÷ 28吨 × 1,487
    "china_clearance": 21235,    # 中国清关: ¥100 × 212.35
    "terminal_trucking": 5688,   # 场站拖车: ¥750 ÷ 28吨 × 212.35
}

# 钽铌矿空运交易成本
COLTAN_AIR_COST = 8  # USD/kg，到广州总成本

# 锂矿折扣系数（尼日利亚市场）
SPODUMENE_DISCOUNT = 0.6  # 锂辉石打六折
LEPIDOLITE_DISCOUNT = 0.3  # 锂云母打三折

# 锂云母提锂参数
LEPIDOLITE_TONS_PER_CARBONATE = 20  # 20吨锂云母 → 1吨碳酸锂
LEPIDOLITE_PROCESSING_COST_CNY = 45000  # 锂云母加工成本 CNY/吨碳酸锂
LEPIDOLITE_BASE_GRADE = 2.5  # 基准品位 Li₂O%


class PriceCalculator:
    """矿产品采购价格倒推计算器"""
    
    def __init__(self, price_data: Dict[str, Any]):
        """
        初始化计算器
        
        Args:
            price_data: 从JSON文件读取的价格数据
        """
        self.price_data = price_data
        self.date = price_data.get("date", datetime.now().strftime("%Y-%m-%d"))
        
        # 提取汇率
        exchange_rates = price_data.get("exchange_rates", {})
        
        # 处理嵌套的汇率格式
        usd_ngn = exchange_rates.get("usd_ngn", {})
        usd_cny = exchange_rates.get("usd_cny", {})
        cny_ngn = exchange_rates.get("cny_ngn", {})
        
        self.USD_NGN = usd_ngn.get("rate", 1487) if isinstance(usd_ngn, dict) else usd_ngn
        self.USD_CNY = usd_cny.get("rate", 7.0) if isinstance(usd_cny, dict) else usd_cny
        
        # 奈拉汇率：优先使用手动覆盖值
        if CNY_NGN_OVERRIDE is not None:
            self.CNY_NGN = CNY_NGN_OVERRIDE
            self.CNY_NGN_SOURCE = "Manual Override"
        else:
            self.CNY_NGN = cny_ngn.get("rate", 212.35) if isinstance(cny_ngn, dict) else cny_ngn
            self.CNY_NGN_SOURCE = "Auto"
        
        # 同步更新 USD/NGN（基于 CNY/NGN 和 USD/CNY）
        self.USD_NGN = self.CNY_NGN * self.USD_CNY
        
        # 提取SMM价格
        self.smm = price_data.get("smm_prices", {})
    
    def _get_price(self, key: str, field: str = "price_avg", fallback_keys: list = None) -> Optional[float]:
        """
        安全获取价格，支持多个可能的字段名
        
        Args:
            key: 主要字段名
            field: 价格字段名（如 price_avg, price）
            fallback_keys: 备用字段名列表
        """
        # 尝试主要字段名
        data = self.smm.get(key, {})
        if isinstance(data, dict):
            price = data.get(field) or data.get("price")
            if price is not None:
                return float(price) if price != 0 else None
        
        # 尝试备用字段名
        if fallback_keys:
            for fallback_key in fallback_keys:
                data = self.smm.get(fallback_key, {})
                if isinstance(data, dict):
                    price = data.get(field) or data.get("price")
                    if price is not None:
                        return float(price) if price != 0 else None
        
        # 如果都没找到，打印调试信息
        print(f"⚠️ 警告: 未找到价格数据 - key: {key}, field: {field}")
        print(f"   可用的 SMM 字段: {list(self.smm.keys())}")
        return None
    
    # ==================== 各矿种计算方法 ====================
    
    def calc_tin_ore(self, grade_percent: float) -> float:
        """
        锡矿采购上限计算
        
        Args:
            grade_percent: 矿石品位 (如70表示70%)
        
        Returns:
            max_price_ngn_per_kg: 最高采购价 NGN/kg
        """
        metal_price_usd = self._get_price("tin")
        if not metal_price_usd:
            return 0
        
        # 中国售价 = 金属价 × 品位
        china_price_usd = metal_price_usd * (grade_percent / 100)
        china_price_ngn = china_price_usd * self.USD_NGN
        
        # 扣除物流成本
        fob_price_ngn = china_price_ngn - LOGISTICS_COST_SEA
        
        # 扣除增值税
        max_price_ngn_per_ton = fob_price_ngn / VAT_RATE
        
        # 换算每公斤
        return max_price_ngn_per_ton / 1000
    
    def calc_coltan(self, grade_percent: float) -> float:
        """
        钽铌矿采购上限计算（千克度法，空运）
        
        Args:
            grade_percent: Ta2O5品位 (如30表示30%)
        
        Returns:
            max_price_ngn_per_kg: 最高采购价 NGN/kg
        """
        ta2o5_price_usd_kg = self._get_price("tantalum_oxide")
        if not ta2o5_price_usd_kg:
            return 0
        
        # 千克度单价 = (氧化物价格 - 交易成本) / 增值税 / 100 × 汇率
        unit_price_per_grade = ((ta2o5_price_usd_kg - COLTAN_AIR_COST) / VAT_RATE / 100) * self.USD_NGN
        
        # 采购上限 = 品位 × 千克度单价
        return grade_percent * unit_price_per_grade
    
    def calc_monazite(self, grade_percent: float) -> float:
        """
        独居石采购上限计算
        
        Args:
            grade_percent: TREO品位 (如50表示50%)
        
        Returns:
            max_price_ngn_per_kg: 最高采购价 NGN/kg
        """
        # 尝试多个可能的字段名
        smm_price_usd_ton = self._get_price(
            "monazite_concentrate", 
            fallback_keys=["monazite", "monazite_concentrate"]
        )
        if not smm_price_usd_ton:
            print(f"❌ Monazite 价格数据缺失，无法计算 {grade_percent}% 品位的价格")
            return 0
        
        BASE_GRADE = 60  # SMM基准品位
        
        # 按品位折算中国售价
        china_price_ngn = smm_price_usd_ton * self.USD_NGN * (grade_percent / BASE_GRADE)
        
        # 扣除物流成本
        fob_price_ngn = china_price_ngn - LOGISTICS_COST_SEA
        
        # 如果扣除物流成本后为负数，说明价格太低，返回0
        if fob_price_ngn <= 0:
            print(f"⚠️ Monazite {grade_percent}%: 扣除物流成本后为负数 ({fob_price_ngn:.2f} NGN/吨)")
            return 0
        
        # 扣除增值税
        max_price_ngn_per_ton = fob_price_ngn / VAT_RATE
        
        # 换算每公斤
        result = max_price_ngn_per_ton / 1000
        print(f"✅ Monazite {grade_percent}%: 源价={smm_price_usd_ton} USD/吨, 结果={result:.2f} NGN/kg")
        return result
    
    def calc_titanium(self) -> float:
        """
        钛铁矿采购上限计算
        
        Returns:
            max_price_ngn_per_ton: 最高采购价 NGN/吨
        """
        smm_price_cny_ton = self._get_price("titanium_concentrate")
        if not smm_price_cny_ton:
            return 0
        
        # 换算奈拉
        china_price_ngn = smm_price_cny_ton * self.CNY_NGN
        
        # 扣除物流成本
        fob_price_ngn = china_price_ngn - LOGISTICS_COST_SEA
        
        # 扣除增值税
        return fob_price_ngn / VAT_RATE
    
    def calc_zircon(self) -> float:
        """
        锆英砂采购上限计算
        
        Returns:
            max_price_ngn_per_ton: 最高采购价 NGN/吨
        """
        smm_price_usd_ton = self._get_price("zircon_sand")
        if not smm_price_usd_ton:
            return 0
        
        # 换算奈拉
        china_price_ngn = smm_price_usd_ton * self.USD_NGN
        
        # 扣除物流成本
        fob_price_ngn = china_price_ngn - LOGISTICS_COST_SEA
        
        # 扣除增值税
        return fob_price_ngn / VAT_RATE
    
    def calc_spodumene(self, grade_percent: float) -> float:
        """
        锂辉石采购上限计算（打六折）
        
        Args:
            grade_percent: Li2O品位 (如5表示5%)
        
        Returns:
            max_price_ngn_per_ton: 最高采购价 NGN/吨
        """
        smm_price_usd_ton = self._get_price("spodumene")
        if not smm_price_usd_ton:
            return 0
        
        BASE_GRADE = 6  # SMM基准品位
        
        # 按品位折算中国售价
        china_price_ngn = smm_price_usd_ton * self.USD_NGN * (grade_percent / BASE_GRADE)
        
        # 扣除物流成本
        fob_price_ngn = china_price_ngn - LOGISTICS_COST_SEA
        
        # 扣除增值税
        max_price_ngn_per_ton = fob_price_ngn / VAT_RATE
        
        # 打六折
        return max_price_ngn_per_ton * SPODUMENE_DISCOUNT
    
    def calc_lepidolite(self, grade_percent: float) -> float:
        """
        锂云母采购上限计算（从碳酸锂动态倒推，打六折）
        
        Args:
            grade_percent: Li2O品位 (如2.5表示2.5%)
        
        Returns:
            max_price_ngn_per_ton: 最高采购价 NGN/吨
        """
        # 从碳酸锂价格倒推锂云母价格
        carbonate_price_usd = self._get_price("lithium_carbonate")
        if not carbonate_price_usd:
            return 0
        
        # 碳酸锂价格转CNY
        carbonate_price_cny = carbonate_price_usd * self.USD_CNY
        
        # 锂云母价格 = (碳酸锂价格 - 加工成本) / 吨矿耗量 × (实际品位/基准品位)
        lepidolite_price_cny = ((carbonate_price_cny - LEPIDOLITE_PROCESSING_COST_CNY) / 
                                LEPIDOLITE_TONS_PER_CARBONATE * 
                                (grade_percent / LEPIDOLITE_BASE_GRADE))
        
        # 换算奈拉
        china_price_ngn = lepidolite_price_cny * self.CNY_NGN
        
        # 扣除物流成本
        fob_price_ngn = china_price_ngn - LOGISTICS_COST_SEA
        
        # 扣除增值税
        max_price_ngn_per_ton = fob_price_ngn / VAT_RATE
        
        # 打三折
        return max_price_ngn_per_ton * LEPIDOLITE_DISCOUNT
    
    def calc_lead_ore(self, grade_percent: float) -> float:
        """
        铅矿采购上限计算
        
        Args:
            grade_percent: Pb品位 (如50表示50%)
        
        Returns:
            max_price_ngn_per_ton: 最高采购价 NGN/吨
        """
        metal_price_usd = self._get_price("lead")
        if not metal_price_usd:
            return 0
        
        # 中国售价 = 金属价 × 品位
        china_price_usd = metal_price_usd * (grade_percent / 100)
        china_price_ngn = china_price_usd * self.USD_NGN
        
        # 扣除物流成本
        fob_price_ngn = china_price_ngn - LOGISTICS_COST_SEA
        
        # 扣除增值税
        return fob_price_ngn / VAT_RATE
    
    def calc_zinc_ore(self, grade_percent: float) -> float:
        """
        锌矿采购上限计算
        
        Args:
            grade_percent: Zn品位 (如50表示50%)
        
        Returns:
            max_price_ngn_per_ton: 最高采购价 NGN/吨
        """
        metal_price_usd = self._get_price("zinc")
        if not metal_price_usd:
            return 0
        
        # 中国售价 = 金属价 × 品位
        china_price_usd = metal_price_usd * (grade_percent / 100)
        china_price_ngn = china_price_usd * self.USD_NGN
        
        # 扣除物流成本
        fob_price_ngn = china_price_ngn - LOGISTICS_COST_SEA
        
        # 扣除增值税
        return fob_price_ngn / VAT_RATE
    
    # ==================== 计算所有价格 ====================
    
    def calculate_all(self) -> Dict[str, Any]:
        """计算所有矿种的采购上限价格"""
        
        result = {
            "date": self.date,
            "calculation_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "exchange_rates": {
                "usd_ngn": self.USD_NGN,
                "usd_cny": self.USD_CNY,
                "cny_ngn": self.CNY_NGN,
                "cny_ngn_source": getattr(self, 'CNY_NGN_SOURCE', 'Auto')
            },
            "parameters": {
                "vat_rate": VAT_RATE,
                "logistics_cost_sea_ngn": LOGISTICS_COST_SEA,
                "coltan_air_cost_usd": COLTAN_AIR_COST,
                "spodumene_discount": SPODUMENE_DISCOUNT,
                "lepidolite_discount": LEPIDOLITE_DISCOUNT
            },
            "source_prices": {},
            "max_purchase_prices": {}
        }
        
        # 记录源价格
        source_prices = {
            "tin": {"price": self._get_price("tin"), "unit": "USD/mt"},
            "tantalum_oxide": {"price": self._get_price("tantalum_oxide"), "unit": "USD/kg"},
            "monazite": {"price": self._get_price("monazite_concentrate"), "unit": "USD/mt"},
            "titanium": {"price": self._get_price("titanium_concentrate"), "unit": "CNY/mt"},
            "zircon": {"price": self._get_price("zircon_sand"), "unit": "USD/mt"},
            "spodumene": {"price": self._get_price("spodumene"), "unit": "USD/mt"},
            "lithium_carbonate": {"price": self._get_price("lithium_carbonate"), "unit": "USD/mt"},
            "lead": {"price": self._get_price("lead"), "unit": "USD/mt"},
            "zinc": {"price": self._get_price("zinc"), "unit": "USD/mt"}
        }
        result["source_prices"] = source_prices
        
        # 计算各矿种采购上限
        max_prices = {}
        
        # 1. 锡矿 (NGN/kg)
        max_prices["tin_ore"] = {
            "unit": "NGN/kg",
            "base_grade": "70%",
            "grades": {
                "60%": round(self.calc_tin_ore(60), 0),
                "65%": round(self.calc_tin_ore(65), 0),
                "70%": round(self.calc_tin_ore(70), 0),
                "75%": round(self.calc_tin_ore(75), 0)
            }
        }
        
        # 2. 钽铌矿 (NGN/kg)
        max_prices["coltan"] = {
            "unit": "NGN/kg",
            "base_grade": "30% Ta₂O₅",
            "note": "Air freight",
            "grades": {
                "20%": round(self.calc_coltan(20), 0),
                "25%": round(self.calc_coltan(25), 0),
                "30%": round(self.calc_coltan(30), 0),
                "35%": round(self.calc_coltan(35), 0)
            }
        }
        
        # 3. 独居石 (NGN/kg)
        max_prices["monazite"] = {
            "unit": "NGN/kg",
            "base_grade": "60% TREO",
            "grades": {
                "30%": round(self.calc_monazite(30), 0),
                "40%": round(self.calc_monazite(40), 0),
                "45%": round(self.calc_monazite(45), 0),
                "50%": round(self.calc_monazite(50), 0),
                "60%": round(self.calc_monazite(60), 0)
            }
        }
        
        # 4. 钛铁矿 (NGN/吨)
        max_prices["titanium"] = {
            "unit": "NGN/ton",
            "base_grade": "≥50% TiO₂",
            "grades": {
                "50%": round(self.calc_titanium(), 0)
            }
        }
        
        # 5. 锆英砂 (NGN/吨)
        max_prices["zircon"] = {
            "unit": "NGN/ton",
            "base_grade": "≥65% Zr(Hf)O₂",
            "grades": {
                "65%": round(self.calc_zircon(), 0)
            }
        }
        
        # 6. 锂辉石 (NGN/吨)
        max_prices["spodumene"] = {
            "unit": "NGN/ton",
            "base_grade": "6% Li₂O",
            "grades": {
                "3%": round(self.calc_spodumene(3), 0),
                "4%": round(self.calc_spodumene(4), 0),
                "5%": round(self.calc_spodumene(5), 0),
                "6%": round(self.calc_spodumene(6), 0)
            }
        }
        
        # 7. 锂云母 (NGN/吨) - 从碳酸锂动态倒推
        max_prices["lepidolite"] = {
            "unit": "NGN/ton",
            "base_grade": "2.5% Li₂O",
            "grades": {
                "2.0%": round(self.calc_lepidolite(2.0), 0),
                "2.5%": round(self.calc_lepidolite(2.5), 0),
                "3.0%": round(self.calc_lepidolite(3.0), 0)
            }
        }
        
        # 8. 铅矿 (NGN/吨)
        max_prices["lead_ore"] = {
            "unit": "NGN/ton",
            "base_grade": "50% Pb",
            "grades": {
                "40%": round(self.calc_lead_ore(40), 0),
                "50%": round(self.calc_lead_ore(50), 0),
                "60%": round(self.calc_lead_ore(60), 0)
            }
        }
        
        # 9. 锌矿 (NGN/吨)
        max_prices["zinc_ore"] = {
            "unit": "NGN/ton",
            "base_grade": "50% Zn",
            "grades": {
                "40%": round(self.calc_zinc_ore(40), 0),
                "50%": round(self.calc_zinc_ore(50), 0),
                "60%": round(self.calc_zinc_ore(60), 0)
            }
        }
        
        result["max_purchase_prices"] = max_prices
        return result
    
    def print_results(self, results: Dict[str, Any]):
        """打印计算结果到控制台"""
        
        print("\n" + "=" * 80)
        print(f"📊 尼日利亚矿产品采购价格倒推 ({results['date']})")
        print("=" * 80)
        
        # 汇率
        rates = results["exchange_rates"]
        cny_ngn_note = f" ({rates.get('cny_ngn_source', 'Auto')})" if rates.get('cny_ngn_source') else ""
        print(f"\n💱 汇率: 1 USD = {rates['usd_ngn']:,.0f} NGN | 1 USD = {rates['usd_cny']:.4f} CNY | 1 CNY = {rates['cny_ngn']:.2f} NGN{cny_ngn_note}")
        
        # 参数
        params = results["parameters"]
        print(f"📦 物流成本: {params['logistics_cost_sea_ngn']:,} NGN/吨 (从码头起)")
        print(f"📦 增值税: {(params['vat_rate']-1)*100:.0f}% | 锂辉石折扣: {params['spodumene_discount']*100:.0f}% | 锂云母折扣: {params['lepidolite_discount']*100:.0f}%")
        
        # 源价格
        print("\n" + "-" * 80)
        print("【SMM 源价格】")
        print("-" * 80)
        for name, data in results["source_prices"].items():
            if data["price"]:
                print(f"  {name:<20} | {data['price']:>12,.2f} {data['unit']}")
        
        # 采购上限价格
        print("\n" + "-" * 80)
        print("【最高采购价格 (0利润基准)】")
        print("-" * 80)
        
        names_cn = {
            "tin_ore": "锡矿",
            "coltan": "钽铌矿",
            "monazite": "独居石",
            "titanium": "钛铁矿",
            "zircon": "锆英砂",
            "spodumene": "锂辉石",
            "lepidolite": "锂云母",
            "lead_ore": "铅矿",
            "zinc_ore": "锌矿"
        }
        
        for key, data in results["max_purchase_prices"].items():
            name_cn = names_cn.get(key, key)
            unit = data["unit"]
            note = f" ({data['note']})" if data.get("note") else ""
            
            print(f"\n  📍 {name_cn} [{unit}]{note}")
            print(f"     基准品位: {data['base_grade']}")
            
            for grade, price in data["grades"].items():
                if price > 0:
                    print(f"     {grade:>6} → {price:>15,} {unit}")
                else:
                    print(f"     {grade:>6} → {'数据缺失':>15}")
        
        print("\n" + "=" * 80)
        print("⚠️  以上为0利润采购上限，实际采购需预留利润空间")
        print("=" * 80)


def load_latest_prices(data_dir: str = "data") -> Optional[Dict[str, Any]]:
    """加载最新的价格数据"""
    
    # 查找最新的价格文件
    today = datetime.now().strftime("%Y-%m-%d")
    price_file = os.path.join(data_dir, f"prices_{today}.json")
    
    if not os.path.exists(price_file):
        # 尝试查找最近的文件
        files = [f for f in os.listdir(data_dir) if f.startswith("prices_") and f.endswith(".json")]
        if files:
            files.sort(reverse=True)
            price_file = os.path.join(data_dir, files[0])
        else:
            print(f"❌ 未找到价格数据文件")
            return None
    
    print(f"📂 读取价格文件: {price_file}")
    
    with open(price_file, "r", encoding="utf-8") as f:
        return json.load(f)


def save_results(results: Dict[str, Any], data_dir: str = "data"):
    """保存计算结果到JSON文件"""
    
    date = results["date"]
    output_file = os.path.join(data_dir, f"max_purchase_prices_{date}.json")
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 结果已保存到: {output_file}")


def main():
    """主函数"""
    
    print("\n" + "=" * 60)
    print("🏭 Kursi Trades 采购价格倒推系统")
    print("=" * 60)
    
    # 加载价格数据
    price_data = load_latest_prices()
    if not price_data:
        return
    
    # 创建计算器
    calculator = PriceCalculator(price_data)
    
    # 计算所有价格
    results = calculator.calculate_all()
    
    # 打印结果
    calculator.print_results(results)
    
    # 保存结果
    save_results(results)
    
    print("\n✅ 计算完成!")


if __name__ == "__main__":
    main()
