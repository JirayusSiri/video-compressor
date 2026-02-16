import os
import sys
import questionary
import ffmpeg
from colorama import init, Fore, Style
from tqdm import tqdm
from dotenv import load_dotenv

# Initialize colorama and load env
init(autoreset=True)
load_dotenv()

def setup_ffmpeg_path():
    """
    Checks if ffmpeg/ffmpeg.exe exists in the same directory as the executable/script.
    If so, adds that directory to the PATH to ensure it is picked up.
    Also checks for ffprobe.
    """
    # Determine the directory where the app is running
    if getattr(sys, 'frozen', False):
        app_dir = os.path.dirname(sys.executable)
    else:
        app_dir = os.path.dirname(os.path.abspath(__file__))

    ffmpeg_exe = "ffmpeg.exe" if os.name == 'nt' else "ffmpeg"
    ffprobe_exe = "ffprobe.exe" if os.name == 'nt' else "ffprobe"
    
    local_ffmpeg = os.path.join(app_dir, ffmpeg_exe)
    local_ffprobe = os.path.join(app_dir, ffprobe_exe)

    # If local ffmpeg exists, add to PATH
    if os.path.exists(local_ffmpeg):
        os.environ["PATH"] = app_dir + os.pathsep + os.environ["PATH"]
        
        # Check for ffprobe too, as it is required for probing duration
        if not os.path.exists(local_ffprobe):
            print(Fore.RED + f"Warning: Found '{ffmpeg_exe}' but missing '{ffprobe_exe}'.")
            print(Fore.RED + "The tool requires BOTH to function correctly.")
            print(Fore.YELLOW + "Please copy 'ffprobe.exe' to the same folder.")
        return True
    return False

# Run setup
setup_ffmpeg_path()

# Get defaults from env or use fallbacks
DEFAULT_SOURCE_PATH = os.getenv("DEFAULT_SOURCE_PATH", "./videos")
DEFAULT_OUTPUT_PATH = os.getenv("DEFAULT_OUTPUT_PATH", "./output")
DEFAULT_TARGET_SIZE_MB = os.getenv("DEFAULT_TARGET_SIZE_MB", "50")

def resolve_path(path):
    r"""
    Converts WSL paths (e.g. /mnt/c/Users) to Windows paths (C:\Users)
    if running on Windows.
    """
    if os.name != 'nt':
        return path
        
    # Check for /mnt/x/ pattern
    path = path.replace('/', '\\') # Ensure backslashes first to be safe, though /mnt/ is forward
    
    # We need to handle the forward slash case specifically for the input string
    # Re-normalize to forward slashes for regex checks or simple string checks if simpler
    clean_path = path.replace('\\', '/')
    
    if clean_path.startswith('/mnt/'):
        parts = clean_path.split('/')
        if len(parts) > 2:
            drive_letter = parts[2]
            if len(drive_letter) == 1:
                # /mnt/c/foo -> c:/foo -> c:\foo
                rest = '/'.join(parts[3:])
                win_path = rest.replace('/', '\\')
                return f"{drive_letter}:\\{win_path}"
    
    return path.replace('/', '\\')

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def get_video_files(directory):
    video_extensions = ('.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv')
    files = [f for f in os.listdir(directory) if f.lower().endswith(video_extensions)]
    # Sort by modification time, newest first
    files.sort(key=lambda x: os.path.getmtime(os.path.join(directory, x)), reverse=True)
    return files

def get_duration(file_path):
    try:
        probe = ffmpeg.probe(file_path)
        return float(probe['format']['duration'])
    except ffmpeg.Error as e:
        print(Fore.RED + f"Error probing file: {e.stderr}")
        return None

def get_size_mb(file_path):
    return os.path.getsize(file_path) / (1024 * 1024)

