#!/usr/bin/env python3
# (c) 2011-2017 Simon Budig <simon@budig.de>

import sys, struct, math, getopt
import cairo

# Mensch macht bequem ca. 120-180 UPM.

delta_ticks = 0

models = {
   # https://www.spieluhr.de/Artikel/varAussehen.asp?ArtikelNr=4905
   "china15" : {
      # Gis Dur? SRSLY?
      "lowest"   : 68,  # G#4 / g#'
      "notes"    : [
                     #                       G#4, A#4,
                                               0,   2,
                     # C5, C#5, D#5, F5, G5, G#5, A#5,
                        4,   5,   7,  9, 11,  12,  14,
                     # C6, C#6, D#6, F6, G6, G#6,
                       16,  17,  19, 21, 23,  24 ],
      "program"  :  1,
      "height"   : 41.0,
      "offset"   :  6.0,
      "distance" :  2.0,
      "diameter" :  1.8,
      "step"     :  8.0,
      "speed"    :  300./49,     # mm/U
   },
   # https://www.spieluhr.de/Artikel/varAussehen.asp?ArtikelNr=4972
   "sankyo20" : {
      "lowest"   : 60,  # C4 / c'
      "notes"    : [ # C4, D4, E4, F4, G4, A4, B4,
                        0,  2,  4,  5,  7,  9, 11,
                     # C5, D5, E5, F5, G5, A5, B5,
                       12, 14, 16, 17, 19, 21, 23,
                     # C6, D6, E6, F6, G6, A6,
                       24, 26, 28, 29, 31, 33 ],
      "program"  :  2,
      "height"   : 70.0,
      "offset"   :  6.5,
      "distance" :  3.0,
      "diameter" :  2.4,
      "step"     :  7.0,
      "speed"    :  300./53,
   },
   # http://www.njdean.co.uk/musical-movements-mbm30hp.htm
   # http://www.mmdigest.com/Gallery/Sounds/mg_Teamola30n.html
   # https://www.spieluhr.de/Artikel/varAussehen.asp?ArtikelNr=5984
   "china30" : {
      "lowest"   : 53,  # F3 / f
      "notes"    : [
                     #                       F3, F#3, G3, G#3, A3, A#3, B3,
                                              0,       2,
                     # C4, C#4, D4, D#4, E4, F4, F#4, G4, G#4, A4, A#4, B4,
                        7,       9,      11, 12,      14,      16, 17,  18,
                     # C5, C#5, D5, D#5, E5, F5, F#5, G5, G#5, A5, A#5, B5,
                       19,  20, 21,  22, 23, 24,  25, 26,  27, 28, 29,  30,
                     # C6, C#6, D6, D#6, E6, F6, F#6, G6, G#6, A6
                       31,  32, 33,  34, 35, 36,      38,      40
                     ],
      "program"  :  3,
      "height"   : 70.0,
      "offset"   :  6.0,
      "distance" :  2.0,
      "diameter" :  1.8,
      "step"     :  7.25,
      "speed"    :  300./45.5,
   },
   # http://www.leturlutain.fr/index.php?item=33-notes-sankyo-music-box&action=article&group_id=10000033&aid=5796&lang=EN
   # http://www.spieluhr.de/Artikel/varAussehen.asp?ArtikelNr=5663
   "sankyo33" : {
      "lowest"   : 60,  # C4 / c'
      "notes"    : [ # C4, C#4  D4, D#4, E4, F4, F#4, G4, G#4, A4, A#4, B4,
                        0,       2,   3,  4,  5,   6,  7,   8,  9,  10, 11,
                     # C5, C#5, D5, D#5, E5, F5, F#5, G5, G#5, A5, A#5. B5,
                       12,  13, 14,  15, 16, 17,  18, 19,  20, 21,  22, 23,
                     # C6, C#6, D6, D#6, E6, F6, F#6, G6, G#6, A6,
                       24,  25, 26,  27, 28, 29,  30, 31,  32, 33 ],
      "program"  :  4,
      "height"   : 70.0,
      "offset"   :  5.3,
      "distance" :  1.8,
      "diameter" :  1.7,
      "step"     :  8.0,
      "speed"    :  600./106,
   }
}


