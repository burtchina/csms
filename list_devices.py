#!/usr/bin/env python
# -*- coding: utf-8 -*-

from src.app import create_app
from src.models.device import Device

def main():
    app = create_app()
    
    with app.app_context():
        devices = Device.query.all()
        print(f'找到 {len(devices)} 个设备:')
        for d in devices:
            print(f'ID: {d.id}, 名称: {d.name}, IP: {d.ip_address}, 状态: {d.status}')

if __name__ == '__main__':
    main() 