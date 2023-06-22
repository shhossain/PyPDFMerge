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


class PDFMerge:
    def __init__(self, pdf_file, output_file=None, group_size=2, quality=1.5,page_number=True,debug=True):
        """ Merge PDF pages
        
        Args:
            pdf_file (str): Path to the PDF file.
            output_file (str, optional): Path to the output PDF file. Defaults to "output.pdf".
            group_size (int, optional): Number of pages to merge. Defaults to 2.
            quality (float, optional): Quality of the output PDF. Defaults to 1.5.
            page_number (bool, optional): Whether to add page number to the output PDF. Defaults to True.
            debug (bool, optional): Whether to print debug messages. Defaults to True.
        """
        
        if output_file is None:
            output_file = "output.pdf"

        self.pdf_path = pdf_file
        self.output_path = output_file
        self.debug = debug
        self.page_number = page_number

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
            print(f"Saved {self.page_count-self.after_page_count} pages in {t}")

        return path

    def merge(self, images) -> PILImage:
        # 2 = side by side, 3 = 2 side 1 down, 4 = 2 top 2 down, ...
        n = len(images)
        if n == 1:
            return images[0]

        if n == 2:
            # Merge 2 images side by side
            merged_image = Image.new("RGB", (2 * images[0].width, images[0].height))
            merged_image.paste(images[0], (0, 0))
            merged_image.paste(images[1], (images[0].width, 0))
        elif n == 3:
            # Merge 2 images side by side and 1 image below
            merged_width = 2 * images[0].width
            merged_height = 2 * images[0].height
            merged_image = Image.new(
                "RGB", (merged_width, merged_height), color="white"
            )

            # Paste the images into the merged image, preserving the original aspect ratio
            first_image = images[0]
            second_image = images[1]
            third_image = images[2]

            # Calculate the width and height for the side-by-side images
            side_by_side_width = merged_width // 2
            side_by_side_height = merged_height - first_image.height

            # Resize the side-by-side images while maintaining aspect ratio
            resized_first_image = first_image.resize(
                (side_by_side_width, side_by_side_height)
            )
            resized_second_image = second_image.resize(
                (side_by_side_width, side_by_side_height)
            )

            # Paste the resized images into the merged image
            merged_image.paste(resized_first_image, (0, 0))
            merged_image.paste(resized_second_image, (side_by_side_width, 0))
            merged_image.paste(third_image, (0, side_by_side_height))
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
        font = ImageFont.truetype("arial.ttf", self.dpi // 10)
        draw.text((20, 20), str(page_no), (0, 0, 0), font=font)
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

        merged_imgs: list[PILImage] = []
        for img_group in img_groups:
            merged_imgs.append(self.merge(img_group))

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
    parser.add_argument("-g", "--group-size", type=int, help="number of pages to merge")
    parser.add_argument("-q", "--quality", type=int, help="quality of the output file")
    parser.add_argument("-w", "--watch", type=str, help="watch directory for new files")
    parser.add_argument(
        "-c", "--count", help="count pages in pdfs in directory"
    )

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

    pdf = PDFMerge(pdf_file=args.path, group_size=args.group_size, quality=args.quality)
    pdf.run()

    
    
if __name__ == "__main__":
    main()
