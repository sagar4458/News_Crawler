import re
from html import unescape

class CleanTextPipeline:
    def process_item(self, item, spider):
        # Clean title
        if item.get('title'):
            item['title'] = unescape(re.sub(r'\s+', ' ', item['title']).strip())
        # Clean body
        if item.get('body'):
            # Remove extra whitespace, newlines, and HTML entities
            item['body'] = unescape(re.sub(r'\s+', ' ', item['body']).strip())
        return item