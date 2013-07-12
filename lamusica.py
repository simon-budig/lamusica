#!/usr/bin/env python
import sys, struct, math, getopt
import cairo

band = None
trktime = 0

cur_track = 0
tracks = range (1024)

delta_ticks = 0

models = {
   "sankyo15" : {
      # Gis Dur? SRSLY?
      "lowest"   : 56,
      "notes"    : [ #  C,  D,  E,  F,  G,  A,  B,
                        0,  2,  4,  5,  7,  9, 11,
                     # C1, D1, E1, F1, G1, A1, B1,
                       12, 14, 16, 17, 19, 21, 23,
                     # C2,
                       24 ],
      "height"   : 41.0,
      "offset"   :  6.0,
      "distance" :  2.0,
      "diameter" :  1.8,
      "step"     :  8.0,
   },
   "sankyo20" : {
      "lowest"   : 48,
      "notes"    : [ #  C,  D,  E,  F,  G,  A,  B,
                        0,  2,  4,  5,  7,  9, 11,
                     # C1, D1, E1, F1, G1, A1, B1,
                       12, 14, 16, 17, 19, 21, 23,
                     # C2, D2, E2, F2, G2, A2,
                       24, 26, 28, 29, 31, 33 ],
      "height"   : 70.0,
      "offset"   :  6.5,
      "distance" :  3.0,
      "diameter" :  2.4,
      "step"     :  7.0,
   },
   # http://www.njdean.co.uk/musical-movements-mbm30hp.htm
   # http://www.mmdigest.com/Gallery/Sounds/mg_Teamola30n.html
   "teanola30" : {
      "lowest"   : 41,
      "notes"    : [
                     #                        F,  F#,  G,  G#,  A,  A#,  B,
                                              0,       2,
                     # C1, C#1, D1, D#1, E1, F1, F#1, G1, G#1, A1, A#1, B1,
                        7,       9,      11, 12,      14,      16, 17,  18,
                     # C2, C#2, D2, D#2, E2, F2, F#2, G2, G#2, A2, A#2, B2,
                       19,  20, 21,  22, 23, 24,  25, 26,  27, 28, 29,  30,
                     # C3, C#3  D3, D#3, E3, F3,      G3,      A3
                       31,  32, 33,  34, 35, 36,      38,      40
                     ],
      "height"   : 70.0,
      "offset"   :  6.0,
      "distance" :  2.0,
      "diameter" :  1.8,
      "step"     :  8.0,
   },
   # http://www.spieluhr.de/Artikel/varAussehen.asp?ArtikelNr=5663
   "sankyo33" : {
      "lowest"   : 48,
      "notes"    : [ #  C,       D,  D#,  E,  F,  F#,  G,  F#,  A,  A#,  B,
                        0,       2,   3,  4,  5,   6,  7,   8,  9,  10, 11,
                     # C1, C#1  D1, D#1, E1, F1, F#1, G1, G#1, A1, A#1, B1,
                       12,  13, 14,  15, 16, 17,  18, 19,  20, 21,  22, 23,
                     # C2, C#2, D2, D#2, E2, F2, F#2, G2, G#2, A2,
                       24,  25, 26,  27, 28, 29,  30, 31,  32, 33 ],
      "height"   : 70.0,
      "offset"   :  5.3,
      "distance" :  1.8,
      "diameter" :  1.7,
      "step"     :  8.0,
   }
}



def handle_midi_event (dt, command):
   global band, trktime

   trktime += dt
   mc = ord (command[0]) >> 4

   if mc == 0x08:
      pass
      # print >>sys.stderr, dt, ": noteoff"
   elif mc == 0x09:
      # print >>sys.stderr, dt, ": noteon", ord (command[1])
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
      elif ord(mc) in [0xf0, 0xf7]:
         command = mc
         l = 0
         while ord (t[0]) & 0x80:
            command += t[0]
            l = (l + (ord (t[0]) & 0x7f)) << 7
            t = t[1:]
         l += ord (t[0])
         command += t[:l+1]
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
      else:
         print >>sys.stderr, "ignoring track %d\n" % cur_track
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



