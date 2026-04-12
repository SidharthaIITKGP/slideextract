import streamlit as st
import cv2
import yt_dlp
import numpy as np
from fpdf import FPDF
import os
import tempfile
from PIL import Image

# ---------------------- DOWNLOAD ----------------------
def download_video(youtube_url, output_path):
    ydl_opts = {
        'format': 'bestvideo[height<=1080][ext=mp4]/best[ext=mp4]/best',
        'outtmpl': output_path,
        'quiet': True,
        'no_warnings': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=True)
            return info.get('title', 'video')
    except Exception as e:
        st.error(f"Error downloading video: {e}")
        return None

# ---------------------- PLAYLIST ----------------------
def get_playlist_videos(playlist_url):
    ydl_opts = {
        'quiet': True,
        'extract_flat': True,
    }

    video_urls = []

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(playlist_url, download=False)

        if 'entries' in info:
            for entry in info['entries']:
                if entry:
                    video_urls.append(f"https://www.youtube.com/watch?v={entry['id']}")

    return video_urls

# ---------------------- FRAME DIFF ----------------------
def is_frame_different(frame1, frame2, threshold, mask_rect=None):
    if frame1 is None or frame2 is None:
        return True

    gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)

    if mask_rect:
        x, y, w, h = mask_rect
        gray1[y:y+h, x:x+w] = 0
        gray2[y:y+h, x:x+w] = 0

    diff = cv2.absdiff(gray1, gray2)
    score = np.mean(diff)

    return score > threshold

# ---------------------- PDF ----------------------
def create_pdf(image_paths, output_filename):
    pdf = FPDF()
    pdf.set_auto_page_break(0)

    for img_path in image_paths:
        with Image.open(img_path) as img:
            width, height = img.size

        mm_per_pixel = 0.264583
        pdf_w = width * mm_per_pixel
        pdf_h = height * mm_per_pixel

        pdf.add_page(format=(pdf_w, pdf_h))
        pdf.image(img_path, x=0, y=0, w=pdf_w, h=pdf_h)

    pdf.output(output_filename)

# ---------------------- UI ----------------------
st.set_page_config(page_title="Playlist Slide Extractor", layout="wide")
st.title("📺 Playlist + Video Slide Extractor")

mode = st.radio("Select Mode", ["Single Video", "Playlist"])
url = st.text_input("Enter YouTube URL")

interval = st.slider("Capture Interval (sec)", 5, 60, 10)
threshold = st.slider("Change Threshold", 1.0, 50.0, 5.0)
max_videos = st.slider("Max Videos (Playlist)", 1, 50, 10)

mask_position = st.selectbox("Professor Position", ["Bottom Left", "Bottom Right", "None"])
mask_size = st.slider("Mask Size (%)", 10, 50, 30)

# ---------------------- MAIN ----------------------
if st.button("Extract Slides"):
    if not url:
        st.warning("Enter URL")
    else:
        with tempfile.TemporaryDirectory() as temp_dir:

            # GET VIDEO LIST
            if mode == "Playlist":
                video_list = get_playlist_videos(url)[:max_videos]
            else:
                video_list = [url]

            all_saved_frames = []

            for idx, video_url in enumerate(video_list):
                st.write(f"Processing {idx+1}/{len(video_list)}")

                video_path = os.path.join(temp_dir, f"video_{idx}.mp4")
                title = download_video(video_url, video_path)

                if not title:
                    continue

                cap = cv2.VideoCapture(video_path)

                fps = cap.get(cv2.CAP_PROP_FPS) or 30
                total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

                step_frames = int(interval * fps)

                # MASK
                mask_rect = None
                mx = int(width * (mask_size / 100))
                my = int(height * (mask_size / 100))

                if mask_position == "Bottom Left":
                    mask_rect = (0, height - my, mx, my)
                elif mask_position == "Bottom Right":
                    mask_rect = (width - mx, height - my, mx, my)

                prev_frame = None
                frame_count = 0

                while cap.isOpened():
                    pos = frame_count * step_frames
                    if pos >= total_frames:
                        break

                    cap.set(cv2.CAP_PROP_POS_FRAMES, pos)
                    ret, frame = cap.read()

                    if not ret:
                        break

                    if is_frame_different(prev_frame, frame, threshold, mask_rect):
                        filename = os.path.join(
                            temp_dir, f"v{idx}_slide_{len(all_saved_frames):05d}.png"
                        )
                        cv2.imwrite(filename, frame)
                        all_saved_frames.append(filename)
                        prev_frame = frame

                    frame_count += 1

                cap.release()

            # CREATE PDF
            if all_saved_frames:
                pdf_path = os.path.join(temp_dir, "final_slides.pdf")
                create_pdf(all_saved_frames, pdf_path)

                with open(pdf_path, "rb") as f:
                    st.download_button(
                        "Download PDF",
                        f.read(),
                        file_name="playlist_slides.pdf",
                        mime="application/pdf"
                    )

                st.success(f"Done! {len(all_saved_frames)} slides extracted.")
            else:
                st.error("No slides found.")