def output_file (model, filename, is_pdf, notelist, mindelta):
   pwidth  = 1200.0 - 20
   pheight = 500.0 - 20
   pborder = 10    - 8
   height  = model["height"]
   offset  = model["offset"]
   radius  = model["diameter"] / 2
   dist    = model["distance"]
   step    = model["step"] / mindelta
   leadin  = 50.0
   leadout = 50.0

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
   print (splits)

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
      cr.set_line_width (0.4)
      # cr.rectangle (pborder, y0, x1 - x0, y1 - y0)
      cr.move_to (pborder, y0)
      cr.line_to (pborder, y1)
      cr.move_to (pborder + x1 - x0, y0)
      cr.line_to (pborder + x1 - x0, y1)
      cr.stroke ()

      if 0:
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
      cr.set_line_width (0.4)
      border_end = pborder;
      while holes and holes[0][0] < x1:
         x, y = holes.pop (0)
         cr.new_sub_path ()
         cr.arc (x - x0 + pborder, y + y0, radius, 0.0*math.pi, 0.5*math.pi)
         cr.arc (x - x0 + pborder, y + y0, radius, 0.5*math.pi, 1.0*math.pi)
         cr.arc (x - x0 + pborder, y + y0, radius, 1.0*math.pi, 1.5*math.pi)
         cr.arc (x - x0 + pborder, y + y0, radius, 1.5*math.pi, 2.0*math.pi)
         cr.close_path ()
         if x - x0 + pborder - border_end >= 50:
            cr.move_to (border_end, y0)
            cr.line_to (x - x0 + pborder, y0)
            cr.move_to (border_end, y1)
            cr.line_to (x - x0 + pborder, y1)
            cr.new_sub_path ()
            border_end = x - x0 + pborder

      if border_end < x1:
         cr.move_to (border_end, y0)
         cr.line_to (x1 - x0 + pborder, y0)
         cr.move_to (border_end, y1)
         cr.line_to (x1 - x0 + pborder, y1)
         cr.new_sub_path ()

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
   eventdata = b''
   # program select
   eventdata += bytes ([0x00, 0xc0, model["program"]])

   for t, i, on in events:
      dt = t - last_time
      if (dt >> 21):
         eventdata += bytes ([0x80 | ((dt >> 21) & 0x7f)])
      if (dt >> 14):
         eventdata += bytes ([0x80 | ((dt >> 14) & 0x7f)])
      if (dt >> 7):
         eventdata += bytes ([0x80 | ((dt >>  7) & 0x7f)])

      eventdata += bytes ([0x00 | ((dt >> 0) & 0x7f)])
      if on:
         eventdata += bytes ([0x90, i, 127])
      else:
         eventdata += bytes ([0x80, i, 127])
      last_time += dt

   eventdata += b"\x00\xFF\x2F\x00"

   outfile = open (filename, "wb")
   outfile.write (b'MThd' + struct.pack (">ihhh", 6, 0, 1, delta_ticks))
   outfile.write (b'MTrk' + struct.pack (">i", len (eventdata)))
   outfile.write (eventdata)
   outfile.close ()



class Note (object):
   def __init__ (self, note, ticks, channel, track):
      self.note = note
      self.ticks = ticks
      self.channel = channel
      self.track = track
      self.filtered = set()


   def __repr__ (self):
      return "Note (%s, %d, %d, %d)" % (self.note, self.ticks, self.channel, self.track)


