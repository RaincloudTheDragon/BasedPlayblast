import bpy  # type: ignore
import requests  # type: ignore
import zipfile
import tempfile
import os
import shutil
import json
from bpy.app.handlers import persistent  # type: ignore
import threading
import time

# Updater configuration
GITHUB_REPO = "RaincloudTheDragon/BasedPlayblast"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
UPDATE_CHECK_INTERVAL = 86400  # 24 hours in seconds

# Updater state tracking
class UpdaterState:
    checking_for_updates = False
    update_available = False
    update_version = ""
    update_download_url = ""
    error_message = ""
    last_check_time = 0

def get_current_version():
    """Get the current addon version as a string"""
    from .. import bl_info  # type: ignore
    version = bl_info["version"]
    return ".".join(str(v) for v in version)

def version_tuple_from_string(version_str):
    """Convert a version string to a tuple for comparison"""
    try:
        return tuple(int(n) for n in version_str.split('.'))
    except:
        return (0, 0, 0)

def check_for_updates(async_check=True):
    """Check for updates on GitHub"""
    if async_check:
        thread = threading.Thread(target=_check_for_updates_async)
        thread.daemon = True
        thread.start()
    else:
        return _check_for_updates_async()

def _check_for_updates_async():
    """Check for updates asynchronously"""
    UpdaterState.checking_for_updates = True
    UpdaterState.error_message = ""
    
    try:
        current_version = get_current_version()
        current_version_tuple = version_tuple_from_string(current_version)
        
        # Request the latest release info from GitHub
        headers = {}
        response = requests.get(GITHUB_API_URL, headers=headers, timeout=10)
        response.raise_for_status()
        
        release_data = response.json()
        latest_version = release_data["tag_name"].lstrip('v')
        latest_version_tuple = version_tuple_from_string(latest_version)
        
        # Check if update is available
        if latest_version_tuple > current_version_tuple:
            UpdaterState.update_available = True
            UpdaterState.update_version = latest_version
            
            # Get the zip file URL
            for asset in release_data["assets"]:
                if asset["name"].endswith(".zip"):
                    UpdaterState.update_download_url = asset["browser_download_url"]
                    break
            
            if not UpdaterState.update_download_url:
                UpdaterState.update_download_url = release_data["zipball_url"]
        else:
            UpdaterState.update_available = False
            
        UpdaterState.last_check_time = time.time()
        result = True
        
    except Exception as e:
        UpdaterState.error_message = str(e)
        result = False
    
    UpdaterState.checking_for_updates = False
    return result

def download_and_install_update():
    """Download and install the addon update"""
    if not UpdaterState.update_available or not UpdaterState.update_download_url:
        return False
    
    try:
        # Create a temporary directory
        temp_dir = tempfile.mkdtemp()
        temp_zip_path = os.path.join(temp_dir, "addon_update.zip")
        
        # Download the zip file
        response = requests.get(UpdaterState.update_download_url, stream=True, timeout=60)
        response.raise_for_status()
        
        with open(temp_zip_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        # Get the addon directory
        addon_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        
        # Extract to temporary location
        extract_dir = os.path.join(temp_dir, "extracted")
        with zipfile.ZipFile(temp_zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        
        # Find the addon root in the extracted files
        addon_root = None
        for root, dirs, files in os.walk(extract_dir):
            if "__init__.py" in files:
                # Found potential addon root
                with open(os.path.join(root, "__init__.py"), 'r') as f:
                    content = f.read()
                    if "bl_info" in content:
                        addon_root = root
                        break
        
        if not addon_root:
            # Try with the first directory if no clear addon root was found
            for item in os.listdir(extract_dir):
                if os.path.isdir(os.path.join(extract_dir, item)):
                    addon_root = os.path.join(extract_dir, item)
                    break
        
        if not addon_root:
            raise Exception("Could not find addon root in the downloaded files")
        
        # Copy files to addon directory
        # First, remove all old files except user settings
        for item in os.listdir(addon_dir):
            if item == "__pycache__":
                continue  # Skip pycache
            item_path = os.path.join(addon_dir, item)
            if os.path.isfile(item_path):
                os.remove(item_path)
            elif os.path.isdir(item_path) and item != "user_settings":
                shutil.rmtree(item_path)
        
        # Copy new files
        for item in os.listdir(addon_root):
            s = os.path.join(addon_root, item)
            d = os.path.join(addon_dir, item)
            if os.path.isfile(s):
                shutil.copy2(s, d)
            elif os.path.isdir(s):
                shutil.copytree(s, d)
        
        # Clean up
        shutil.rmtree(temp_dir)
        
        # Mark for reload
        bpy.ops.script.reload()
        
        return True
    
    except Exception as e:
        UpdaterState.error_message = str(e)
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        return False

@persistent
def check_for_updates_handler(dummy):
    """Handler to check for updates when Blender starts"""
    # Wait a bit to let Blender start up properly
    def delayed_check():
        time.sleep(2)  # Wait 2 seconds after startup
        if time.time() - UpdaterState.last_check_time > UPDATE_CHECK_INTERVAL:
            check_for_updates()
    
    thread = threading.Thread(target=delayed_check)
    thread.daemon = True
    thread.start()

# Add handler to check for updates on Blender startup
if check_for_updates_handler not in bpy.app.handlers.load_post:
    bpy.app.handlers.load_post.append(check_for_updates_handler) 