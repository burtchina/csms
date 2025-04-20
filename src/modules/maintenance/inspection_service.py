#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
网络设备批量信息巡检服务模块
"""

import time
import json
import logging
import multiprocessing
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

from sqlalchemy.exc import SQLAlchemyError
from src.core.db import db
from src.models.device import Device
from src.models.maintenance import InspectionReport, InspectionItem
from src.core.models import Fault
from src.modules.performance.ssh_monitor import (
    get_connection, 
    get_cpu_usage, 
    get_memory_usage, 
    get_uptime, 
    get_interface_stats,
    close_connection
)
from sqlalchemy import text

# 配置日志
logger = logging.getLogger(__name__)

# 巡检阈值配置
INSPECTION_THRESHOLDS = {
    'cpu_usage': 80.0,  # CPU使用率阈值，高于此值视为异常
    'memory_usage': 80.0,  # 内存使用率阈值，高于此值视为异常
    'port_usage': 80.0,  # 端口使用率阈值，高于此值视为异常
    'system_load': 0.7,  # 系统负载阈值，高于此值视为异常
}

# 基线配置
FIRMWARE_BASELINE = {
    '路由器': ['V800R021C10', 'V800R021C00'],  # 路由器固件基线版本列表
    '交换机': ['V200R010C00', 'V200R010C10'],  # 交换机固件基线版本列表
    '防火墙': ['V500R005C00', 'V500R005C10'],  # 防火墙固件基线版本列表
}

def get_batch_collect_dev_infos() -> List[Dict]:
    """
    获取需要批量巡检的设备信息列表
    
    Returns:
        设备信息列表
    """
    try:
        # 查询所有网络设备（路由器、交换机、防火墙）
        network_device_types = ['路由器', '交换机', '防火墙']
        devices = Device.query.join(Device.type).filter(
            Device.type.has(name=text("'" + "' OR name = '".join(network_device_types) + "'"))
        ).all()
        
        if not devices:
            logger.warning("没有找到需要巡检的网络设备")
            return []
        
        device_infos = []
        for device in devices:
            # 确保设备有连接信息
            if not device.ip_address or not device.username or not device.password:
                logger.warning(f"设备 {device.name} (ID: {device.id}) 缺少连接信息，将跳过巡检")
                continue
                
            device_infos.append({
                'id': device.id,
                'name': device.name,
                'ip_address': device.ip_address,
                'username': device.username,
                'password': device.password,
                'port': device.port or 22,
                'type': device.type.name if device.type else "未知",
                'model': device.model or "未知",
                'firmware_version': device.firmware_version or "未知"
            })
        
        return device_infos
    
    except Exception as e:
        logger.error(f"获取设备信息失败: {str(e)}")
        return []

def network_device_info_collect(device_info: Dict) -> Dict:
    """
    收集单个网络设备的信息
    
    Args:
        device_info: 设备信息字典
        
    Returns:
        巡检结果字典
    """
    device_id = device_info['id']
    device_name = device_info['name']
    device_type = device_info['type']
    
    logger.info(f"开始巡检设备 {device_name} (ID: {device_id})")
    
    # 初始化结果
    result = {
        'device_id': device_id,
        'device_name': device_name,
        'device_type': device_type,
        'status': '失败',
        'cpu_usage': None,
        'memory_usage': None,
        'uptime': None,
        'firmware_version': device_info.get('firmware_version', '未知'),
        'port_usage': None,
        'system_load': None,
        'error_message': None,
        'inspection_results': {},
        'has_fault': False
    }
    
    try:
        # 尝试连接设备
        conn = get_connection(
            device_id, 
            device_info['ip_address'], 
            device_info['username'], 
            device_info['password'], 
            device_info.get('port', 22)
        )
        
        if not conn:
            logger.error(f"无法连接到设备 {device_name} (ID: {device_id})")
            result['error_message'] = "无法连接到设备"
            return result
        
        # 获取CPU使用率
        cpu_usage = get_cpu_usage(device_id, conn)
        result['cpu_usage'] = cpu_usage
        
        # 获取内存使用率
        memory_usage = get_memory_usage(device_id, conn)
        result['memory_usage'] = memory_usage
        
        # 获取运行时间
        uptime = get_uptime(device_id, conn)
        result['uptime'] = uptime
        
        # 获取接口状态
        interface_stats = get_interface_stats(device_id, conn)
        result['port_usage'] = json.dumps(interface_stats, ensure_ascii=False)
        
        # 获取系统负载（这里简化为随机值，实际应该从设备获取）
        system_load = min(1.0, cpu_usage / 100.0 * 0.8 + memory_usage / 100.0 * 0.2)
        result['system_load'] = system_load
        
        # 关闭连接
        close_connection(device_id)
        
        # 标记巡检成功
        result['status'] = '正常'
        
        # 判断设备状态是否异常
        inspection_results = analyze_device_status(result, device_info)
        result['inspection_results'] = json.dumps(inspection_results, ensure_ascii=False)
        
        # 如果有异常项，状态设为"异常"
        if inspection_results.get('abnormal_items', []):
            result['status'] = '异常'
            result['has_fault'] = True
        
        logger.info(f"完成设备 {device_name} (ID: {device_id}) 的巡检")
        
    except Exception as e:
        logger.error(f"巡检设备 {device_name} (ID: {device_id}) 出错: {str(e)}")
        result['error_message'] = str(e)
    
    return result

def analyze_device_status(device_result: Dict, device_info: Dict) -> Dict:
    """
    分析设备状态，判断是否异常
    
    Args:
        device_result: 设备巡检结果
        device_info: 设备信息
        
    Returns:
        分析结果字典
    """
    abnormal_items = []
    normal_items = []
    
    # 检查CPU使用率
    if device_result['cpu_usage'] is not None:
        if device_result['cpu_usage'] > INSPECTION_THRESHOLDS['cpu_usage']:
            abnormal_items.append({
                'item': 'CPU使用率',
                'value': f"{device_result['cpu_usage']}%",
                'threshold': f"{INSPECTION_THRESHOLDS['cpu_usage']}%",
                'message': f"CPU使用率过高: {device_result['cpu_usage']}%"
            })
        else:
            normal_items.append({
                'item': 'CPU使用率',
                'value': f"{device_result['cpu_usage']}%",
                'threshold': f"{INSPECTION_THRESHOLDS['cpu_usage']}%",
                'message': '正常'
            })
    
    # 检查内存使用率
    if device_result['memory_usage'] is not None:
        if device_result['memory_usage'] > INSPECTION_THRESHOLDS['memory_usage']:
            abnormal_items.append({
                'item': '内存使用率',
                'value': f"{device_result['memory_usage']}%",
                'threshold': f"{INSPECTION_THRESHOLDS['memory_usage']}%",
                'message': f"内存使用率过高: {device_result['memory_usage']}%"
            })
        else:
            normal_items.append({
                'item': '内存使用率',
                'value': f"{device_result['memory_usage']}%",
                'threshold': f"{INSPECTION_THRESHOLDS['memory_usage']}%",
                'message': '正常'
            })
    
    # 检查系统负载
    if device_result['system_load'] is not None:
        if device_result['system_load'] > INSPECTION_THRESHOLDS['system_load']:
            abnormal_items.append({
                'item': '系统负载',
                'value': f"{device_result['system_load']:.2f}",
                'threshold': f"{INSPECTION_THRESHOLDS['system_load']}",
                'message': f"系统负载过高: {device_result['system_load']:.2f}"
            })
        else:
            normal_items.append({
                'item': '系统负载',
                'value': f"{device_result['system_load']:.2f}",
                'threshold': f"{INSPECTION_THRESHOLDS['system_load']}",
                'message': '正常'
            })
    
    # 检查固件版本是否符合基线
    device_type = device_info['type']
    if device_type in FIRMWARE_BASELINE and device_result['firmware_version'] != '未知':
        if device_result['firmware_version'] not in FIRMWARE_BASELINE[device_type]:
            abnormal_items.append({
                'item': '固件版本',
                'value': device_result['firmware_version'],
                'threshold': f"基线版本: {', '.join(FIRMWARE_BASELINE[device_type])}",
                'message': f"固件版本不符合基线要求: {device_result['firmware_version']}"
            })
        else:
            normal_items.append({
                'item': '固件版本',
                'value': device_result['firmware_version'],
                'threshold': f"基线版本: {', '.join(FIRMWARE_BASELINE[device_type])}",
                'message': '符合基线要求'
            })
    
    # 检查端口使用情况
    if device_result['port_usage']:
        try:
            port_data = json.loads(device_result['port_usage'])
            for port_name, port_info in port_data.items():
                if 'input_rate' in port_info and 'output_rate' in port_info:
                    max_rate = max(port_info['input_rate'], port_info['output_rate'])
                    max_bps = max_rate / 1000000.0  # 转换为Mbps
                    
                    # 简单起见，假设链路是1Gbps，计算使用率
                    port_usage_percent = (max_bps / 1000.0) * 100
                    
                    if port_usage_percent > INSPECTION_THRESHOLDS['port_usage']:
                        abnormal_items.append({
                            'item': f'端口 {port_name} 使用率',
                            'value': f"{port_usage_percent:.2f}%",
                            'threshold': f"{INSPECTION_THRESHOLDS['port_usage']}%",
                            'message': f"端口 {port_name} 使用率过高: {port_usage_percent:.2f}%"
                        })
                    else:
                        normal_items.append({
                            'item': f'端口 {port_name} 使用率',
                            'value': f"{port_usage_percent:.2f}%",
                            'threshold': f"{INSPECTION_THRESHOLDS['port_usage']}%",
                            'message': '正常'
                        })
        except Exception as e:
            logger.error(f"解析端口使用情况失败: {str(e)}")
    
    return {
        'device_id': device_result['device_id'],
        'device_name': device_result['device_name'],
        'abnormal_items': abnormal_items,
        'normal_items': normal_items,
        'total_items': len(abnormal_items) + len(normal_items),
        'abnormal_count': len(abnormal_items)
    }

def save_inspection_results(report_id: int, results: List[Dict]) -> None:
    """
    保存巡检结果到数据库
    
    Args:
        report_id: 巡检报告ID
        results: 巡检结果列表
    """
    try:
        for result in results:
            # 创建巡检项
            inspection_item = InspectionItem(
                report_id=report_id,
                device_id=result['device_id'],
                status=result['status'],
                cpu_usage=result['cpu_usage'],
                memory_usage=result['memory_usage'],
                uptime=result['uptime'],
                firmware_version=result['firmware_version'],
                port_usage=result['port_usage'],
                system_load=result['system_load'],
                error_message=result['error_message'],
                inspection_results=result['inspection_results']
            )
            db.session.add(inspection_item)
            
            # 如果有故障，创建故障记录
            if result['has_fault'] and result['status'] == '异常':
                # 解析巡检结果以获取异常项
                try:
                    inspection_results = json.loads(result['inspection_results'])
                    abnormal_items = inspection_results.get('abnormal_items', [])
                    
                    if abnormal_items:
                        # 构造故障描述
                        description = f"设备巡检发现异常：\n"
                        for item in abnormal_items:
                            description += f"- {item['item']}: {item['message']}\n"
                        
                        # 确定故障严重程度
                        severity = "medium"  # 默认中等严重度
                        if len(abnormal_items) > 2:
                            severity = "high"  # 异常项超过2个，设为高严重度
                        
                        # 创建故障记录
                        fault = Fault(
                            device_id=result['device_id'],
                            fault_type="巡检异常",
                            severity=severity,
                            description=description,
                            status="open"
                        )
                        db.session.add(fault)
                except Exception as e:
                    logger.error(f"创建故障记录失败: {str(e)}")
        
        db.session.commit()
        logger.info(f"成功保存巡检结果到数据库，报告ID: {report_id}")
    
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"数据库错误: {str(e)}")
    
    except Exception as e:
        logger.error(f"保存巡检结果失败: {str(e)}")

def update_inspection_report(report_id: int, results: List[Dict]) -> None:
    """
    更新巡检报告统计信息
    
    Args:
        report_id: 巡检报告ID
        results: 巡检结果列表
    """
    try:
        report = InspectionReport.query.get(report_id)
        if not report:
            logger.error(f"找不到巡检报告: {report_id}")
            return
        
        # 统计各类设备数量
        total_devices = len(results)
        successful_devices = sum(1 for r in results if r['status'] == '正常')
        failed_devices = sum(1 for r in results if r['status'] == '失败')
        abnormal_devices = sum(1 for r in results if r['status'] == '异常')
        
        # 更新报告统计数据
        report.total_devices = total_devices
        report.successful_devices = successful_devices
        report.failed_devices = failed_devices
        report.abnormal_devices = abnormal_devices
        report.end_time = datetime.now()
        
        # 生成报告摘要
        abnormal_device_details = []
        for result in results:
            if result['status'] == '异常' and result['inspection_results']:
                try:
                    inspection_results = json.loads(result['inspection_results'])
                    abnormal_device_details.append({
                        'device_name': result['device_name'],
                        'abnormal_count': inspection_results.get('abnormal_count', 0)
                    })
                except:
                    pass
        
        # 构建报告摘要
        summary = f"巡检报告：共巡检{total_devices}台设备，"
        summary += f"正常{successful_devices}台，"
        summary += f"异常{abnormal_devices}台，"
        summary += f"无法连接{failed_devices}台。\n\n"
        
        if abnormal_device_details:
            summary += "异常设备列表：\n"
            for detail in abnormal_device_details:
                summary += f"- {detail['device_name']}: 发现{detail['abnormal_count']}个异常项\n"
        
        report.summary = summary
        
        db.session.commit()
        logger.info(f"成功更新巡检报告 ID: {report_id}")
    
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"数据库错误: {str(e)}")
    
    except Exception as e:
        logger.error(f"更新巡检报告失败: {str(e)}")

def batch_info_collect(max_workers: int = 5, operator: str = "系统") -> Optional[int]:
    """
    批量信息巡检主函数，创建进程池并发巡检所有网络设备
    
    Args:
        max_workers: 最大并发进程数
        operator: 操作人员
        
    Returns:
        巡检报告ID，如果失败则返回None
    """
    logger.info("开始网络设备批量信息巡检")
    
    try:
        # 1. 获取需要巡检的设备列表
        device_infos = get_batch_collect_dev_infos()
        
        if not device_infos:
            logger.warning("没有找到需要巡检的网络设备")
            return None
        
        # 2. 创建巡检报告
        report = InspectionReport(
            title=f"网络设备批量巡检报告 {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            start_time=datetime.now(),
            end_time=datetime.now(),  # 临时，后面会更新
            total_devices=len(device_infos),
            operator=operator
        )
        db.session.add(report)
        db.session.commit()
        report_id = report.id
        
        # 3. 创建进程池，并发执行巡检
        logger.info(f"创建进程池，最大并发数: {max_workers}")
        
        with multiprocessing.Pool(processes=max_workers) as pool:
            # 提交所有设备的巡检任务
            inspection_results = pool.map(network_device_info_collect, device_infos)
        
        # 4. 保存巡检结果
        save_inspection_results(report_id, inspection_results)
        
        # 5. 更新巡检报告信息
        update_inspection_report(report_id, inspection_results)
        
        logger.info(f"完成网络设备批量信息巡检，报告ID: {report_id}")
        return report_id
    
    except Exception as e:
        logger.error(f"执行批量巡检失败: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None 