import pandas as pd
import jinja2
import yaml
from pathlib import Path
from constants import DATA_DIR
from lib.gmail import Gmail


REQUIRED_COLUMNS = ["prize",
                    "place_1st",
                    "place_2nd",
                    "place_3rd",
                    "place_others"]


def format_race_records(row):
    return f"{row['place_1st']}-{row['place_2nd']}-{row['place_3rd']}-{row['place_others']}"


def main():
    file_system_loader = jinja2.FileSystemLoader(searchpath="templates")
    env = jinja2.Environment(loader=file_system_loader)
    template = env.get_template("ranking.jinja")

    with open('gmail_config.yml', 'r') as f:
        config = yaml.safe_load(f)

    all_group_files = Path(DATA_DIR).glob("*.csv")
    for group_file in all_group_files:
        group_name = group_file.name.rstrip(".csv")
        df = pd.read_csv(group_file)

        df_sorted = df.sort_values(["owner_name", "prize"], ascending=False)
        df_sorted_owner_rank = df.groupby(["owner_name"]).sum()[REQUIRED_COLUMNS].sort_values("prize", ascending=False)
        df_sorted_owner_rank = df_sorted_owner_rank.reset_index()
        df_sorted_owner_rank["race_records"] = df_sorted_owner_rank.apply(format_race_records, axis=1)

        df_owners = []
        for owner_name in df_sorted_owner_rank["owner_name"]:
            df_owner = df_sorted[df_sorted["owner_name"] == owner_name]
            df_owners.append(df_owner)

        subject = f"[poger] 集計結果 ({group_name})"
        body = template.render({
            'df_sorted_owner_rank': df_sorted_owner_rank,
            'df_owners': df_owners,
        })
        print(body)

        login_addr = config["login_account"]
        to_addr = config["groups"][group_name]
        app_password = config["app_password"]
        gmail = Gmail(login_addr, app_password)
        gmail.send(to_addr, subject, body)


if __name__ == "__main__":
    main()
