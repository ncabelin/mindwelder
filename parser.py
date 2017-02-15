import bleach

def markdown(content, status):
    params = {}
    if status == 'test':
        params = { '<u>': '<span class="answer">',
                '</u>': '</span>' }
    params['\n'] = '<br>'
    for p in params:
        content = content.replace(p, params[p])

    attrs = {
        '*': ['class'],
        'a': ['href', 'rel'],
        'font': ['size'],
        'blockquote': ['style'],
        'span': ['class']
        }
    bleached_content = bleach.clean(content,
        tags = ['strong','b','i','em','h1',
        'h2','pre','code', 'br', 'u', 'li',
        'ul', 'ol', 'q', 'a', 'div', 'font',
        'blockquote', 'br', 'span'], attributes=attrs)

    return bleached_content