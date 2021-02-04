# Jci-Hitachi Library

[![Python package](https://github.com/qqaatw/LibJciHitachi/workflows/Python%20package/badge.svg)](https://github.com/qqaatw/LibJciHitachi/actions)

## Supported devices

*支援日立雲端模組的以下機種與功能*

- Hitachi Air Conditioner 日立冷氣
  - Power 電源
  - Mode 運轉模式
  - Air speed 風速
  - Target temperature 目標溫度
  - Indoor temperature 室內溫度
  - Sleep timer 睡眠計時器
- ~~Hitachi Dehumidifier 日立除濕機~~ (Under development)
- ~~Hitachi HeatExchanger 日立全熱交換機~~ (Under development)

## Usage

See [example](example.py).

## Todo

*Priority order*

1. Sending job commands to the API. (connection.py/CreateJob)
2. Homeassistant support.
3. Dehumidifier & heat exchanger support.

## License

Apache License 2.0