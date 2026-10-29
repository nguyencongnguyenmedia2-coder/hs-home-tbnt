import os
from PIL import Image, ImageDraw, ImageFont

base_dir = os.path.dirname(os.path.abspath(__file__))
icons_dir = os.path.join(base_dir, 'icons')
os.makedirs(icons_dir, exist_ok=True)

def create_brand_icon(size, output_path):
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw rounded rectangle background (Hoa Sen Red)
    radius = int(size * 0.22)
    draw.rounded_rectangle([(0, 0), (size-1, size-1)], radius=radius, fill='#C8102E')
    
    # Inner border / gold accent
    inset = max(2, int(size * 0.035))
    draw.rounded_rectangle([(inset, inset), (size-1-inset, size-1-inset)], radius=int(radius*0.85), outline='#FFD700', width=max(1, int(size*0.02)))
    
    cx, cy = size / 2, size / 2
    
    try:
        font_size = int(size * 0.28)
        font = ImageFont.truetype('arialbd.ttf', font_size)
        sub_font = ImageFont.truetype('arial.ttf', int(size * 0.12))
    except:
        font = ImageFont.load_default()
        sub_font = ImageFont.load_default()
    
    petal_color = '#FFFFFF'
    gold_color = '#FFD700'
    
    top_y = size * 0.18
    mid_y = size * 0.42
    bot_y = size * 0.50
    w = size * 0.22
    
    # Central petal
    draw.polygon([(cx, top_y), (cx - w*0.4, mid_y), (cx, bot_y), (cx + w*0.4, mid_y)], fill=gold_color)
    # Left petal
    draw.polygon([(cx - w*0.35, top_y + size*0.06), (cx - w*0.9, mid_y), (cx - w*0.2, bot_y), (cx, mid_y)], fill=petal_color)
    # Right petal
    draw.polygon([(cx + w*0.35, top_y + size*0.06), (cx, mid_y), (cx + w*0.2, bot_y), (cx + w*0.9, mid_y)], fill=petal_color)
    
    # Base ark
    draw.arc([(cx - size*0.3, size*0.38), (cx + size*0.3, size*0.56)], 0, 180, fill=gold_color, width=max(2, int(size*0.025)))
    
    # Draw 'HSH' text
    bbox = draw.textbbox((0, 0), 'HSH', font=font)
    tw = bbox[2] - bbox[0]
    draw.text((cx - tw/2, size*0.55), 'HSH', fill='#FFFFFF', font=font)
    
    # Draw 'SALES PRO' text
    bbox2 = draw.textbbox((0, 0), 'SALES PRO', font=sub_font)
    t2w = bbox2[2] - bbox2[0]
    draw.text((cx - t2w/2, size*0.81), 'SALES PRO', fill='#FFD700', font=sub_font)
    
    img.save(output_path)

icon_512 = os.path.join(icons_dir, 'icon-512.png')
icon_192 = os.path.join(icons_dir, 'icon-192.png')
favicon_ico = os.path.join(base_dir, 'favicon.ico')

create_brand_icon(512, icon_512)
create_brand_icon(192, icon_192)

img_512 = Image.open(icon_512)
img_512.save(favicon_ico, format='ICO', sizes=[(16,16), (32,32), (48,48), (64,64)])
print('SUCCESS_ICONS_GENERATED')

