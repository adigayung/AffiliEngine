from colorama import Fore, Style, init
from includes.config_loader import get_app_config

# Inisialisasi colorama
init(autoreset=True)
config = get_app_config()

# Level
INFO = "info"
WARNING = "warning"
ERROR = "error"
LOG = "log"
DEBUG = "debug"


def logger(level, message):
    if config["debug"] == True :
        colors = {
            INFO: Fore.LIGHTCYAN_EX,      # Biru muda
            WARNING: Fore.LIGHTYELLOW_EX, # Kuning
            ERROR: Fore.LIGHTRED_EX,      # Merah
            LOG: Fore.WHITE,              # Putih
            DEBUG: Fore.LIGHTMAGENTA_EX,  # Ungu muda
        }

        color = colors.get(level.lower(), Fore.WHITE)

        print(f"{color}[{level.upper()}]{Style.RESET_ALL} {message}")