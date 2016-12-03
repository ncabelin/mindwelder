import bleach

def markdown(content):
    attrs = {
        '*': ['class'],
        'a': ['href', 'rel'],
        'font': ['size'],
        'blockquote': ['style']
        }
    bleached_content = bleach.clean(content,
        tags = ['strong','b','i','em','h1',
        'h2','pre','code', 'br', 'u', 'li',
        'ul', 'ol', 'q', 'a', 'div', 'font',
        'blockquote'], attributes=attrs)

    params = { '\n': '<br>',
    		'<q>': '<span class="question">',
    		'</q>': '</span>',
    		'<u>': '<span class="answer">',
    		'</u>': '</span>' }
    for p in params:
    	bleached_content = bleached_content.replace(p, params[p])

    return bleached_content