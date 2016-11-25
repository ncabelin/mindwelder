import bleach

def markdown(content):
    bleached_content = bleach.clean(content,
        tags = ['strong','b','i','em','h1','h2','pre','code', 'br', 'u', 'li', 'ul', 'ol'])
    c = bleached_content.split('\n')
    # first line (description) will be a bigger font size
    c[0] = '<h3>%s</h3>' % c[0]
    content = '\n'.join(c)
    content = content.replace('\n', '<br>')
    return content