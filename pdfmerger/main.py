import math
import os
import shutil
from PIL import Image, ImageDraw, ImageFont
import fitz
import argparse
import time
from PIL.Image import Image as PILImage
import sys
from glob import glob
from pathlib import Path
from typing import Literal
import io


class PDFMerge:
    def __init__(
        self,
        pdf_file,
        output_file=None,
        group_size=2,
        quality=1.5,
        page_number=True,
        page_number_position: Literal[
            "top-left",
            "top-right",
            "bottom-left",
            "bottom-right",
            "top-center",
            "bottom-center",
        ] = "top-right",
        ignore_blank=True,
        background_color=(255, 255, 255),
        compression_quality=100,
        debug=True,
    ):
        """Merge PDF pages

        Args:
            pdf_file (str): Path to the PDF file.
            output_file (str, optional): Path to the output PDF file. Defaults to "output.pdf".
            group_size (int, optional): Number of pages to merge. Defaults to 2.
            quality (float, optional): Quality of the output PDF. Defaults to 1.5.
            page_number (bool, optional): Whether to add page number to the output PDF. Defaults to True.
            ignore_blank (bool, optional): Whether to ignore blank pages. Defaults to True.
            black_page_color (tuple, optional): Color of the blank page. Defaults to (255,255,255).
            debug (bool, optional): Whether to print debug messages. Defaults to True.
        """

        if not os.path.exists(pdf_file):
            raise FileNotFoundError(f"File `{pdf_file}` not found.")

        output_file_name = str(Path(pdf_file).stem) + f"_merged_{group_size}.pdf"

        if output_file is None:
            output_file = output_file_name
        else:
            f = Path(output_file)
            if f.is_dir():
                output_file = f / output_file_name
            else:
                if not f.suffix == ".pdf":
                    output_file = f.parent / (f.stem + ".pdf")
                else:
                    output_file = f
            output_file = str(output_file)
            f = None

        self.pdf_path = pdf_file
        self.output_path = output_file
        self.debug = debug
        self.page_number = page_number
        self.ignore_blank = ignore_blank
        self.background_color = background_color
        self.pnp = page_number_position
        self.compression_quality = compression_quality

        self.group_size = group_size
        self.dpi = int(quality * 100)

        self.page_count = 0
        self.after_page_count = 0

    def format_time(self, t) -> str:
        if t < 60:
            return f"{t:.2f} seconds"
        else:
            m, s = int(t // 60), t % 60
            return f"{m} minutes and {s:.2f} seconds"

    def run(self):
        s = time.time()
        path = self.split()

        t = self.format_time(time.time() - s)
        if self.debug:
            print(f"Saved {self.output_path}({self.page_count-self.after_page_count} pages) in {t}")

        return path

    def merge(self, images) -> PILImage:
        # 2 = side by side, 3 = 2 side 1 down, 4 = 2 top 2 down, ...
        n = len(images)
        if n == 1:
            return images[0]

        if n == 2:
            # Merge 2 images side by side
            width, height = sum(i.width for i in images), max(i.height for i in images)
            merged_image = Image.new("RGB", (width, height))
            merged_image.paste(images[0], (0, 0))
            merged_image.paste(images[1], (images[0].width, 0))
        elif n == 3:
            raise NotImplementedError("Group size 3 is not supported.")
        else:
            # Calculate the number of rows and columns based on the specified layout
            num_cols = 2
            num_rows = (n + 1) // 2

            # Create a new blank image to hold the merged result
            first_image = images[0]
            merged_width = first_image.width * num_cols
            merged_height = first_image.height * num_rows
            merged_image = Image.new("RGB", (merged_width, merged_height))

            # Iterate through the images and paste them into the merged image
            for i in range(n):
                row = i // num_cols
                col = i % num_cols
                image = images[i]
                merged_image.paste(
                    image, (col * first_image.width, row * first_image.height)
                )

        return merged_image

    def add_page_number(self, img, page_no) -> PILImage:
        draw = ImageDraw.Draw(img)
        font = ImageFont.truetype("arial.ttf", self.dpi // 5)
        pos = (20, 20)
        if self.pnp == "top-left":
            pos = (20, 20)
        elif self.pnp == "top-right":
            pos = (img.width - 20, 20)
        elif self.pnp == "bottom-left":
            pos = (20, img.height - 40)
        elif self.pnp == "bottom-right":
            pos = (img.width - 40, img.height - 40)
        elif self.pnp == "top-center":
            pos = (img.width // 2, 20)
        elif self.pnp == "bottom-center":
            pos = (img.width // 2, img.height - 40)
            
        imgc = img.copy().convert("RGB").resize((100, 100))
        data = imgc.getdata()
        imgc.close()
        imgc = None
        avg = sum([sum(d) for d in data]) / len(data)
        data = None
        color = (255,255,255)
        if avg > 127.5:
            color = (0,0,0)
        draw.text(pos, str(page_no), color, font=font)
        return img

    def create_pdf(self, file_name, imgs: list[PILImage]) -> str:
        imgs[0].save(
            file_name, "PDF", resolution=100.0, save_all=True, append_images=imgs[1:]
        )
        return file_name

    def create_groups(self, items, group_size) -> list:
        return [items[i : i + group_size] for i in range(0, len(items), group_size)]

    def extract_images(self) -> list[PILImage]:
        doc = fitz.open(self.pdf_path)  # type: ignore
        self.page_count = doc.page_count
        imgs = []
        for i in range(self.page_count):
            page = doc.load_page(i)
            pix = page.get_pixmap(dpi=self.dpi)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)  # type: ignore
            if self.ignore_blank:
                imgc = img.copy().convert("RGB").resize((100, 100))
                data = imgc.getdata()
                if all([d == self.background_color for d in data]):
                    continue
                else:
                    imgs.append(img)
                imgc.close()
                imgc = None
                data = None
            else:
                imgs.append(img)

        return imgs

    def cp(self, src, dst):
        shutil.copy(src, dst)

    def split(self) -> str:
        imgs = self.extract_images()
        if len(imgs) == 1:
            self.cp(self.pdf_path, self.output_path)
            return self.output_path
        
        if self.page_number:
            imgs = [self.add_page_number(img, i + 1) for i, img in enumerate(imgs)]

        img_groups = self.create_groups(imgs, self.group_size)
        imgs = None

        merged_imgs: list[PILImage] = []
        for img_group in img_groups:
            merged_imgs.append(self.merge(img_group))

        if self.compression_quality < 100:
            mg = []
            for img in merged_imgs:
                pc = io.BytesIO()
                img = img.convert("RGB")
                img.save(pc, "JPEG", quality=self.compression_quality)
                mg.append(Image.open(pc))
                img.close()
            merged_imgs = mg
            mg = None


        self.after_page_count = len(merged_imgs)

        return self.create_pdf(self.output_path, merged_imgs)


def autocheck(watch_dir: str):
    watch_dir = os.path.abspath(watch_dir)
    print(f"Watching {watch_dir} for new files...")
    before = glob(os.path.join(watch_dir, "*.pdf"))
    try:
        while 1:
            input("Press enter to check for new files...")
            after = glob(os.path.join(watch_dir, "*.pdf"))
            added = [f for f in after if not f in before]
            before = after
            if added:
                print("Added: ", ", ".join(added))
                input("Press enter to START merging...")
                pdfpath = os.path.join(watch_dir, added[0])
                pdf = PDFMerge(pdfpath)
                pdf.run()
                print("Done!")
    except KeyboardInterrupt:
        print("Exiting...")


def count_pages_in_dir(watch_dir: str, group_size: int = 2):
    files = glob(os.path.join(watch_dir, "*.pdf"))
    total = 0
    tpg = 0
    for file in files:
        doc = fitz.open(file)  # type: ignore
        pg = doc.page_count
        rp = math.ceil(pg / (group_size * 2))
        print(f"{file}: {pg}/{rp} pages")
        tpg += rp
        total += pg
    print(f"Total pages: {total}")
    print(f"Total pages after merge: {tpg}")
    return total


def main():
    parser = argparse.ArgumentParser(
        description="Merge PDF files by stitching pages together"
    )
    parser.add_argument("path", type=str, help="path to pdf file")
    parser.add_argument("-o", "--output", type=str, help="output file name")
    parser.add_argument(
        "-g", "--group-size", type=int, help="number of pages to merge default=2"
    )
    parser.add_argument(
        "-b",
        "--blank",
        action="store_true",
        help="ignore blank pages in pdf",
        default=True,
    )
    parser.add_argument(
        "-bpc",
        "--blank-page-color",
        type=str,
        help="color of the blank page default=(255,255,255)",
        default="(255,255,255)",
    )
    parser.add_argument(
        "-p",
        "--page-number",
        action="store_true",
        help="add page number to the output pdf",
        default=True,
    )
    parser.add_argument(
        "-pn",
        "--page-number-position",
        type=str,
        help="position of the page number",
        default="top-right",
        choices=[
            "top-left",
            "top-right",
            "bottom-left",
            "bottom-right",
            "top-center",
            "bottom-center",
        ],
    )
    parser.add_argument(
        "-q", "--quality", type=int, help="quality of the output file default=1.5"
    )
    parser.add_argument(
        "-cq",
        "--compression-quality",
        type=int,
        help="compression quality of the output file default=100",
        default=100,
    )
    parser.add_argument("-w", "--watch", type=str, help="watch directory for new files")
    parser.add_argument("-c", "--count", help="count pages in pdfs in directory")

    unsupplied_args = ["-w", "-c"]
    if len(sys.argv) > 1:
        if sys.argv[1] in unsupplied_args:
            watch_dir = None
            if len(sys.argv) < 3:
                watch_dir = os.getcwd()
            else:
                watch_dir = sys.argv[2]

            if sys.argv[1] == "-w":
                autocheck(watch_dir)
            elif sys.argv[1] == "-c":
                if len(sys.argv) > 3:
                    count_pages_in_dir(watch_dir, int(sys.argv[3]))
                else:
                    count_pages_in_dir(watch_dir)
            return

    args = parser.parse_args()

    if args.group_size is None:
        args.group_size = 2
    if args.quality is None:
        args.quality = 1.5

    if args.blank_page_color is not None:
        args.blank_page_color = eval(args.blank_page_color)

    pdf = PDFMerge(
        pdf_file=args.path,
        group_size=args.group_size,
        quality=args.quality,
        output_file=args.output,
        page_number=args.page_number,
        ignore_blank=args.blank,
        background_color=args.blank_page_color,
        compression_quality=args.compression_quality,
        page_number_position=args.page_number_position,
    )
    pdf.run()


if __name__ == "__main__":
    main()