def prepare_band (model, band, fix_trans):
   print >>sys.stderr, "notes used:",
   lowest = 127
   highest = 0
   for i in range (128):
      if band[i]:
         lowest = min (lowest, i)
         highest = max (lowest, i)
         print >>sys.stderr, "%d (%d)," % (i, len (band[i])),
   print >>sys.stderr, "range: %d - %d\n" % (lowest, highest)
   print >>sys.stderr

   # fix up notes to correspond to midi notes
   notes = [ n + model["lowest"] for n in model["notes"] ]

   transpose = 0
   transpose_error = sys.maxint

   for trans in range (min (notes) - highest - 1,
                       max (notes) - lowest + 2):
      if fix_trans != None and trans % 12 != fix_trans % 12:
         continue

      errcount = 0
      for i in range (128):
         if band[i] and (i+trans) not in notes:
            errcount += len (band[i])
      if errcount < transpose_error:
         transpose_error = errcount
         transpose = trans
      
   print >>sys.stderr, "transposing by %d octaves and %d halftones" % (transpose / 12, transpose % 12)
   print >>sys.stderr, "    --> %d notes not playable" % (transpose_error)

   notelist = [[] for i in range (len(notes))]
   deltas = {}

   for i in range (len(notes)):
      cur_note = notes[i] - transpose
      notelist[i] += band [cur_note].keys ()

      cur_note = notes[i] - transpose - 12
      while cur_note >= 0 and cur_note + transpose not in notes:
         notelist[i] += band [cur_note].keys ()
      #  print >>sys.stderr, "adding to %d: %d (%d)" % (i, cur_note, len (band [cur_note].keys ()))
         cur_note -= 12

      cur_note = notes[i] - transpose + 12
      while cur_note < 128 and cur_note + transpose not in notes:
         notelist[i] += band [cur_note].keys ()
      #  print >>sys.stderr, "adding to %d: %d (%d)" % (i, cur_note, len (band [cur_note].keys ()))
         cur_note += 12

      notelist[i] = list (set (notelist[i]))
      notelist[i].sort()
      for j in range (len (notelist[i]) - 1):
         delta = notelist[i][j+1] - notelist[i][j]
         deltas[delta] = deltas.get (delta, 0) + 1

   ks = deltas.keys()
   ks.sort()

   for i in range (10):
      print >>sys.stderr, "delta: %d, (%d times)" % (ks[i], deltas[ks[i]])

   return notelist, ks[0]



def filter_band (model, notelist, filter):
   deltas = {}

   for i in range (len (notelist)):
      last_time = - 2 * filter
      newnotes = []
      for note in notelist[i]:
         if note - last_time >= filter:
            newnotes.append (note)
            last_time = note
      notelist[i] = newnotes
            
      for j in range (len (notelist[i]) - 1):
         delta = notelist[i][j+1] - notelist[i][j]
         deltas[delta] = deltas.get (delta, 0) + 1

   ks = deltas.keys()
   ks.sort()

   for i in range (10):
      print >>sys.stderr, "delta: %d, (%d times)" % (ks[i], deltas[ks[i]])

   return notelist, ks[0]



def output_file (model, filename, is_pdf, notelist, mindelta):
   pwidth  = 420.0
   pheight = 297.0
   pborder = 10
   height  = model["height"]
   offset  = model["offset"]
   radius  = model["diameter"] / 2
   dist    = model["distance"]
   step    = model["step"] / mindelta
   leadin  = 20.0
   leadout = 20.0

   alltimes = list (set (sum (notelist, [])))
   alltimes.sort ()
   start   = alltimes[0]
   end     = alltimes[-1]
   length  = int (end - start) * step + radius * 2 + leadin + leadout

   splits = [0.0]
   startpos = splits[0]
   breakpos = splits[0]

   for i in range (1, len(alltimes)):
      middlepos = leadin + (alltimes[i] + alltimes[i-1]) * step / 2
      if middlepos - startpos > pwidth - 2 * pborder:
         splits.append (breakpos)
         startpos = breakpos

      if (alltimes[i] - alltimes[i-1]) * step > radius * 4:
         breakpos = middlepos
         
   splits.append (length)
   print splits

   holes = [(leadin + (n - start) * step, i * dist + offset) for i in range (len (notelist)) for n in notelist[i]]
   holes.sort ()

   if is_pdf:
      surface = cairo.PDFSurface (filename,
                                  pwidth / 25.4 * 72,
                                  pheight / 25.4 * 72)
   else:
      # cairo svg cannot deal with multiple pages
      pheight = len (splits) * (height + pborder) - height + 1
      surface = cairo.SVGSurface (filename,
                                  pwidth / 25.4 * 72,
                                  pheight / 25.4 * 72)

   cr = cairo.Context (surface)

   cr.scale (2.83464, -2.83464)
   cr.translate (0.0, -pheight)
   cr.set_line_width (0.2)

   cr.move_to (4, 5)
   cr.line_to (7, 7)
   cr.line_to (7, 5.7)
   cr.line_to (17, 5.7)
   cr.line_to (17, 4.3)
   cr.line_to (7, 4.3)
   cr.line_to (7, 3)
   cr.close_path ()
   cr.fill ()

   y0 = pborder
   y1 = y0 + height

   x0 = splits.pop (0)
   while splits:
      x1 = splits.pop (0)
      cr.set_source_rgb (0, 0, 1)
      cr.rectangle (pborder, y0, x1 - x0, y1 - y0)
      cr.stroke ()

      cr.set_source_rgb (0.7, 0.7, 0.7)
      for i in range (len (model["notes"])):
         y = y0 + offset + i * dist
         cr.move_to (pborder, y)
         cr.line_to (pborder + x1 - x0, y)
         if model["notes"][i] % 12 in [0, 2, 4, 5, 7, 9, 11]:
            if model["notes"][i] % 12 == 0:
               cr.set_line_width (0.4)
            else:
               cr.set_line_width (0.2)
            cr.set_dash ([], 0)
         else:
            cr.set_line_width (0.2)
            cr.set_dash ([.5, 1], 0)
         cr.stroke ()

      cr.set_dash ([], 0)
      while holes and holes[0][0] < x1:
         x, y = holes.pop (0)
         cr.new_sub_path ()
         cr.arc (x - x0 + pborder, y + y0, radius, 0.0*math.pi, 0.5*math.pi)
         cr.arc (x - x0 + pborder, y + y0, radius, 0.5*math.pi, 1.0*math.pi)
         cr.arc (x - x0 + pborder, y + y0, radius, 1.0*math.pi, 1.5*math.pi)
         cr.arc (x - x0 + pborder, y + y0, radius, 1.5*math.pi, 2.0*math.pi)
         cr.close_path ()

      cr.set_source_rgb (1, 0, 0)
      cr.stroke ()

      x0 = x1
      y0 = y1 + pborder
      if y0 + height + pborder > pheight:
         y0 = pborder
         cr.show_page ()
      y1 = y0 + height

   del cr
   del surface



