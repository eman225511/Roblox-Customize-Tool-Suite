import json
import re
import os
import sys
import subprocess
import tempfile
import io
import shutil
import ast
import importlib.util
import threading
import psutil
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from colorama import Fore, Style, init

init(autoreset=True)
session_history = []

def traverse_json(data, NoMulti, start_key=None):
    def recursive_search(obj, search_key, path=""):
        results = []
        if isinstance(obj, dict):
            for k, v in obj.items():
                new_path = f"{path}.{k}" if path else k
                if re.search(search_key, k):
                    results.append((new_path, v))
                results.extend(recursive_search(v, search_key, new_path))
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                new_path = f"{path}[{i}]"
                results.extend(recursive_search(item, search_key, new_path))
        return results

    current = data
    history = []
    combined = []

    if start_key:
        try:
            results = recursive_search(data, start_key)
            if not results:
                raise ValueError(f"{Fore.RED}Invalid start key: {start_key}")
            path, value = results[0]
            print(f"\n{Fore.GREEN}Starting at key: {path}")
            current = value
            history.append((data, path))
        except (KeyError, TypeError, ValueError) as e:
            print(f"{Fore.RED}Error: {e}")
            return

    backtrack_limit = len(history)

    while isinstance(current, (dict, list)):
        if isinstance(current, dict):
            print(f"\n{Fore.CYAN}Keys available:")
            keys = list(current.keys())
            for i, key in enumerate(keys):
                print(f"{i+1}: {' ' if i < 9 else ''}{Fore.GREEN}{key}")

            top_level_display = "'back' to go back, " if len(history) > backtrack_limit else ""
            prompt = "Enter a number to explore a key, " + top_level_display + "'search:<key>' to search, 'exit' to exit"
            if not NoMulti:
                prompt += ", or 'all' to collect all values"
                prompt += ", or comma-separated numbers to select multiple keys"
            prompt += ".\n: "

            user_input = input(prompt).strip()

            if user_input.lower() == 'exit':
                print("Exiting traversal.")
                return

            if user_input.lower() == 'back':
                if len(history) > backtrack_limit:
                    current, _ = history.pop()
                else:
                    print(f"\n{Fore.RED}Cannot backtrack beyond the start key.")
                continue

            if user_input.lower().startswith('search:'):
                search_key = user_input.split('search:', 1)[1]
                try:
                    results = recursive_search(data, search_key)
                    if results:
                        print(f"\n{Fore.CYAN}Search results:")
                        d = 0
                        for i, (path, value) in enumerate(results):
                            value_str = value if not isinstance(value, (dict, list)) else '[Nested structure]'
                            if NoMulti and value_str == '[Nested structure]':
                                pass
                            else:
                                d += 1
                                print(f"{d}. {Fore.GREEN}Path: {path}, Value: {value_str}")
                        selection = input("Enter a number to navigate to the result or 'back' to return\n: ").strip()
                        a = d-i
                        if selection.isdigit():
                            idx = int(selection)-a
                            if 0 <= idx < len(results):
                                path, value = results[idx]
                                print(f"Navigating to path: {path}")
                                history.append((current, path))
                                current = [value]
                            else:
                                print("Invalid selection.")
                        continue
                    else:
                        print(f"No results found for key matching '{search_key}'.")
                except re.error as e:
                    print(f"Invalid regex: {e}")
                continue

            if not NoMulti and user_input.lower() == 'all':
                combined.extend(collect_all_values(current))
                break

            if not NoMulti and ',' in user_input:
                try:
                    indices = [int(x) - 1 for x in user_input.split(',')]
                    selected_keys = [keys[i] for i in indices if 0 <= i < len(keys)]
                    valid_keys = []

                    for key in selected_keys:
                        valid_keys.append(key)

                    if not valid_keys:
                        print(f"{Fore.RED}No valid keys selected. All selected keys contain nested structures.")
                        continue

                    for key in valid_keys:
                        if isinstance(current[key], list):
                            combined.extend(current[key])
                        else:
                            combined.append(current[key])
                    break
                except (ValueError, IndexError):
                    print("Invalid input. Please enter valid numbers.")
            else:
                try:
                    index = int(user_input) - 1
                    if 0 <= index < len(keys):
                        key = keys[index]
                        if isinstance(current[key], list):
                            combined.extend(current[key])
                            return combined
                        else:
                            history.append((current, key))
                            current = current[key]
                    else:
                        print(f"{Fore.RED}Invalid index. Please try again.")
                except ValueError:
                    print(f"{Fore.RED}Invalid input. Please enter a valid number.")

        elif isinstance(current, list):
            break

    result = combined if combined else current; return result

def collect_all_values(obj):
    values = []
    if isinstance(obj, dict):
        for v in obj.values():
            values.extend(collect_all_values(v))
    elif isinstance(obj, list):
        for item in obj:
            values.extend(collect_all_values(item))
    else:
        values.append(obj)
    return values

