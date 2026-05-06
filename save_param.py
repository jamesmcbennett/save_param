import os
import svgwrite
from datetime import datetime
import textwrap

class SaveParamsSVG:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "seed": ("INT", {"default": 10}),
                "steps": ("INT", {}),
                "model": ("STRING", {"default": ""}),
                "author": ("STRING", {"default": ""}),
                "output_path": ("STRING", {"default": "[time(%Y-%m-%d)]"}),
                "file_prefix": ("STRING", {"default": "[time(%Y%m%d_%H%M%S)]_param"}),
                "wrap_width": ("INT", {"default": 60}),
                "font_family": ("STRING", {"default": "Arial"}),
                "font_size": ("INT", {"default": 36}),
                "dark_mode": ("BOOLEAN", {"default": False}),
                "save_svg": ("BOOLEAN", {"default": True}),
                "save_yaml": ("BOOLEAN", {"default": True}),
                "prompt": ("STRING", {"multiline": True}),
            },
            "optional": {
                "negative_prompt": ("STRING", {"multiline": True}),
                "additional_text": ("STRING", {"multiline": True}),
            }
        }

    RETURN_TYPES = ()
    FUNCTION = "save"
    OUTPUT_NODE = True
    CATEGORY = "utils"

    def resolve_time_tokens(self, text):
        while "[time(" in text:
            start = text.index("[time(") + 6
            end = text.index(")]", start)
            fmt = text[start:end]
            text = text.replace(f"[time({fmt})]", datetime.now().strftime(fmt))
        return text

    def generate_incremented_filename(self, folder, base_name):
        suffix = ".svg"
        i = 1
        while True:
            filename = f"{base_name}{i}{suffix}"
            full_path = os.path.join(folder, filename)
            if not os.path.exists(full_path):
                return full_path
            i += 1

    def save(self, seed, steps, model, author, output_path, file_prefix,
             wrap_width, font_family, font_size, dark_mode, prompt, 
             negative_prompt=None, additional_text=None, save_svg=True, save_yaml=True):

        if not author.strip():
            raise ValueError("❌ The 'author' field must not be empty.")

        today_date = datetime.today().strftime("%B %d, %Y")
        resolved_folder = self.resolve_time_tokens(output_path.strip())
        resolved_prefix = self.resolve_time_tokens(file_prefix.strip())

        folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "output", resolved_folder))
        os.makedirs(folder, exist_ok=True)

        # Generate SVG and YAML paths
        svg_path = self.generate_incremented_filename(folder, resolved_prefix)
        base_filename = os.path.splitext(os.path.basename(svg_path))[0]

        # Replace 'param' with 'output' in base filename for image reference
        image_base = base_filename.replace("param", "output")
        yml_path = os.path.join(folder, base_filename + ".yml")

        print(f"✅ Saving SVG to: {svg_path}")
        print(f"✅ Saving YAML to: {yml_path}")

        # === SVG generation ===
        text_color = "#ffffff" if dark_mode else "#000000"
        background_color = "#000000" if dark_mode else "#ffffff"
        mid_tone_color = "#888888" if dark_mode else "#666666"
        width_px, height_px = 1024, 768

        dwg = svgwrite.Drawing(svg_path, profile='tiny', size=(f"{width_px}px", f"{height_px}px"))
        dwg.add(dwg.rect(insert=(0, 0), size=("100%", "100%"), fill=background_color))

        # Top Left
        left_y_offset = 40
        for left_line in [f"SEED {seed}", f"STEPS {steps}", "ComfyUI"]:
            dwg.add(dwg.text(left_line, insert=("20px", f"{left_y_offset}px"),
                             font_size=f"{font_size}px", font_family=font_family, fill=text_color))
            left_y_offset += font_size + 6

        # Top Right
        right_x = f"{width_px}px"
        right_y_offset = 40
        dwg.add(dwg.text(model, insert=(right_x, f"{right_y_offset}px"),
                         font_size=f"{font_size}px", font_family=font_family, fill=text_color, text_anchor="end"))
        if author.strip():
            right_y_offset += font_size + 6
            dwg.add(dwg.text(author, insert=(right_x, f"{right_y_offset}px"),
                             font_size=f"{font_size}px", font_family=font_family, fill=text_color, text_anchor="end"))
        right_y_offset += font_size + 6
        dwg.add(dwg.text(today_date, insert=(right_x, f"{right_y_offset}px"),
                         font_size=f"{font_size}px", font_family=font_family, fill=text_color, text_anchor="end"))

        # Prompt
        start_y = max(left_y_offset, right_y_offset) + 40
        for i, line in enumerate(textwrap.wrap("prompt: " + prompt, width=wrap_width)):
            y = start_y + i * (font_size + 6)
            if y + font_size < height_px - 20:
                dwg.add(dwg.text(line, insert=("20px", f"{y}px"),
                                 font_size=f"{font_size}px", font_family=font_family, fill=mid_tone_color))

        # Negative Prompt
        if negative_prompt is not None:
            negative_prompt_text = negative_prompt
            start_y = y + (font_size + 6) * 2
            for i, line in enumerate(textwrap.wrap("negative prompt: " + negative_prompt_text, width=wrap_width)):
                y = start_y + i * (font_size + 6)
                if y + font_size < height_px - 20:
                    dwg.add(dwg.text(line, insert=("20px", f"{y}px"),
                                     font_size=f"{font_size}px", font_family=font_family, fill=mid_tone_color))
                    

        # Additional Text
        if additional_text is not None and additional_text.strip() != "":
            start_y = y + (font_size + 6) * 2  # space below previous text
            for i, line in enumerate(textwrap.wrap(additional_text, width=wrap_width)):
                y = start_y + i * (font_size + 6)
                if y + font_size < height_px - 20:
                    dwg.add(dwg.text(line, insert=("20px", f"{y}px"),
                                    font_size=f"{font_size}px", font_family=font_family, fill=mid_tone_color))

        # === SVG save ===
        if save_svg:
            dwg.save()
            print(f"✅ SVG saved to: {svg_path}")
        else:
            print("⏭️ SVG save skipped.")

        # === YAML save ===
        if save_yaml:
            yaml_lines = [
                f"image_name: {image_base}.png",
                f"output_dir: {folder.replace(os.sep, '/')}",
                f"image_path: {os.path.join(folder, image_base + '.png').replace(os.sep, '/')}",
                f"prompt: \"{prompt}\"",
                f"negative_prompt: \"{negative_prompt or ''}\"",
                f"seed: {seed}",
                f"steps: {steps}",
                f"author: {author}",
                f"additional_text: \"{additional_text or ''}\""
            ]
            with open(yml_path, "w", encoding="utf-8") as f:
                f.write("\n".join(yaml_lines))

            print(f"✅ YAML written to: {yml_path}")


            
        return {}


NODE_CLASS_MAPPINGS = {
    "SaveParamsSVG": SaveParamsSVG
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "SaveParamsSVG": "Save Params as SVG"
}
