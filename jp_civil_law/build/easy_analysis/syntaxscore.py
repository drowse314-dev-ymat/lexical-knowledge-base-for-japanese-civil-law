# encoding: utf-8

from xmlpumpkin import parse_to_tree as totree


AMP_TITLE = 1.4
AMP_SUBJECT = 1.4

def syntaxscore(termset, raw_title, raw_sents, subject=False):
    trees = [totree(sent) for sent in raw_sents]
    scores = []
    scores.append(amplify_by_title(termset, raw_title))
    if subject:
        for t in trees:
            scores.append(amplify_by_syntax(termset, t))

    return {term: sum(score[term] for score in scores) for term in termset}

def amplify_by_title(termset, title):
    base = dict.fromkeys(termset, 1.0)
    t = totree(title)
    surfaces = [c.surface for c in t.chunks]
    for term in termset:
        for surface in surfaces:
            if term in surface:
                base[term] *= AMP_TITLE
    return base

def amplify_by_syntax(termset, tree):
    base = dict.fromkeys(termset, 1.0)
    if not tree.chunks:
        return base
    topicchunks = [
        chunk for chunk in tree.chunks
        if chunk.func_surface in (u'は', u'も', u'場合', u'とき', u'ば', u'なら')
    ] + [tree.root]
    topicfocus = sum([dep_expand(chunk) for chunk in topicchunks], [])
    topicfocus = list(set(topicfocus))
    ts = []
    for term in termset:
        for surface in topicfocus:
            if term in surface:
                ts.append(term)
                base[term] *= AMP_SUBJECT
    return base

def dep_expand(chunk):
    def recursive_deps(root, seen):
        for dep in root.linked:
            if dep not in seen:
                seen.add(dep)
                if dep.linked:
                    recursive_deps(dep, seen)
    seen = set([chunk])
    for c in chunk.linked:
        seen.add(c)
    return [c.surface for c in seen]
