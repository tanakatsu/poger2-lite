## poger2-lite

This is a simple tool for [POG](https://ja.wikipedia.org/wiki/%E3%83%9A%E3%83%BC%E3%83%91%E3%83%BC%E3%82%AA%E3%83%BC%E3%83%8A%E3%83%BC%E3%82%B2%E3%83%BC%E3%83%A0) organizers.

This application can
- calculate all paper owner's total prizes
- notify owner rankings in your group via mail
- notify race entry information via mail
- notify race result information via mail

### Get started

1. Clone this repository
    ```
    $ git clone https://github.com/tanakatsu/poger2-lite.git
    ```
1. Create virtual environment and activate it
    ```
    $ python -m venv venv
    $ . venv/bin/activate
    ```
1. Install packages
    ```
    $ pip install -r requirements.txt
    ```
1. Install browsers
    ```
    $ sudo /path/to/playwright install-deps
    $ playwright install
    ```

##### Prepare horse data file
1. Copy `sample_data_2024.csv` to `{your_group_name}.csv`
1. Place your horse data file in `data/`
1. Edit your csv file
    - Required columns
        - year
        - owner\_name
        - name
        - sire
        - mare
        - id
    - Other columns will be added by system

[Recommended]
You can use [pog\_horse\_selector](https://pog-horse-selector-proto-f6a28.firebaseapp.com/#/login) to generate this file. It's much easier to prepare.

##### Prepare notification configuration file

1. Get your Gmail's app password 
    - Refer to this [link](https://support.google.com/mail/answer/185833?hl=ja) to create app password
1. Copy `gmail_config.sample.yml` to `gmail_config.yml`
1. Edit yml file
    ```
    login_account: YOUR_GMAIL_ACCOUNT@gmail.com
    app_password: YOUR_GMAIL_APP_PASSWORD
    groups:
        {your_group_name}: YOUR_GROUP_REPRESENTATIVE_MAIL_ADDRESS
    ```
    - `{your_group_name}` must be same as your horse filename (`{your_group_name}.csv`)

### Features

##### Notify horse's race entry information
```
$ python task_notify_shutuba.py
```

##### Notify horse's race result information
```
$ python task_notify_result.py
```

##### Notify user ranking information
```
$ python task_notify_ranking.py
```

##### Update horse's names
```
$ python task_update_horse_names.py
```

##### Update horse's prizes
```
$ python task_update_horse_prizes.py
```

### Batch processing

3 shell scripts are provided.

- update\.sh
    - task\_update\_horse\_names\.py
    - task\_update\_horse\_prizes\.py
    - task\_notify\_ranking\.py
- shutuba\.sh
    - task\_notify\_shutuba\.py
- result\.sh
    - task\_notify\_result\.py

Also you can register cron jobs to run these batch scripts periodically.
```
$ cp cronjobs.sample.txt cronjobs.txt  # and EDIT it
$ ./install_cronjobs.sh
```

