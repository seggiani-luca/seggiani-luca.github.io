import re
import random
import json
import inspect

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

# ---- utilities

comment = re.compile(r"^\s*<!--\s*(.*?)\s*-->\s*$")
def get_blurb(file):
    blurbs = []

    for line in file.splitlines():
        m = comment.match(line)
        if m:
            blurbs.append(m.group(1))

    if not blurbs:
        return "Se stai leggendo questo, ho fatto casino"

    # use a rando one
    return f"""<script>
(() => {{
    const blurbs = {json.dumps(blurbs)};
    document.write(blurbs[Math.floor(Math.random() * blurbs.length)]);
}})();
</script>"""

# ---- element macros

# converts kebab case to capitalized names
small = {"di", "ed", "e", "a", "da", "in", "su", "per", "tra", "fra"}
def create_title(nam):
    # tokenize string
    words = nam.split("-")
    return " ".join(words)

# creates a list 
def create_list(dr, number=0, recurse=False, blurb=False):
    # directory relative to source
    dr = src / dr

    res = "<ul>\n"

    # recurse or not?
    recurse = bool(recurse)
    if recurse:
        lst = dr.rglob("*")
    else:
        lst = dr.glob("*")
    
    # last n or all?
    number = int(number)
    if number != 0:
        lst = sorted(lst, reverse=True)[0:number]
    else:
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
        res += f"<li><a href={rel}>{nam}</a>"

        # optional blurb
        if blurb:
            blurb_text = get_blurb(fr.read_text())
            res += f"<p class=blurb>{blurb_text}</p>"

        res += "</li>\n"

    res += "</ul>\n"
    return res

# creates a navbar
def create_nav():
    res = "<nav>\n"

    # basically a page list
    res += create_list("")

    res += "</nav>\n"
    return res

# outputs a random page blurb
def page_blurb(file):
    blurb = get_blurb(file)
    return f"<p class=subtitle>{blurb}</p>"

# estimates page read time
def estimate_time(file):
    # average words per minute
    wpm = 225

    # count words
    file = re.sub(r"```.*?```", "", file, flags=re.DOTALL)
    file = re.sub(r"<!--.*?-->", "", file, flags=re.DOTALL)
    words = len(re.findall(r"\b[\wÀ-ÿ]+\b", file))

    # estimate minutes
    minutes = words / wpm

    res = "<p class=estimate>"

    if minutes < 1:
        res += "< 1 min"
    else:
        res += f"{round(minutes)} min"

    res += "</p>\n"
    return res

# ---- generation logic

# preprocesses a markdown file, expanding macros
pattern = re.compile(r"\{\{\s*(\w+)\s+(.*?)\s*\}\}")
def preprocess(md):
    def repl(match):
        # get function, kwargs and args
        fun_str = match.group(1)
        args = []
        kwargs = {}

        # match kwargs and args
        for arg in match.group(2).split():
            if "=" in arg:
                key, value = arg.split("=", 1)
                kwargs[key] = value
            else:
                args.append(arg)

        # get function
        fun = globals()[fun_str]

        # constants
        if "file" in inspect.signature(fun).parameters:
            kwargs["file"] = md

        return fun(*args, **kwargs)
    
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
