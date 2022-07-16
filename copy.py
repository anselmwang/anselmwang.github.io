import os
import re
import shutil
from urllib.parse import quote

OBSIDIAN_NOTE_DIR = os.environ["OBSIDIAN_NOTE_DIR"]
GIT_NOTE_ROOT = os.environ["GIT_NOTE_ROOT"]
from html import escape

def need_publish(file_name):
    return file_name.startswith("P.") and file_name.endswith(".md")

def get_title(file_name):
    return os.path.splitext(file_name)[0]

def get_link(ancestor_names, file_name):
    segs = ancestor_names + [file_name]
    return "/" + "/".join(quote(seg) for seg in segs)

def generate_sidebar_lines(side_bar, ancestor_names:list):
    cur_side_bar_lines = []
    for k in sorted(side_bar.keys()):
        v = side_bar[k]
        if v is None:
            file_name = k
            title = get_title(file_name)
            link_url = get_link(ancestor_names, file_name)
            cur_side_bar_lines.append(f"* [{title}]({link_url})")
        else:
            cur_side_bar_lines.append(f"* {k}")
            cur_side_bar_lines.extend([f"  {line}"
                 for line in generate_sidebar_lines(side_bar[k], 
                                                    ancestor_names + [k])])
    
    return cur_side_bar_lines

ATTACHMENT_LINK_RE = re.compile(r"!\[\[(.*?)\]\]")
WIKI_LINK_RE = re.compile(r"\[\[(.*?)\]\]")
def process_md_content(file_name, content, doc_root, ancestor_names):
    def attachment_callback(m):
        attachment_path = m.group(1)
        src_path = os.path.join(OBSIDIAN_NOTE_DIR, attachment_path)
        tgt_path = os.path.join(doc_root, attachment_path)
        os.makedirs(os.path.split(tgt_path)[0], exist_ok=True)
        shutil.copy(src_path, tgt_path)
        new_attachment_path = "/".join([".."] * len(ancestor_names)) + "/" + attachment_path
        new_attachment_path = "/".join(
            quote(seg) for seg in new_attachment_path.split("/"))
        return f"![]({new_attachment_path})"
    
    def wiki_link_callback(m):
        wiki_link_path: str = m.group(1)
        link_title = escape(wiki_link_path)

        splitted_path = wiki_link_path.rsplit("#", 1)
        new_wiki_link_path = quote("/" + splitted_path[0])
        if len(splitted_path) == 2:
            new_wiki_link_path += f"?id={quote(splitted_path[1])}"
        return f"[{link_title}]({new_wiki_link_path})"

    content = ATTACHMENT_LINK_RE.sub(attachment_callback, content)
    # I have confirmed for wiki link, no need to url.parse.quote
    content = WIKI_LINK_RE.sub(wiki_link_callback, content)
    content = f"# {get_title(file_name)}\n" + content
    return content

def copy_all_md_files(doc_root, side_bar, ancestor_names: list):
    for k in sorted(side_bar.keys()):
        v = side_bar[k]
        if v is None:
            file_name = k
            src_path = "/".join(ancestor_names) + f"/{file_name}"
            tgt_path = os.path.join(doc_root, src_path)
            os.makedirs(os.path.split(tgt_path)[0], exist_ok=True)
            with open(src_path, encoding="utf-8") as src_f, \
                open(tgt_path, "w", encoding="utf-8") as tgt_f:
                content = process_md_content(file_name, src_f.read(), doc_root, ancestor_names)
                tgt_f.write(content)
        else:
            copy_all_md_files(doc_root, v, ancestor_names + [k])
    

doc_root = os.path.join(GIT_NOTE_ROOT, "docs")
docs_template_path = os.path.join(GIT_NOTE_ROOT, "docs_template")
if os.path.exists(doc_root):
    shutil.rmtree(doc_root)
assert os.path.exists(docs_template_path)

shutil.copytree(
    docs_template_path,
    doc_root
)

os.chdir(OBSIDIAN_NOTE_DIR)
side_bar = {}
for root, dirs, files in os.walk("."):
    files.sort()
    for file_name in files:
        if need_publish(file_name):
            splitted_path = os.path.normpath(root).split(os.path.sep)
            cur_side_bar = side_bar
            for seg in splitted_path:
                if seg not in cur_side_bar:
                    cur_side_bar[seg] = {}
                cur_side_bar = cur_side_bar[seg]
            cur_side_bar[file_name] = None

with open(os.path.join(doc_root, "_sidebar.md"), "w", encoding="utf-8") as out_f:
    side_bar_str = "\n".join(generate_sidebar_lines(side_bar, []))
    out_f.write(side_bar_str)

copy_all_md_files(doc_root, side_bar, [])