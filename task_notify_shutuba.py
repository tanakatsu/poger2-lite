import pandas as pd
import jinja2
import pickle
import yaml
from pathlib import Path
from constants import DATA_DIR, CACHE_DIR
from lib.netkeiba import Netkeiba
from lib.gmail import Gmail


def main():
    file_system_loader = jinja2.FileSystemLoader(searchpath="templates")
    env = jinja2.Environment(loader=file_system_loader)
    template = env.get_template("shutuba.jinja")

    with open('gmail_config.yml', 'r') as f:
        config = yaml.safe_load(f)

    cache_file = Path(CACHE_DIR) / "shutuba.pkl"
    if cache_file.exists():
        with open(cache_file, "rb") as f:
            race_shutuba = pickle.load(f)
    else:
        nkb_client = Netkeiba()
        race_shutuba = nkb_client.get_all_shutuba_info()
        with open(cache_file, "wb") as f:
            pickle.dump(race_shutuba, f)
        print("Saved.")

    shutuba_horses = {}
    for race in race_shutuba:
        for horse in race.horses:
            shutuba_horses[horse.id] = {
                "info": race.info,
                "horse": horse
            }

    all_group_files = Path(DATA_DIR).glob("*.csv")
    for group_file in all_group_files:
        group_name = group_file.name.rstrip(".csv")
        df = pd.read_csv(group_file)

        owners = df.owner_name.unique()
        all_owner_entries = []
        for owner_name in owners:
            df_owner = df[df["owner_name"] == owner_name]
            owner_horse_ids = df_owner.id.tolist()
            owner_entries = []
            for horse_id in owner_horse_ids:
                if horse_id in shutuba_horses.keys():
                    owner_entries.append(shutuba_horses[horse_id])
            all_owner_entries.append((owner_name, owner_entries))

        subject = f"[poger] 出走情報 ({group_name})"
        body = template.render({
            'all_owner_entries': all_owner_entries,
        })
        print(body)

        login_addr = config["login_account"]
        to_addr = config["groups"][group_name]
        app_password = config["app_password"]
        gmail = Gmail(login_addr, app_password)
        gmail.send(to_addr, subject, body)


if __name__ == "__main__":
    main()
