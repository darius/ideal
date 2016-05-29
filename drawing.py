"""
Output SVG.
"""

import xml.dom.minidom as dom

# (I tried using SVG transforms to work within the source coordinate
# system (right handed, original scale), but gave up because then text
# gets mirror reflected and grossly enlarged. The viewBox does let us
# shift the origin.)

def begin():
    print """\
<svg version="1.1" baseProfile="full" xmlns="http://www.w3.org/2000/svg"
     width="800" height="800" viewBox="-400.5 -400.5 800 800">"""
# (viewBox's extra .5 makes for crisp lines at integer coordinates.)

def end():
    print """\
</svg>"""

xscale =  100
yscale = -100

def polyline(points):
    print ('<polyline points="%s" fill="transparent" stroke="black" stroke-width="1"/>'
           % ', '.join('%g %g' % (x*xscale, y*yscale) for x,y in points))

def text(string, justified, at):
    anchor = anchorings[justified]
    x, y = at
    print ('<text text-anchor="%s" x="%g" y="%g">%s</text>'
           % (anchor, x*xscale, y*yscale, xml_escape(string)))

anchorings = {
    'left':  'start',
    '':      'middle',
    'right': 'end',
}

def xml_escape(string):
    t = dom.Text()
    t.data = string
    return t.toxml()