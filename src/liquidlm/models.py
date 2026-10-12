# Generated from the pinned public OpenAPI contract; do not edit.

from __future__ import annotations

from enum import Enum, StrEnum
from typing import Annotated, Any
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, EmailStr, Field, RootModel


class ExpandedScopes(BaseModel):
    api: list[str]
    mcp: list[str]


class BearerClass(StrEnum):
    session = "session"
    pat = "pat"


class AccountSelf(BaseModel):
    id: UUID
    email: EmailStr | None
    bearer_class: Annotated[BearerClass, Field(alias="bearerClass")]
    active_org_id: Annotated[UUID | None, Field(alias="activeOrgId")]
    scope_bundle: Annotated[str | None, Field(alias="scopeBundle")]
    expanded_scopes: Annotated[ExpandedScopes, Field(alias="expandedScopes")]


class ErrorResponse(BaseModel):
    error: str
    message: str | None = None
    code: str | None = None


class ChatSession(BaseModel):
    id: UUID
    title: str | None
    created_at: AwareDatetime
    updated_at: AwareDatetime
    scope_vault_ids: list[UUID] | None


class CreateChatSessionBody(BaseModel):
    title: str | None = None


class ChatCompletionBody(BaseModel):
    message: Annotated[str, Field(min_length=1)]
    vault_ids: Annotated[
        list[str] | None,
        Field(
            description="Omit/null for all visible vaults, [] for model-only baseline, or pass one or more readable vault IDs."
        ),
    ] = None
    has_attachments: bool | None = None
    attachment_knowledge_ids: Annotated[
        list[UUID] | None,
        Field(
            description="Knowledge IDs for already-uploaded attachments. Every ID must be readable in vault_ids; the server fetches them before the model answers.",
            max_length=12,
        ),
    ] = None


class Role(StrEnum):
    user = "user"
    assistant = "assistant"
    system = "system"
    tool = "tool"


class ChatMessage(BaseModel):
    id: UUID
    session_id: UUID
    role: Role
    content: str | None
    tool_calls: Any | None = None
    created_at: AwareDatetime
    feedback_rating: int | None = None


class CustomEntityAlias(BaseModel):
    id: UUID
    vault_id: UUID | None
    org_id: UUID
    name: str
    aliases: list[str]
    entity_type: str
    canonical_id: str
    created_at: AwareDatetime


class CreateEntityAliasBody(BaseModel):
    vault_id: str | None = None
    name: str | None = None
    aliases: list[str] | None = None
    entity_type: str | None = None
    canonical_id: str | None = None


class CustomEntityType(BaseModel):
    id: UUID
    vault_id: UUID | None
    org_id: UUID
    name: str
    description: str | None
    created_at: AwareDatetime


class CreateEntityTypeBody(BaseModel):
    vault_id: str | None = None
    name: str | None = None
    description: str | None = None


class Type(StrEnum):
    file = "file"
    link = "link"
    note = "note"
    image = "image"
    tag = "tag"
    entity = "entity"


class Validity(StrEnum):
    pending = "pending"
    valid = "valid"
    temporal = "temporal"
    expired = "expired"


class GraphNode(BaseModel):
    id: str
    type: Type
    label: str
    subtype: str | None = None
    validity: Annotated[
        Validity | None,
        Field(
            description="Temporal state of a knowledge node: whether it is live, not yet in effect, time-bounded, or expired. Absent on tag and entity nodes."
        ),
    ] = None
    temporal_kind: str | None = None
    vault_id: Annotated[
        str | None,
        Field(
            description="Vault the knowledge node belongs to, so it can be opened in the vault browser."
        ),
    ] = None
    superseded_by: Annotated[
        str | None, Field(description="Id of the knowledge node that supersedes this one.")
    ] = None
    metadata: dict[str, Any] | None = None


class GraphEdge(BaseModel):
    source: str
    target: str
    label: str


