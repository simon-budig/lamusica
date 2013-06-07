#!/usr/bin/env python
import struct, sys

band = None
trktime = 0

cur_track = 0
tracks = range (1024)

delta_ticks = 0

wholenotes = [  0,  2,  4,  5,  7,  9, 11,
               12, 14, 16, 17, 19, 21, 23,
               24, 26, 28, 29, 31, 33 ]

def handle_midi_event (dt, command):
   global band, trktime

   trktime += dt
   mc = ord (command[0]) >> 4

   if mc == 0x08:
      pass
      # print >>sys.stderr, dt, ": noteoff"
   elif mc == 0x09:
      print >>sys.stderr, dt, ": noteon", ord (command[1])
      band[ord (command[1])] [trktime] = 1
   else:
      print >>sys.stderr, "dt: %d, event %r" % (dt, command)


def handle_midi_ticked_events (midi_data):
   global trktime

   trktime = 0
   mc = None
   t = midi_data
   while t:
      dt = 0
      while ord (t[0]) & 0x80:
         dt = (dt + (ord (t[0]) & 0x7f)) << 7
         t = t[1:]
      dt += ord (t[0])

      t = t[1:]
      
      if ord(t[0]) & 0x80:
         mc = t[0]
         t = t[1:]

      if ord(mc) >> 4 in [0x08, 0x09, 0x0a, 0x0b, 0x0e]:
         command = mc + t[:2]
         t = t[2:]
      elif ord(mc) >> 4 in [0x0c, 0x0d]:
         command = mc + t[:1]
         t = t[1:]
      elif ord(mc) in [0xf8, 0xfa, 0xfb, 0xfc]:
         command = mc
      elif ord(mc) == 0xff:
         l = ord (t[1])
         command = mc + t[:2+l]
         t = t[2+l:]
      else:
         raise Exception, 'unknown MIDI event: %d' % ord (t[0])

      handle_midi_event (dt, command)


def handle_chunk (chunkname, chunkdata):
   global cur_track, delta_ticks

   if chunkname == 'MThd':
      if len (chunkdata) != 6:
         raise Exception, "invalid MThd chunk"
      mtype, n_tracks, delta_ticks = struct.unpack (">hhh", chunkdata)
      print >>sys.stderr, "type: %d, n_tracks: %d, delta_ticks: %d" % (mtype, n_tracks, delta_ticks)

   elif chunkname == 'MTrk':
      if cur_track in tracks:
         handle_midi_ticked_events (chunkdata)
      cur_track += 1


def read_midi (filename):
   t = file (filename).read()

   while t:
      if len (t) < 8:
         raise Exception, "Not enough bytes in MIDI file"
      chunkname = t[:4]
      chunklen = struct.unpack (">I", t[4:8])[0]
      if len (t) < 8+chunklen:
         raise Exception, "Not enough bytes in MIDI file"
      chunkdata = t[8:8+chunklen]

      print >>sys.stderr, chunkname, chunklen
      handle_chunk (chunkname, chunkdata)
      t = t[8+chunklen:]


