# ---- markdown renderer

from markdown_it import MarkdownIt
renderer = MarkdownIt("commonmark").enable('table')


# ---- directories

from pathlib import Path
import shutil
src = Path("source")
stt = Path("static")
thm = Path("theme")

# clear a directory
def clear_dir(dr):
    shutil.rmtree(dr)
    dr.mkdir()


# ---- theme constants

head = thm / "head.html"
header = thm / "header.html"
footer = thm / "footer.html"


# ---- element macros

# converts kebab case to capitalized names
small = {"di", "ed", "e", "a", "da", "in", "su", "per", "tra", "fra"}
def create_title(nam):
    # tokenize string
    words = nam.split("-")
    return " ".join(words)

# creates a list 
def create_list(dr, n=0):
    # directory relative to source
    dr = src / dr

    res = "<ul>\n"

    # populate list
    lst = dr.glob("*")
    if n != 0:
        # last n
        lst = sorted(lst, reverse=True)[0:n]
    else:
        # all
        lst = sorted(lst)

    for fr in lst:
        # check for .md files
        if fr.suffix != ".md":
            continue 

        # skip index
        if fr.stem == "index":
            continue

        # insert in list
        rel = "/" + str(fr.with_suffix(".html").relative_to(src))
        nam = create_title(fr.stem) 
        res += f"<li><a href={rel}>{nam}</a></li>\n"

    res += "</ul>\n"
    return res

# creates a navbar
def create_nav():
    res = "<nav>\n"

    # basically a page list
    res += create_list("")

    res += "</nav>\n"
    return res


# ---- generation logic

import re

# preprocesses a markdown file, expanding macros
pattern = re.compile(r"\{\{\s*(\w+)\s+(.*?)\s*\}\}")
def preprocess(md):
    def repl(match):
        # get function and args
        fun = match.group(1)
        args = match.group(2).split()

        # call macro
        return globals()[fun](*args)
    
    return pattern.sub(repl, md)

# processes a markdown file 
def process(file):
    # check for .md files
    if file.suffix != ".md":
        return None

    # initialize result
    res = """<!DOCTYPE html>
<html lang="it">\n"""

    res += head.read_text(encoding="utf-8")

    res += "<body>\n"

    res += header.read_text(encoding="utf-8")

    res += create_nav()

    res += "<main>\n"
    
    md = file.read_text(encoding="utf-8")
    md = preprocess(md)
    res += renderer.render(md)
    
    res += "</main>\n"
    
    res += footer.read_text(encoding="utf-8")
   
    res +="</body>\n"
    return res


# greet the user
print("Generating HTML pages ...")

# clear static pages
clear_dir(stt)

# copy theming
for fr in thm.rglob("*"):
    # get relative path in static files
    to = stt / fr.relative_to(thm)

    if not fr.is_dir() and fr.suffix != ".html":
        # mirror directories
        to.parent.mkdir(parents=True, exist_ok=True)
        
        # not an .html file, just copy
        shutil.copy(fr, to)

# go through source files
for fr in src.rglob("*"):
    # get relative path in static files
    to = stt / fr.relative_to(src)

    # mirror directories
    if fr.is_dir():
        to.mkdir(parents=True, exist_ok=True)
    
    # process files, mirroring structure
    else:
        # mirror directories
        to.parent.mkdir(parents=True, exist_ok=True)
        
        # convert file
        proc = process(fr)
        if proc == None:
            # not an .md file, just copy
            shutil.copy(fr, to)
            continue

        # write html
        to = to.with_suffix(".html")
        to.write_text(proc, encoding="utf-8")
