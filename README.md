# Video Compressor

A simple, interactive, cross-platform video compression tool built in Python.

## Features

- **Interactive CLI**: Easy-to-use command-line interface with arrow key navigation.
- **Smart Compression**: Uses 2-pass encoding with H.264 for high-quality compression at target file sizes.
- **Date Sorting**: Automatically sorts video files by date (newest first) for easy selection.
- **Stats**: Displays detailed compression statistics (Original vs New Size, Reduction %).
- **Portable**: Can be distributed as a standalone `.exe` with portable FFmpeg binaries (no installation required).
- **WSL Support**: Automatically converts WSL paths (e.g., `/mnt/c/...`) to Windows paths when running the Windows executable.
- **Configuration**: Support for `.env` file to set default paths and target sizes.

---

## 🚀 Usage

### Option 1: Standalone Executable (Windows Only)
**Recommended for Windows users.** The `dist` folder already includes the necessary `ffmpeg.exe` and `ffprobe.exe`.

1.  **Download**: Clone or download this repository.
2.  **Run**: Go to the `dist` folder and run `compressor.exe`.
3.  **Note**: Ensure `ffmpeg.exe` and `ffprobe.exe` remain in the same folder as `compressor.exe`.

#### Missing FFmpeg?
If you lost the files or need to download them manually:
1.  Go to [gyan.dev/ffmpeg/builds](https://www.gyan.dev/ffmpeg/builds/)
2.  Download `ffmpeg-release-essentials.zip`
3.  Extract and copy `bin/ffmpeg.exe` and `bin/ffprobe.exe` to the `dist` folder.

### Option 2: Python Script (Cross-Platform)
Works on Windows, macOS, Linux, and native WSL.

1.  **Clone**:
    ```bash
    git clone <repository-url>
    cd video-compressor
    ```

2.  **Install Dependencies**:
    You need to install the required Python libraries (`ffmpeg-python`, `inquirer`, etc.) to run the script.
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run**:
    ```bash
    python compressor.py
    ```

---

## ⚙️ Configuration

You can configure default settings by creating a `.env` file in the project root (or next to the `.exe`).

**Example `.env`**:
```ini
DEFAULT_SOURCE_PATH=./videos
DEFAULT_OUTPUT_PATH=./output
DEFAULT_TARGET_SIZE_MB=50
```

---

## 🛠️ Building the Executable

If you want to build the `.exe` yourself:

1.  Install requirements: `pip install -r requirements.txt`
2.  Run PyInstaller:
    ```bash
    python -m PyInstaller --onefile --copy-metadata readchar --copy-metadata questionary compressor.py
    ```
3.  The executable will be in the `dist/` folder.

---

## ❓ Troubleshooting

### "The system cannot find the file specified"
-   This means **FFmpeg** or **FFprobe** is missing.
-   Ensure both `ffmpeg.exe` and `ffprobe.exe` are installed or placed in the same folder as the tool.

### "Permission denied" (WSL)
-   If running the `.exe` from WSL, ensure you have execute permissions:
    ```bash
    chmod +x compressor.exe
    ```

### "PackageNotFoundError: readchar"
-   If building yourself, ensure you use the `--copy-metadata` flags as shown in the build instructions.
