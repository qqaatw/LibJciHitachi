# Jci-Hitachi Library

[![System Status](https://github.com/qqaatw/LibJciHitachi/actions/workflows/Status.yml/badge.svg)](https://github.com/qqaatw/LibJciHitachi/actions/workflows/Status.yml)
[![CI](https://github.com/qqaatw/LibJciHitachi/actions/workflows/CI.yml/badge.svg)](https://github.com/qqaatw/LibJciHitachi/actions/workflows/CI.yml)
[![codecov](https://codecov.io/gh/qqaatw/LibJciHitachi/branch/master/graph/badge.svg?token=W147MOH1T0)](https://codecov.io/gh/qqaatw/LibJciHitachi)
[![docs](https://readthedocs.org/projects/libjcihitachi/badge/?version=latest)](https://libjcihitachi.readthedocs.io/en/latest/?badge=latest)
[![PyPI](https://img.shields.io/pypi/v/LibJciHitachi.svg?color=%23007ec6)](https://pypi.python.org/pypi/LibJciHitachi/)
[![Python Versions](https://img.shields.io/pypi/pyversions/LibJciHitachi.svg)](https://pypi.python.org/pypi/LibJciHitachi/)
[![Downloads](https://static.pepy.tech/badge/libjcihitachi)](https://pepy.tech/project/libjcihitachi)

## Feature

A Python library for controlling Jci-Hitachi devices.

## Supported devices

*支援以下使用日立雲端模組(雲端智慧控)的機種與功能*

- Hitachi Air Conditioner 日立冷氣
  - Power 電源
  - Mode 運轉模式
  - Air speed 風速
  - Vertical wind swingable 導風板垂直擺動
  - Vertical wind direction 導風板垂直方向
  - Horizontal wind direction 導風板水平方向
  - Target temperature 目標溫度
  - Indoor temperature 室內溫度
  - Sleep timer 睡眠計時器
  - Freeze clean 凍結洗淨
  - Mold prevention 機體防霉
  - Energy saving 節電
  - Fast operation 快速運轉
  - Power consumption 用電統計
  - Monthly power consumption 月用電統計
  - Panel 顯示器亮度
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
  - Monthly power consumption 月用電統計
- Hitachi Heat Exchanger 日立全熱交換機
  - Power 電源
  - Mode 運轉模式
  - Breath mode 換氣模式
  - Air speed 風速
  - Indoor temperature 室內溫度
  - Error code 錯誤代碼
  - Air cleaning filter notification 空氣清淨濾網清潔通知
  - Front filter notification 前置濾網清潔通知
  - PM25 filter notification PM25濾網清潔通知

## Installation

### Python Library

    pip install LibJciHitachi

### Home Assistant Integration

See [JciHitachiHA](https://github.com/qqaatw/JciHitachiHA).

## Documentation

See [docs](https://libjcihitachi.readthedocs.io/en/latest/).

## Todo

1. PM 2.5 panel support.

## Acknowledgement

- @narensankar0529 - Assisting with the dehumidifier support.

## License

Apache License 2.0
