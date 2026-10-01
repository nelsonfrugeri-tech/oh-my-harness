from enum import Enum


class EntityKind(str, Enum):
    PEOPLE = 'people'
    COMPANIES = 'companies'
    PRODUCTS = 'products'
    BRANDS = 'brands'
    ROLES = 'roles'
    PROJECTS = 'projects'
    APPS = 'apps'
    URLS = 'urls'
    REPOS = 'repos'
    PATHS = 'paths'
    DOCUMENTS = 'documents'
    EMAILS = 'emails'
    NAMES = 'names'


LITERAL_KINDS = frozenset({EntityKind.URLS, EntityKind.PATHS, EntityKind.REPOS, EntityKind.EMAILS})
SINGULAR_KINDS = dict(zip(
    ('person', 'company', 'product', 'brand', 'role', 'project', 'app', 'url',
     'repo', 'path', 'document', 'email', 'name'), EntityKind,
))
