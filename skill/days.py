#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
远程拉取 days.pinpe.top 倒数日条目 CLI 脚本
无需修改后端源码，非交互式，常量直接配置
"""

import requests
import base64
import json
import datetime
import sys
import argparse
from requests.exceptions import RequestException
import os
_PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def _load_env():
    env_path = os.path.join(_PROJECT_DIR, 'env.json')
    with open(env_path, encoding='UTF-8') as f:
        return json.load(f)

# ====================== 常量配置（直接写死，无需修改）======================
BASE_URL = "https://days.pinpe.top"  # 部署域名
PASSWORD = _load_env()['days_password']            # 后端登录密码（原始密码，无需加密）
# ==========================================================================

def calculate_days(target_date: str) -> int:
    """和后端完全一致的天数计算逻辑"""
    target = datetime.datetime.strptime(target_date, '%Y-%m-%d').date()
    today = datetime.date.today()
    return (target - today).days

def _login():
    """创建会话并登录，返回 session 对象，失败返回 None"""
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (CLI) Python/Requests"
    })
    try:
        login_url = f"{BASE_URL}/get_login"
        login_data = {"password": PASSWORD}
        login_resp = session.post(login_url, data=login_data, allow_redirects=False)
        if login_resp.status_code != 302:
            return None
        return session
    except RequestException:
        return None

def add_days(icon: str, name: str, date: str) -> bool:
    """添加倒数日条目
    
    Args:
        icon: 表情符号
        name: 名称
        date: 日期（格式 YYYY-MM-DD）
    
    Returns:
        成功返回 True，失败返回 False
    """
    session = _login()
    if not session:
        print("❌ 登录失败：密码错误或服务器异常")
        return False
    
    try:
        add_url = f"{BASE_URL}/add"
        add_data = {
            "icon": icon,
            "name": name,
            "date": date
        }
        resp = session.post(add_url, data=add_data, timeout=10)
        if resp.status_code == 200:
            return True
        else:
            return False
    except RequestException:
        return False

def remove_days(name: str) -> bool:
    """删除倒数日条目
    
    Args:
        name: 要删除的条目名称
    
    Returns:
        成功返回 True，失败返回 False
    """
    session = _login()
    if not session:
        print("❌ 登录失败：密码错误或服务器异常")
        return False
    
    try:
        remove_url = f"{BASE_URL}/remove"
        remove_data = {"remove-target": name}
        resp = session.post(remove_url, data=remove_data, timeout=10)
        if resp.status_code == 200:
            return True
        else:
            return False
    except RequestException:
        return False

def fetch_days_data():
    """核心逻辑：登录 -> 下载数据库 -> 解析数据"""
    # 创建会话（保持登录Cookie）
    session = _login()
    if not session:
        print("❌ 登录失败：密码错误或服务器异常")
        return

    try:
        # 2. 调用导出接口下载数据库文件（/export）
        export_url = f"{BASE_URL}/export"
        export_resp = session.get(export_url, timeout=10)
        export_resp.raise_for_status()

        # 3. 解析数据库（和后端一致：Base64解码 -> JSON加载）
        db_content = export_resp.content
        raw_data = json.loads(base64.b64decode(db_content).decode("utf-8"))
        items = raw_data.get("content", [])

        if not items:
            print("ℹ️ 暂无倒数日条目")
            return

        # 4. 按后端相同规则排序
        sorted_items = []
        for item in items:
            days = calculate_days(item["date"])
            sorted_items.append((
                item["icon"],
                item["name"],
                days
            ))

        # 排序规则：未来日期在前（天数升序），过去日期在后（天数降序）
        sorted_items.sort(key=lambda x: (0, x[2]) if x[2] >= 0 else (1, -x[2]))

        # 5. 格式化输出
        print("=" * 50)
        print("📅 远程倒数日条目列表")
        print("=" * 50)
        for idx, (icon, name, days) in enumerate(sorted_items, 1):
            if days > 0:
                status = f"还有 {days} 天"
            elif days == 0:
                status = "今天"
            else:
                status = f"已过 {-days} 天"
            print(f"{idx}. {icon}  {name} | {status}")
        print("=" * 50)

    except RequestException as e:
        print(f"❌ 网络请求失败：{str(e)}")
    except base64.binascii.Error:
        print("❌ 数据库解析失败：文件格式错误")
    except json.JSONDecodeError:
        print("❌ JSON解析失败：数据库损坏")
    except Exception as e:
        print(f"❌ 未知错误：{str(e)}")

def show_help():
    """显示帮助信息"""
    print("=" * 50)
    print("📅 days.py - 倒数日管理工具")
    print("=" * 50)
    print("用法: days.py [选项]")
    print()
    print("选项:")
    print("  无参数              显示倒数日列表")
    print("  -a <名称>           添加倒数日")
    print("  -i <icon>           指定图标 (emoji，如 🎂)")
    print("  -d <日期>           指定日期 (格式 YYYY-MM-DD，如 2026-05-01)")
    print("  -r <名称>           删除倒数日")
    print("  -h, --help          显示帮助信息")
    print()
    print("示例:")
    print("  days.py                              # 查看列表")
    print("  days.py -a 生日 -i 🎂 -d 2026-05-01  # 添加倒数日")
    print("=" * 50)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="倒数日管理工具", add_help=False)
    parser.add_argument("-a", "--add", dest="add_name", metavar="名称", help="添加倒数日")
    parser.add_argument("-i", "--icon", dest="icon", metavar="图标", help="图标 (emoji)")
    parser.add_argument("-d", "--date", dest="date", metavar="日期", help="日期 (格式 YYYY-MM-DD)")
    parser.add_argument("-r", "--remove", dest="remove_name", metavar="名称", help="删除倒数日")
    parser.add_argument("-h", "--help", action="store_true", help="显示帮助信息")
    args = parser.parse_args()
    
    if args.help:
        show_help()
        sys.exit(0)
    
    if args.add_name:
        # 添加倒数日（参数必须全部提供）
        if not args.icon or not args.date:
            print("❌ 添加倒数日需要指定 -i (图标) 和 -d (日期)")
            print("   示例: days.py -a 生日 -i 🎂 -d 2026-05-01")
            sys.exit(1)
        
        icon = args.icon.strip() if args.icon.strip() else "📅"
        name = args.add_name.strip()
        date = args.date.strip()
        
        print(f"添加倒数日条目: {icon} {name} | {date}")
        
        if add_days(icon, name, date):
            print("✅ 添加成功!")
        else:
            print("❌ 添加失败!")
            sys.exit(1)
        
        # 重新获取数据并显示更新后的列表
        print()
        fetch_days_data()
    
    elif args.remove_name:
        # 删除倒数日
        name = args.remove_name.strip()
        print(f"正在删除: {name}")
        
        if remove_days(name):
            print("✅ 删除成功!")
        else:
            print("❌ 删除失败!")
            sys.exit(1)
        
        # 重新获取数据并显示更新后的列表
        print()
        fetch_days_data()
    
    else:
        # 无参数，显示列表
        fetch_days_data()
