#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Atlassian Token Validator
校验 Atlassian Cloud 账户的 API Token 是否有效
特别用于检测账户被禁用后 Token 是否仍能使用
"""

import argparse
import requests
import sys
from typing import Dict, Tuple, Optional


class AtlassianValidator:
    """Atlassian API Token 校验器"""

    # 各产品的校验端点
    ENDPOINTS = {
        'jira': '/rest/api/3/myself',
        'confluence': '/wiki/rest/api/user/current',
        'bitbucket': '/2.0/user',  # Bitbucket 使用不同的域名
    }

    def __init__(self, email: str, token: str, domain: str):
        self.email = email
        self.token = token
        self.domain = domain
        self.base_url = f"https://{domain}.atlassian.net"
        self.bitbucket_url = "https://api.bitbucket.org"

    def _make_request(self, url: str) -> Tuple[int, Optional[Dict], Optional[str]]:
        """
        发送请求并返回状态码、响应数据和错误信息
        """
        try:
            response = requests.get(
                url,
                auth=(self.email, self.token),
                headers={'Accept': 'application/json'},
                timeout=10
            )

            if response.status_code == 200:
                return response.status_code, response.json(), None
            else:
                error_msg = self._parse_error(response)
                return response.status_code, None, error_msg

        except requests.exceptions.Timeout:
            return 0, None, "请求超时"
        except requests.exceptions.ConnectionError:
            return 0, None, "连接失败，请检查网络或域名是否正确"
        except requests.exceptions.RequestException as e:
            return 0, None, f"请求异常: {str(e)}"

    def _parse_error(self, response: requests.Response) -> str:
        """解析错误响应"""
        try:
            data = response.json()
            # Atlassian API 错误格式
            if 'message' in data:
                return data['message']
            if 'errorMessages' in data:
                return '; '.join(data['errorMessages'])
            if 'error' in data:
                return data['error']
            return response.text[:200]
        except:
            return response.text[:200] if response.text else f"HTTP {response.status_code}"

    def validate_jira(self) -> Dict:
        """校验 Jira Cloud Token"""
        url = f"{self.base_url}{self.ENDPOINTS['jira']}"
        status_code, data, error = self._make_request(url)

        result = {
            'product': 'Jira Cloud',
            'valid': status_code == 200,
            'status_code': status_code,
        }

        if data:
            result['user_info'] = {
                'displayName': data.get('displayName', 'N/A'),
                'emailAddress': data.get('emailAddress', 'N/A'),
                'accountId': data.get('accountId', 'N/A'),
                'active': data.get('active', 'N/A'),
            }
        if error:
            result['error'] = error

        return result

    def validate_confluence(self) -> Dict:
        """校验 Confluence Cloud Token"""
        url = f"{self.base_url}{self.ENDPOINTS['confluence']}"
        status_code, data, error = self._make_request(url)

        result = {
            'product': 'Confluence Cloud',
            'valid': status_code == 200,
            'status_code': status_code,
        }

        if data:
            result['user_info'] = {
                'displayName': data.get('displayName', 'N/A'),
                'email': data.get('email', 'N/A'),
                'accountId': data.get('accountId', 'N/A'),
                'accountType': data.get('accountType', 'N/A'),
            }
        if error:
            result['error'] = error

        return result

    def validate_bitbucket(self) -> Dict:
        """校验 Bitbucket Cloud Token"""
        url = f"{self.bitbucket_url}{self.ENDPOINTS['bitbucket']}"
        status_code, data, error = self._make_request(url)

        result = {
            'product': 'Bitbucket Cloud',
            'valid': status_code == 200,
            'status_code': status_code,
        }

        if data:
            result['user_info'] = {
                'displayName': data.get('display_name', 'N/A'),
                'username': data.get('username', 'N/A'),
                'accountId': data.get('account_id', 'N/A'),
                'isStaff': data.get('is_staff', 'N/A'),
            }
        if error:
            result['error'] = error

        return result

    def validate_all(self) -> list:
        """校验所有支持的 Atlassian 产品"""
        return [
            self.validate_jira(),
            self.validate_confluence(),
            self.validate_bitbucket(),
        ]


def print_result(result: Dict):
    """格式化打印校验结果"""
    product = result['product']
    valid = result['valid']
    status_code = result['status_code']

    # 状态图标
    icon = "\033[92m[PASS]\033[0m" if valid else "\033[91m[FAIL]\033[0m"

    print(f"\n{icon} {product}")
    print(f"    状态码: {status_code}")

    if valid and 'user_info' in result:
        print("    用户信息:")
        for key, value in result['user_info'].items():
            print(f"      - {key}: {value}")

    if not valid and 'error' in result:
        print(f"    \033[91m错误信息: {result['error']}\033[0m")


def print_summary(results: list):
    """打印汇总信息"""
    total = len(results)
    passed = sum(1 for r in results if r['valid'])
    failed = total - passed

    print("\n" + "=" * 50)
    print("校验结果汇总")
    print("=" * 50)
    print(f"  总计: {total}")
    print(f"  \033[92m通过: {passed}\033[0m")
    print(f"  \033[91m失败: {failed}\033[0m")

    if failed > 0:
        print("\n\033[93m提示: Token 校验失败可能的原因:\033[0m")
        print("  1. API Token 错误或已过期")
        print("  2. Email 地址不正确")
        print("  3. 账户已被禁用 (Deactivated)")
        print("  4. 该产品未开通或无访问权限")
        print("  5. 域名 (domain) 配置错误")


def get_input_interactively() -> Tuple[str, str, str]:
    """交互式获取输入"""
    print("\n=== Atlassian Token Validator ===\n")
    email = input("请输入 Email 地址: ").strip()
    token = input("请输入 API Token: ").strip()
    domain = input("请输入 Atlassian 域名 (例如: your-company): ").strip()
    return email, token, domain


def main():
    parser = argparse.ArgumentParser(
        description='Atlassian Cloud API Token 校验工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python validator.py --email user@example.com --token YOUR_API_TOKEN --domain your-company
  python validator.py  # 交互式输入

支持的产品:
  - Jira Cloud
  - Confluence Cloud
  - Bitbucket Cloud
        """
    )

    parser.add_argument('--email', '-e', help='Atlassian 账户邮箱')
    parser.add_argument('--token', '-t', help='API Token')
    parser.add_argument('--domain', '-d', help='Atlassian 域名 (不含 .atlassian.net)')
    parser.add_argument('--product', '-p',
                        choices=['jira', 'confluence', 'bitbucket', 'all'],
                        default='all',
                        help='指定要校验的产品 (默认: all)')

    args = parser.parse_args()

    # 如果没有提供所有必要参数，则交互式输入
    if not all([args.email, args.token, args.domain]):
        email, token, domain = get_input_interactively()
    else:
        email, token, domain = args.email, args.token, args.domain

    # 验证输入
    if not email or not token or not domain:
        print("\033[91m错误: Email、Token 和 Domain 都是必填项\033[0m")
        sys.exit(1)

    print(f"\n正在校验 Token...")
    print(f"  Email: {email}")
    print(f"  Domain: {domain}.atlassian.net")

    # 创建校验器
    validator = AtlassianValidator(email, token, domain)

    # 根据参数选择校验产品
    if args.product == 'all':
        results = validator.validate_all()
    elif args.product == 'jira':
        results = [validator.validate_jira()]
    elif args.product == 'confluence':
        results = [validator.validate_confluence()]
    elif args.product == 'bitbucket':
        results = [validator.validate_bitbucket()]

    # 打印结果
    for result in results:
        print_result(result)

    # 打印汇总
    print_summary(results)

    # 如果有失败的校验，返回非零退出码
    if any(not r['valid'] for r in results):
        sys.exit(1)


if __name__ == '__main__':
    main()
