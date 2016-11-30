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
    # c = bleached_content.split('\n')

    # # first line (description) will be a bigger font size
    # c[0] = '<h3>%s</h3>' % c[0]
    # content = '\n'.join(c)

    params = { '\n': '<br>',
    		'<q>': '<span class="question">',
    		'</q>': '</span>',
    		'<a>': '<span class="answer">',
    		'</a>': '</span>' }
    for p in params:
    	bleached_content = bleached_content.replace(p, params[p])

    return content