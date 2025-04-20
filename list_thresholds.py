#!/usr/bin/env python
# -*- coding: utf-8 -*-

from src.app import create_app
from src.models import Threshold

def main():
    app = create_app()
    
    with app.app_context():
        thresholds = Threshold.query.all()
        print(f'找到 {len(thresholds)} 个阈值设置:')
        for t in thresholds:
            print(f'ID: {t.id}, 设备ID: {t.device_id}, 指标: {t.metric_name}, 警告: {t.warning_threshold}%, 严重: {t.critical_threshold}%')

if __name__ == '__main__':
    main() 