"""Step 11: illustration of the rating screen at the peak of the film (Supplementary Figure S1).

This is a COMPOSITE ILLUSTRATION, not a screenshot: the film frame at 10:36 (the woman held over the edge) with the
rating grid redrawn to match the layout of the task (see vmp_film_rating docs/img/study2_affect2d.png, a real
screenshot). The dot is placed at the confirmatory group's mean rating at that second, so it shows data, not an
invented position. The film frame is third-party material (Tikhomirov, 2017): permission is needed before publication.

The film is not in this repository; the frame is read from the tooling repository's copy. Run with OpenCV available:
      uv run --with opencv-python-headless python analysis/11_task_illustration.py
Writes manuscript/figures/task_illustration.png and a run record.
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # so `analysis` can be imported
from analysis import run_record, study_data  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
FILM = ROOT.parent / "vmp_film_rating" / "media" / "towerClimb.mp4"
OUT = ROOT / "manuscript" / "figures"
SECOND = 636  # 10:36, during the scene in which the woman is held over the edge
INSTRUCTION = "How do you feel right now? Left–right: unpleasant–pleasant. Down–up: low–high activation."


def film_frame(second):
    import cv2  # only needed here; not a project dependency

    capture = cv2.VideoCapture(str(FILM))
    capture.set(cv2.CAP_PROP_POS_FRAMES, int(second * capture.get(cv2.CAP_PROP_FPS)))
    ok, frame = capture.read()
    if not ok:
        sys.exit(f"Could not read the film at {second} s from {FILM}")
    return Image.fromarray(frame[:, :, ::-1])  # BGR -> RGB


def font(size, bold=False):
    for name in (("arialbd.ttf" if bold else "arial.ttf"), "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def label(draw, centre, text, size=15):
    """A small dark box with white text, as in the task."""
    box = draw.textbbox((0, 0), text, font=font(size))
    width, height = box[2] - box[0] + 12, box[3] - box[1] + 10
    x, y = centre[0] - width / 2, centre[1] - height / 2
    draw.rounded_rectangle([x, y, x + width, y + height], radius=3, fill=(70, 66, 60, 215))
    draw.text((x + 6, y + 4 - box[1]), text, font=font(size), fill=(255, 255, 255, 255))


def main():
    record = run_record.make_record("11_task_illustration.py", "confirmatory", seed=None,
                                    inputs=sorted(study_data.DATA.glob("*.csv")), settings={"second": SECOND})
    participants, valence, arousal = study_data.load()
    primary = study_data.analysis_samples(participants[participants["sample"] == "confirmatory"])["primary"].index
    mean_valence, mean_arousal = valence[primary, SECOND].mean(), arousal[primary, SECOND].mean()

    # Layout copied from the real screenshot: 1400 x 860 canvas, film at (60, 90), 1280 x 718.
    canvas = Image.new("RGBA", (1400, 860), (17, 17, 17, 255))
    canvas.paste(film_frame(SECOND).convert("RGBA").resize((1280, 718)), (60, 90))
    overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # Instruction line above the film
    text_box = draw.textbbox((0, 0), INSTRUCTION, font=font(19))
    draw.text(((1400 - (text_box[2] - text_box[0])) / 2, 54), INSTRUCTION, font=font(19), fill=(230, 230, 230, 255))

    # Rating grid in the lower right corner (160 x 160 px), with axis labels and the dot
    left, top, size = 1091, 616, 160
    draw.rounded_rectangle([left, top, left + size, top + size], radius=6, fill=(80, 70, 55, 150),
                           outline=(230, 225, 215, 200), width=2)
    draw.line([left + size / 2, top, left + size / 2, top + size], fill=(230, 225, 215, 140), width=1)
    draw.line([left, top + size / 2, left + size, top + size / 2], fill=(230, 225, 215, 140), width=1)
    label(draw, (left + size / 2, top - 18), "High activation")
    label(draw, (left + size / 2, top + size + 18), "Low activation")
    label(draw, (left - 47, top + size / 2), "Unpleasant")
    label(draw, (left + size + 37, top + size / 2), "Pleasant")
    dot_x = left + mean_valence / 100 * size
    dot_y = top + (1 - mean_arousal / 100) * size
    draw.ellipse([dot_x - 8, dot_y - 8, dot_x + 8, dot_y + 8], fill=(255, 255, 255, 255))

    OUT.mkdir(parents=True, exist_ok=True)
    Image.alpha_composite(canvas, overlay).convert("RGB").save(OUT / "task_illustration.png", dpi=(300, 300))
    run_record.save_record(record, OUT)
    print(f"wrote {OUT / 'task_illustration.png'} (dot at valence {mean_valence:.1f}, arousal {mean_arousal:.1f})")


if __name__ == "__main__":
    main()
