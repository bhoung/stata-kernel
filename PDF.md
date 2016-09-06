## PDF conversion
 
**Suppressing Input**
  
You may find it useful to suppress input cells, as Stata echoes the commands in the output, by adding the following code to the latex template you are using - [1]. The default template is article.tplx, which is located in the Anaconda installation directory (C:\Users\%USER%\AppData\Local\Continuum\Anaconda\Lib\site-packages\IPython\nbconvert\templates\latex).
 
    % Disable input cells
    ((* block input_group *))
    ((* endblock input_group *))

**Graph Size** 

The default size of the graphs is too large. I edited base.tplx, which is extended by article.tplx and report.tplx, to reduce the size of the graphs in the code under '% Draw a figure using the graphicx package'. Change the max size in the line below to your liking. I opted for 0.6 linewidth and 0.3 paperheight.

    \adjustimage{max size={0.6\linewidth}{0.3\paperheight}}{((( filename )))}

**Page Breaks** 

You will probably run into the annoyance of seeing your (regression) output being broken across pages. We can avoid this but the tradeoff is that you can't insert large blocks of code that you want to be broken across pages into a single cell. Add the following snippet under ((* block packages *)) in base.tplx [2]:

    \newenvironment{absolutelynopagebreak}
    {\par\nobreak\vfil\penalty0\vfilneg
    \vtop\bgroup}
    {\par\xdef\tpd{\the\prevdepth}\egroup
    \prevdepth=\tpd}

Then, insert the following line under '((* block stream *))':   

    \begin{absolutelynopagebreak}

and the following line above '((* endblock stream *))':

    \end{absolutelynopagebreak}

**Single Spacing**

For single spacing repeat the above (as per non page breaks) with the following: 

    \usepackage[doublespacing]{setspace} % under block packages

    \begin{singlespace} % under block stream

    \end{singlespace}


**References**

[1] http://blog.juliusschulz.de/blog/ultimate-ipython-notebook

[2] http://tex.stackexchange.com/questions/94699/absolutely-definitely-preventing-page-break
