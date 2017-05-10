# Lamusica...

I've dabbled with music boxes for all of my life. My father had a paper-strip
based music box for ages and I loved playing with it.

In 2006 I started a project to build a hole-punching robot. But it never got
anywhere beyond buying some parts, including some CNCed parts for mechanical
structure:

![Image of ordered parts](http://www.home.unix-ag.org/simon/files/lamusica-parts.jpg)

But it was always lingering in the back of my head and in 2011, when attending
the Chaos Communication Camp, there suddenly was a "FabLabTruck" and it had a
laser cutter...

The first holes were cut there and it seemed to work...

In 2013 I did a collaboration with Jørgen Lang to encode a composition from
Rüddiger Oppermann onto tape, so that his friends could surprise him with a
music box. It was well received   :)


## Features

lamusica.py analyzes an input midi file, tries to transpose it optimally for a
given music box model ("minimizing the number of non-playable notes"). It can generate an output midi file, simulating what it'd sound like on the music box, so that the impact of the missing notes can be judged before cutting actual paper.

For lasercutting it can generate SVG or PDF, where the holes and the strip
outlines are drawn using different colors, so that lasercutting software can
cut them in different passes.


## Usage

```
Usage: ./lamusica.py [arguments] <midi-file>
  -h, --help: show usage
  -t, --transpose=number: transpose by n halftones (avoid auto)
  -f, --filter=number: ignore note-repetition faster than <ticks>
  -b, --box=type: music box type: sankyo15, sankyo20, teanola30, sankyo33
  -m, --midi=filename: output midi file name (omit if not wanted)
  -p, --pdf=filename: output pdf file name (omit if not wanted)
  -s, --svg=filename: output svg file name (omit if not wanted)
```

