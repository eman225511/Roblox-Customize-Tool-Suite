import urllib.request
import subprocess
import os
import zipfile
import json
import shutil
import stat
from concurrent.futures import ThreadPoolExecutor, as_completed

def kill_roblox_processes():
    print("Killing all Roblox processes...")
    roblox_processes = [
        "RobloxPlayerBeta.exe",
        "RobloxStudioBeta.exe",
        "RobloxPlayerLauncher.exe"
    ]
    for proc in roblox_processes:
        subprocess.call(['taskkill', '/f', '/im', proc], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def is_read_only(file_path): 
    return os.path.exists(file_path) and not os.access(file_path, os.W_OK)

def set_read_only(file_path):
    os.chmod(file_path, stat.S_IREAD)

appdata_roblox_dir = os.path.join(os.getenv('LOCALAPPDATA'), 'Roblox')
os.makedirs(appdata_roblox_dir, exist_ok=True)
file_path = os.path.join(appdata_roblox_dir, "rbx-storage.db")

if is_read_only(file_path):
    print("rbx-storage.db already exists and is read-only. Skipping download.")
else:
    print("Downloading rbx-storage.db...")
    try:
        kill_roblox_processes()
        urllib.request.urlretrieve(
            "https://raw.githubusercontent.com/qrhrqiohj/Fleasion-Backend/main/rbx-storage.db",
            file_path
        )
        set_read_only(file_path)
        print(f"Downloaded and set rbx-storage.db to read-only at {appdata_roblox_dir}")
    except Exception as e:
        print(f"Failed to download or replace rbx-storage.db: {e}")

temp_roblox_http_dir = os.path.join(os.getenv('TEMP'), 'Roblox', 'http')
os.makedirs(temp_roblox_http_dir, exist_ok=True)
print(f"Ensured directory exists: {temp_roblox_http_dir}")

with urllib.request.urlopen("https://raw.githubusercontent.com/qrhrqiohj/Fleasion-Backend/main/requirements.txt") as response:
    requirements = response.read().decode('utf-8').splitlines()

for package in requirements:
    try:
        subprocess.check_call(["pip", "show", package])
        print(f"{package} is installed.")
    except subprocess.CalledProcessError:
        print(f"{package} is NOT installed. Installing...")
        subprocess.check_call(["pip", "install", package])
    os.system('cls')

urllib.request.urlretrieve("https://raw.githubusercontent.com/qrhrqiohj/Fleasion-Backend/refs/heads/main/run.bat", "../run.bat")
urllib.request.urlretrieve("https://raw.githubusercontent.com/qrhrqiohj/Fleasion-Backend/main/main.py", "../main.py")
urllib.request.urlretrieve("https://raw.githubusercontent.com/qrhrqiohj/Fleasion-Backend/refs/heads/main/cached_files_downloader.py", "../storage/cached_files_downloader.py")
urllib.request.urlretrieve("https://raw.githubusercontent.com/qrhrqiohj/Fleasion-Backend/refs/heads/main/autoupdate.py", "../storage/autoupdate.py")

settings_url = "https://raw.githubusercontent.com/qrhrqiohj/Fleasion-Backend/main/settings.json"
local_settings_path = "../storage/settings.json"

try:
    with urllib.request.urlopen(settings_url) as response:
        remote_settings_content = json.loads(response.read().decode('utf-8'))
    print("Successfully fetched remote settings.json.")

    if os.path.exists(local_settings_path):
        print("Local settings.json found. Checking for new entries...")
        try:
            with open(local_settings_path, 'r') as f:
                local_settings_content = json.load(f)
            
            updated_settings = local_settings_content.copy()
            for key, value in remote_settings_content.items():
                if key not in updated_settings:
                    updated_settings[key] = value
                    print(f"Added new entry to settings.json: {key}")
            
            with open(local_settings_path, 'w') as f:
                json.dump(updated_settings, f, indent=4)
            print("Local settings.json updated with new entries.")

        except json.JSONDecodeError:
            print(f"Error reading local settings.json as JSON. Overwriting with remote version.")
            urllib.request.urlretrieve(settings_url, local_settings_path)
            print("settings.json downloaded and replaced.")
        except Exception as e:
            print(f"An error occurred during local settings.json processing: {e}")
            urllib.request.urlretrieve(settings_url, local_settings_path)
            print("settings.json downloaded and replaced.")
    else:
        print("Local settings.json not found. Downloading...")
        urllib.request.urlretrieve(settings_url, local_settings_path)
        print("settings.json downloaded.")

except Exception as e:
    print(f"Failed to fetch remote settings.json or process it: {e}")
    if not os.path.exists(local_settings_path):
        print("Local settings.json does not exist and remote fetch failed. Attempting to download directly as fallback.")
        try:
            urllib.request.urlretrieve(settings_url, local_settings_path)
            print("settings.json downloaded (fallback).")
        except Exception as e_fallback:
            print(f"Fallback download of settings.json also failed: {e_fallback}")

json_url = "https://raw.githubusercontent.com/qrhrqiohj/Fleasion-Backend/main/CLOG"

def download_file(url, filename):
    try:
        urllib.request.urlretrieve(url, filename)
        print(f"Downloaded: {filename}")
    except Exception as e:
        print(f"Error downloading {filename}: {e}")

def unzip_file(zip_file, extract_to):
    try:
        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        print(f"Unzipped to: {extract_to}")
    except Exception as e:
        print(f"Error unzipping {zip_file}: {e}")

def delete_file_or_directory(path):
    try:
        if os.path.isdir(path):
            shutil.rmtree(path)
            print(f"Deleted directory: {path}")
        else:
            os.remove(path)
            print(f"Deleted file: {path}")
    except Exception as e:
        print(f"Error deleting {path}: {e}")

def process_item(key, url, base_dir):
    log_exist = False
    repo_url = f"https://github.com/{url.split('/')[3]}/{url.split('/')[4]}/archive/refs/heads/main.zip"
    folder_name = os.path.join(base_dir, key)
    log_path = os.path.join(folder_name, "log.txt")
    
    if os.path.exists(log_path):
        with open(log_path, 'r') as log_file:
            log = log_file.read()
        log_exist = True
    
    os.makedirs(folder_name, exist_ok=True)
    zip_file_path = os.path.join(base_dir, f"{key}.zip")
    
    download_file(repo_url, zip_file_path)
    unzip_file(zip_file_path, base_dir)
    
    extracted_folder = os.path.join(base_dir, f"{url.split('/')[4]}-main")
    if os.path.isdir(extracted_folder):
        for item in os.listdir(extracted_folder):
            s = os.path.join(extracted_folder, item)
            d = os.path.join(folder_name, item)
            if os.path.isdir(s):
                shutil.move(s, d)
            else:
                shutil.move(s, d)
        delete_file_or_directory(extracted_folder)
    
    delete_file_or_directory(zip_file_path)
    
    if log_exist:
        with open(log_path, 'w') as file:
            file.write(log)

def process_category(category, base_dir):
    with ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(process_item, key, url, base_dir)
            for key, url in category.items()
        ]
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"Error processing item: {e}")

response = urllib.request.urlopen(json_url)
data = json.loads(response.read())

process_category(data["games"], "../assets/games")
process_category(data["community"], "../assets/community")

os.system('cls')
subprocess.run(["python", "main.py"], cwd=os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