def prepare_band (band):
   print >>sys.stderr, "notes used:",
   for i in range (128):
      if band[i]:
         print >>sys.stderr, "%d (%d)," % (i, len (band[i])),
   print >>sys.stderr

   transpose = 0
   transpose_error = sys.maxint

   for trans in range(12):
      errcount = 0;
      for i in range (128):
         if band[i] and (i+trans) % 12 in [ 1, 3, 6, 8, 10 ]:
            errcount += len (band[i])
      if errcount < transpose_error:
         transpose_error = errcount
         transpose = trans

   octshift = 0
   octshift_error = sys.maxint

   for os in range (-12, 12):
      errcount = 0
      for i in range (128):
         if (i + transpose + os*12 < 0) or (i + transpose + os*12 > 33):
            errcount += len (band[i])
      if errcount < octshift_error:
         octshift_error = errcount
         octshift = os

   print >>sys.stderr, "transposing by %d octaves and %d halftones" % (octshift, transpose)
   print >>sys.stderr, "    --> %d halftone errors, %d notes out of range" % (transpose_error, octshift_error)

   notelist = [[] for i in range (20)]
   mindelta = sys.maxint
   for i in range (20):
      if i < 8:
         for j in range (wholenotes[i] - octshift * 12 - transpose, -1, -12):
            notelist[i] += band[j].keys()
      elif i < 12:
         for j in range (wholenotes[i] - octshift * 12 - transpose, -1, -12):
            notelist[i] += band[j].keys()
         for j in range (wholenotes[i] - octshift * 12 - transpose + 12, 128, 12):
            notelist[i] += band[j].keys()
      else:
         for j in range (wholenotes[i] - octshift * 12 - transpose, 128, 12):
            notelist[i] += band[j].keys()
      notelist[i] = list (set (notelist[i]))
      notelist[i].sort()
      for j in range (len (notelist[i]) - 1):
         mindelta = min (mindelta, notelist[i][j+1] - notelist[i][j])

   return notelist, mindelta



def output_svg (notelist, mindelta):
   step = 3.0 / mindelta

   start = min ([min (i) for i in notelist if i])
   l = int ((max ([max (i) for i in notelist if i]) - start) * 3.0 * step + 1) + 40

   print """<?xml version="1.0" encoding="utf-8" standalone="yes"?>
<svg xmlns="http://www.w3.org/2000/svg" width="%dmm" height="70mm">
  <g transform="scale(3.5433,-3.5433) translate(0,-70)">
    <path style="fill:black; stroke:none;"
          d="M 4 5 L 7 7 7 5.7 17 5.7 17 4.3 7 4.3 7 3 z" />
    <path style="fill:none; stroke:blue; stroke-width:0.1;"
          d="M 3 0
             a 3 3 0 0 0 -3  3 l 0 64
             a 3 3 0 0 0  3  3 l %d 0
             a 3 3 0 0 0  3 -3 l 0 -64
             a 3 3 0 0 0 -3 -3 z" />
    <g style="fill:none; stroke:red; stroke-width:0.03333;"
       transform="translate(20,6.5) scale(3,3)">""" % (l, l - 6)
   note = 0
   for note in range(20):
      for n in notelist[note]:
         print "      <circle cx=\"%g\" cy=\"%d\" r=\"0.40\"/>" % ((n - start) * step, note)

   print "    </g>\n  </g>\n</svg>"

def output_midi (notelist, mindelta):
   sys.stdout.write ("MThd" + struct.pack (">ihhh", 6, 0, 1, delta_ticks))

   events = []
   for i in range (20):
      events += [(t, i) for t in notelist[i]]

   events.sort()

   last_time = 0
   eventdata = ""
   for t, i in events:
      dt = t - last_time
      if (dt >> 21):
         eventdata += chr (0x80 | ((dt >> 21) & 0x7f))
      if (dt >> 14):
         eventdata += chr (0x80 | ((dt >> 14) & 0x7f))
      if (dt >> 7):
         eventdata += chr (0x80 | ((dt >> 7) & 0x7f))

      eventdata += chr (0x00 | ((dt >> 0) & 0x7f))
      eventdata += chr (0x90) + chr (60 + wholenotes[i]) + chr (127)
      last_time += dt

   eventdata += "\x00\xFF\x2F\x00"
   sys.stdout.write ("MTrk" + struct.pack (">i", len (eventdata)))
   sys.stdout.write (eventdata)



if __name__=='__main__':
   band = [ {} for i in range (128) ]
   trktime = 0
   tracks = [0, 1, 2, 3]

   read_midi (sys.argv[1])

   notelist, mindelta = prepare_band (band)
 # output_midi (notelist, mindelta)
   output_svg (notelist, mindelta)
