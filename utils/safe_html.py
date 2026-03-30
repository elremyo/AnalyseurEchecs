"""Échappement pour fragments HTML affichés avec unsafe_allow_html."""

import html


def escape_html(text) -> str:
    if text is None:
        return ""
    return html.escape(str(text), quote=True)
