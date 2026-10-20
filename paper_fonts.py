"""Validate FreeType font faces and glyph coverage; fail clearly instead of producing tofu."""
from pathlib import Path
from matplotlib import pyplot as plt,font_manager,ft2font
from matplotlib.text import Text
R=Path(__file__).resolve().parent
FACES={}
def configure(lang):
 errors=[]
 if lang=='zh':
  # No redistributable font binaries are shipped. Use installed system CJK fonts.
  candidates=font_manager.findSystemFonts(fontext='ttf')+font_manager.findSystemFonts(fontext='otf')
  candidates.sort(key=lambda p:(0 if 'NotoSansCJK' in p.replace('-','') else 1,p))
  for p in candidates:
   try:
    face=ft2font.FT2Font(str(p))
    cmap=set(face.get_charmap())
    if all(ord(c) in cmap for c in '中文属性声明数字证明优化'): 
     font_manager.fontManager.addfont(str(p));FACES[lang]=(face.family_name,cmap);break
   except (RuntimeError,OSError,ValueError) as e:errors.append((str(p),str(e)))
  if lang not in FACES:raise RuntimeError('No system CJK font found. Install fonts-noto-cjk, then retry.')
 else:
  p=font_manager.findfont('DejaVu Sans');f=ft2font.FT2Font(p);FACES[lang]=(f.family_name,set(f.get_charmap()))
 plt.rcParams.update({'font.family':FACES[lang][0],'font.size':9,'axes.labelsize':10,'legend.fontsize':8,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42,'ps.fonttype':42,'svg.fonttype':'path','axes.unicode_minus':False,'savefig.bbox':'tight'})
def validate_text(fig,lang):
 chars={c for obj in fig.findobj(match=Text) for c in obj.get_text() if not c.isspace() and c not in '$\\^_{}'};missing=sorted(c for c in chars if ord(c) not in FACES[lang][1])
 if missing:raise RuntimeError('Font missing glyphs: '+''.join(missing)+'; install a complete CJK font into fonts/')
