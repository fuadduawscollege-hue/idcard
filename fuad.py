"""
আব্দুল ওদুদ শাহ ডিগ্রি কলেজ - শিক্ষক আইডি কার্ড
streamlit run fuad.py
"""
import streamlit as st
from PIL import Image, ImageDraw, ImageOps
import io, os
import uharfbuzz as hb
import freetype
import numpy as np

st.set_page_config(page_title="আইডি কার্ড", layout="centered")

FONT_DIR     = "fonts"
FONT_BOLD    = os.path.join(FONT_DIR, "NotoSansBengali-Bold.ttf")
FONT_REGULAR = os.path.join(FONT_DIR, "NotoSansBengali-Regular.ttf")
ASSET_DIR    = "assets"
DEFAULT_LOGO = os.path.join(ASSET_DIR, "logo.png")
DEFAULT_SIGN = os.path.join(ASSET_DIR, "signature.png")

NAVY    = (13,  40,  84)
NAVY2   = (22,  60, 120)
GOLD    = (196, 160,  50)
GOLD_LT = (218, 185,  80)
WHITE   = (255, 255, 255)
BODY_BG = (235, 237, 243)
DARK    = (20,  30,  55)

_FC = {}
def _check(p):
    if not os.path.exists(p): st.error(f"ফন্ট নেই: {p}"); st.stop()
def _hb(fp,sz):
    k=(fp,sz)
    if k in _FC: return _FC[k]
    _check(fp)
    hf=hb.Font(hb.Face(hb.Blob.from_file_path(fp))); hf.scale=(sz*64,sz*64)
    ft=freetype.Face(fp); ft.set_pixel_sizes(0,sz)
    _FC[k]=(hf,ft); return hf,ft
def _shape(text,fp,sz):
    hf,ft=_hb(fp,sz)
    b=hb.Buffer(); b.add_str(text); b.guess_segment_properties(); hb.shape(hf,b)
    px=py=0; gl=[]
    for i,p in zip(b.glyph_infos,b.glyph_positions):
        gl.append({"id":i.codepoint,"x":px+p.x_offset/64.,"y":py-p.y_offset/64.})
        px+=p.x_advance/64.; py-=p.y_advance/64.
    a=ft.size.ascender/64.; d=ft.size.descender/64.
    return gl,px,a-d,a
def rtext(text,fp,sz,col=(0,0,0,255)):
    if not text: return Image.new("RGBA",(1,1),(0,0,0,0)),0,0
    gl,tw,th,asc=_shape(text,fp,sz)
    _,ft=_hb(fp,sz)
    pad=4; W2=max(1,int(tw)+pad*2); H2=max(1,int(th)+pad*2)
    cv=np.zeros((H2,W2),dtype=np.uint8)
    for g in gl:
        ft.load_glyph(g["id"],freetype.FT_LOAD_RENDER|freetype.FT_LOAD_TARGET_NORMAL)
        bm=ft.glyph.bitmap
        if bm.width==0 or bm.rows==0: continue
        buf=np.array(bm.buffer,dtype=np.uint8).reshape(bm.rows,bm.width)
        dx=int(g["x"])+ft.glyph.bitmap_left+pad
        dy=int(pad+asc-ft.glyph.bitmap_top+g["y"])
        for r in range(bm.rows):
            ty_=dy+r
            if ty_<0 or ty_>=H2: continue
            for c in range(bm.width):
                tx_=dx+c
                if tx_<0 or tx_>=W2: continue
                v=buf[r,c]
                if v>cv[ty_,tx_]: cv[ty_,tx_]=v
    out=np.zeros((H2,W2,4),dtype=np.uint8)
    out[...,0]=col[0]; out[...,1]=col[1]; out[...,2]=col[2]; out[...,3]=cv
    return Image.fromarray(out,"RGBA"),W2,H2
def mtext(t,fp,sz):
    if not t: return 0,0
    _,w,h,_=_shape(t,fp,sz); return w,h
def fit_sz(t,fp,mw,s0,mn=8):
    s=s0
    while s>mn:
        if mtext(t,fp,s)[0]<=mw: return s
        s-=1
    return mn
def cwrap(t,fp,sz,mw):
    ww=t.split(" "); lines=[]; cur=""
    for w in ww:
        tr=(cur+" "+w).strip()
        if mtext(tr,fp,sz)[0]<=mw or not cur: cur=tr
        else: lines.append(cur); cur=w
    if cur: lines.append(cur)
    return lines
def ct(card,text,fp,sz,cx,y,fill=(0,0,0,255)):
    img,w,h=rtext(text,fp,sz,fill)
    card.paste(img,(int(cx-w/2),int(y)),img); return h
