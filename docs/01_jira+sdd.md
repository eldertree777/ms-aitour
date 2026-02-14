# JIRA + SDD를 이용한 자동화


## 시스템 구성도

- jira mcp(local container)
- MS ai search
- jira agent
- teams or outlook(trigger)

## 가드레일

- 토큰 정보
- 사용자 이메일 / 패스워드 정보
- (검토) 요청한 팀 및 직원 이름


## Flow

### v1
![alt text](/img/01.png)

(티켓 생성 할 때는 agent 대신 llm 사용하는 방향 검토)

#### 검토 필요

- 토큰 감소
- copilot PR 생성 시, 제목에 티켓 이름 넣을 수 있는 지 검토 필요(speckit?)
- 팀즈 / 메일 이용할 수 있는 지 검토. 만약 불가능하다면, 사양 티켓을 주기적으로 읽도록 수정 필요(orchestrator 없이)

## 고도화 방향

- MS Foundry tools 이용하여 MCP 배포
  - 현재 무료 계정에서는 배포 한계가 있는 것으로 보임.
- 만약 기존 사양이 자주 변경될 경우, 토큰 비용 문제 있을 수 있음.(v1)
- Merge 되면, 해당 히스토리를 컨플루언스 등에 자동으로 요약하고 기록할 수 있도록