def output_midi (model, filename, notelist, mindelta):
   # fix up notes to correspond to midi notes
   notes = [ n + model["lowest"] for n in model["notes"] ]

   events = []
   for i in range (len (notelist)):
      events += [(t, notes[i], 1) for t in notelist[i]]
      # add events to shut off the notes
      events += [(t+mindelta, notes[i], 0) for t in notelist[i]]

   events.sort()

   last_time = 0
   eventdata = ""
   for t, i, on in events:
      dt = t - last_time
      if (dt >> 21):
         eventdata += chr (0x80 | ((dt >> 21) & 0x7f))
      if (dt >> 14):
         eventdata += chr (0x80 | ((dt >> 14) & 0x7f))
      if (dt >> 7):
         eventdata += chr (0x80 | ((dt >> 7) & 0x7f))

      eventdata += chr (0x00 | ((dt >> 0) & 0x7f))
      if on:
         eventdata += chr (0x90) + chr (i) + chr (127)
      else:
         eventdata += chr (0x80) + chr (i) + chr (127)
      last_time += dt

   eventdata += "\x00\xFF\x2F\x00"

   outfile = file (filename, "w")
   outfile.write ("MThd" + struct.pack (">ihhh", 6, 0, 1, delta_ticks))
   outfile.write ("MTrk" + struct.pack (">i", len (eventdata)))
   outfile.write (eventdata)
   outfile.close ()



def usage ():
   print >>sys.stderr, "Usage: %s [arguments] <midi-file>" % sys.argv[0]
   print >>sys.stderr, "  -h, --help: show usage"
   print >>sys.stderr, "  -t, --transpose=number: transpose by n halftones (avoid auto)"
   print >>sys.stderr, "  -f, --filter=number: ignore note-repetition faster than <ticks>"
   print >>sys.stderr, "  -b, --box=type: music box type: sankyo15, sankyo20, teanola30, sankyo33"
   print >>sys.stderr, "  -m, --midi=filename: output midi file name (omit if not wanted)"
   print >>sys.stderr, "  -p, --pdf=filename: output pdf file name (omit if not wanted)"
   print >>sys.stderr, "  -s, --svg=filename: output svg file name (omit if not wanted)"



if __name__=='__main__':
   try:
      opts, args = getopt.getopt (sys.argv[1:],
                                  "ht:f:b:m:s:p:",
                                  ["help", "transpose=",
                                  "filter=", "box=",
                                  "midi=", "svg=", "pdf="])
   except getopt.GetoptError as err:
      usage()
      sys.exit (2)

   if len (args) != 1:
      usage()
      sys.exit (2)

   midifile = None
   svgfile = None
   pdffile = None
   filter = 0
   boxtype = "sankyo20"
   transpose = None

   for o, a in opts:
      if o in ("-h", "--help"):
         usage()
         sys.exit()
      elif o in ("-t", "--transpose"):
         transpose = int (a)
      elif o in ("-f", "--filter"):
         filter = int (a)
      elif o in ("-b", "--box"):
         boxtype = a
      elif o in ("-m", "--midi"):
         midifile = a
      elif o in ("-s", "--svg"):
         svgfile = a
      elif o in ("-p", "--pdf"):
         pdffile = a
      else:
         assert False, "unhandled option"

   model = models.get (boxtype, None)
   if not model:
      print >>sys.stderr, "Boxtype unknown. Available boxtypes are:"
      ms = models.keys ()
      ms.sort ()
      print >>sys.stderr, "  * %s" % "\n  * ".join (ms)
      sys.exit (2)

   band = [ {} for i in range (128) ]
   trktime = 0
   tracks = [ 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15 ]

   read_midi (args[0])

   notelist, mindelta = prepare_band (model, band, transpose)

   if filter > 0:
      notelist, mindelta = filter_band (model, notelist, filter)
      
   if midifile:
      output_midi (model, midifile, notelist, mindelta)
   
   if pdffile:
      output_file (model, pdffile, True, notelist, mindelta)
   if svgfile:
      output_file (model, svgfile, False, notelist, mindelta)