def strip_bg(img,thr=235):
    img=img.convert("RGBA")
    img.putdata([(r,g,b,0) if r>thr and g>thr and b>thr else (r,g,b,a)
                 for r,g,b,a in img.getdata()])
    return img
def gold_badge(card,cx,y,text,fp,sz):
    tw,th=mtext(text,fp,sz); px,py=26,10
    bw=int(tw)+px*2; bh=int(th)+py*2; bx=int(cx-bw/2)
    ImageDraw.Draw(card).rounded_rectangle([bx,int(y),bx+bw,int(y)+bh],
                                           radius=bh//2,fill=GOLD)
    ct(card,text,fp,sz,cx,y+py-1,fill=WHITE+(255,))
    return bh+8

def draw_blue_wave(card, W, H, BLUE_H, WAVE_D, BRAD):
    """RGB card এ সরাসরি নীল হেডার + wave আঁকো"""
    # নীল gradient ইমেজ
    arr=np.zeros((H,W,3),dtype=np.uint8)
    for i in range(min(BLUE_H+WAVE_D,H)):
        t=i/max(BLUE_H+WAVE_D-1,1)
        arr[i,:]=[int(NAVY[0]+(NAVY2[0]-NAVY[0])*t),
                  int(NAVY[1]+(NAVY2[1]-NAVY[1])*t),
                  int(NAVY[2]+(NAVY2[2]-NAVY[2])*t)]
    blue_img=Image.fromarray(arr,"RGB")
    # মাস্ক: উপরে rect + নিচে ellipse wave
    hm=Image.new("L",(W,H),0)
    dhm=ImageDraw.Draw(hm)
    dhm.rectangle([0,0,W,BLUE_H],fill=255)
    dhm.ellipse([-(W//3),BLUE_H-WAVE_D,W+W//3,BLUE_H+WAVE_D],fill=255)
    card.paste(blue_img,(0,0),hm)
    # সোনালি wave বর্ডার
    ImageDraw.Draw(card).arc([-(W//3),BLUE_H-WAVE_D,W+W//3,BLUE_H+WAVE_D],
                              start=0,end=180,fill=GOLD,width=4)

def draw_photo(card, PCX, PCY, PH, RING, photo_img):
    """গোলাকার ছবি আঁকো"""
    px0=PCX-PH//2; py0=PCY-PH//2
    draw=ImageDraw.Draw(card)
    draw.ellipse([px0-RING,py0-RING,px0+PH+RING,py0+PH+RING],fill=GOLD)
    draw.ellipse([px0-3,py0-3,px0+PH+3,py0+PH+3],fill=WHITE)
    if photo_img:
        ph=ImageOps.fit(photo_img.convert("RGB"),(PH,PH))
        mask=Image.new("L",(PH,PH),0)
        ImageDraw.Draw(mask).ellipse((0,0,PH,PH),fill=255)
        card.paste(ph,(px0,py0),mask)
    else:
        draw.ellipse([px0,py0,px0+PH,py0+PH],fill=NAVY)

def add_frame(final, BRAD, margin=24, border_w=4, border_col=NAVY):
    """কার্ডের চারপাশে সাদা মার্জিন + গোলাকার বর্ডার যোগ করে"""
    W,H=final.size
    W2,H2=W+margin*2,H+margin*2
    framed=Image.new("RGB",(W2,H2),WHITE)
    framed.paste(final,(margin,margin))
    draw=ImageDraw.Draw(framed)
    inset=border_w//2+2
    draw.rounded_rectangle([inset,inset,W2-1-inset,H2-1-inset],
                            radius=BRAD+margin//2,outline=border_col,width=border_w)
    return framed

# =========================================================================
# পোর্ট্রেট  638 × 1013 px
# =========================================================================
def make_portrait(name,designation,subject,photo_img,logo_img,sign_img,exam_title,center_code):
    W,H=638,1013; BRAD=28; PH=180; RING=12; BLUE_H=310; WAVE_D=80; pad=22

    card_mask=Image.new("L",(W,H),0)
    ImageDraw.Draw(card_mask).rounded_rectangle([0,0,W-1,H-1],radius=BRAD,fill=255)
    card=Image.new("RGB",(W,H),BODY_BG)
    draw_blue_wave(card,W,H,BLUE_H,WAVE_D,BRAD)

    cy=pad
    if logo_img:
        logo=logo_img.copy(); logo.thumbnail((52,52))
        card.paste(logo,(pad,cy+2),logo if logo.mode=="RGBA" else None)
    cn_sz=fit_sz("আব্দুল ওদুদ শাহ ডিগ্রি কলেজ",FONT_BOLD,W-2*pad-60,26)
    cy+=ct(card,"আব্দুল ওদুদ শাহ ডিগ্রি কলেজ",FONT_BOLD,cn_sz,W/2,cy,fill=WHITE+(255,))+5
    cy+=ct(card,"দামুড়হুদা, চুয়াডাঙ্গা",FONT_BOLD,15,W/2,cy,fill=GOLD_LT+(255,))+10
    ImageDraw.Draw(card).line([(pad,cy),(W-pad,cy)],fill=GOLD,width=2); cy+=10
    el=f"{exam_title}  |  কেন্দ্র: {center_code}"
    ex_sz=fit_sz(el,FONT_BOLD,W-2*pad,15)
    cy+=ct(card,el,FONT_BOLD,ex_sz,W/2,cy,fill=GOLD+(255,))+10
    lbl="শিক্ষক পরিচয়পত্র"
    lw,lh=mtext(lbl,FONT_BOLD,17); lp=18
    lbx0=int(W/2-lw/2-lp); lbx1=int(W/2+lw/2+lp); lby0=int(cy); lby1=int(cy+lh+12)
    draw=ImageDraw.Draw(card)
    draw.rounded_rectangle([lbx0,lby0,lbx1,lby1],radius=10,outline=GOLD_LT,width=2)
    ct(card,lbl,FONT_BOLD,17,W/2,lby0+6,fill=WHITE+(255,))

    draw_photo(card,W//2,BLUE_H+25,PH,RING,photo_img)

    cy=BLUE_H+PH//2+50
    nm_sz=fit_sz(name,FONT_BOLD,W-2*pad,34)
    cy+=ct(card,name,FONT_BOLD,nm_sz,W/2,cy,fill=DARK+(255,))+12
    cy+=gold_badge(card,W/2,cy,designation,FONT_BOLD,18)+8
    if subject.strip():
        sub_sz=fit_sz(subject,FONT_BOLD,W-2*pad,17)
        for ln in cwrap(subject,FONT_BOLD,sub_sz,W-2*pad):
            cy+=ct(card,ln,FONT_BOLD,sub_sz,W/2,cy,fill=NAVY+(255,))+5

    sign_y=H-120; sign_xc=W//2; sw=150
    if sign_img:
        sign=strip_bg(sign_img.copy()); sign.thumbnail((sw,60))
        card.paste(sign,(int(sign_xc-sign.size[0]/2),sign_y),sign if sign.mode=="RGBA" else None)
    draw=ImageDraw.Draw(card)
    ly=sign_y+65
    draw.line([(sign_xc-sw//2,ly),(sign_xc+sw//2,ly)],fill=GOLD,width=1)
    ct(card,"অধ্যক্ষ (ভারপ্রাপ্ত)",FONT_REGULAR,13,sign_xc,ly+6,fill=DARK+(255,))

    final=Image.new("RGB",(W,H),WHITE)
    final.paste(card,(0,0),card_mask)
    return add_frame(final,BRAD)

# =========================================================================
# ল্যান্ডস্কেপ  1013 × 638 px
# =========================================================================
def make_landscape(name,designation,subject,photo_img,logo_img,sign_img,exam_title,center_code):
    W,H=1013,638; BRAD=28; PH=190; RING=12; BLUE_H=320; WAVE_D=90; pad=22

    card_mask=Image.new("L",(W,H),0)
    ImageDraw.Draw(card_mask).rounded_rectangle([0,0,W-1,H-1],radius=BRAD,fill=255)
    card=Image.new("RGB",(W,H),BODY_BG)
    draw_blue_wave(card,W,H,BLUE_H,WAVE_D,BRAD)

    cy=pad
    if logo_img:
        logo=logo_img.copy(); logo.thumbnail((55,55))
        card.paste(logo,(pad,cy+2),logo if logo.mode=="RGBA" else None)
    cn_sz=fit_sz("আব্দুল ওদুদ শাহ ডিগ্রি কলেজ",FONT_BOLD,W-2*pad-65,36)
    cy+=ct(card,"আব্দুল ওদুদ শাহ ডিগ্রি কলেজ",FONT_BOLD,cn_sz,W/2,cy,fill=WHITE+(255,))+6
    cy+=ct(card,"দামুড়হুদা, চুয়াডাঙ্গা",FONT_BOLD,18,W/2,cy,fill=GOLD_LT+(255,))+10
    ImageDraw.Draw(card).line([(pad,cy),(W-pad,cy)],fill=GOLD,width=2); cy+=10
    el=f"{exam_title}  |  কেন্দ্র: {center_code}"
    ex_sz=fit_sz(el,FONT_BOLD,W-2*pad,18)
    cy+=ct(card,el,FONT_BOLD,ex_sz,W/2,cy,fill=GOLD+(255,))+10
    lbl="শিক্ষক পরিচয়পত্র"
    lw,lh=mtext(lbl,FONT_BOLD,18); lp=20
    lbx0=int(W/2-lw/2-lp); lbx1=int(W/2+lw/2+lp); lby0=int(cy); lby1=int(cy+lh+12)
    draw=ImageDraw.Draw(card)
    draw.rounded_rectangle([lbx0,lby0,lbx1,lby1],radius=10,outline=GOLD_LT,width=2)
    ct(card,lbl,FONT_BOLD,18,W/2,lby0+6,fill=WHITE+(255,))

    draw_photo(card,W//2,BLUE_H+25,PH,RING,photo_img)

    ty=BLUE_H+PH//2+40
    nm_sz=fit_sz(name,FONT_BOLD,W-2*pad,32)
    ty+=ct(card,name,FONT_BOLD,nm_sz,W/2,ty,fill=DARK+(255,))+8
    ty+=gold_badge(card,W/2,ty,designation,FONT_BOLD,18)+6
    if subject.strip():
        sub_sz=fit_sz(subject,FONT_BOLD,W-2*pad,18)
        for ln in cwrap(subject,FONT_BOLD,sub_sz,W-2*pad):
            ty+=ct(card,ln,FONT_BOLD,sub_sz,W/2,ty,fill=NAVY+(255,))+4

    sxc=W-pad-120; sw=180; sy=H-95
    if sign_img:
        sign=strip_bg(sign_img.copy()); sign.thumbnail((sw,60))
        card.paste(sign,(int(sxc-sign.size[0]/2),sy),sign if sign.mode=="RGBA" else None)
    draw=ImageDraw.Draw(card)
    ly2=sy+65
    draw.line([(sxc-sw//2,ly2),(sxc+sw//2,ly2)],fill=GOLD,width=1)
    ct(card,"অধ্যক্ষ (ভারপ্রাপ্ত)",FONT_REGULAR,13,sxc,ly2+6,fill=DARK+(255,))

    final=Image.new("RGB",(W,H),WHITE)
    final.paste(card,(0,0),card_mask)
    return add_frame(final,BRAD)

def make_id_card(name,designation,subject,photo_img,logo_img,sign_img,
                 exam_title="উচ্চ মাধ্যমিক পরীক্ষা-২০২৬",
                 center_code="২৯৫",orientation="পোর্ট্রেট"):
    if orientation=="ল্যান্ডস্কেপ":
        return make_landscape(name,designation,subject,photo_img,logo_img,sign_img,exam_title,center_code)
    return make_portrait(name,designation,subject,photo_img,logo_img,sign_img,exam_title,center_code)

st.title("🪪 শিক্ষক আইডি কার্ড")
st.caption("আব্দুল ওদুদ শাহ ডিগ্রি কলেজ — CR80 300 DPI")
c1,c2=st.columns(2)
with c1:
    name=st.text_input("নাম","")
    designation=st.selectbox("পদবি",["সহ: অধ্যাপক","প্রভাষক","সহ: শিক্ষক","প্রদর্শক"])
with c2:
    subject=st.text_input("বিষয়","")
    orientation=st.radio("ধরন",["পোর্ট্রেট","ল্যান্ডস্কেপ"],horizontal=True)
st.markdown("---")
e1,e2=st.columns(2)
with e1: exam_title=st.text_input("পরীক্ষার নাম","উচ্চ মাধ্যমিক পরীক্ষা-২০২৬")
with e2: center_code=st.text_input("কেন্দ্র কোড","২৯৫")
st.markdown("---")
f1,f2,f3=st.columns(3)
with f1: photo_file=st.file_uploader("ছবি",type=["jpg","jpeg","png"])
with f2: logo_file=st.file_uploader("লোগো",type=["jpg","jpeg","png"])
with f3: sign_file=st.file_uploader("স্বাক্ষর",type=["jpg","jpeg","png"])

if st.button("তৈরি করুন ✅",type="primary"):
    if not name.strip(): st.warning("নাম লিখুন।")
    else:
        photo_img=Image.open(photo_file).convert("RGBA") if photo_file else None
        logo_img=(Image.open(logo_file).convert("RGBA") if logo_file else
                  Image.open(DEFAULT_LOGO).convert("RGBA") if os.path.exists(DEFAULT_LOGO) else None)
        sign_img=(Image.open(sign_file).convert("RGBA") if sign_file else
                  Image.open(DEFAULT_SIGN).convert("RGBA") if os.path.exists(DEFAULT_SIGN) else None)
        card=make_id_card(name,designation,subject,photo_img,logo_img,sign_img,
                          exam_title=exam_title,center_code=center_code,orientation=orientation)
        st.image(card,caption="প্রিভিউ",use_container_width=False)
        buf=io.BytesIO(); card.save(buf,format="PNG",dpi=(300,300))
        st.download_button("📥 ডাউনলোড PNG 300 DPI",buf.getvalue(),
                           f"{name.strip()}_idcard.png","image/png")
