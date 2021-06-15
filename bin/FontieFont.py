import os
import shutil
import glob
import uuid
import fontforge
import re
import traceback

from FontieException import FontieException

FONT_ROOT = "/tmp"
FONT_PREFIX = "font_"
EOTFAST = "WINEDLLOVERRIDES=\"t2embed.dll=n\" wine /opt/eotfast/EOTFAST-1.EXE"
SCOUR = "scour --indent=none --remove-metadata --quiet"
TTFAUTOHINT = "ttfautohint --windows-compatibility"
WOFF2 = "/opt/woff2/woff2_compress"
FIXLOOKUPS = "/opt/fontie/helper/fix_lookups.ff"

class FontieFont:
    def __init__(self, file=None, id=None):
        self._font = None
        self._properties = None
        self._original = None
        self._tmppath = {}
        self.id = None
        self.path = None
        self.orig = None
        self.cssname = None
        if file != None:
            self.create(file)
        elif id != None:
            self.open(id)
        else:
            raise Exception("FontieFont constructor requires either file or id");

    @property
    def font(self):
        try:
            if self._font == None:
                self._font = fontforge.open(self.path)
            return self._font
        except Exception as e:
            raise FontieException(400, "unable to open font", e)

    @property
    def properties(self):
        if self._properties == None:
            tmppath = self._get_tmppath("svg")
            with open(tmppath, 'r') as svgfile:
                svghead = svgfile.read(1024)
            stylematch = re.compile('font-style="([^"]+)"').search(svghead)
            stretchmatch = re.compile('font-stretch="([^"]+)"').search(svghead)
            weightmatch = re.compile('font-weight="([^"]+)"').search(svghead)
            rangematch = re.compile('unicode-range="([^"]+)"').search(svghead)
            self._properties = {
                'style': stylematch.group(1) if stylematch else 'normal',
                'stretch': stretchmatch.group(1) if stretchmatch else 'normal',
                'weight': weightmatch.group(1) if weightmatch else 'normal',
                'range': rangematch.group(1) if rangematch else 'U+0-10FFFF'
            }
        return self._properties
 
    @property
    def original(self):
        if self._properties == None:
            font = fontforge.open(self.orig)
            self._original = {
                'fontname': font.fontname,
                'fullname': font.fullname,
                'familyname': font.familyname
            }
            font.close()
        return self._original

    def _close_font(self, strict=True):
        if self._font != None:
            try:
                self._font.close()
                self._font = None
            except:
                if strict: raise
                traceback.print_exc()

    def _has_letter_o(self):
        try:
            font[0x6f]
            return True
        except:
            return False

    def _get_tmppath(self, format):
        if not format in self._tmppath:
            tmppath = "%s.%s" % (self.path, format)
            if (format == "sfd"):
                self.font.save(tmppath)
            else:
                self.font.generate(tmppath)
            self._tmppath[format] = tmppath
        return self._tmppath[format]

    def _clear_tmppath(self, strict=True):
        for format in list(self._tmppath):
            try:
                os.remove(self._tmppath[format])
                del self._tmppath[format]
            except:
                if strict: raise
                traceback.print_exc()

    def create(self, file):
        id = "%s%s" % (FONT_PREFIX, uuid.uuid4())
        path = os.path.join(FONT_ROOT, id)
        orig = "%s_orignal" % path
        try:
            with open(path, 'wb', 1024) as f:
                chunk = file.read(1024)
                while chunk:
                    f.write(chunk)
                    chunk = file.read(1024)
        except Exception as e:
            raise FontieException(413, "unable to write font", e)
        shutil.copy(path, orig)
        self.id = id
        self.path = path
        self.orig = orig

    def open(self, id):
        path = os.path.join(FONT_ROOT, id)
        orig = os.path.abspath("%s_orignal" % path)
        if not os.path.exists(orig):
            raise FontieException(404, "font original does not exist")
        shutil.copy(orig, path)
        self.id = id
        self.path = path
        self.orig = orig
        self._clear_tmppath()

    def close(self, strict=True):
        self._close_font(strict)
        self._clear_tmppath(strict)
        self._properties = None
        if self.path:
            try:
                os.remove(self.path)
            except:
                if strict: raise
                traceback.print_exc()
            self.path = None

    def destroy(self, strict=True):
        self.close(strict)
        if self.orig:
            try:
                os.remove(self.orig)
            except:
                if strict: raise
                traceback.print_exc()
            self.orig = None

    def subset(self, ranges):
        unicodes = []
        for r in ranges:
            m = re.compile('([\dABCDEF]+)(?:-([\dABCDEF]+))?').search(r)
            if m.group(1):
                if m.group(2):
                    unicodes += range(int(m.group(1), 16), int(m.group(2), 16)) 
                else:
                    unicodes += [int(m.group(1), 16)]
        for u in unicodes:
            try:
                if self.font[u].isWorthOutputting():
                    self.font.selection.select(('more', 'unicode'), u)
                    for r in self.font[u].references:
                        self.font.selection.select(('more',), r[0])
            except:
                #print("Selecting glyph u+%04x failed" % u)
                pass
        self.font.selection.invert()
        for glyph in self.font.selection.byGlyphs:
            glyph.removePosSub("*")
            self.font.removeGlyph(glyph)
        self.font.selection.none()
        self._clear_tmppath()
        self._properties = None

    def fix_lookups(self):
        tmppath = self._get_tmppath("sfd")
        self._close_font()
        r = os.system("%s \"%s\" \"%s\"" % (FIXLOOKUPS, tmppath, self.path))
        if r != 0:
            raise Exception("fixlookups error %d" % r)
        self._clear_tmppath()
        #for name in self.font:
        #   lookups = self.font[name].getPosSub("*")
        #    self.font[name].removePosSub("*")
        #    for lookup in lookups:
        #        valid = True
        #        if lookup[1] in ["Pair", "Substitution"]:
        #            print(lookup[2])
        #        elif lookup[1] in ["Multiple", "Alternate"]:
        #            print(lookup)
        #        elif lookup[1] in ["Ligature"]:
        #            print(lookup)
        #        else:
        #            raise Exception("Unknown lookup type")
        #        if valid:
        #            print(lookup)
        #            lookup = list(lookup)
        #            del lookup[1]
        #            #self.font[name].addPosSub(*lookup)
        #            self.font[name].addPosSub("'ss06' Style Set 6 lookup 28 subtable", "ampersant.alt", 2)

    def fix_name(self):
        fullname_match = re.compile("^(%s)\\W?(.*)" % self.font.familyname).search(self.font.fullname)
        fontname_match = re.compile("^(\w)+(?:-(\S+))?$").search(self.font.fontname)
        if fullname_match:
            family = fullname_match.group(1)
            style = fullname_match.group(2)
        elif fontname_match:
            family = fontname_match.group(1)
            style = fontname_match.group(2)
        else:
            raise FontieException(400, 'unable to fix font names');
        # NOTE The fontname should have 29 chars at max, but we ignore this
        #      here, since there is not intelligend way to shorten a generated
        #      fontname, which is too long due to the length of the fullname.
        if not fontname_match:
            font = family
            if style:
                font += "-" + style
            font.replace(" ","")
        else:
            font = self.font.fontname
        if not fullname_match:
            full = family
            if style:
                full += " " + style
        else:
            full = self.font.fullname
        self.font.fontname = 'Fontie-Dummy'
        self.font.fullname = 'Fontie Dummy'
        self.font.familyname = 'Fontie'
        self.font.fontname = font
        self.font.fullname = full
        self.font.familyname = family

    def fix_glyphs(self):
        # NOTE Working fix orders: RDOEr, RDOemr, RDOEem
        #self.font.em = 2048 # improves hinting, but changes glyps
        self.font.selection.all()
        self.font.correctDirection()
        self.font.removeOverlap()
        self.font.addExtrema() # does not work with em & round
        self.font.round() # does not work with em & addExtrema
        # NOTE Some extra cleanup
        #self.font.canonicalContours()
        #self.font.canonicalStart()
        #self.font.simplify() # might fix or change a glyp, does not work with canonicalStart/Contours
        self._clear_tmppath()
        self.font.selection.none()

    def fix_references(self):
        self.font.selection.all()
        self.font.correctReferences()
        self._clear_tmppath()
        self.font.selection.none()

    def fix_metrics(self, strategy="microsoft"):
        self.font.os2_winascent += self.font.os2_winascent_add
        self.font.os2_windescent += self.font.os2_windescent_add
        self.font.os2_typoascent += self.font.os2_typoascent_add
        self.font.os2_typodescent += self.font.os2_typodescent_add
        self.font.hhea_ascent += self.font.hhea_ascent_add
        self.font.hhea_descent += self.font.hhea_descent_add
        self.font.os2_winascent_add = 0
        self.font.os2_windescent_add = 0
        self.font.os2_typoascent_add = 0
        self.font.os2_typoascent_add = 0
        self.font.hhea_ascent_add = 0
        self.font.hhea_descent_add = 0
        # REF https://github.com/googlefonts/gf-docs/blob/master/VerticalMetricsRecommendations.md
        if strategy == "google":
            self.font.hhea_ascent = self.font.os2_winascent
            self.font.hhea_descent = -self.font.os2_windescent
            self.font.hhea_linegap = 0
            self.font.os2_typoascent = self.font.os2_winascent
            self.font.os2_typodescent = -self.font.os2_windescent
            self.font.os2_typolinegap = 0
        # REF https://www.glyphsapp.com/tutorials/vertical-metrics
        elif strategy == "adobe":
            self.font.os2_typolinegap = self.font.os2_winascent + self.font.os2_windescent - self.font.em
            self.font.hhea_ascent = self.font.os2_typoascent
            self.font.hhea_descent = self.font.os2_typodescent
            self.font.hhea_linegap = self.font.os2_typolinegap
        elif strategy == "microsoft":
            self.font.hhea_ascent = self.font.os2_winascent
            self.font.hhea_descent = -self.font.os2_windescent
            self.font.hhea_linegap = 0
            self.font.os2_typolinegap = self.font.os2_winascent + self.font.os2_windescent - self.font.em
        elif strategy == "webfont":
            self.font.hhea_ascent = round(self.font.em * self.font.os2_winascent / (self.font.os2_winascent + self.font.os2_windescent))
            self.font.hhea_descent = self.font.os2_typoascent - self.font.em
            self.font.hhea_linegap = self.font.os2_winascent + self.font.os2_windescent - self.font.em
            self.font.os2_typoascent = self.font.hhea_ascent
            self.font.os2_typodescent = self.font.hhea_descent
            self.font.os2_typolinegap = self.font.hhea_linegap
        else:
            raise FontieException(400, "unknown vertical metrics fixing strategy")
        self._clear_tmppath()
        #print(self.font.fullname)
        #print("em                  %s" % self.font.em)
        #print("hhea_ascent         %s" % self.font.hhea_ascent)
        #print("hhea_ascent_add     %s" % self.font.hhea_ascent_add)
        #print("hhea_descent        %s" % self.font.hhea_descent)
        #print("hhea_descent_add    %s" % self.font.hhea_descent_add)
        #print("hhea_linegap        %s" % self.font.hhea_linegap)
        #print("os2_winascent       %s" % self.font.os2_winascent)
        #print("os2_winascent_add   %s" % self.font.os2_winascent_add)
        #print("os2_windescent      %s" % self.font.os2_windescent)
        #print("os2_windescent_add  %s" % self.font.os2_windescent_add)
        #print("os2_typoascent      %s" % self.font.os2_typoascent)
        #print("os2_typoascent_add  %s" % self.font.os2_typoascent_add)
        #print("os2_typodescent     %s" % self.font.os2_typodescent)
        #print("os2_typodescent_add %s" % self.font.os2_typodescent_add)
        #print("os2_typolinegap     %s" % self.font.os2_typolinegap)

    def hint(self, method):
        ttfautohint = TTFAUTOHINT
        if method == "gdi":
            ttfautohint += " --strong-stem-width=G"
        elif method == "directwrite":
            ttfautohint += " --strong-stem-width=D"
        elif method == "grayscale":
            ttfautohint += " --strong-stem-width=g"
        elif method == "nohint":
            ttfautohint += " --dehint"
        else:
            raise FontieException(400, "unknown hinting method")
        if not self._has_letter_o():
            ttfautohint += " --symbol"
        tmppath = self._get_tmppath("ttf")
        self._close_font()
        r = os.system("%s \"%s\" \"%s\"" % (ttfautohint, tmppath, self.path))
        if r != 0:
            raise Exception("ttfautohint error %d" % r)
        self._clear_tmppath()

    def export_ttf(self, outpath):
        tmppath = self._get_tmppath("ttf")
        shutil.copyfile(tmppath, outpath)

    def export_otf(self, outpath):
        tmppath = self._get_tmppath("otf")
        shutil.copyfile(tmppath, outpath)

    def export_woff(self, outpath):
        tmppath = self._get_tmppath("woff")
        shutil.copyfile(tmppath, outpath)

    def export_woff2(self, outpath):
        woff2path = "%s.%s" % (self.path, "woff2")
        tmppath = self._get_tmppath("ttf")
        r = os.system("%s \"%s\"" % (WOFF2, tmppath))
        if r != 0:
            raise Exception("woff2 error %d" % r)
        shutil.move(woff2path, outpath)

    def export_eot(self, outpath):
        tmppath = self._get_tmppath("ttf")
        r = os.system("%s \"%s\" \"%s\"" % (EOTFAST, tmppath, outpath))
        if r != 0:
            raise Exception("eotfast error %d" % r)

    def export_svg(self, outpath):
        tmppath = self._get_tmppath("svg")
        r = os.system("%s -i \"%s\" -o \"%s\"" % (SCOUR, tmppath, outpath))
        if r != 0:
            raise Exception("scour error %d" % r)
