"""
JIRA API 테스트 - KAN-4 이슈 조회
"""

import asyncio
from tools.jira_tools import JiraAutomationTools
from dotenv import load_dotenv
import os


def test_jira_tools():
    """JiraAutomationTools를 사용한 JIRA 이슈 조회 테스트"""
    
    load_dotenv(override=True)
    
    try:
        # 1. JiraAutomationTools 초기화
        print("🔧 JiraAutomationTools 초기화...")
        tools = JiraAutomationTools()
        print("✅ 초기화 완료\n")
        
        # 2. 환경 변수 확인
        print("📋 환경 변수 확인:")
        print(f"  - JIRA_SERVER_URL: {os.getenv('JIRA_SERVER_URL')}")
        print(f"  - JIRA_USER_EMAIL: {os.getenv('JIRA_USER_EMAIL')}")
        print(f"  - JIRA_API_TOKEN: {'설정됨' if os.getenv('JIRA_API_TOKEN') else '미설정'}")
        print(f"  - JIRA_PROJECT_KEY: {os.getenv('JIRA_PROJECT_KEY')}")
        print()
        
        # 3. 이슈 타입 조회 테스트
        print("🔍 프로젝트 이슈 타입 조회 중...")
        try:
            types_result = tools.get_issue_types()
            print(f"✅ {types_result}\n")
        except Exception as e:
            print(f"⚠️  이슈 타입 조회 실패: {e}\n")
        
        # 4. KAN-4 이슈 조회 테스트
        print("🔍 KAN-4 이슈 조회 중...")
        print("   URL: https://yonghakwon12.atlassian.net/browse/KAN-4\n")
        try:
            result = tools.get_jira_issue("KAN-4")
            print(f"✅ 조회 성공:")
            print(f"   {result}\n")
        except Exception as e:
            print(f"❌ KAN-4 조회 실패: {e}\n")
        
        # 4. 다른 이슈들도 테스트 (선택사항)
        test_issues = ["KAN-1", "KAN-2", "KAN-3"]
        print("🔍 추가 이슈 조회 테스트:")
        for issue_key in test_issues:
            try:
                result = tools.get_jira_issue(issue_key)
                print(f"   ✅ {issue_key}: {result.split(',')[0]}")
            except Exception as e:
                print(f"   ⚠️  {issue_key}: {str(e)[:50]}")
        
        print("\n" + "="*60)
        print("✅ 테스트 완료!")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        print("\n💡 해결 방법:")
        print("  1. JIRA_SERVER_URL이 정확한지 확인 (예: https://yonghakwon12.atlassian.net)")
        print("  2. JIRA_USER_EMAIL과 JIRA_API_TOKEN이 설정되어 있는지 확인")
        print("  3. API 토큰이 유효한지 확인 (https://id.atlassian.com/manage-profile/security/api-tokens)")
        print("  4. KAN-4 이슈가 실제로 존재하는지 확인")


if __name__ == "__main__":
    print("🚀 JIRA API 테스트 시작\n")
    print("="*60)
    test_jira_tools()