def compress_video(video_full_path, output_full_path, target_size_mb):
    duration = get_duration(video_full_path)
    if not duration:
        return

    # Target size in bits
    target_total_bitrate = (target_size_mb * 1024 * 1024 * 8) / duration
    
    # Audio bitrate (assume 128k for standard quality)
    audio_bitrate = 128 * 1000
    
    # Video bitrate
    video_bitrate = target_total_bitrate - audio_bitrate
    
    # Ensure video bitrate is positive
    if video_bitrate < 1000:
        print(Fore.YELLOW + "Warning: Target size is too small! Setting minimum video bitrate.")
        video_bitrate = 100000 # 100kbps min

    print(Fore.CYAN + f"Target Video Bitrate: {int(video_bitrate/1000)}k")

    # Two-pass encoding
    try:
        # Pass 1
        print(Fore.YELLOW + "Pass 1/2: Analyzing...")
        (
            ffmpeg
            .input(video_full_path)
            .output(os.devnull, format='null', **{'c:v': 'libx264', 'b:v': video_bitrate, 'pass': 1})
            .overwrite_output()
            .run(quiet=True)
        )
        
        # Pass 2
        print(Fore.GREEN + "Pass 2/2: Compressing...")
        
        # Using tqdm for a fake progress bar since ffmpeg-python doesn't support real-time progress easily
        with tqdm(total=100, desc="Processing", bar_format="{l_bar}{bar}|") as pbar:
             (
                ffmpeg
                .input(video_full_path)
                .output(output_full_path, **{'c:v': 'libx264', 'b:v': video_bitrate, 'pass': 2, 'c:a': 'aac', 'b:a': audio_bitrate})
                .overwrite_output()
                .run(quiet=False) 
            )
             pbar.update(100)

        # Stats
        original_size = get_size_mb(video_full_path)
        new_size = get_size_mb(output_full_path)
        reduction = original_size - new_size
        percent = (reduction / original_size) * 100

        print(Fore.GREEN + f"\nCompression Complete! Saved to: {output_full_path}")
        print(Style.BRIGHT + Fore.WHITE + "----------------------------------------")
        print(f"Original Size: {original_size:.2f} MB")
        print(f"New Size:      {new_size:.2f} MB")
        print(f"Reduced by:    {reduction:.2f} MB ({percent:.1f}%)")
        print(Style.BRIGHT + Fore.WHITE + "----------------------------------------")

    except ffmpeg.Error as e:
        print(Fore.RED + f"An error occurred: {e.stderr.decode('utf8')}")
        
    # Cleanup pass log files
    for f in os.listdir('.'):
        if f.startswith('ffmpeg2pass'):
            os.remove(f)

def main():
    clear_screen()
    print(Style.BRIGHT + Fore.CYAN + "========================================")
    print(Style.BRIGHT + Fore.CYAN + "      Video Compressor Executable       ")
    print(Style.BRIGHT + Fore.CYAN + "========================================\n")

    # 1. Video Path Selection
    path_type = questionary.select(
        "Select Video Source Directory",
        choices=[
            f'Default Path ({DEFAULT_SOURCE_PATH})',
            'Enter Custom Path'
        ]
    ).ask()
    
    if not path_type: return # Handle exit

    if path_type.startswith('Default Path'):
        source_dir = os.path.abspath(resolve_path(DEFAULT_SOURCE_PATH))
        if not os.path.exists(source_dir):
            try:
                os.makedirs(source_dir)
                print(Fore.YELLOW + f"Created '{source_dir}'. Please add videos there and restart.")
                input("Press Enter to exit...")
                return
            except OSError as e:
                print(Fore.RED + f"Error creating directory: {e}")
                return
    else:
        raw_path = questionary.text("Enter full path to video folder:").ask()
        source_dir = resolve_path(raw_path)
        if not source_dir or not os.path.exists(source_dir):
             print(Fore.RED + f"Directory does not exist! (Checked: {source_dir})")
             return

    # 2. File Selection
    video_files = get_video_files(source_dir)
    if not video_files:
        print(Fore.RED + "No video files found in that directory.")
        return

    selected_video = questionary.select(
        "Select Video to Compress",
        choices=video_files
    ).ask()
    
    if not selected_video: return

    full_video_path = os.path.join(source_dir, selected_video)

    # 3. Target Size
    target_size_str = questionary.text(
        "Enter Target Size (MB)",
        default=DEFAULT_TARGET_SIZE_MB,
        validate=lambda text: text.isdigit() or "Please enter a valid number"
    ).ask()
    
    if not target_size_str: return
    target_size = int(target_size_str)

    # 4. Output Path
    out_type = questionary.select(
        "Select Output Directory",
        choices=[
            f'Default Path ({DEFAULT_OUTPUT_PATH})',
            'Enter Custom Path'
        ]
    ).ask()

    if not out_type: return

    if out_type.startswith('Default Path'):
        output_dir = os.path.abspath(resolve_path(DEFAULT_OUTPUT_PATH))
    else:
        raw_out_path = questionary.text("Enter full path to output folder:").ask()
        output_dir = resolve_path(raw_out_path)

    if not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir)
        except OSError as e:
            print(Fore.RED + f"Error creating directory: {e}")
            return

    output_filename = f"compressed_{selected_video}"
    output_full_path = os.path.join(output_dir, output_filename)

    # 5. Confirmation
    print(f"\n{Fore.YELLOW}--- Confirmation ---")
    print(f"Source: {full_video_path}")
    print(f"Target Size: {target_size} MB")
    print(f"Destination: {output_full_path}")
    print(f"--------------------")

    confirm = questionary.confirm("Proceed with compression?", default=True).ask()
    if not confirm:
        print("Aborted.")
        return

    # 6. Compress
    compress_video(full_video_path, output_full_path, target_size)
    
    input(Fore.CYAN + "\nPress Enter to exit...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)
    except Exception as e:
        print(Fore.RED + f"\nCRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        input(Fore.YELLOW + "\nPress Enter to exit...")
        sys.exit(1)