def replacer(result, result2, temp=None, download=None, game_pre=None, display_names=None):
    folder_path = os.path.join(os.getenv('TEMP'), 'roblox', 'http')
    session_history.extend([result, result2])

    def find_cached_file_path():
        if temp:
            target_file_path = os.path.join(folder_path)
            return target_file_path
        
        if game_pre:
            return f"{game_pre}cached_files"
        
        search_dirs = ["assets/games", "assets/community", "assets/custom"]
        for base_dir in search_dirs:
            if not os.path.exists(base_dir):
                continue
            for sub_folder in os.listdir(base_dir):
                cached_files_path = os.path.join(base_dir, sub_folder, "cached_files")
                target_file_path = os.path.join(cached_files_path, result2)
                if os.path.exists(target_file_path):
                    return cached_files_path
        return None

    local_cached_files_path = find_cached_file_path()
    if not local_cached_files_path:
        print(f'{Fore.RED}No valid cached_files directory found for {result2}.{Style.RESET_ALL}')
        return

    try:
        copy_file_path = os.path.join(local_cached_files_path, result2)
        if os.path.exists(copy_file_path):
            for file_to_replace in result:
                target_file_path = os.path.join(folder_path, file_to_replace)
                shutil.copy(copy_file_path, target_file_path)
                if not display_names:
                    print(f'\'{Fore.BLUE}{file_to_replace}{Style.RESET_ALL}\' has been replaced with \'{Fore.BLUE}{result2}{Style.RESET_ALL}\'')
            if display_names:
                result_d, result2_d = find_keys_for_results(result, result2, asset_dirs)
                print(f'\'{Fore.BLUE}{result_d}{Style.RESET_ALL}\' has been replaced with \'{Fore.BLUE}{result2_d}{Style.RESET_ALL}\'{Style.RESET_ALL}')
            if download:
                if not os.path.exists(os.path.join('assets/custom/storage/cached_files', result2)):
                    try:
                        shutil.copy(copy_file_path, os.path.join('assets/custom/storage/cached_files', result2))
                        print(f"\n{Fore.GREEN}Copied {result2} from Roblox temp into 'assets/custom/storage/cached_files'.{Style.RESET_ALL}")
                    except Exception as e:
                        print(f"An error occurred: {e}")
        else:
            print(f'{Fore.RED}{result2} not found in {local_cached_files_path}.{Style.RESET_ALL}')

    except Exception as e:
        if hasattr(e, 'winerror') and e.winerror == 183:
            pass
        else:
            print(f'{Fore.RED}An error occurred: {e}{Style.RESET_ALL}\n')

def backbone(json_data, start_key, start_key2, addon, addon2, skip, game_pre, display_names):
    if not skip:
        result = collect_all_values(addon if addon else traverse_json(json_data, NoMulti=False, start_key=start_key))
        result = [result] if not isinstance(result, list) else result
        if result and all(r is not None for r in result):
            result2 = addon2 if addon2 else traverse_json(json_data, NoMulti=True, start_key=start_key2)
            if isinstance(result2, list) and len(result2) == 1:
                result2 = result2[0]
            
            if result2:
                replacer(result, result2, temp=False, download=False, game_pre=game_pre, display_names=display_names)

            return json_data, start_key, start_key2, result, result2, skip, game_pre, display_names

def game_runner(game_pre, display_names):
    json_file_path = f"{game_pre}assets.json"
    game_code = f"{game_pre}code.py"

    start_key, start_key2, addon, addon2 = "", "", "", ""
    skip = False

    try:
        with open(json_file_path, 'r') as file:
            json_data = json.load(file)
    except FileNotFoundError:
        print(f"\n{Fore.RED}File not found: {json_file_path}{Style.RESET_ALL}")
    except json.JSONDecodeError as e:
        print(f"\n{Fore.RED}Error decoding JSON: {e}{Style.RESET_ALL}")

    try:
        spec = importlib.util.spec_from_file_location("game_code_module", game_code)
        game_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(game_module)

        if hasattr(game_module, "run"):
            json_data, start_key, start_key2, addon, addon2, skip, game_pre, display_names = game_module.run(json_data, start_key, start_key2, addon, addon2, skip, game_pre, display_names)
            backbone(json_data, start_key, start_key2, addon, addon2, skip, game_pre, display_names)
        else:
            print(f"\n{Fore.RED}Error: The file {game_code} does not contain a `run` function.{Style.RESET_ALL}")
    except FileNotFoundError:
        print(f"\n{Fore.RED}Error: The file {game_code} was not found.{Style.RESET_ALL}")
    except Exception as e:
        print(f"\n{Fore.RED}Error executing run(): {e}{Style.RESET_ALL}")

def load_settings():
    global startup_launch, startup_preset, display_names, bootstrapper

    try:
        with open("storage/settings.json", 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"{Fore.RED}The settings file does not exist. Please ensure 'storage/settings.json' is available.{Style.RESET_ALL}") from None
    except json.JSONDecodeError:
        raise ValueError(f"{Fore.RED}The settings file contains invalid JSON. Please check the file contents.{Style.RESET_ALL}") from None

    required_keys = ['startup_launch', 'display_names', 'startup_preset', 'bootstrapper']
    for key in required_keys:
        if key not in data:
            raise KeyError(f"{Fore.RED}Missing required setting: '{key}' in the settings file.{Style.RESET_ALL}") from None

    startup_launch = data.get('startup_launch')
    display_names = data.get('display_names')
    startup_preset = data.get('startup_preset')
    bootstrapper = data.get('bootstrapper')

    return data

def background_autolaunch():
    def get_roblox_pids():
        roblox_pids = []
        for proc in psutil.process_iter(['pid', 'name']):
            if 'Roblox' in proc.info['name']:
                roblox_pids.append(proc.info['pid'])
        return roblox_pids

    def apply_preset(preset_path, preset):
        try:
            with open(preset_path, 'r') as file:
                preset_choice = ast.literal_eval(file.read())

                if preset_choice:
                    print(f"\n\nApplied {preset}:")
                    for i in range(0, len(preset_choice), 2):
                        replacer(preset_choice[i], preset_choice[i+1], temp=False, download=False, game_pre=game_pre, display_names=display_names)
                else:
                    print(f"{Fore.RED}Error running startup launch{Style.RESET_ALL}\n")
        except Exception as e:
            print(f"\n\n{Fore.RED}Error loading preset as preset does not exist: {e}{Style.RESET_ALL}\nContinue selecting previous changes\n: ", end="")

    def process_new_pids(new_pids, preset_dir, startup_preset):
        for pid in new_pids:
            for preset in startup_preset:
                selected_folder = f"{preset}.txt"
                preset_path = os.path.join(preset_dir, selected_folder)
                apply_preset(preset_path, preset)
            print("\n\nContinue selecting changes\n: ", end="")

    def track_roblox_pids():
        known_pids = set(get_roblox_pids())
        preset_dir = "assets/presets"
        skip = False

        while True:
            if startup_launch and startup_preset:
                time.sleep(0.25)
                current_pids = set(get_roblox_pids())
                new_pids = current_pids - known_pids
                
                if new_pids and not skip:
                    skip = True
                    process_new_pids(new_pids, preset_dir, startup_preset)
                    known_pids = current_pids
                    continue

                if new_pids and skip:
                    skip = False

                known_pids = current_pids
            else:
                time.sleep(0.25)

    thread = threading.Thread(target=track_roblox_pids)
    thread.daemon = True
    thread.start()

