import qrcode
img_name = 'yankouskay.png'

def generate(data= 'https://onliner.com'):
    img = qrcode.make(data)
    img.save()
    return img
generate()