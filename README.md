# Jci-Hitachi Library

[![Python package](https://github.com/qqaatw/LibJciHitachi/workflows/Python%20package/badge.svg)](https://github.com/qqaatw/LibJciHitachi/actions)
[![docs](https://readthedocs.org/projects/libjcihitachi/badge/?version=latest)](https://libjcihitachi.readthedocs.io/en/latest/?badge=latest)
[![Python Versions](https://img.shields.io/pypi/pyversions/LibJciHitachi.svg)](https://pypi.python.org/pypi/LibJciHitachi/)
[![Downloads](https://pepy.tech/badge/libjcihitachi)](https://pepy.tech/project/libjcihitachi)

**Help wanted: I've been developing the heat exchanger support, but I've no such device to test its functionality. If you want to help with the development, please contact me via email: `qqaatw[a-t]gmail.com`. Thank you.**

**Help wanted: 我目前正在開發支援全熱交換機，但是沒有裝置可以測試。若您願意協助此功能的開發，請透過email: `qqaatw[a-t]gmail.com` 聯繫我。Thank you.**

## Supported devices

*支援以下使用日立雲端模組(雲端智慧控)的機種與功能*

- Hitachi Air Conditioner 日立冷氣
  - Power 電源
  - Mode 運轉模式
  - Air speed 風速
  - Vertical wind swingable 導風板垂直擺動 (Untested)
  - Vertical wind direction 導風板垂直方向 (Untested)
  - Horizontal wind direction 導風板水平方向 (Untested)
  - Target temperature 目標溫度
  - Indoor temperature 室內溫度
  - Outdoor temperature 室外溫度 (No longer supported after v0.4)
  - Sleep timer 睡眠計時器
  - Mold prevention 機體防霉
  - Energy saving 節電
  - Fast operation 快速運轉
  - Power consumption 用電統計
- Hitachi Dehumidifier 日立除濕機
  - Power 電源
  - Mode 運轉模式
  - Air speed 風速
  - Wind swingable 導風板擺動
  - Side vent 側吹
  - Target humidity 目標濕度
  - Indoor humidity 室內溼度
  - Water full warning 滿水警示
  - Clean filter notify 濾網清潔通知
  - Mold prevention 機體防霉
  - Error code 錯誤代碼
  - PM2.5 value PM2.5數值
  - Sound control 聲音控制
  - Display brightness 顯示器亮度
  - Odor level 異味等級
  - Air cleaning filter setting 空氣清淨濾網設定
  - Power consumption 用電統計
- ~~Hitachi HeatExchanger 日立全熱交換機~~ (Under development)

## Installation

### Python Library

    pip install LibJciHitachi

### Home Assistant Integration

See [JciHitachiHA](https://github.com/qqaatw/JciHitachiHA)

## Documentation

See [docs](https://libjcihitachi.readthedocs.io/en/latest/).

## Todo

1. Heat exchanger support.
2. PM 2.5 panel support.

## Acknowledgement

- @narensankar0529 - Assisting with the dehumidifier support.

## License

Apache License 2.0