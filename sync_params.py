"""读当期活动页, 打印可直接抄进 snap_up_server.py CONFIG 的参数.

活动页 __NEXT_DATA__ 里已经写明会场 id、场次(business.id)、商品 act_id、
regionMap、defaultGoodsParam, 不必再 F12 抓包。只读, 不下单、不改文件。

用法:
    python sync_params.py              # 列出今天/明天所有场次
    python sync_params.py --sku 4核4G3M  # 只看指定 SKU 关键字
"""

import json
import re
import sys

import requests

ACT_URL = "https://cloud.tencent.com/act/pro/double11-202611?page=featured-202607"
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"
)


def load_activity(url=ACT_URL):
    resp = requests.get(url, headers={"User-Agent": UA}, timeout=20)
    resp.raise_for_status()
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', resp.text, re.S)
    if not m:
        raise RuntimeError("页面里找不到 __NEXT_DATA__, 活动页结构可能变了")
    return json.loads(m.group(1))["props"]["pageProps"]["activityData"]


def region_list(goods):
    """regionMap -> 按页面顺序的 region_id 列表."""
    out = []
    for area_items in (goods.get("regionMap") or {}).get("data", {}).values():
        for item in area_items:
            if item["value"] not in out:
                out.append(item["value"])
    return out


def print_session(activity_id, session, keyword):
    sid = session["id"]
    head = f"{session['start_date']} {session['start_time']} 场 (business.id={sid}, {session['dynamic_status_cn']})"
    hits = [
        g
        for g in session.get("sales") or []
        if not keyword or keyword in g.get("goods_name", "")
    ]
    if not hits:
        return
    print(f"\n=== {head}")
    for g in hits:
        params = g.get("defaultGoodsParam") or {}
        print(f"  商品: {g['goods_name']}")
        print(f"    ACTIVITY_ID  = {activity_id}")
        print(f"    CHECK/BUY_ID = {g['act_id']}")
        print(f"    BUSINESS     = {{\"id\": {sid}, \"from\": \"lightningDeals\"}}")
        print(f"    SKU          = {params.get('type')}")
        print(f"    REGION       = {region_list(g)}")


def main():
    keyword = ""
    if "--sku" in sys.argv:
        idx = sys.argv.index("--sku")
        if idx + 1 < len(sys.argv):
            keyword = sys.argv[idx + 1]
    activity = load_activity()
    activity_id = activity["activityId"]
    flash = activity.get("twoDaySeckillState", {}).get("flashResult", {})
    print(f"会场 activityId = {activity_id}")
    print(f"活动周期: {activity['activityDetail']}")
    for day in sorted(flash):
        for session in flash[day]:
            print_session(activity_id, session, keyword)
    print("\n把上面数字抄进 snap_up_server.py 的 CONFIG, 再改 SECKILL_TIME_STR 就完事。")


if __name__ == "__main__":
    main()
