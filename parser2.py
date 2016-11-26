import bleach

def markdown(content):
    bleached_content = bleach.clean(content,
        tags = ['strong','b','i','em','h1','h2','pre','code', 'br', 'u', 'li', 'ul', 'ol', 'q', 'a'])
    c = bleached_content.split('\n')
    # first line (description) will be a bigger font size
    c[0] = '<h3>%s</h3>' % c[0]
    content = '\n'.join(c)
    
    params = { '\n': '<br>',
    		'<q>': '<span class="question">',
    		'</q>': '</span>',
    		'<a>': '<span class="answer">',
    		'</a>': '</span>' }

    for p in params:
    	content = content.replace(p, params[p])

    print content
    return content