class PianoRoll (object):
   def __init__ (self, notes=[]):
      self.notes = notes
      self.transpose = [0]


   def __repr__ (self):
      return "PianoRoll (%r)" % (self.notes)


   def add (self, note):
      self.notes.append (note)


   def get_compat_band (self, model):
      self.notes.sort (key=lambda x: x.ticks)

      notes = [n + model["lowest"] for n in model["notes"]]
      band = [[] for i in range (len(notes))]
      for i in range (len (notes)):
         source_notes = [notes[i]]
         n = notes[i] - 12
         while n >= 0 and n not in notes:
            source_notes.append (n)
            n -= 12
         n = notes[i] + 12
         while n <= 127 and  n not in notes:
            source_notes.append (n)
            n += 12

         band[i] = [n.ticks for n in self.notes
                        if n.note + self.transpose[n.track % len (self.transpose)] in source_notes
                        if not n.filtered]
         band[i] = sorted (list (set (band[i])))

      return band


   def min_repetition (self):
      self.notes.sort (key=lambda x: x.ticks)
      self.notes.sort (key=lambda x: x.note)
      mindelta = sys.maxsize
      n0 = self.notes[0]
      for n in self.notes[1:]:
         d = n.ticks - n0.ticks
         # notes at the same tick are considered identical
         if n.note == n0.note and d > 0 and d < mindelta:
            mindelta = n.ticks - n0.ticks
         n0 = n

      if mindelta == sys.maxsize:
         mindelta = 1000

      return mindelta


   def find_transpose (self, available_notes,
                       allow_octaves=True, allow_halftones=True):
      transpose = 0
      transpose_error = sys.maxsize

      highest = max ([n.note for n in self.notes])
      lowest  = min ([n.note for n in self.notes])

      notecount = [len ([n for n in self.notes if n.note == i])
                   for i in range (128)]

      for trans in range (min (available_notes) - highest - 1,
                          max (available_notes) - lowest + 2):
         if not allow_halftones and trans % 12 != 0:
            continue

         if not allow_halftones and not allow_octaves and trans % 12 == 0:
            continue

         errcount = 0
         for i in range (128):
            if (i+trans) not in available_notes:
               errcount += notecount[i]
         if errcount < transpose_error or (errcount == transpose_error and abs(trans) < abs (transpose)):
            transpose_error = errcount
            transpose = trans

      print ("transposing by %d octaves and %d halftones" % (transpose / 12, transpose % 12), file=sys.stderr)
      print ("    --> %d notes not playable" % (transpose_error), file=sys.stderr)

      return transpose


   def filter_repetition (self, delta):
      self.notes.sort (key=lambda x: x.ticks)
      self.notes.sort (key=lambda x: x.note)
      count = 0
      n0 = self.notes[0]
      for n1 in self.notes[1:]:
         if n1.note == n0.note:
            d = n1.ticks - n0.ticks
            if d < delta:
               n1.filtered.add ("delta")
               count += 1
            else:
               n1.filtered.discard ("delta")
               n0 = n1
         else:
            n0 = n1
            n0.filtered.discard ("delta")

      return count



class MidiImporter (object):
   def __init__ (self, target):
      self.target = target
      self.timediv = 0
      self.num_tracks = 0
      self.cur_program = -1


   def import_event (self, ticks, track, eventdata):
      cur_program = -1;
      mc = eventdata[0] >> 4
      ch = eventdata[0] & 0x0f

      # fix up noteon with velocity = 0 to noteoff.
      if mc == 0x09 and eventdata[2] == 0:
         mc = 0x08

      if mc == 0x08:
         pass
         # print >>sys.stderr, ticks, ": noteoff"
      elif mc == 0x09:
         # print >>sys.stderr, ticks, ": noteon (%d)" % (eventdata[0] & 0x0f), eventdata[1], eventdata[2]
         if self.cur_program != 127: # exclude percussion track
            n = Note (eventdata[1], ticks, ch, track)
            self.target.add (n)
      elif mc == 0x0b:
         # print >>sys.stderr, ticks, ": controller", eventdata[1]
         pass
      elif mc == 0x0c:
         print (ticks, ": program change", eventdata[1], file=sys.stderr)
         self.cur_program = eventdata[1]
         pass
      elif mc == 0x0d:
         # print >>sys.stderr, ticks, ": aftertouch", eventdata[1]
         pass
      elif mc == 0x0e:
         # print >>sys.stderr, ticks, ": pitch bend"
         pass
      else:
         print ("ticks: %d, event %r" % (ticks, eventdata), file=sys.stderr)
         pass


   def import_ticked_events (self, track, eventdata):
      ticks = 0
      mc = None
      t = eventdata
      while t:
         dt = 0
         while t[0] & 0x80:
            dt = (dt + (t[0] & 0x7f)) << 7
            t = t[1:]
         dt += t[0]

         t = t[1:]

         if t[0] & 0x80:
            mc = t[0]
            t = t[1:]

         if mc >> 4 in [0x08, 0x09, 0x0a, 0x0b, 0x0e]:
            command = bytes ([mc, t[0], t[1]])
            t = t[2:]
         elif mc >> 4 in [0x0c, 0x0d]:
            command = bytes ([mc, t[0]])
            t = t[1:]
         elif mc in [0xf8, 0xfa, 0xfb, 0xfc]:
            command = bytes ([mc])
         elif mc == 0xff:
            # meta event
            type = t[0]
            t = t[1:]
            command = bytes ([mc, type])
            l = 0
            while t[0] & 0x80:
               command += bytes ([t[0]])
               l = (l + (t[0] & 0x7f)) << 7
               t = t[1:]
            l += t[0]
            command += t[:l+1]
            t = t[l+1:]
         elif mc in [0xf0, 0xf7]:
            command = bytes ([mc])
            l = 0
            while t[0] & 0x80:
               command += bytes ([t[0]])
               l = (l + (t[0] & 0x7f)) << 7
               t = t[1:]
            l += t[0]
            command += t[:l+1]
            t = t[l+1:]
         else:
            raise Exception ('unknown MIDI event: %d' % t[0])

         ticks += dt
         self.import_event (ticks, track, command)


   def import_chunk (self, chunkname, chunkdata, ignoretracks):
      if self.timediv == 0 and chunkname != b'MThd':
         raise Exception ("first chunk is not MThd")

      if chunkname == b'MThd':
         global delta_ticks

         if self.timediv != 0:
            raise Exception ("multiple MThd chunks")

         if len (chunkdata) != 6:
            raise Exception ("invalid MThd chunk")
         mtype, n_tracks, delta_ticks = struct.unpack (">hhh", chunkdata)
         self.timediv = delta_ticks

         print ("type: %d, n_tracks: %d, delta_ticks: %d" % (mtype, n_tracks, delta_ticks), file=sys.stderr)

      elif chunkname == b'MTrk':
         if self.num_tracks not in ignoretracks:
            self.import_ticked_events (self.num_tracks, chunkdata)
         self.num_tracks += 1


   def import_file (self, filename, ignoretracks):
      t = open (filename, "rb").read()

      while t:
         if len (t) < 8:
            print ("%d bytes remaining at end of MIDI file" % len(t), file=sys.stderr)
            break
         chunkname = t[:4]
         chunklen = struct.unpack (">I", t[4:8])[0]
         if len (t) < 8+chunklen:
            raise Exception ("Not enough bytes in MIDI file")
         chunkdata = t[8:8+chunklen]

         print (chunkname, chunklen, file=sys.stderr)
         self.import_chunk (chunkname, chunkdata, ignoretracks)
         t = t[8+chunklen:]
      print ("%d tracks" % self.num_tracks)



