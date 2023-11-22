def protect_for_html(text_data):
    return text_data.replace('&', '&amp;')\
                    .replace('<', '&lt;')\
                    .replace('>', '&gt;')

def singleton(cls, *args, **kw):
    instances = {}
    def _singleton(*args, **kw):
        if cls not in instances:
            instances[cls] = cls(*args, **kw)
        return instances[cls]
    return _singleton


