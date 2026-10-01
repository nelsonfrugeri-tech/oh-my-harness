from dataclasses import dataclass

from .vocabulary import Harness, NoteType, Scope, Status


@dataclass(frozen=True)
class Entities:
    people: tuple[str, ...] = ()
    companies: tuple[str, ...] = ()
    products: tuple[str, ...] = ()
    brands: tuple[str, ...] = ()
    roles: tuple[str, ...] = ()
    projects: tuple[str, ...] = ()
    apps: tuple[str, ...] = ()
    urls: tuple[str, ...] = ()
    repos: tuple[str, ...] = ()
    paths: tuple[str, ...] = ()
    documents: tuple[str, ...] = ()
    emails: tuple[str, ...] = ()
    names: tuple[str, ...] = ()


@dataclass(frozen=True)
class Generated:
    harness: Harness
    model: str | None
    session_id: str
    cwd: str
    machine_id: str


@dataclass(frozen=True)
class Frontmatter:
    id: str
    type: NoteType
    title: str
    description: str
    summary: str
    tags: tuple[str, ...]
    status: Status
    version: int
    created_at: str
    updated_at: str
    generated: Generated
    entities: Entities = Entities()
    occurred_at: str | None = None
    parent: str | None = None
    related: tuple[str, ...] = ()
    children: tuple[str, ...] = ()
    superseded_at: str | None = None
    superseded_reason: str | None = None
    repository_path: str | None = None
    remote_url: str | None = None
    default_branch: str | None = None


@dataclass(frozen=True)
class NotePath:
    scope: Scope
    domain: str
    entities: tuple[str, ...]
    name: str

    @property
    def relative_path(self) -> str:
        return "/".join((self.scope.value, self.domain, *self.entities,
                         self.name, self.name + ".md"))


@dataclass(frozen=True)
class Section:
    heading: str
    text: str


@dataclass(frozen=True)
class Note:
    path: NotePath
    frontmatter: Frontmatter
    sections: tuple[Section, ...]

    @property
    def body(self) -> str:
        return "\n\n".join(f"## {section.heading}\n\n{section.text}" for section in self.sections)


@dataclass(frozen=True)
class FrozenVersion:
    note: Note
    relative_path: str


@dataclass(frozen=True)
class VersionedUpdate:
    frozen: FrozenVersion
    current: Note
