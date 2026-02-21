import asyncio
import datetime
from azure.identity.aio import ClientSecretCredential
from msgraph import GraphServiceClient

# 1. 인증 정보 (실제 환경에서는 .env 사용을 강력 추천합니다)
AZURE_CLIENT_ID=your_client_id_here
AZURE_TENANT_ID=your_tenant_id_here
AZURE_CLIENT_SECRET=your_client_secret_here
AZURE_USER_ID=your_user_object_id_here

### [메서드 1: 인증 및 클라이언트 생성] ###
async def get_authenticated_client():
    # 비동기 환경에 맞는 ClientSecretCredential 사용
    credential = ClientSecretCredential(
        tenant_id=TENANT_ID,
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET
    )
    scopes = ["https://graph.microsoft.com/.default"]
    return GraphServiceClient(credential, scopes)

### [메서드 2: 팀즈 메시지 수집 로직] ###
async def fetch_recent_teams_messages(graph_client: GraphServiceClient):
    lookback_time = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1)
    
    # [변경 전] chats = await graph_client.me.chats.get()
    # [변경 후] 특정 사용자의 채팅 목록을 가져옵니다.
    chats = await graph_client.users.by_user_id(USER_ID).chats.get()
    
    results = []
    if chats and chats.value:
        for chat in chats.value:
            # [변경 전] messages = await graph_client.me.chats.by_chat_id(chat.id).messages.get()
            # [변경 후] 특정 사용자의 특정 채팅방 메시지를 가져옵니다.
            messages = await graph_client.users.by_user_id(USER_ID).chats.by_chat_id(chat.id).messages.get()
            
            if messages and messages.value:
                for msg in messages.value:
                    # 시간대 비교 및 내용 존재 여부 확인
                    if msg.created_date_time > lookback_time and msg.body and msg.body.content:
                        sender = msg.from_.user.display_name if msg.from_ and msg.from_.user else "Unknown"
                        results.append({"from": sender, "content": msg.body.content})
    return results

### [메인 실행부: 결과 출력] ###
async def main():
    try:
        # 1. 인증된 클라이언트 확보
        print("🔐 인증 진행 중...")
        graph_client = await get_authenticated_client()

        # 2. 메시지 수집
        print("📨 최근 24시간 내 Teams 메시지를 가져오는 중...")
        messages = await fetch_recent_teams_messages(graph_client)

        # 3. 결과 출력
        print("\n" + "="*60)
        print(f"📊 수집된 메시지 개수: {len(messages)}개")
        print("="*60)

        if not messages:
            print("최근 24시간 동안 새로운 메시지가 없습니다.")
        else:
            for idx, m in enumerate(messages, 1):
                print(f"[{idx}] {m['time'].strftime('%m/%d %H:%M')} | {m['from']}")
                print(f"    내용: {m['content'][:100].strip()}...") 
                print("-" * 60)

    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    asyncio.run(main())