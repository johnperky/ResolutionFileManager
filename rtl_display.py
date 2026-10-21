"""Visual RTL order for Linux Tk 8.6, retaining logical character positions.

Windows Tk already shapes/reorders text. Never apply this layer there.
The mapping keeps Help search and hyperlinks tied to the original text.
"""
from dataclasses import dataclass
import re
import sys

RTL_CODES={"ar","he","ur","fa"}
MARK="\u200e"

def needs_visual_order(language, platform=None):
    return (platform or sys.platform).startswith("linux") and language in RTL_CODES

def ordered(text):
    if not re.search(r"[\u0590-\u08ff]",text): return text,list(range(len(text)))
    import arabic_reshaper
    from bidi import algorithm as bidi
    reshaper=arabic_reshaper.ArabicReshaper(configuration={"delete_harakat":False,"support_ligatures":False,"support_zwj":False})
    shaped=reshaper.reshape(text)
    if len(shaped)!=len(text):
        raise ValueError("RTL shaping changed character count; logical mapping needs review")
    storage=bidi.get_empty_storage(); storage["base_level"]=1; storage["base_dir"]="R"
    bidi.get_embedding_levels(shaped,storage,False,False)
    for index,char in enumerate(storage["chars"]): char["logical_index"]=index
    bidi.explicit_embed_and_overrides(storage,False)
    bidi.resolve_weak_types(storage,False)
    bidi.resolve_neutral_types(storage,False)
    bidi.resolve_implicit_levels(storage,False)
    bidi.reorder_resolved_levels(storage,False)
    bidi.apply_mirroring(storage,False)
    return "".join(c["ch"] for c in storage["chars"]),[c["logical_index"] for c in storage["chars"]]

def display_text(value,language,platform=None):
    if not isinstance(value,str) or not needs_visual_order(language,platform) or value.startswith(MARK): return value
    if not re.search(r"[\u0590-\u08ff]",value): return value
    return MARK+"\n".join(ordered(line)[0] for line in value.split("\n"))

@dataclass
class VisualLine:
    text:str
    logical_indices:list[int]

def render_document(logical,width,measure):
    result=[]; offset=0
    for line in logical.split("\n"):
        start=0; current=""
        for match in re.finditer(r"\S+\s*|\s+",line):
            token=match.group()
            if current and measure(ordered(current+token)[0])>width:
                visual,mapping=ordered(current)
                result.append(VisualLine(visual,[offset+start+i for i in mapping]))
                start+=len(current); current=""
            current+=token
        visual,mapping=ordered(current)
        result.append(VisualLine(visual,[offset+start+i for i in mapping]))
        offset+=len(line)+1
    return "\n".join(line.text for line in result),result

def mapped_ranges(lines,start,end):
    """Yield visual (row,start,end) spans for any exact logical match."""
    for row,line in enumerate(lines,1):
        active=None
        for index,logical in enumerate([*line.logical_indices,-1]):
            included=start<=logical<end
            if included and active is None: active=index
            elif not included and active is not None:
                yield row,active,index
                active=None