def usage ():
   print ("Usage: %s [arguments] <midi-file>" % sys.argv[0], file=sys.stderr)
   print ("  -h, --help: show usage", file=sys.stderr)
   print ("  -t, --transpose=number: transpose by n halftones (avoid auto)", file=sys.stderr)
   print ("  -f, --filter=number: ignore note-repetition faster than <ticks>", file=sys.stderr)
   print ("  -b, --box=type: music box type: sankyo15, sankyo20, teanola30, sankyo33", file=sys.stderr)
   print ("  -m, --midi=filename: output midi file name (omit if not wanted)", file=sys.stderr)
   print ("  -p, --pdf=filename: output pdf file name (omit if not wanted)", file=sys.stderr)
   print ("  -s, --svg=filename: output svg file name (omit if not wanted)", file=sys.stderr)



if __name__=='__main__':
   try:
      opts, args = getopt.getopt (sys.argv[1:],
                                  "ht:f:i:b:m:s:p:",
                                  ["help", "transpose=",
                                  "filter=", "ignore=", "box=",
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
   filter = 1
   boxtype = "sankyo20"
   transpose = None
   ignoretracks = []

   for o, a in opts:
      if o in ("-h", "--help"):
         usage()
         sys.exit()
      elif o in ("-t", "--transpose"):
         transpose = [ int (t) for t in a.split (",") ]
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
      elif o in ("-i", "--ignore"):
         ignoretracks = [ int (t) for t in a.split (",") ]
      else:
         assert False, "unhandled option"

   model = models.get (boxtype, None)
   if not model:
      print ("Boxtype unknown. Available boxtypes are:", file=sys.stderr)
      ms = list(models.keys ())
      ms.sort ()
      print ("  * %s" % "\n  * ".join (ms), file=sys.stderr)
      sys.exit (2)

   roll = PianoRoll()
   mi = MidiImporter (roll)
   mi.import_file (args[0], ignoretracks)

   print (roll.min_repetition ())
   roll.filter_repetition (filter)

   if transpose == None:
      roll.transpose = [ roll.find_transpose ([model["lowest"] + i for i in model["notes"]]) ]
   else:
      roll.transpose = transpose

   notelist = roll.get_compat_band (model)
   mindelta = roll.min_repetition ()

   if midifile:
      output_midi (model, midifile, notelist, mindelta)

   if pdffile:
      output_file (model, pdffile, True, notelist, mindelta)
   if svgfile:
      output_file (model, svgfile, False, notelist, mindelta)
