import streamlit as st
import cv2
import yt_dlp
import numpy as np
from fpdf import FPDF
import os
import tempfile
from PIL import Image

def download_video(youtube_url, output_path, progress_callback=None):
    """Downloads the video to a local file for faster processing."""
    ydl_opts = {
        # Download best video quality, capped at 1080p
        'format': 'bestvideo[height<=1080][ext=mp4]/bestvideo[height<=1080]/best[ext=mp4]/best',
        'outtmpl': output_path,
        'quiet': True,
        'no_warnings': True,
    }
    
    # Add progress hook if callback provided
    if progress_callback:
        ydl_opts['progress_hooks'] = [progress_callback]
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=True)
            return info.get('title', 'slides')
    except Exception as e:
        st.error(f"Error downloading video: {e}")
        return None

def is_frame_different(frame1, frame2, threshold, mask_rect=None):
    """
    Compares two frames to check if they are significantly different.
    """
    if frame1 is None or frame2 is None:
        return True
    
    # Convert to grayscale
    gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
    
    # Apply mask (Prof's area)
    if mask_rect:
        x, y, w, h = mask_rect
        # Set the masked area to black (0) in both frames so differences there are ignored
        gray1[y:y+h, x:x+w] = 0
        gray2[y:y+h, x:x+w] = 0

    # Compute absolute difference
    diff = cv2.absdiff(gray1, gray2)
    score = np.mean(diff)
    
    return score > threshold

def create_pdf(image_paths, output_filename):
    """Converts a list of image paths to a single PDF."""
    pdf = FPDF()
    pdf.set_auto_page_break(0)
    
    for img_path in image_paths:
        with Image.open(img_path) as img:
            width, height = img.size
            
        # Convert pixels to mm (assuming 72 DPI is roughly 1 point)
        # We set the page size to exactly match the image aspect ratio
        # to avoid any scaling artifacts.
        mm_per_pixel = 0.264583 # 1 px = 0.264 mm
        pdf_w = width * mm_per_pixel
        pdf_h = height * mm_per_pixel
        
        pdf.add_page(format=(pdf_w, pdf_h))
        pdf.image(img_path, x=0, y=0, w=pdf_w, h=pdf_h)
        
    pdf.output(output_filename)

# --- UI Setup ---
st.set_page_config(page_title="NPTEL Slide Extractor", layout="wide")
st.title("📺 High-Res NPTEL Slide Extractor")
st.markdown("Extract HD slides from lecture videos.")

# Sidebar
with st.sidebar:
    st.header("Settings")
    interval = st.slider("Capture Interval (seconds)", 5, 60, 10)
    threshold = st.slider("Change Threshold", 1.0, 50.0, 5.0)
    
    st.markdown("### 🎭 Professor Masking")
    mask_position = st.selectbox("Professor Position", ["Bottom Left", "Bottom Right", "None"], index=0)
    mask_size = st.slider("Mask Size (%)", 10, 50, 30)

url = st.text_input("YouTube Video URL", "https://youtu.be/0aINWe1gMi4")

if st.button("Extract Slides"):
    if not url:
        st.warning("Please enter a URL.")
    else:
        status_text = st.empty()
        progress_bar = st.progress(0)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Download video to local file first
            video_path = os.path.join(temp_dir, "video.mp4")
            status_text.text("📥 Downloading video... (this ensures fast processing)")
            
            video_title = download_video(url, video_path)
            
            if video_title:
                status_text.text("Processing downloaded video...")
                
                # Now process the LOCAL video file (much faster seeking!)
                cap = cv2.VideoCapture(video_path)
                
                # Get video metadata
                fps = cap.get(cv2.CAP_PROP_FPS)
                if fps == 0: fps = 30
                total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                v_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                v_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                
                # Verify Resolution to User
                st.info(f"Processing Video Resolution: **{v_width}x{v_height}**")
                
                step_frames = int(interval * fps)
                saved_frames = []
                prev_frame = None
                frame_count = 0
                
                # Determine mask coordinates
                mask_rect = None
                mx = int(v_width * (mask_size / 100))
                my = int(v_height * (mask_size / 100))
                
                if mask_position == "Bottom Left":
                    mask_rect = (0, v_height - my, mx, my)
                elif mask_position == "Bottom Right":
                    mask_rect = (v_width - mx, v_height - my, mx, my)
                
                status_text.text("Scanning for slides...")
                
                while cap.isOpened():
                    current_frame_pos = frame_count * step_frames
                    if current_frame_pos >= total_frames:
                        break
                        
                    cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame_pos)
                    ret, frame = cap.read()
                    
                    if not ret:
                        break
                        
                    if is_frame_different(prev_frame, frame, threshold, mask_rect):
                        # Save as PNG for lossless quality
                        frame_filename = os.path.join(temp_dir, f"slide_{len(saved_frames):04d}.png")
                        cv2.imwrite(frame_filename, frame, [cv2.IMWRITE_PNG_COMPRESSION, 3])
                        saved_frames.append(frame_filename)
                        prev_frame = frame
                    
                    frame_count += 1
                    progress_bar.progress(min(current_frame_pos / total_frames, 1.0))
                
                cap.release()
                
                if saved_frames:
                    status_text.text(f"Compiling PDF from {len(saved_frames)} slides...")
                    pdf_filename = f"{video_title}_slides.pdf".replace(" ", "_")
                    pdf_path = os.path.join(temp_dir, pdf_filename)
                    create_pdf(saved_frames, pdf_path)
                    
                    st.success(f"Success! Extracted {len(saved_frames)} slides at {v_width}x{v_height}.")
                    
                    with open(pdf_path, "rb") as f:
                        st.download_button(
                            label="Download High-Res PDF",
                            data=f.read(),
                            file_name=pdf_filename,
                            mime="application/pdf"
                        )
                        
                    # Preview
                    with st.expander("Preview"):
                        st.image(saved_frames[:3], caption=["Slide 1", "Slide 2", "Slide 3"])
                else:
                    st.warning("No slides found. Try lowering the threshold.")
            else:
                st.error("Could not download video.")