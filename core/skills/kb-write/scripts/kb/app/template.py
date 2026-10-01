from kb.note.template import render_template
from kb.note.vocabulary import NoteType


def template(kind: NoteType) -> str:
    return render_template(kind)
