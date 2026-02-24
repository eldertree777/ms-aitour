"""
AI Search Tools - Azure AI Search를 이용한 티켓 관리
사양 티켓 기반으로 생성된 개발 티켓과 GitHub 이슈의 존재 여부를 벡터 검색으로 조회합니다.

저장 데이터:
- 사양 티켓 링크 (spec_ticket_link)
- 사양 티켓 내용 (spec_ticket_content)
- 개발 티켓 링크 (dev_ticket_link)
- 깃허브 이슈 링크 (github_issue_link)

참고: https://github.com/ChangJu-Ahn/azure_aisearch_workshop/tree/main/03-vector_search
"""

import os
import time
import logging
import hashlib
from typing import Annotated

from pydantic import Field
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchField,
    SearchFieldDataType,
    SearchableField,
    SimpleField,
    SearchIndex,
    VectorSearch,
    VectorSearchProfile,
    HnswAlgorithmConfiguration,
    ExhaustiveKnnAlgorithmConfiguration,
)
from azure.search.documents.models import VectorizedQuery
from openai import AzureOpenAI

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 유사도 임계치 (이 값 이상이면 기존 티켓이 존재한다고 판단)
SIMILARITY_THRESHOLD = 0.85
INDEX_NAME = "sdd-tickets-index"
VECTOR_DIMENSIONS = 1536  # text-embedding-3-small / text-embedding-ada-002 기준


def _preprocess_text(text: str) -> str:
    """
    임베딩을 위한 최소 전처리.
    과도한 전처리는 의미 손실을 유발하므로 최소한의 정리만 수행.
    """
    if not text or not isinstance(text, str):
        return "내용 없음"
    # 기본 공백 정리 및 과도한 줄바꿈 축소
    text = text.strip()
    while "\n\n\n" in text:
        text = text.replace("\n\n\n", "\n\n")
    return text