def find_preset(selected_folder):
    if not folders:
        print(f"{Fore.RED}\nNo presets available in the directory.{Style.RESET_ALL}")
        skip=0
        return skip
    else:
        print("\nAvailable presets:")
        for idx, folder in enumerate(folders):
            folder_name = folder.replace('.txt', '')
            print(f"{idx + 1}: {Fore.GREEN}{folder_name}{Style.RESET_ALL}")

        try:
            choice = int(input("Select a preset by number.\n: ")) - 1
            if 0 <= choice < len(folders):
                selected_folder = folders[choice]
                return selected_folder
            else:
                print(f"\n{Fore.RED}Invalid selection.{Style.RESET_ALL}")
        except ValueError:
            print(f"\n{Fore.RED}Invalid input. Please enter a number.{Style.RESET_ALL}")

def get_valid_input(prompt, valid_values=None, top=None):
    while True:
        user_input = input(prompt).strip().lower()
        if user_input == 'back' and top == False:
            return 'back'
        try:
            if valid_values is None or int(user_input) in valid_values:
                return int(user_input)
            else:
                print(f"{Fore.RED}\nInvalid option. Please choose from {valid_values}.{Style.RESET_ALL}")
        except ValueError:
            print(f"{Fore.RED}\nInvalid input. Please enter a valid number.{Style.RESET_ALL}")

def find_exact_key(data, target):
    if isinstance(data, dict):
        for key, value in data.items():
            if value == target:
                return key
            if isinstance(value, (list, dict)):
                found = find_exact_key(value, target)
                if found:
                    return found
    elif isinstance(data, list) and target in data:
        return None
    return None

asset_dirs = ["assets/games/", "assets/community/", "assets/custom/"]
def find_keys_for_results(result, result2, directories):
    if len(result) == 1:
        result = result[0]
    def search_in_directory(directory):
        for root, _, files in os.walk(directory):
            if 'assets.json' in files:
                with open(os.path.join(root, 'assets.json'), 'r') as json_file:
                    return json.load(json_file)
        return None

    for directory in directories:
        data = search_in_directory(directory)
        if data:
            result_key = find_exact_key(data, result)
            result2_key = find_exact_key(data, result2)
            if result_key:
                result = result_key
            if result2_key:
                result2 = result2_key                                                                      

    return result or "unknown", result2 or "unknown"

def export(filepath):
    ftype = None
    try:
        with open(filepath, 'rb') as file:
            for line_number in range(256):
                tell = file.tell()
                line = file.readline()
                if line_number == 0:
                    continue
                if not line:
                    break
                if b': ' in line:
                    continue
                else:
                    data_pos = tell
                    header = line[:12]
                    if header.startswith(b'\x89PNG\r\n'):
                        ftype = '.png'
                    elif header.startswith(b'\xabKTX 11\xbb\r\n'):
                        ftype = '.ktx2'
                    elif header.startswith(b'<roblox!'):
                        ftype = '.rbxl'
                    elif header.startswith(b'OggS'):
                        ftype = '.ogg'
                    break
            file.seek(data_pos)
            data = io.BytesIO(file.read())
    except FileNotFoundError:
        print(f"The file {filepath} was not found.")

    if not ftype:
        print("file type not found/exists")

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=ftype) as file:
            file.write(data.getvalue())
            tempfile_name = file.name
            filename = os.path.basename(tempfile_name)
            print(f"\n{Fore.GREEN}successfully written to {tempfile_name}{Style.RESET_ALL}")
            print(f"{Fore.BLUE}Viewing {filename}{Style.RESET_ALL}")
    except Exception as e:
        print(f"failed to write file: {e}")

    if sys.platform.startswith('win32'):
        # Windows
        os.startfile(tempfile_name)
    elif sys.platform.startswith('darwin'):
        # macOS
        subprocess.run(['open', tempfile_name])
    else:
        # Linux and other Unix-like systems
        subprocess.run(['xdg-open', tempfile_name])

