import pandas as pd
import re
from datetime import datetime
from pathlib import Path
from lib.netkeiba import Netkeiba
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

        for index, row in df.iterrows():
            year = row.year
            horse_name = row["name"]
            mare = row.mare

            if re.search(rf"の{year - 2}$", horse_name):
                print(f"Checking {horse_name}...")
                results = nkb_client.query_horse_by_mare(mare)
                filtered_result = [res for res in results if str(res.id).startswith(f"{year - 2}")]
                if len(filtered_result):
                    new_name = filtered_result[0].name
                    if not re.search(rf"の{year - 2}$", new_name):
                        df.loc[index, "name"] = new_name
                        print("Updated.")
                        updates += 1
                    else:
                        print("Not updated.")
                else:
                    print("Not updated.")

        print(f"{group_name}: {updates} updates")
        if updates:
            version = create_backup_version()
            backup_filename = group_file.name.replace(".csv", f".{version}.csv")
            df_orig.to_csv(Path(BACKUP_DIR) / backup_filename, index=False)
            df.to_csv(group_file, index=False)


if __name__ == "__main__":
    main()
