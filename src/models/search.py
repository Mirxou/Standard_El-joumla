"""
نماذج البحث والفلترة المتقدمة
Advanced Search & Filter Models
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import date, datetime
from enum import Enum


class SearchEntity(Enum):
    """الكيانات القابلة للبحث"""
    ALL = "الكل"
    PRODUCTS = "المنتجات"
    CUSTOMERS = "العملاء"
    SUPPLIERS = "الموردين"
    SALES = "المبيعات"
    PURCHASES = "المشتريات"
    QUOTES = "عروض الأسعار"
    RETURNS = "المرتجعات"
    ACCOUNTS = "الحسابات"


class FilterOperator(Enum):
    """عوامل الفلترة"""
    EQUALS = "يساوي"
    NOT_EQUALS = "لا يساوي"
    CONTAINS = "يحتوي"
    NOT_CONTAINS = "لا يحتوي"
    STARTS_WITH = "يبدأ بـ"
    ENDS_WITH = "ينتهي بـ"
    GREATER_THAN = "أكبر من"
    LESS_THAN = "أصغر من"
    GREATER_OR_EQUAL = "أكبر من أو يساوي"
    LESS_OR_EQUAL = "أصغر من أو يساوي"
    BETWEEN = "بين"
    IN = "ضمن"
    NOT_IN = "ليس ضمن"
    IS_NULL = "فارغ"
    IS_NOT_NULL = "غير فارغ"


class SortDirection(Enum):
    """اتجاه الترتيب"""
    ASC = "تصاعدي"
    DESC = "تنازلي"


@dataclass
class SearchFilter:
    """فلتر بحث واحد"""
    field: str
    operator: FilterOperator
    value: Any = None
    value2: Any = None  # For BETWEEN operator
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'field': self.field,
            'operator': self.operator.name,
            'value': self.value,
            'value2': self.value2
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SearchFilter':
        return cls(
            field=data['field'],
            operator=FilterOperator[data['operator']],
            value=data.get('value'),
            value2=data.get('value2')
        )


@dataclass
class SortCriteria:
    """معايير الترتيب"""
    field: str
    direction: SortDirection = SortDirection.ASC
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'field': self.field,
            'direction': self.direction.name
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SortCriteria':
        return cls(
            field=data['field'],
            direction=SortDirection[data['direction']]
        )


@dataclass
class SearchQuery:
    """استعلام بحث كامل"""
    entity: SearchEntity
    keyword: str = ""
    filters: List[SearchFilter] = field(default_factory=list)
    sort_by: List[SortCriteria] = field(default_factory=list)
    limit: int = 100
    offset: int = 0
    
    # Advanced options
    case_sensitive: bool = False
    whole_word: bool = False
    include_inactive: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'entity': self.entity.name,
            'keyword': self.keyword,
            'filters': [f.to_dict() for f in self.filters],
            'sort_by': [s.to_dict() for s in self.sort_by],
            'limit': self.limit,
            'offset': self.offset,
            'case_sensitive': self.case_sensitive,
            'whole_word': self.whole_word,
            'include_inactive': self.include_inactive
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SearchQuery':
        return cls(
            entity=SearchEntity[data['entity']],
            keyword=data.get('keyword', ''),
            filters=[SearchFilter.from_dict(f) for f in data.get('filters', [])],
            sort_by=[SortCriteria.from_dict(s) for s in data.get('sort_by', [])],
            limit=data.get('limit', 100),
            offset=data.get('offset', 0),
            case_sensitive=data.get('case_sensitive', False),
            whole_word=data.get('whole_word', False),
            include_inactive=data.get('include_inactive', False)
        )


@dataclass
class SavedFilter:
    """فلتر محفوظ"""
    id: Optional[int] = None
    name: str = ""
    description: str = ""
    entity: SearchEntity = SearchEntity.ALL
    query_data: str = ""  # JSON serialized SearchQuery
    is_default: bool = False
    is_shared: bool = False
    created_by: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'entity': self.entity.name,
            'query_data': self.query_data,
            'is_default': self.is_default,
            'is_shared': self.is_shared,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


@dataclass
class SearchResult:
    """نتيجة بحث"""
    entity_type: SearchEntity
    records: List[Dict[str, Any]] = field(default_factory=list)
    total_count: int = 0
    page: int = 1
    page_size: int = 100
    has_more: bool = False
    execution_time_ms: float = 0.0
    
    @property
    def total_pages(self) -> int:
        if self.page_size == 0:
            return 0
        return (self.total_count + self.page_size - 1) // self.page_size


@dataclass
class SearchSuggestion:
    """اقتراح بحث"""
    text: str
    entity: SearchEntity
    score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