def games_game_pre(game_pre, selected_folder, mode="games"):
    base_dir = "assets/games" if mode == "games" else "assets/community"
    no_items_message = (
        f"{Fore.RED}\nNo games available in the directory.{Style.RESET_ALL}"
        if mode == "games"
        else f"{Fore.RED}\nNo tweaks available in the directory.{Style.RESET_ALL}"
    )
    available_items_label = "Available games:" if mode == "games" else "Available tweaks:"

    folders = [f for f in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, f))]

    if not folders:
        print(no_items_message)
        return None
    else:
        while True:
            print(f"\n{available_items_label}")
            for idx, folder in enumerate(folders):
                print(f"{idx + 1}: {Fore.GREEN}{folder}{Style.RESET_ALL}")

            try:
                choice = input("Type 'back' to return to the main menu.\n: ")
                if choice == 'back':
                    print(f"{Fore.CYAN}\nReturning to main menu.{Style.RESET_ALL}")
                    return None
                choice = int(choice) - 1
                if 0 <= choice < len(folders):
                    selected_folder = folders[choice]
                    game_pre = os.path.join(base_dir, selected_folder, "")
                    with open(os.path.join(game_pre, "log.txt"), "r") as file:
                        lines = file.read().splitlines()
                        content = urllib.request.urlopen(lines[2]).read().decode('utf-8').splitlines()
                        if content[1] != lines[1]:
                            print(f"\n{Fore.CYAN}Update needed!{Style.RESET_ALL}")
                            cache_down(lines[0], game_pre)
                            if not os.path.exists(os.path.join(game_pre, "cached_files")):
                                break
                            urllib.request.urlretrieve(lines[2], os.path.join(game_pre, 'log.txt'))                            
                        if not os.path.exists(os.path.join(game_pre, "cached_files")):
                            cache_down(lines[0], game_pre)
                            if not os.path.exists(os.path.join(game_pre, "cached_files")):
                                break
                    return game_pre, selected_folder
                else:
                    print("\nInvalid selection.")
            except ValueError:
                print("\nInvalid input. Please enter a number.")

def update_settings():
    with open('storage/settings.json', 'w') as file:
        json.dump(settings, file, indent=4)

    print(f"\n{Fore.GREEN}Settings have been updated.{Style.RESET_ALL}")
    load_settings() 

