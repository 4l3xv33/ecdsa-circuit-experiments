#!/usr/bin/env python3
"""Deterministically turn REPORT.md into an academic LaTeX source document.

The deliberately small Markdown subset covers this report only. Compilation
is separate; no network calls or package installation occur here.
"""
from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[1]
def esc(s):
    return ''.join({'\\':r'\textbackslash{}','&':r'\&','%':r'\%','$':r'\$','#':r'\#','_':r'\_',
      '{':r'\{','}':r'\}','~':r'\textasciitilde{}','^':r'\textasciicircum{}'}.get(c,c) for c in s)
def inline(s):
    pattern=r'(`[^`]+`|\*\*[^*]+\*\*|\*[^*]+\*|\[[^\]]+\]\([^)]+\))'
    parts=re.split(pattern,s)
    out=[]
    for t in parts:
        if t.startswith('`'):
            code=t[1:-1]
            out.append(r'\texttt{'+esc(code)+'}' if ' ' in code else r'\path{'+code+'}')
        elif t.startswith('**'):out.append(r'\textbf{'+esc(t[2:-2])+'}')
        elif t.startswith('*'):out.append(r'\emph{'+esc(t[1:-1])+'}')
        elif re.fullmatch(r'\[[^\]]+\]\([^)]+\)',t):
            label,url=re.match(r'\[([^\]]+)\]\(([^)]+)\)',t).groups()
            out.append(r'\href{'+url+'}{'+esc(label)+'}')
        else:out.append(esc(t))
    return ''.join(out)
lines=(ROOT/'REPORT.md').read_text().splitlines()
# Title, author and date are typeset by LaTeX, using the exact requested labels.
start=next(i for i,l in enumerate(lines) if l=='## Executive summary')
lines=lines[start:]
out=[];i=0
while i<len(lines):
    l=lines[i]
    if not l.strip():i+=1;continue
    if l.startswith('## '):out.append(r'\section{'+esc(l[3:])+'}');i+=1;continue
    if l.startswith('### '):out.append(r'\subsection{'+esc(l[4:])+'}');i+=1;continue
    if l=='$$':
        i+=1;math=[]
        while i<len(lines) and lines[i]!='$$':math.append(lines[i]);i+=1
        out.append('\\[\n'+'\n'.join(math)+'\n\\]');i+=1;continue
    if l.startswith('```'):
        i+=1;code=[]
        while i<len(lines) and not lines[i].startswith('```'):code.append(lines[i]);i+=1
        out.append('\\begin{lstlisting}\n'+'\n'.join(code)+'\n\\end{lstlisting}');i+=1;continue
    if l.startswith('|'):
        rows=[]
        while i<len(lines) and lines[i].startswith('|'):
            cells=[x.strip() for x in lines[i].strip('|').split('|')]
            if not all(re.fullmatch(r'[-: ]+',x) for x in cells):rows.append(cells)
            i+=1
        n=len(rows[0])
        # Full-width tables with wrapping, repeated headings and generous rows.
        fractions={3:[.48,.26,.26],4:[.40,.18,.22,.20],5:[.24,.20,.20,.18,.18]}[n]
        width=6.30-0.14*n
        spec=''.join('>{\\raggedright\\arraybackslash}p{'+f'{width*x:.3f}'+'in}' for x in fractions)
        head=' & '.join(r'\textbf{'+inline(x)+'}' for x in rows[0])+r' \\'
        out.append('{\\small\n\\setlength{\\tabcolsep}{5pt}\n\\renewcommand{\\arraystretch}{1.18}\n'
          +'\\begin{longtable}{'+spec+'}\n\\toprule\n'+head+'\n\\midrule\n\\endfirsthead\n\\toprule\n'+head+'\n\\midrule\n\\endhead\n'
          +'\n'.join(' & '.join(inline(x) for x in row)+r' \\' for row in rows[1:])
          +'\n\\bottomrule\n\\end{longtable}\n}')
        continue
    if l.startswith('- ') or re.match(r'\d+\. ',l):
        ordered=bool(re.match(r'\d+\. ',l));kind='enumerate' if ordered else 'itemize'
        items=[]
        while i<len(lines):
            if not lines[i].strip():i+=1;continue
            m=re.match(r'(?:\d+\. |- )(.*)',lines[i])
            if not m:break
            items.append(r'\item '+inline(m.group(1)));i+=1
        out.append('\\begin{'+kind+'}\n'+'\n'.join(items)+'\n\\end{'+kind+'}');continue
    para=[]
    while i<len(lines) and lines[i].strip() and not lines[i].startswith(('##','|','```')) and lines[i]!='$$':
        para.append(lines[i]);i+=1
    out.append(inline(' '.join(para))+'\n')
preamble=r'''\documentclass[11pt,letterpaper]{article}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{lmodern}
\usepackage[margin=1in]{geometry}
\usepackage{amsmath,amssymb,booktabs,longtable,array}
\usepackage{microtype}
\usepackage{xcolor}
\usepackage{xurl}
\usepackage{listings}
\usepackage{enumitem}
\usepackage{hyperref}
\hypersetup{colorlinks=true,linkcolor=black,urlcolor=blue!45!black,
 pdftitle={Reversible Point Addition Experiments},
 pdfauthor={Umbra (Alex's Bot) and Alex (Umbra's Human)},
 pdfsubject={Experimental ECDSA.fail circuit optimization report, October 29, 2026}}
\setlength{\parindent}{0pt}
\setlength{\parskip}{0.5em}
\setlength{\emergencystretch}{2em}
\setlist{itemsep=0.4em,topsep=0.3em,leftmargin=1.5em}
\lstset{basicstyle=\ttfamily\footnotesize,breaklines=true,columns=fullflexible,
 keepspaces=true,showstringspaces=false,frame=single,rulecolor=\color{black!20},xleftmargin=0.2em,xrightmargin=0.2em}
\title{Reversible Point Addition Experiments\\[0.35em]\large Exact Local Savings and Unresolved Arithmetic Reliability}
\author{Umbra (Alex's Bot) \and Alex (Umbra's Human)}
\date{October 29, 2026}
\begin{document}
\maketitle
\begin{center}\small Technical research report. Experimental snapshot; not peer reviewed.\end{center}
'''
(ROOT/'report').mkdir(exist_ok=True)
(ROOT/'report/main.tex').write_text(preamble+'\n\n'.join(out)+'\n\\end{document}\n')
print('Generated report/main.tex from REPORT.md')
