import pandas as pd
from datetime import datetime
from pathlib import Path
from netkeiba import Netkeiba
from constants import DATA_DIR, BACKUP_DIR


def create_backup_version() -> str:
    now = datetime.now()
    version = f"{now.year}{now.month:02d}{now.day:02d}{now.hour:02d}{now.minute:02d}{now.second:02d}"
    return version


def main():
    nkb_client = Netkeiba()
    Path(BACKUP_DIR).mkdir(exist_ok=True)

    all_group_files = Path(DATA_DIR).glob("*.csv")
    for group_file in all_group_files:
        group_name = group_file.name.rstrip(".csv")
        df = pd.read_csv(group_file)
        df_orig = df.copy()
        updates = 0
        print(group_name)

        if "prize" not in df.columns:
            df["prize"] = 0
        if "retired" not in df.columns:
            df["retired"] = False
        if "place_1st" not in df.columns:
            df["place_1st"] = 0
        if "place_2nd" not in df.columns:
            df["place_2nd"] = 0
        if "place_3rd" not in df.columns:
            df["place_3rd"] = 0
        if "place_others" not in df.columns:
            df["place_others"] = 0
        if "sex" not in df.columns:
            df["sex"] = ""
        if "trainer" not in df.columns:
            df["trainer"] = ""
        if "stable_location" not in df.columns:
            df["stable_location"] = ""

        for index, row in df.iterrows():
            if row.retired:
                continue

            horse_id = row["id"]
            print(horse_id)
            horse_info = nkb_client.get_horse_info(horse_id)

            cur_prize = df.loc[index, "prize"]
            new_prize = horse_info.prize_jra + horse_info.prize_nra
            place_counts = horse_info.race_place_counts

            df.loc[index, "prize"] = new_prize
            df.loc[index, "retired"] = horse_info.retired
            df.loc[index, "place_1st"] = place_counts[0]
            df.loc[index, "place_2nd"] = place_counts[1]
            df.loc[index, "place_3rd"] = place_counts[2]
            df.loc[index, "place_others"] = place_counts[3]
            df.loc[index, "sex"] = horse_info.sex
            df.loc[index, "trainer"] = horse_info.trainer
            df.loc[index, "stable_location"] = horse_info.stable_location
            if not cur_prize == new_prize:
                updates += 1
            print(horse_info)

        print(f"{group_name}: {updates} updates")
        if updates:
            version = create_backup_version()
            backup_filename = group_file.name.replace(".csv", f".{version}.csv")
            df_orig.to_csv(Path(BACKUP_DIR) / backup_filename, index=False)
            df.to_csv(group_file, index=False)


if __name__ == "__main__":
    main()