class AISearchTools:
    def __init__(self):
        """
        __init__은 직렬화 가능한 config 문자열만 저장합니다.
        httpx 기반 클라이언트(AzureOpenAI, SearchClient 등)는 RLock을 포함하여
        pickle 불가능하므로, 각 메서드 호출 시 팩토리 메서드로 생성합니다.
        """
        # Azure AI Search 설정 (SEARCH_ENDPOINT / SEARCH_ADMIN_KEY 우선, 없으면 AZURE_* 폴백)
        self._search_endpoint = os.getenv("SEARCH_ENDPOINT") or os.getenv("AZURE_SEARCH_ENDPOINT")
        self._search_admin_key = os.getenv("SEARCH_ADMIN_KEY") or os.getenv("AZURE_SEARCH_ADMIN_KEY")

        # Azure OpenAI 설정 (임베딩용)
        self._openai_endpoint = os.getenv("FOUNDRY_PROJECT_ENDPOINT")
        self._openai_api_key = os.getenv("FOUNDRY_PROJECT_KEY")
        self._embedding_deployment = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")
        self._openai_api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01")

        # 인덱스 초기화 여부 플래그 (bool은 pickle 가능)
        self._index_checked = False

        logger.info("AISearchTools 초기화 완료 (클라이언트는 lazy 생성)")

    # ------------------------------------------------------------------ #
    # 팩토리 메서드 - 매 호출마다 새 클라이언트 생성 (pickle 이슈 방지)  #
    # ------------------------------------------------------------------ #

    def _make_openai_client(self) -> AzureOpenAI:
        return AzureOpenAI(
            api_key=self._openai_api_key,
            azure_endpoint=self._openai_endpoint,
            api_version=self._openai_api_version,
        )

    def _make_search_credential(self) -> AzureKeyCredential:
        return AzureKeyCredential(self._search_admin_key)

    def _make_index_client(self) -> SearchIndexClient:
        return SearchIndexClient(
            endpoint=self._search_endpoint,
            credential=self._make_search_credential(),
        )

    def _make_search_client(self) -> SearchClient:
        return SearchClient(
            endpoint=self._search_endpoint,
            index_name=INDEX_NAME,
            credential=self._make_search_credential(),
        )

    def _ensure_index_exists(self):
        """인덱스가 없으면 생성합니다. 이미 확인한 경우 건너뜁니다."""
        if self._index_checked:
            return
        try:
            index_client = self._make_index_client()
            existing_indexes = [idx.name for idx in index_client.list_indexes()]
            if INDEX_NAME not in existing_indexes:
                logger.info(f"인덱스 '{INDEX_NAME}' 생성 중...")
                self._create_index(index_client)
                logger.info(f"인덱스 '{INDEX_NAME}' 생성 완료")
            else:
                logger.info(f"인덱스 '{INDEX_NAME}' 이미 존재함")
            self._index_checked = True
        except Exception as e:
            logger.error(f"인덱스 확인/생성 실패: {str(e)}", exc_info=True)
            raise

    def _create_index(self, index_client: SearchIndexClient | None = None):
        """
        SDD 티켓 저장용 Azure AI Search 인덱스를 생성합니다.

        알고리즘:
        - HNSW: 빠른 근사 검색 (기본 검색에 사용)
        - ExhaustiveKNN: 정확한 전수 검색 (정확도 우선 시 사용)
        """
        fields = [
            SimpleField(
                name="id",
                type=SearchFieldDataType.String,
                key=True,
                filterable=True
            ),
            SimpleField(
                name="spec_ticket_link",
                type=SearchFieldDataType.String,
                filterable=True
            ),
            SearchableField(
                name="spec_ticket_content",
                type=SearchFieldDataType.String,
            ),
            SearchField(
                name="spec_ticket_vector",
                type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                searchable=True,
                retrievable=True,  # 검색 결과에서 벡터 값 확인 가능 (디버깅용)
                vector_search_dimensions=VECTOR_DIMENSIONS,
                vector_search_profile_name="hnsw-profile"
            ),
            SimpleField(
                name="dev_ticket_link",
                type=SearchFieldDataType.String,
                filterable=True
            ),
            SimpleField(
                name="github_issue_link",
                type=SearchFieldDataType.String,
                filterable=True
            ),
        ]

        vector_search = VectorSearch(
            algorithms=[
                # HNSW: 빠른 근사 검색 (m, efConstruction, efSearch 최적화)
                HnswAlgorithmConfiguration(
                    name="hnsw-config",
                    parameters={
                        "m": 4,               # 노드당 연결 수 (4~10 권장, 낮을수록 빠름)
                        "efConstruction": 400, # 인덱스 빌드 품질 (높을수록 정확, 느림)
                        "efSearch": 500,       # 검색 시 탐색 범위 (높을수록 정확, 느림)
                        "metric": "cosine"     # 유사도 측정 방식
                    }
                ),
                # ExhaustiveKNN: 정확한 전수 검색 (소규모 데이터 또는 정확도 우선 시)
                ExhaustiveKnnAlgorithmConfiguration(
                    name="knn-config",
                    parameters={
                        "metric": "cosine"
                    }
                ),
            ],
            profiles=[
                VectorSearchProfile(
                    name="hnsw-profile",
                    algorithm_configuration_name="hnsw-config"
                ),
                VectorSearchProfile(
                    name="knn-profile",
                    algorithm_configuration_name="knn-config"
                ),
            ]
        )

        index = SearchIndex(
            name=INDEX_NAME,
            fields=fields,
            vector_search=vector_search
        )
        client = index_client or self._make_index_client()
        client.create_or_update_index(index)

    def _get_embedding(self, text: str, max_retries: int = 3) -> list[float]:
        """
        텍스트를 벡터로 변환합니다.
        실패 시 지수 백오프(exponential backoff)로 최대 max_retries회 재시도합니다.
        """
        processed = _preprocess_text(text)

        for attempt in range(max_retries):
            try:
                response = self._make_openai_client().embeddings.create(
                    input=processed,
                    model=self._embedding_deployment
                )
                return response.data[0].embedding
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2
                    logger.warning(f"임베딩 생성 실패 ({attempt + 1}/{max_retries}), {wait_time}초 후 재시도... 오류: {e}")
                    time.sleep(wait_time)
                else:
                    logger.error(f"임베딩 생성 최종 실패: {str(e)}", exc_info=True)
                    raise

    def search_similar_tickets(self,
        spec_ticket_content: Annotated[str, Field(description="사양 티켓의 내용 (description). 이 내용으로 유사한 기존 개발 티켓을 검색합니다.")]
    ) -> str:
        """
        사양 티켓 내용 기반으로 기존에 생성된 개발 티켓 및 GitHub 이슈를 벡터 검색으로 조회합니다.
        HNSW 알고리즘으로 빠른 근사 검색을 수행하며,
        유사도 임계치(0.85) 이상인 결과가 있으면 해당 정보를 반환합니다.
        없으면 새로 생성해야 함을 알립니다.
        """
        logger.info("유사 티켓 검색 시작")
        logger.debug(f"검색 내용: {spec_ticket_content[:100]}...")

        try:
            self._ensure_index_exists()
            vector = self._get_embedding(spec_ticket_content)

            # HNSW 프로필을 사용한 벡터 검색
            vector_query = VectorizedQuery(
                vector=vector,
                k_nearest_neighbors=5,
                fields="spec_ticket_vector"
            )

            results = self._make_search_client().search(
                search_text=None,  # 순수 벡터 검색
                vector_queries=[vector_query],
                select=["id", "spec_ticket_link", "spec_ticket_content", "dev_ticket_link", "github_issue_link"],
                top=5,
                include_total_count=True
            )

            matched = []
            for result in results:
                score = result.get("@search.score", 0)
                if score >= SIMILARITY_THRESHOLD:
                    matched.append({
                        "score": score,
                        "spec_ticket_link": result.get("spec_ticket_link"),
                        "spec_ticket_content": result.get("spec_ticket_content"),
                        "dev_ticket_link": result.get("dev_ticket_link"),
                        "github_issue_link": result.get("github_issue_link"),
                    })

            if matched:
                logger.info(f"유사 티켓 {len(matched)}개 발견 (임계치: {SIMILARITY_THRESHOLD})")
                result_lines = [f"✅ 유사한 기존 티켓 {len(matched)}개를 찾았습니다:"]
                for i, item in enumerate(matched, 1):
                    result_lines.append(f"\n[{i}] 유사도 점수: {item['score']:.4f}")
                    result_lines.append(f"    사양 티켓: {item['spec_ticket_link']}")
                    result_lines.append(f"    개발 티켓: {item['dev_ticket_link']}")
                    result_lines.append(f"    GitHub 이슈: {item['github_issue_link']}")
                return "\n".join(result_lines)
            else:
                logger.info("유사 티켓 없음 → 새로 생성 필요")
                return "❌ 유사한 기존 티켓이 없습니다. 새로운 개발 티켓과 GitHub 이슈를 생성해주세요."

        except Exception as e:
            logger.error(f"유사 티켓 검색 실패: {str(e)}", exc_info=True)
            return f"Error searching similar tickets: {str(e)}"

    def save_ticket_mapping(self,
        spec_ticket_link: Annotated[str, Field(description="사양 티켓의 JIRA 링크 (예: https://xxx.atlassian.net/browse/KAN-4)")],
        spec_ticket_content: Annotated[str, Field(description="사양 티켓의 내용 (description)")],
        dev_ticket_link: Annotated[str, Field(description="생성된 개발 티켓의 JIRA 링크")],
        github_issue_link: Annotated[str, Field(description="생성된 GitHub 이슈 링크 (예: https://github.com/owner/repo/issues/1)")]
    ) -> str:
        """
        새로 생성한 개발 티켓과 GitHub 이슈 정보를 Azure AI Search에 저장합니다.
        merge_or_upload_documents를 사용하여 동일 문서 중복 저장을 방지합니다.
        이후 동일/유사한 사양 티켓이 입력될 때 중복 생성을 방지합니다.
        """
        logger.info(f"티켓 매핑 저장: {spec_ticket_link}")
        try:
            self._ensure_index_exists()
            vector = self._get_embedding(spec_ticket_content)

            # spec_ticket_link 기반으로 고유 ID 생성 (동일 링크는 항상 동일 ID)
            doc_id = hashlib.md5(spec_ticket_link.encode()).hexdigest()

            document = {
                "id": doc_id,
                "spec_ticket_link": spec_ticket_link,
                "spec_ticket_content": spec_ticket_content,
                "spec_ticket_vector": vector,
                "dev_ticket_link": dev_ticket_link,
                "github_issue_link": github_issue_link,
            }

            # merge_or_upload: 기존 문서가 있으면 업데이트, 없으면 새로 생성
            result = self._make_search_client().merge_or_upload_documents(documents=[document])
            for r in result:
                if r.succeeded:
                    logger.info(f"티켓 매핑 저장 성공: {r.key}")
                else:
                    logger.error(f"티켓 매핑 저장 실패: {r.error_message}")
                    return f"Error saving ticket mapping: {r.error_message}"

            return (
                f"✅ 티켓 매핑이 성공적으로 저장되었습니다.\n"
                f"  사양 티켓: {spec_ticket_link}\n"
                f"  개발 티켓: {dev_ticket_link}\n"
                f"  GitHub 이슈: {github_issue_link}"
            )

        except Exception as e:
            logger.error(f"티켓 매핑 저장 실패: {str(e)}", exc_info=True)
            return f"Error saving ticket mapping: {str(e)}"
