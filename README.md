> **版权与归属（Copyright & Attribution）**
>
> 本项目改编自 [@zhouyifan007](https://github.com/zhouyifan007) 的开源项目 [tencentyun-snake-up](https://github.com/zhouyifan007/tencentyun-snake-up)。
> 在原脚本基础上，本人结合 AI 进行了迭代修改并补充了配套教程，属于**二次创作（derivative work）**。
> 原作者保留其原始代码与思路的版权；本仓库仅作个人学习研究用途，使用产生的任何后果由使用者自行承担。

# tencentyun-seckill

腾讯云轻量应用服务器秒杀脚本：扫码登录 → 库存检测 → 并发抢购 → 抢到弹付款。
目标商品：`double11-202611` 会场秒杀轻量 4 核 4G3M（`bundle_budget_mc_lg4_01`）。

> **每场必改的是 `BUSINESS.id`**：它就是活动页里的「场次 id」，一天两场（10:00 / 15:00）各一个，
> 换场不换就必然打不动。用 `python sync_params.py` 一键读当期参数，不用手抄。

```
先跑 get_cookies.py 扫码登录（含人脸确认）
再跑 snap_up_server.py 等开抢（提前 3 分钟启动）
```

## 文件说明

| 文件 | 作用 |
|---|---|
| `get_cookies.py` | Playwright 扫码登录，保存 `cookies.json`，同步活动 URL + 人脸状态到 `config.json` |
| `snap_up_server.py` | 抢购主程序：自检 → 对时等待 → 提前开打 → 并发重试 → 成功弹付款 |
| `sync_params.py` | 只读活动页 `__NEXT_DATA__`，打印当期 `ACTIVITY_ID` / 场次 `business.id` / `act_id` / region，开抢前抄参数用 |

运行产生的文件（**不要上传到公开库**）：`cookies.json`（登录态）、`config.json`（自动同步配置）、`logs/`（运行日志）。

### 返回码（`do-goods`）

| 码 | 含义 | 脚本动作 |
|---|---|---|
| `0` | 下单成功 | 停，弹付款 |
| `1100202` | 要人脸核身 | 停（开抢前预检已提前预警） |
| `1101411` | 有未支付订单占坑 | 停，弹订单页（先付/先撤才能再抢） |
| `408` | 频率过快 | 退避 1.5 秒继续 |
| `1100205` | 系统繁忙 | 继续 |
| `1101001` | 秒杀尚未开始（还没到点） | 继续（提前开枪的正常回音，也是验参成功的信号） |
| `1100136` | 不在抢购时间 | 继续（提前开枪的正常回音） |
| `CSRF-ERROR` / `NOT-LOGINED` | 会话失效 | 停，重新扫码 |

## 使用说明

### 环境

```bash
pip install requests playwright
playwright install chromium
```

### 步骤

1. **扫码登录**：`python get_cookies.py`，浏览器弹出来后扫码，顺手把人脸核身做了（没过会直接跳验证页），看到“浏览器已关闭”就行。
2. **核对当期参数**：`python sync_params.py` 打印当期会场 / 场次 / act_id / region / SKU，抄进 `snap_up_server.py` 顶部 `CONFIG`；重点改 `SECKILL_TIME_STR`、`ACTIVITY_ID`、`CHECK_ACT_ID`、`BUY_ACT_ID`、`BUSINESS.id`（=场次 id）。
3. **提前 3 分钟运行**：`python snap_up_server.py`，看到 `✅ 人脸核身已通过` + `🕒 钟差已校准` 就可以等了，日志在 `logs/` 里。
4. **抢到付款**：脚本自动弹付款页，尽快付（超时订单会被释放）；若提示有未付单，先去订单中心处理。

## 注意事项

1. **每次开抢前重扫码**：cookie 有有效期，且每次登录都会刷新 `skey`（token 是现算的，不用手填）。
2. **人脸提前做**：开打时才报 `1100202` 神仙难救，登录流程里就会卡你一次。
3. **`408` 连片是 IP 级限流**：脚本降速救不了，先切出口 IP 或冷却；单发探测回到 `1100136` 即解封。当天高频 hammer 过的号/IP，第二天都可能还在小黑屋。
4. **`1101411` 是占坑不是没抢到**：说明已有未支付订单（超时没回包也可能建单成功），先付/先撤，否则所有新单全被挡。
5. **敏感文件勿传**：`cookies.json`、`config.json`、`logs/` 含登录态和订单号，本库只收三个 `.py` 与文档。
6. **每期必核对**：`ACTIVITY_ID`、`CHECK_ACT_ID`、`BUY_ACT_ID`、`BUSINESS.id`、开抢时间，会场一换就可能全变。
7. **超时≠失败**：网络超时时服务端可能已建单，看到超时多先去订单中心看一眼，别无脑重抢（会撞 `1101411`）。
8. 仅供个人学习研究，抢到与否看库存和手速，脚本只解决“快”和“不断线”。
