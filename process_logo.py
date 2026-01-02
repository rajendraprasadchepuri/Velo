from PIL import Image
import os

def process_logo():
    base_dir = r"C:\Users\rajendra.chepuri\OneDrive - TTEC Digital\Documents\C_Drive\prs\git\Velo\assets"
    input_path = os.path.join(base_dir, "logo.png")
    output_path = os.path.join(base_dir, "logo_processed.png")
    
    if not os.path.exists(input_path):
        print(f"Error: {input_path} does not exist.")
        return

    img = Image.open(input_path).convert("RGBA")
    datas = img.getdata()

    new_data = []
    for item in datas:
        # Change all white (also shades of whites) to transparent
        # Threshold of 240 for R, G, B
        if item[0] > 240 and item[1] > 240 and item[2] > 240:
            new_data.append((255, 255, 255, 0))
        else:
            new_data.append(item)

    img.putdata(new_data)
    
    # Crop to content (remove transparent borders)
    bbox = img.getbbox()
    if bbox:
        img = img.crop(bbox)
        
    img.save(output_path, "PNG")
    print(f"Saved processed logo to {output_path}")

if __name__ == "__main__":
    process_logo()
