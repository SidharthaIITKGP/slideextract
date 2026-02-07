# 📺 YouTube Slide Extractor

A high-quality slide extraction tool for educational videos, particularly optimized for NPTEL lectures. Automatically detects and extracts unique slides from lecture videos while intelligently ignoring the professor's movements.

## ✨ Features

- **High-Resolution Output**: Downloads and processes videos at up to 1080p quality
- **Smart Detection**: Detects slide changes while masking out professor movements
- **Lossless Quality**: Saves slides as PNG for maximum clarity
- **PDF Export**: Compiles all extracted slides into a single, properly-formatted PDF
- **Fast Processing**: Downloads video first for rapid local frame extraction
- **Customizable Settings**: Adjustable capture intervals, change thresholds, and professor masking

## 🚀 Live Demo

Try it out: [Streamlit Cloud Link] *(Add your link after deployment)*

## 🛠️ Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Setup

1. Clone the repository:
```bash
git clone https://github.com/YOUR_USERNAME/slide-extractor.git
cd slide-extractor
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the app:
```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

## 📖 Usage

1. **Enter YouTube URL**: Paste the link to your lecture video
2. **Adjust Settings** (optional):
   - **Capture Interval**: How often to check for new slides (in seconds)
   - **Change Threshold**: Sensitivity to slide changes (lower = more sensitive)
   - **Professor Masking**: Select where the professor appears to ignore their movements
   - **Mask Size**: Percentage of screen to mask
3. **Extract Slides**: Click the button and wait for processing
4. **Download PDF**: Get your high-resolution PDF with all extracted slides

## 📋 Requirements

- streamlit
- opencv-python
- yt-dlp
- img2pdf
- numpy
- fpdf2
- Pillow

## 🎯 How It Works

1. **Download Phase**: Downloads the video at highest available quality (up to 1080p)
2. **Frame Analysis**: Samples frames at regular intervals
3. **Change Detection**: Compares consecutive frames using grayscale difference analysis
4. **Smart Masking**: Ignores professor area to avoid false positives
5. **PNG Export**: Saves unique slides as lossless PNG images
6. **PDF Compilation**: Combines all slides into a single PDF with proper aspect ratios

## 🤝 Contributing

Contributions are welcome! Feel free to:
- Report bugs
- Suggest features
- Submit pull requests

## 📄 License

MIT License - feel free to use this project for personal or commercial purposes.

## 🙏 Acknowledgments

- Built with [Streamlit](https://streamlit.io/)
- Video downloading powered by [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- Designed for NPTEL and educational content

## 📧 Contact

Created by Sidhartha - feel free to reach out!

---

**Note**: This tool is intended for educational purposes. Please respect copyright and terms of service when downloading videos.
