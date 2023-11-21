def _protect_for_html(text_data):
    return text_data.replace('&', '&amp;')\
                    .replace('<', '&lt;')\
                    .replace('>', '&gt;')