class GraphResult(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    truncated: bool | None = None


class Version(Enum):
    number_1 = 1


class Status(StrEnum):
    disabled = "disabled"


class DiarizationStatus1(BaseModel):
    version: Version
    status: Status


class Status1(StrEnum):
    failed = "failed"


class ErrorCode(StrEnum):
    initialization_failed = "initialization_failed"
    inference_failed = "inference_failed"
    timeout = "timeout"
    child_failed = "child_failed"


class DiarizationStatus2(BaseModel):
    version: Version
    status: Status1
    error_code: ErrorCode


class Status2(StrEnum):
    completed = "completed"


class DiarizationStatus3(BaseModel):
    version: Version
    status: Status2
    speaker_count: Annotated[int, Field(ge=0)]
    model: str
    revision: str


class DiarizationStatus(RootModel[DiarizationStatus1 | DiarizationStatus2 | DiarizationStatus3]):
    root: DiarizationStatus1 | DiarizationStatus2 | DiarizationStatus3


class Segment(BaseModel):
    chunk_index: int
    text: str
    media_start_sec: Annotated[
        float | None,
        Field(
            description="Start offset in seconds for transcribed audio/video; null when unavailable."
        ),
    ]
    media_end_sec: float | None
    speakers: Annotated[
        list[str] | None,
        Field(
            description="All assigned speaker IDs in this chunk, scoped to this recording. Not person names."
        ),
    ] = None


class TranscriptChunks(BaseModel):
    count: int
    extracted_text: str
    diarization: DiarizationStatus | None = None
    segments: list[Segment]


class Type1(StrEnum):
    file = "file"
    image = "image"
    link = "link"
    note = "note"


class KnowledgeRecord(BaseModel):
    id: UUID
    user_id: UUID
    org_id: UUID
    vault_id: UUID
    type: Type1
    title: str | None
    summary: str | None
    tags: list[str]
    parent_knowledge_id: UUID | None
    indexing_status: str
    indexing_error: str | None
    indexing_attempts: int
    source_url: str | None
    body: str | None
    metadata: dict[str, Any]
    chunks: TranscriptChunks | None = None
    created_at: AwareDatetime
    updated_at: AwareDatetime
    indexed_at: str | None
    temporal_kind: str | None = None
    content_date: str | None = None
    valid_from: str | None = None
    valid_until: str | None = None


class ListItemsResult(BaseModel):
    items: list[KnowledgeRecord]
    total: int
    has_more: Annotated[bool, Field(alias="hasMore")]


class CreateItemBody(BaseModel):
    id: Annotated[
        UUID | None,
        Field(
            description="Client-generated UUID for idempotent note creation retries. Accepted only when `type` is `note`."
        ),
    ] = None
    type: Annotated[str | None, Field(description="`link`, `note`, or `image`.")] = None
    vault_id: Annotated[str | None, Field(description="Defaults to the caller's default vault.")] = (
        None
    )
    title: str | None = None
    url: Annotated[str | None, Field(description="Required for `link` items.")] = None
    content: str | None = None
    tags: list[str] | None = None
    metadata: dict[str, Any] | None = None
    s3_key: str | None = None
    content_date: Annotated[
        str | None,
        Field(
            description="Semantic date the content is about (ISO 8601). When set, the row is marked temporally overridden so indexing won't re-derive it."
        ),
    ] = None


class UpdateItemBody(BaseModel):
    title: str | None = None
    body: str | None = None
    content: Annotated[str | None, Field(description="Legacy alias for `body` (note text).")] = None
    source_url: str | None = None
    tags: list[str] | None = None
    metadata: dict[str, Any] | None = None
    temporal_kind: str | None = None
    temporal_decay_half_life_days: float | None = None
    content_date: str | None = None
    valid_from: str | None = None
    valid_until: str | None = None


class Frame(BaseModel):
    knowledge_id: str
    parent_knowledge_id: str
    frame_number: float
    timestamp_sec: float
    title: str | None
    summary: str | None
    indexing_status: str
    thumbnail_url: str | None = None


class VideoFramesResult(BaseModel):
    parent_knowledge_id: str
    video_title: str | None
    frames: list[Frame]
    next_cursor: str | None


class DocumentPage(BaseModel):
    knowledge_id: str
    parent_knowledge_id: str
    document_title: str
    pdf_page_number: int
    page_label: str | None
    summary: str | None
    indexing_status: str
    transcription_status: str
    thumbnail_url: str | None = None


class Numbering(StrEnum):
    pdf = "pdf"


class Totals(BaseModel):
    expected: int | None
    available: int
    ready: int
    failed: int
    indexing: int
    pending: int


class DocumentPagesResult(BaseModel):
    parent_knowledge_id: str
    document_title: str
    generation: str
    numbering: Numbering
    text_indexing_status: str
    totals: Totals
    pages: list[DocumentPage]
    next_cursor: str | None


class Engine(StrEnum):
    vision_ocr = "vision-ocr"


class ReextractKnowledgeBody(BaseModel):
    engine: Engine


class KnowledgeLink(BaseModel):
    id: UUID | None = None
    src_knowledge_id: UUID
    dst_knowledge_id: UUID
    link_type: str
    metadata: dict[str, Any] | None = None
    created_at: AwareDatetime | None = None


class TargetType(StrEnum):
    file = "file"
    item = "item"


class RelateKnowledgeBody(BaseModel):
    target_id: str
    target_type: TargetType
    label: str | None = None


class RelatedFileReference(BaseModel):
    id: UUID
    s3_key: str | None
    relative_key: str | None = None
    file_name: str
    mime_type: str
    vault_id: UUID


class Direction(StrEnum):
    incoming = "incoming"
    outgoing = "outgoing"


class RelatedEntity(BaseModel):
    link: KnowledgeLink
    direction: Direction
    item: KnowledgeRecord | None = None
    file: RelatedFileReference | None = None


class SupersedesKnowledgeBody(BaseModel):
    predecessor_id: str


class DayItem(KnowledgeRecord):
    matched_content_date: bool
    matched_created_at: bool


class DayItemsResult(BaseModel):
    items: list[DayItem]
    truncated: Annotated[
        bool,
        Field(
            description="The window held more rows than the limit. Rendering a range with days silently missing from it is worse than saying so."
        ),
    ]


class Reason(StrEnum):
    generating = "generating"
    unavailable = "unavailable"


class DayDigestResult(BaseModel):
    summary: str | None
    item_count: Annotated[int, Field(ge=0)]
    note_count: Annotated[int, Field(ge=0)]
    connector_run_count: Annotated[
        int,
        Field(
            description="Connector syncs that ran against the scoped vaults that day — the answer to why a day holds hundreds of items.",
            ge=0,
        ),
    ]
    pending: bool
    reason: Annotated[
        Reason | None,
        Field(
            description="Why there is no summary. `generating` is worth waiting for; `unavailable` means no generator is configured here and waiting will not help."
        ),
    ] = None


class Row(BaseModel):
    content_date: str | None
    created_at: str
    type: str
    updated_at: Annotated[
        str,
        Field(description="Last touch. The calendar takes the newest per day to mark stale days."),
    ]


class DayMarkersResult(BaseModel):
    rows: list[Row]


class Entity(BaseModel):
    name: str
    entity_type: str
    canonical_id: str | None
    mention_count: int
    knowledge_count: int
    sample_knowledge_ids: list[str]


class EntitiesResult(BaseModel):
    entities: list[Entity]


class ForgetEntityBody(BaseModel):
    name: Annotated[str, Field(min_length=1)]
    entity_type: Annotated[str | None, Field(min_length=1)] = None
    canonical_id: Annotated[str | None, Field(min_length=1)] = None


class Item(BaseModel):
    knowledge_id: str
    title: str | None
    type: str
    vault_id: str
    created_at: str
    mention_count: int


class EntityKnowledgeResult(BaseModel):
    items: list[Item]


class Direction1(StrEnum):
    outgoing = "outgoing"
    incoming = "incoming"


class Relation(BaseModel):
    direction: Direction1
    predicate: str
    name: str
    entity_type: str
    canonical_id: str | None
    count: int


class EntityRelationsResult(BaseModel):
    relations: list[Relation]


class ActorType(StrEnum):
    user = "user"
    agent = "agent"
    connector = "connector"


class LastModifiedBy(BaseModel):
    actor_type: Annotated[ActorType, Field(alias="actorType")]
    user_id: Annotated[str | None, Field(alias="userId")]
    user_display_name: Annotated[str | None, Field(alias="userDisplayName")]
    token_id: Annotated[str | None, Field(alias="tokenId")]
    token_name: Annotated[str | None, Field(alias="tokenName")]


class IndexingStatus(StrEnum):
    pending = "pending"
    indexing = "indexing"
    ready = "ready"
    failed = "failed"


class Item1(BaseModel):
    id: UUID
    s3_key: str
    relative_key: str
    file_name: str
    mime_type: str
    size_bytes: float | None
    tags: list[str]
    summary: str | None = None
    indexing_status: IndexingStatus
    indexed_at: str | None
    last_modified_at: Annotated[str | None, Field(alias="lastModifiedAt")]
    last_modified_by: Annotated[LastModifiedBy | None, Field(alias="lastModifiedBy")]


class IndexedFilesResult(BaseModel):
    items: list[Item1]
    next_cursor: str | None


class SearchFileRecord(BaseModel):
    id: UUID
    s3_key: str
    file_name: str | None = None
    mime_type: str | None = None
    size_bytes: float | None = None
    vault_id: UUID | None = None
    knowledge_id: UUID | None = None
    title: str | None = None
    summary: str | None = None
    indexing_status: str | None = None


class Chunk(BaseModel):
    content: str
    chunk_index: int
    metadata: dict[str, Any] | None = None


class SearchResult(BaseModel):
    knowledge_id: UUID
    chunk_id: str
    type: Type1
    title: str | None
    vault_id: UUID
    chunk: Chunk
    score: float
    file_path: Annotated[
        str | None, Field(description="Storage path, for attribution in the result row.")
    ] = None
    source_url: Annotated[str | None, Field(description="Original URL for link-type results.")] = (
        None
    )
    mime_type: Annotated[
        str | None,
        Field(
            description="MIME type of the underlying file, where there is one. Distinguishes audio and video results, which both carry type 'file'."
        ),
    ] = None
    updated_at: str | None = None
    document_match_score: float | None = None
    temporal_kind: str | None = None
    temporal_decay_half_life_days: float | None = None
    content_date: str | None = None
    valid_from: str | None = None
    valid_until: str | None = None
    validity_state: str | None = None


class DateRange(BaseModel):
    from_: Annotated[str | None, Field(alias="from")] = None
    to: str | None = None


class Entities(BaseModel):
    canonical_ids: list[str] | None = None
    names: list[str] | None = None


class SearchFilters(BaseModel):
    tags: list[str] | None = None
    mime_type: list[str] | None = None
    types: Annotated[
        list[Type1] | None,
        Field(
            description="Restrict to these knowledge types. Distinct from mime_type: notes and links have no file row, so a MIME filter cannot match them."
        ),
    ] = None
    date_range: DateRange | None = None
    vault_ids: Annotated[
        list[UUID] | None,
        Field(
            description="Restrict to these vaults. Omit for every readable vault; an empty set matches nothing rather than widening."
        ),
    ] = None
    vault_id: Annotated[
        str | None, Field(description="Degenerate single-vault form of `vault_ids`.")
    ] = None
    parent_knowledge_id: str | None = None
    folder_id: UUID | None = None
    indexing_status: str | None = None
    entities: Entities | None = None


class SearchBody(BaseModel):
    query: Annotated[str, Field(min_length=1)]
    limit: Annotated[int | None, Field(gt=0)] = None
    filters: SearchFilters | None = None
    rerank: bool | None = None
    include_expired: bool | None = None
    include_pending: bool | None = None


class EmptyReason(StrEnum):
    no_visible_vaults = "no_visible_vaults"
    no_indexed_knowledge = "no_indexed_knowledge"
    no_matches = "no_matches"


class SearchKnowledgeResult(BaseModel):
    results: list[SearchResult]
    advice: str | None = None
    empty_reason: EmptyReason | None = None


class IndexingStatusResult(BaseModel):
    pending: int
    failed: int
    indexed: int


class YourRole(StrEnum):
    owner = "owner"
    writer = "writer"
    reader = "reader"


class Mode(StrEnum):
    all_public = "all_public"
    allowlist = "allowlist"


class LinkDomainPolicy(BaseModel):
    mode: Mode
    allow_domains: Annotated[list[str], Field(alias="allowDomains", max_length=200)]
    deny_domains: Annotated[list[str], Field(alias="denyDomains", max_length=200)]
    include_subdomains: Annotated[bool, Field(alias="includeSubdomains")]


class Vault(BaseModel):
    id: UUID
    user_id: UUID
    org_id: UUID
    is_default: bool
    label: str
    s3_prefix: str
    created_at: AwareDatetime
    file_count: int | None = None
    knowledge_count: int | None = None
    your_role: Annotated[
        YourRole | None,
        Field(
            description="The calling user's role in this vault. Present so a vault row can show what you can do with it, including for people who cannot manage shares."
        ),
    ] = None
    last_activity_at: Annotated[
        str | None,
        Field(
            description="When anything in the vault last changed, derived from the newest knowledge row. Null for an empty vault."
        ),
    ] = None
    chat_system_prompt: str | None = None
    chunk_size: int | None = None
    index_pdf_pages: bool | None = None
    link_extraction_enabled: bool | None = None
    persist_linked_images: bool | None = None
    persist_linked_audio: bool | None = None
    persist_linked_video: bool | None = None
    link_domain_policy: LinkDomainPolicy | None = None
    fpm: int | None = None
    temporal_weight: float | None = None


class CreateVaultBody(BaseModel):
    label: str | None = None


class LinkDomainPolicy1(BaseModel):
    mode: Mode
    allow_domains: Annotated[list[str], Field(alias="allowDomains", max_length=200)]
    deny_domains: Annotated[list[str], Field(alias="denyDomains", max_length=200)]
    include_subdomains: Annotated[bool, Field(alias="includeSubdomains")]


class UpdateVaultBody(BaseModel):
    label: str | None = None
    chat_system_prompt: str | None = None
    chunk_size: Annotated[float | None, Field(alias="chunkSize")] = None
    index_pdf_pages: Annotated[bool | None, Field(alias="indexPdfPages")] = None
    link_extraction_enabled: Annotated[bool | None, Field(alias="linkExtractionEnabled")] = None
    persist_linked_images: Annotated[bool | None, Field(alias="persistLinkedImages")] = None
    persist_linked_audio: Annotated[bool | None, Field(alias="persistLinkedAudio")] = None
    persist_linked_video: Annotated[bool | None, Field(alias="persistLinkedVideo")] = None
    link_domain_policy: Annotated[LinkDomainPolicy1 | None, Field(alias="linkDomainPolicy")] = None
    fpm: float | None = None
    temporal_weight: Annotated[float | None, Field(alias="temporalWeight")] = None


class ExtractedImage(BaseModel):
    title: str
    url: str
    tags: list[str]
    summary: str | None
    page: int | None


class FileMetaResult(BaseModel):
    file: dict[str, Any]
    last_modified_by: Annotated[Any | None, Field(alias="lastModifiedBy")] = None
    last_modified_at: Annotated[AwareDatetime | None, Field(alias="lastModifiedAt")]
    chunks: TranscriptChunks
    extracted_images: list[ExtractedImage]


class FileUrlResult(BaseModel):
    url: str
    expires_at: Annotated[AwareDatetime, Field(alias="expiresAt")]


class FileVersion(BaseModel):
    version_id: Annotated[str, Field(alias="versionId")]
    last_modified: Annotated[AwareDatetime, Field(alias="lastModified")]
    size: float
    is_latest: Annotated[bool, Field(alias="isLatest")]
    actor_user_id: Annotated[UUID | None, Field(alias="actorUserId")]
    source_relative_key: Annotated[str | None, Field(alias="sourceRelativeKey")]
    moved_at: Annotated[AwareDatetime | None, Field(alias="movedAt")]


class Ok(Enum):
    boolean_true = True


class ForgetResult(BaseModel):
    ok: Ok
    forgotten_at: AwareDatetime
    forgotten_batch_id: str
    restorable_until: AwareDatetime


class MoveFilesBody(BaseModel):
    keys: list[str] | None = None
    to: str | None = None


class MoveFilesToVaultBody(BaseModel):
    keys: list[str] | None = None
    to_vault_id: str | None = None


class RestoreFileBody(BaseModel):
    key: str | None = None
    version_id: Annotated[str | None, Field(alias="versionId")] = None
    source_key: Annotated[str | None, Field(alias="sourceKey")] = None


class FolderBody(BaseModel):
    path: str | None = None


class MoveFolderBody(BaseModel):
    from_: Annotated[str | None, Field(alias="from")] = None
    to: str | None = None


class ForgetKnowledgeBody(BaseModel):
    reason: str | None = None


class PinResult(BaseModel):
    ok: Ok
    knowledge_id: str
    pinned_at: AwareDatetime | None


class RestoreResult(BaseModel):
    ok: Ok
    restored: int


class ForgetBulkBody(BaseModel):
    knowledge_ids: list[str] | None = None
    reason: str | None = None


class Role1(StrEnum):
    reader = "reader"
    writer = "writer"


class VaultMember(BaseModel):
    user_id: UUID
    email: EmailStr | None
    role: Role1


class AddVaultMemberBody(BaseModel):
    user_id: str | None = None
    role: str | None = None


class ReindexVaultBody(BaseModel):
    file: str | None = None
    failed: bool | None = None


class ShareVaultBody(BaseModel):
    email: str | None = None
    role: str | None = None


class TrashItem(BaseModel):
    id: UUID
    type: str
    title: str | None
    summary: str | None
    forgotten_at: AwareDatetime
    forgotten_by: UUID | None
    forgotten_via: str | None
    forgotten_reason: str | None
    forgotten_batch_id: str | None
    vault_id: UUID
    org_id: UUID
    restorable_until: AwareDatetime


class AbortUploadBody(BaseModel):
    file_name: Annotated[str | None, Field(alias="fileName")] = None
    reason: str | None = None
    attempt_id: Annotated[UUID | None, Field(alias="attemptId")] = None


class FinalizeUploadBody(BaseModel):
    file_name: Annotated[str | None, Field(alias="fileName")] = None
    file_size: Annotated[float | None, Field(alias="fileSize")] = None
    hash: str | None = None
    s3_version_id: Annotated[str | None, Field(alias="s3VersionId")] = None
    attempt_id: Annotated[UUID | None, Field(alias="attemptId")] = None


class Protocol(StrEnum):
    attempt_v1 = "attempt-v1"


class PresignUploadBody(BaseModel):
    file_name: Annotated[str | None, Field(alias="fileName")] = None
    file_size: Annotated[float | None, Field(alias="fileSize")] = None
    content_type: Annotated[str | None, Field(alias="contentType")] = None
    content_sha256_hex: Annotated[str | None, Field(alias="contentSha256Hex")] = None
    protocol: Protocol | None = None
    attempt_id: Annotated[UUID | None, Field(alias="attemptId")] = None