def cache_down(file_id, game_pre):
    try:
        subprocess.run(['python', 'storage/cached_files_downloader.py', str(file_id), str(game_pre)], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error executing script: {e}")

if __name__ == "__main__":
    load_settings()
    background_autolaunch()
    print(f'>> {Fore.MAGENTA}MOST CHANGES MADE WITH ROBLOX OPEN WILL NOT APPLY UNTIL REJOIN{Style.RESET_ALL} <<\nChanges not appearing ingame? Try use this flag "FFlagHttpUseRbxStorage10": "False"\n\nFor news and more resources, check out our discord server!\ndiscord.gg/hXyhKehEZF')
    while True:
        game_pre = ""
        run_option = get_valid_input(f"\nWelcome to: Fleasion!\n"
                           f"0: {Fore.GREEN}Custom{Style.RESET_ALL}\n"
                           f"1: {Fore.GREEN}Games{Style.RESET_ALL}\n"
                           f"2: {Fore.GREEN}Community{Style.RESET_ALL}\n"
                           f"3: {Fore.GREEN}Presets{Style.RESET_ALL}\n"
                           f"4: {Fore.GREEN}Previewer{Style.RESET_ALL}\n"
                           f"5: {Fore.GREEN}Blocker{Style.RESET_ALL}\n"
                           f"6: {Fore.GREEN}Cache Settings{Style.RESET_ALL}\n"
                           f"7: {Fore.GREEN}Fleasion Settings{Style.RESET_ALL}\n"
                           f"8: {Fore.GREEN}Credits{Style.RESET_ALL}\n"
                           f"Enter which option you want to select.\n: ",
                           valid_values=[0, 1, 2, 3, 4, 5, 6, 7, 8],
                           top = True
        )
        try:
            match run_option:
                case 0:
                    while True:
                        custom_option = get_valid_input(
                            f"\nEnter custom option:\n"
                            f"1: {Fore.GREEN}From Fleasion Assets{Style.RESET_ALL}\n"
                            f"2: {Fore.GREEN}From Roblox Temp{Style.RESET_ALL}\n"
                            f"Type 'back' to return to the main menu.\n: ",
                            valid_values=[1, 2],
                            top = False
                        )
                        if custom_option == 'back':
                            print(f"{Fore.CYAN}\nReturning to main menu.{Style.RESET_ALL}")
                            break

                        match custom_option:
                            case 1:
                                result = input("\nEnter asset to change, type comma-separated hashes to select multiple values.\n: ")
                                result = result.split(', ') if ',' in result else [result]
                                result2 = input("\nEnter replacement\n: ")
                                replacer(result, result2, temp=False, download=False, game_pre=game_pre, display_names=display_names)
                                break
                            case 2:
                                result = input("\nEnter asset to change, type comma-separated hashes to select multiple values.\n: ")
                                result = result.split(', ') if ',' in result else [result]
                                result2 = input("\nEnter replacement\n: ")
                                replacer(result, result2, temp=True, download=True, game_pre=game_pre, display_names=display_names)
                                break
                case 1:
                    result = games_game_pre(game_pre, selected_folder="", mode="games")
                    if result is None:
                        continue
                    game_pre, selected_folder = result
                    print(f"\nViewing: {selected_folder}")
                    game_runner(game_pre, display_names)
                case 2:
                    result = games_game_pre(game_pre, selected_folder="", mode="community")
                    if result is None:
                        continue
                    game_pre, selected_folder = result
                    print(f"\nViewing: {selected_folder}")
                    game_runner(game_pre, display_names)
                case 3:
                    preset_dir = "assets/presets"
                    folders = [f for f in os.listdir(preset_dir) if f.endswith('.txt')]                    
                    while True:                    
                        preset_option = get_valid_input(
                                        f"\nSelect preset option:\n"
                                        f"1: {Fore.GREEN}Load Preset{Style.RESET_ALL}\n"
                                        f"2: {Fore.GREEN}Create Preset{Style.RESET_ALL}\n"
                                        f"3: {Fore.GREEN}Edit Preset{Style.RESET_ALL}\n"
                                        f"Type 'back' to return to the main menu.\n: ",
                                        valid_values=[1,2,3],
                                        top = False
                        )
                        if preset_option == 'back':
                            print(f"{Fore.CYAN}\nReturning to main menu.{Style.RESET_ALL}")
                            break

                        try:
                            match preset_option:
                                case 1:
                                    while True:                    
                                        selected_folder = find_preset("")
                                        if isinstance(selected_folder, (int)):
                                            break        
                                        if selected_folder:
                                            with open(os.path.join(preset_dir, selected_folder), 'r') as file:
                                                preset_choice = ast.literal_eval(file.read())
                                                for i in range(0, len(preset_choice), 2):
                                                    result = preset_choice[i]
                                                    result2 = preset_choice[i+1]
                                                    replacer(result, result2, temp=False, download=False, game_pre=game_pre, display_names=display_names)
                                            break
                                    break
                                case 2:
                                    if not session_history:
                                        print(f"{Fore.RED}\nNo history to snapshot.{Style.RESET_ALL}")
                                        break
                                    else:
                                        while True:
                                            preset_name = input("\nEnter preset name\n: ")
                                            invalid_chars = r'[<>:"/\\|?*\x00-\x1F]'
                                            if re.search(invalid_chars, preset_name):
                                                print(f"\n{Fore.RED}Invalid preset name! Preset must not contain any of the following: {invalid_chars}{Style.RESET_ALL}"); pass
                                            else:
                                                break
                                        file_path = os.path.join(preset_dir, preset_name + ".txt")
                                        try:
                                            with open(file_path, 'w') as file:
                                                file.write(str(session_history))
                                            print(f"{Fore.GREEN}\nSnapshot saved successfully as {preset_name}.{Style.RESET_ALL}")
                                        except Exception as e:
                                            print(f"{Fore.RED}\nFailed to save snapshot: {e}{Style.RESET_ALL}")
                                        break
                                case 3:
                                    while True:
                                        selected_folder = find_preset("")
                                        if isinstance(selected_folder, (int)):
                                            break                            
                                        if selected_folder:
                                            while True:                    
                                                edit_option = get_valid_input(
                                                                f"\nSelect preset option:\n"
                                                                f"1: {Fore.GREEN}View Preset{Style.RESET_ALL}\n"
                                                                f"2: {Fore.GREEN}Delete Preset{Style.RESET_ALL}\n"
                                                                f"Type 'back' to return to preset options.\n: ",
                                                                valid_values=[1,2,],
                                                                top = False
                                                )
                                                if edit_option == 'back':
                                                    print(f"{Fore.CYAN}\nReturning to preset options.{Style.RESET_ALL}")
                                                    break

                                                match edit_option:
                                                    case 1:
                                                        with open(os.path.join(preset_dir, selected_folder), 'r') as file:
                                                            preset_choice = ast.literal_eval(file.read())
                                                            
                                                            print(f"\nViewing {selected_folder[:-4]}:")
                                                            for i in range(0, len(preset_choice), 2):
                                                                result = preset_choice[i][0] if isinstance(preset_choice[i], list) and len(preset_choice[i]) == 1 else preset_choice[i]
                                                                if isinstance(result, str):
                                                                    result = [result]
                                                                result2 = preset_choice[i + 1]
                                                                resultf, result2f = result, result2

                                                                result, result2 = find_keys_for_results(result, result2, asset_dirs)
                                                                if resultf == result:
                                                                    result = f"unknown"                                                                  
                                                                if result2f == result2:
                                                                    result2 = f"unknown"                                                            
                                                                print(f"{Fore.RED if result == 'unknown' else Fore.BLUE}{result}{Style.RESET_ALL} replaced by {Fore.RED if result2 == 'unknown' else Fore.BLUE}{result2}{Style.RESET_ALL}")
                                                        break
                                                    case 2:
                                                        file_path = os.path.join(preset_dir, selected_folder)
                                                        try:
                                                            os.remove(file_path)
                                                            print(f"File '{file_path}' was successfully deleted.")
                                                        except Exception as e:
                                                            print(f"An error occurred while deleting '{file_path}': {e}")
                                                        break
                                            break
                                    if edit_option != 'back':
                                        break
                        except Exception as e:
                            print(f"{Fore.RED}\nAn error occurred: {e}{Style.RESET_ALL}")
                case 4:
                    while True:                    
                        preview_opion = get_valid_input(
                                        f"\nSelect preview option:\n"
                                        f"0: {Fore.GREEN}Temp{Style.RESET_ALL}\n"
                                        f"1: {Fore.GREEN}Games{Style.RESET_ALL}\n"
                                        f"2: {Fore.GREEN}Community{Style.RESET_ALL}\n"
                                        f"3: {Fore.GREEN}Custom{Style.RESET_ALL}\n"
                                        f"Type 'back' to return to the main menu.\n: ",
                                        valid_values=[0,1,2,3],
                                        top = False
                        )
                        if preview_opion == 'back':
                            print(f"{Fore.CYAN}\nReturning to main menu.{Style.RESET_ALL}")
                            break

                        match preview_opion:
                            case 0:
                                folder_path = os.path.join(os.getenv('TEMP'), 'roblox', 'http')
                                custom_hash = input("\nEnter hash to view\n: ")
                                export(os.path.join(folder_path, custom_hash)) 
                                break    
                            case 1:
                                result = games_game_pre(game_pre, selected_folder="", mode="games")
                                if result:
                                    game_pre, selected_folder = result
                                    assets_path = os.path.join(game_pre, "assets.json")
                                    with open(assets_path, 'r') as file:
                                        data = json.load(file)
                                    file_path = os.path.join(game_pre, "cached_files", traverse_json(data, NoMulti=True))
                                    export(file_path)
                                    break
                            case 2:
                                result = games_game_pre(game_pre, selected_folder="", mode="community")
                                if result:
                                    game_pre, selected_folder = result
                                    assets_path = os.path.join(game_pre, "assets.json")
                                    with open(assets_path, 'r') as file:
                                        data = json.load(file)
                                    file_path = os.path.join(game_pre, "cached_files", traverse_json(data, NoMulti=True))
                                    export(file_path)
                                    break
                            case 3:
                                custom_hash = input("\nEnter hash to view\n: ")
                                export("assets/custom/storage/cached_files/" + custom_hash) 
                                break                                                                               
                case 5:
                    FILE_PATH = r"C:\Windows\System32\drivers\etc\hosts"

                    def get_confirmation():
                        """Prompt the user to confirm they want to proceed."""
                        warning_message = (
                            f"\n{Fore.RED}Warning: This script modifies the hosts file. Run as admin and proceed with caution."
                            f"\nType 'proceed' to proceed or anything else to cancel.\n: {Style.RESET_ALL}"
                        )
                        return input(warning_message).strip().lower() == "proceed"

                    def parse_hosts_file(content):
                        """Parse the hosts file to identify blocked and unblocked entries."""
                        blocked, unblocked = [], []
                        for prefix in ("c", "t"):
                            for i in range(8):
                                entry = f"127.0.0.1 {prefix}{i}.rbxcdn.com"
                                if f"#{entry}" in content:
                                    unblocked.append(f"{prefix}{i}")
                                elif entry in content:
                                    blocked.append(f"{prefix}{i}")
                        return blocked, unblocked

                    def get_user_input():
                        """Collect website block/unblock requests from the user."""
                        print("Enter c(num)/t(num) to block/unblock (type 'done' when finished):")
                        entries = []
                        while True:
                            entry = input("Enter string: ").strip().lower()
                            if entry == "done":
                                break
                            entries.append(entry)
                        return entries

                    def modify_hosts_file(content, entries):
                        """Modify the hosts file content based on user input."""
                        modified_content = content
                        for entry in entries:
                            target = f"127.0.0.1 {entry}.rbxcdn.com"
                            commented_target = f"#{target}"
                            
                            if commented_target in content:
                                modified_content = modified_content.replace(commented_target, target)
                                print(f"{entry} - Blocked!")
                            elif target in content:
                                modified_content = modified_content.replace(target, commented_target)
                                print(f"{entry} - Unblocked!")
                            else:
                                modified_content += f"\n{target}"
                                print(f"{entry} - Newly blocked!")
                        return modified_content

                    def block_main():
                        if not get_confirmation():
                            return

                        try:
                            with open(FILE_PATH, "r") as file:
                                content = file.read()
                        except Exception as e:
                            print(f"{Fore.RED}Error reading hosts file: {e}{Style.RESET_ALL}")
                            return

                        blocked, unblocked = parse_hosts_file(content)
                        print("\nCurrently blocked:", ", ".join([f"{Fore.RED}{item}{Style.RESET_ALL}" for item in blocked]))
                        print("Currently unblocked:", ", ".join([f"{Fore.GREEN}{item}{Style.RESET_ALL}" for item in unblocked]))

                        entries = get_user_input()
                        try:
                            updated_content = modify_hosts_file(content, entries)
                            with open(FILE_PATH, "w") as file:
                                file.write(updated_content)
                            print(f"{Fore.RED}Hosts file updated successfully!{Style.RESET_ALL}")
                        except Exception as e:
                            print(f"{Fore.RED}Error writing to hosts file: {e}{Style.RESET_ALL}")
                    
                    block_main()
                case 6:
                    folder_path = os.path.join(os.getenv('TEMP'), 'roblox', 'http')

                    def delete_file_or_directory(path):
                        try:
                            if os.path.isfile(path) or os.path.islink(path):
                                os.unlink(path)
                            elif os.path.isdir(path):
                                shutil.rmtree(path)
                            return True, path, None
                        except Exception as e:
                            return False, path, e

                    def clear_full_cache():
                        if not os.path.exists(folder_path):
                            print(f"{Fore.RED}The directory {folder_path} does not exist.{Style.RESET_ALL}")
                            return

                        files_and_dirs = os.listdir(folder_path)
                        if not files_and_dirs:
                            print(f"\n{Fore.YELLOW}The directory {folder_path} is already empty.{Style.RESET_ALL}")
                            return

                        with ThreadPoolExecutor() as executor:
                            futures = [executor.submit(delete_file_or_directory, os.path.join(folder_path, item)) for item in files_and_dirs]
                            
                            all_successful = True
                            for future in futures:
                                success, path, error = future.result()
                                if not success:
                                    print(f"{Fore.RED}Failed to delete {path}. Reason: {error}{Style.RESET_ALL}")
                                    all_successful = False
                        
                        if all_successful:
                            print(f"\n{Fore.GREEN}Cleared cache!{Style.RESET_ALL}")
                        else:
                            print(f"\n{Fore.YELLOW}Cache clear completed with some errors.{Style.RESET_ALL}")

                    def delete_single_file(file_path, file_name):
                        if os.path.exists(file_path):
                            try:
                                os.remove(file_path)
                                print(f"{Fore.BLUE}Deleted: {file_name}{Style.RESET_ALL}")
                                return True, file_name, None
                            except Exception as e:
                                print(f"{Fore.RED}Error deleting {file_name}{Style.RESET_ALL}: {e}")
                                return False, file_name, e
                        else:
                            print(f"{Fore.RED}File not found: {file_name}{Style.RESET_ALL}")
                            return False, file_name, "File not found"

                    def delete_filtered_files(filtered_history):
                        def flatten(lst):
                            result = []
                            for item in lst:
                                if isinstance(item, list):
                                    result.extend(flatten(item))
                                else:
                                    result.append(item)
                            return result

                        flattened_history = flatten(filtered_history)

                        if not flattened_history:
                            print(f"{Fore.YELLOW}No files to delete based on the filtered history.{Style.RESET_ALL}")
                            return

                        with ThreadPoolExecutor() as executor:
                            futures = []
                            for file_name in flattened_history:
                                file_path = os.path.join(folder_path, file_name)
                                futures.append(executor.submit(delete_single_file, file_path, file_name))
                            
                            all_successful = True
                            for future in futures:
                                success, file_name, error = future.result()
                                if not success and error != "File not found":
                                    all_successful = False
                        
                        if all_successful:
                            print(f"\n{Fore.GREEN}Filtered files deletion completed!{Style.RESET_ALL}")
                        else:
                            print(f"\n{Fore.YELLOW}Filtered files deletion completed with some errors.{Style.RESET_ALL}")
                        
                        global session_history
                        session_history = []

                    while True:
                        cache_option = get_valid_input(
                                    "\nEnter cache replacement option:\n"\
                                    f"1: {Fore.GREEN}Revert Session Replacements{Style.RESET_ALL}\n"
                                    f"2: {Fore.GREEN}Clear Full Cache{Style.RESET_ALL}\n"
                                    f"3: {Fore.GREEN}Undo specific change{Style.RESET_ALL}\n"
                                    f"Type 'back' to return to the main menu.\n: ",
                                    valid_values=[1,2, 3],
                                    top = False
                        )
                        if cache_option == 'back':
                            print(f"{Fore.CYAN}\nReturning to main menu.{Style.RESET_ALL}")
                            break

                        try:
                            match cache_option:
                                case 1:
                                    if not session_history:
                                        print(f"\n{Fore.YELLOW}Session is already empty, try making a change!{Style.RESET_ALL}"); continue
                                    filtered_history = []
                                    i = 0
                                    while i < len(session_history):
                                        item = session_history[i]
                                        if isinstance(item, list) and i + 1 < len(session_history):
                                            filtered_history.append(item)
                                            i += 2
                                        else:
                                            filtered_history.append(item)
                                            i += 1

                                    delete_filtered_files()
                                    break
                                case 2:
                                    clear_full_cache()
                                    break
                                case 3:
                                    result = games_game_pre(game_pre, selected_folder="", mode="games")
                                    if result:
                                        game_pre, selected_folder = result
                                        assets_path = os.path.join(game_pre, "assets.json")
                                        with open(assets_path, 'r') as file:
                                            data = json.load(file)
                                        traversed = traverse_json(data, NoMulti=False)
                                        if traversed is not None:
                                            try:
                                                print("") #this only exists to drop a line :^)
                                                if isinstance(traversed, list):
                                                    for item in traversed:
                                                        file_path = os.path.join(game_pre, "cached_files", item)
                                                        joined_path = os.path.join(folder_path, os.path.basename(file_path))
                                                        os.remove(joined_path)
                                                        print(f"{Fore.RED}Reset {os.path.basename(file_path)}{Style.RESET_ALL}")
                                                else: #todo add dict support
                                                    file_path = os.path.join(game_pre, "cached_files", traversed)
                                                    joined_path = os.path.join(folder_path, os.path.basename(file_path))
                                                    os.remove(joined_path)
                                                    print(f"{Fore.RED}Reset {os.path.basename(file_path)}{Style.RESET_ALL}")
                                            except:
                                                print(f"{Fore.RED}{os.path.basename(file_path)} not found{Style.RESET_ALL}")
                                    break                                
                        except Exception as e:
                            print(f"{Fore.RED}An error occurred: {e}{Style.RESET_ALL}")
                case 7:
                    settings = load_settings()
                    while True:
                        settings_option = get_valid_input(
                                            f"\nSelect setting option:\n"
                                            f"1: {Fore.GREEN}Apply preset on launch{Style.RESET_ALL}: {Fore.GREEN if startup_launch else Fore.RED}{', '.join(startup_preset) if startup_preset else 'N/A'}{Style.RESET_ALL}\n"
                                            f"2: {Fore.GREEN}Display changes as names: {Fore.GREEN if display_names else Fore.RED}{display_names}{Style.RESET_ALL}\n" 
                                            f"3: {Fore.GREEN}Default Bootstrapper: {Fore.GREEN}{bootstrapper}{Style.RESET_ALL}\n"
                                            f"4: {Fore.GREEN}Clear session history{Style.RESET_ALL}\n"
                                            f"Type 'back' to return to the main menu.\n: ",
                                            valid_values=[1,2,3,4],
                                            top = False
                        )
                        if settings_option == 'back':
                            print(f"{Fore.CYAN}\nReturning to main menu.{Style.RESET_ALL}")
                            break

                        try:
                            match settings_option:
                                case 1:
                                    while True:
                                        launch_option = get_valid_input(
                                                        f"\nSelect launch option:\n"
                                                        f"1: {Fore.GREEN}Preset to apply on launch: {Style.RESET_ALL}{', '.join(startup_preset) if startup_preset else 'N/A'}\n"
                                                        f"2: {Fore.GREEN}Apply preset on launch:{Style.RESET_ALL} {startup_launch}\n"
                                                        f"Type 'back' to return to Fleasion settings.\n: ",
                                                        valid_values=[1,2],
                                                        top = False
                                        )
                                        if launch_option == 'back':
                                            print(f"{Fore.CYAN}\nReturning to Fleasion settings.{Style.RESET_ALL}")
                                            break

                                        try:
                                            match launch_option:
                                                case 1:
                                                    preset_dir = "assets/presets"                                            
                                                    folders = [f for f in os.listdir(preset_dir) if f.endswith('.txt')]
                                                    while True:                                                                    
                                                        apply_on_launch_option = get_valid_input(
                                                                                f"\nSelect launch option:\n"
                                                                                f"1: {Fore.GREEN}Add preset{Style.RESET_ALL}\n"
                                                                                f"2: {Fore.GREEN}Remove preset{Style.RESET_ALL}\n"
                                                                                f"Type 'back' to return to Fleasion settings.\n: ",
                                                                                valid_values=[1,2],
                                                                                top = False
                                                        )
                                                        if apply_on_launch_option == 'back':
                                                            print(f"{Fore.CYAN}\nReturning to launch options.\n{Style.RESET_ALL}")
                                                            break  

                                                        match apply_on_launch_option:
                                                            case 1:
                                                                user_input = find_preset("")
                                                                if isinstance(user_input, (int)):
                                                                    break                                                                        
                                                                settings['startup_preset'].append(user_input[:-4])
                                                                update_settings()
                                                                break
                                                            case 2:
                                                                if startup_preset:
                                                                    print("\nAvailable presets:")                                                               
                                                                    for idx, preset in enumerate(startup_preset, 1):
                                                                        print(f"{idx}: {Fore.GREEN}{preset}{Style.RESET_ALL}")

                                                                    while True:
                                                                        try:
                                                                            selection = int(input(f"Enter the number of the preset you want to select (1-{len(startup_preset)}).\n: "))
                                                                            if 1 <= selection <= len(startup_preset):
                                                                                print(f"\n{Fore.GREEN}Removed {startup_preset[selection - 1]}{Style.RESET_ALL}")
                                                                                settings['startup_preset'].remove(startup_preset[selection - 1])
                                                                                update_settings()
                                                                                break
                                                                            else:
                                                                                print(f"Please enter a number between 1 and {len(startup_preset)}.")
                                                                        except ValueError:
                                                                            print("Invalid input, please enter a valid number.")
                                                                    break
                                                                else:
                                                                    print(f"\n{Fore.RED}No Presets to remove!{Style.RESET_ALL}")
                                                                    break
                                                    if apply_on_launch_option != 'back':
                                                        break
                                                case 2:
                                                    settings['startup_launch'] = not settings['startup_launch']
                                                    update_settings()
                                        except Exception as e:
                                            print(f"{Fore.RED}An error occurred: {e}{Style.RESET_ALL}")
                                case 2:
                                    settings['display_names'] = not settings['display_names']
                                    update_settings()
                                case 3:
                                    while True:
                                        bootstrapper_option = get_valid_input(
                                                        f"\nSelect default bootstrapper:\n"
                                                        f"1: {Fore.GREEN}Bloxstrap{Style.RESET_ALL}\n"
                                                        f"2: {Fore.GREEN}Fishstrap{Style.RESET_ALL}\n"
                                                        f"3: {Fore.GREEN}Voidstrap{Style.RESET_ALL}\n"
                                                        f"4: {Fore.GREEN}Custom{Style.RESET_ALL}\n"
                                                        f"Type 'back' to return to Fleasion settings.\n: ",
                                                        valid_values=[1,2,3,4],
                                                        top = False
                                        )
                                        if bootstrapper_option == 'back':
                                            print(f"{Fore.CYAN}\nReturning to Fleasion settings.{Style.RESET_ALL}")
                                            break

                                        match bootstrapper_option:
                                            case 1:
                                                settings['bootstrapper'] = "Bloxstrap"
                                                update_settings()
                                                break
                                            case 2:
                                                settings['bootstrapper'] = "Fishstrap"
                                                update_settings()
                                                break
                                            case 3:
                                                settings['bootstrapper'] = "Voidstrap"
                                                update_settings()
                                                break
                                            case 4:
                                                custom_bootstrapper = input("Enter custom bootstrapper name: ").strip()
                                                if custom_bootstrapper:
                                                    settings['bootstrapper'] = custom_bootstrapper
                                                    update_settings()
                                                else:
                                                    print(f"{Fore.RED}Bootstrapper name cannot be empty.{Style.RESET_ALL}")
                                                break
                                    break
                                case 4:
                                    if not session_history:
                                        print(f"\n{Fore.GREEN}History is already empty!{Style.RESET_ALL}")
                                    else:
                                        session_history = []
                                        print(f"\n{Fore.GREEN}Reset session history!{Style.RESET_ALL}")
                                    break                              
                        except Exception as e:
                            print(f"{Fore.RED}An error occurred: {e}{Style.RESET_ALL}")
                case 8:
                    credits = input(f"""
{Fore.YELLOW}Founded by:{Style.RESET_ALL} 
    - Crop {Fore.BLUE}@cro.p{Style.RESET_ALL}
{Fore.YELLOW}Made and continued support by:{Style.RESET_ALL}
    - Tyler {Fore.BLUE}@8ar{Style.RESET_ALL}
{Fore.YELLOW}Contributed to by:{Style.RESET_ALL} 
    - etcy {Fore.BLUE}@3tcy{Style.RESET_ALL} (run.bat)
    - yolo {Fore.BLUE}@yoloblokers{Style.RESET_ALL} (maintaining)
    - o0x {Fore.BLUE}@.o0x{Style.RESET_ALL} (maintaining)
{Fore.YELLOW}Thanks to the community for supporting this project!{Style.RESET_ALL}
    - All of your supported and continued enthusiasm despite issues I may impose - Tyler
{Fore.YELLOW}Special thanks to server boosters:{Style.RESET_ALL}
    - {Fore.MAGENTA}@motion_7{Style.RESET_ALL}, {Fore.MAGENTA}@.o0x{Style.RESET_ALL}, {Fore.MAGENTA}@brigh.t{Style.RESET_ALL}, {Fore.MAGENTA}@corasyn{Style.RESET_ALL}, {Fore.MAGENTA}@er0der{Style.RESET_ALL}, {Fore.MAGENTA}@dr_gonfxre{Style.RESET_ALL}, {Fore.MAGENTA}@moldybiscuit73{Style.RESET_ALL}, {Fore.MAGENTA}@riiftt{Style.RESET_ALL}, {Fore.MAGENTA}@yoloblokers{Style.RESET_ALL}

Enter to return: """
                    )
        except Exception as e:
            print(f"{Fore.RED}An error occurred: {e}{Style.RESET_ALL}")
