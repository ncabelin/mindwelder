import bleach

def markdown(content):
    bleached_content = bleach.clean(content,
        tags = ['strong','b','i','em','h1','h2','pre','code', 'br', 'u', 'li', 'ul', 'ol', 'q', 'a'])
    c = bleached_content.split('\n')
    # first line (description) will be a bigger font size
    c[0] = '<h3>%s</h3>' % c[0]
    content = '\n'.join(c)
    content = content.replace('\n', '<br>')
    content = content.replace('<q>', '<span class="question">')
    content = content.replace('</q>', '</span>')
    content = content.replace('<a>', '<span class="answer">')
    content = content.replace('</a>', '</span>')
    print content
    return content