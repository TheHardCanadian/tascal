import json
import logging
from pathlib import Path

from platformdirs import PlatformDirs

class TascalApp:
    def __init__(self) -> None:
        dirs = PlatformDirs("Tascal", "GeoffCompany")

        self.db_path = Path(dirs.user_data_dir) / "tascal.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self.config_path = Path(dirs.user_config_path) / "settings.json"
        self.credentials_path = Path(dirs.user_config_path) / "credentials.json"
        self.tokens_path = Path(dirs.user_config_path) / "tokens.json"
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        self.cache_dir = Path(dirs.user_cache_path)
        self.cache_dir.parent.mkdir(parents=True, exist_ok=True)

        log_file = Path(dirs.user_log_path) / "tascal.log"
        log_file.parent.mkdir(parents=True, exist_ok=True)

        if not logging.getLogger().hasHandlers():
            logging.basicConfig(filename=log_file, level=logging.INFO)

        self.statepath = dirs.user_state_path / "window.json"
        
    def save_tokens(self, tokens_json: str) -> None:
        self.tokens_path.parent.mkdir(parents=True, exist_ok=True)
        self.tokens_path.write_text(tokens_json)


    def load_config(self) -> dict:
        if self.config_path.exists():
            return json.loads(self.config_path.read_text())
        default_config = {"theme": "light", "autosave": True}
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.config_path.write_text(json.dumps(default_config))
        return default_config

    


#print(dirs.user_data_dir)
#print(dirs.user_cache_dir)
#print(dirs.user_log_dir)