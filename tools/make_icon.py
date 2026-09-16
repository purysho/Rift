from pathlib import Path
from PIL import Image, ImageDraw
BG='#09110f'; A='#79e6af'; B='#d7f6e6'
def rgb(h):
    h=h.lstrip('#'); return tuple(int(h[i:i+2],16) for i in (0,2,4))+(255,)
img=Image.new("RGBA",(256,256),rgb(BG)); d=ImageDraw.Draw(img); A=rgb(A); B=rgb(B)
d.line([(42,54),(112,54),(84,92),(122,128),(84,166),(112,202),(42,202)],fill=A,width=18,joint='curve'); d.line([(214,54),(144,54),(172,92),(134,128),(172,166),(144,202),(214,202)],fill=B,width=18,joint='curve'); d.line([(128,42),(128,214)],fill=(185,255,220,190),width=5)
out=Path(__file__).resolve().parents[1]/"assets"/"icon.ico"
out.parent.mkdir(exist_ok=True)
img.save(out,format="ICO",sizes=[(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)])
print(out)