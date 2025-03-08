# create a python script that will convert .md to .html
def convert_md_to_html(md_file, html_file):
    with open(md_file, 'r') as f:
        md = f.read()
    
    html = markdown.markdown(md)
    
    with open(html_file, 'w') as f:
        f.write(html)
        