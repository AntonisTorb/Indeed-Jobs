# Indeed Jobs
An app that scrapes the website `Indeed` with Selenium for job postings based on the provided configuration, keeps data in a `sqlite` database, and notifies the user on Discord.

## Table of Contents
- [About](#about)
- [Requirements](#requirements)
    - [Dependencies](#dependencies)
    - [Configuration file](#configuration-file)
    - [.env file](#env-file)
    - [Discord bot](#discord-bot)
    - [Discord Channels](#discord-channels)
    - [Selenium webdriver and Firefox](#selenium-webdriver-and-firefox)
- [How to run](#how-to-run)
- [Discord bot commands](#discord-bot-commands)

## About
This application is created with the goal of keeping track of job postings in the website `indeed.com` that interest you. It will notify you on Discord for postings that meet the configuration criteria, and will allow you to interact with the data that is gathered and kept in a local `sqlite` database. The data is kept in a table called `indeed_jobs` with the following column names:

- `id (int)`: Primary key, a unique incrementing identifier for each posting.
- `url (str)`: The URL for the job posting.
- `job_title (str)`: The title of the position.
- `employer (str)`: The name of the employer.
- `description (str)`: A short description for the position as provided in the posting.
- `date_posted (str)`: The approximate date the job was posted.
- `notified (bool)`: Whether the user has been notified on `Discord`.
- `interested (bool)`: Whether the user is interested in the job posting.
- `applied (bool)`: Whether the user has submitted an application for the job posting.
- `response (bool)`: Whether the user has received a response from the employer/recruiter.
- `rejected (bool)`: Whether the user received a rejection notification for the position.
- `interviews (int)`: The number of interviews the user participated in for the position.
- `job_offer (bool)`: Whether the user has received an employment offer for the position.

 If you notice any bugs, feel free to submit an issue, or your solution in a pull request. I hope this helps in your job seeking endeavour!

## Requirements
Other than having Python installed in your system, these are the additional requirements:

- ### Dependencies
    Open a command line window in the main directory (where the `main.py` file is located) and execute the following command in order to install all the required third party packages:

        pip install -r requirements.txt

- ### Configuration file
    Create a `config.json` file in the main directory. The format is presented in the included in the `config-template.json` file.

    For the location, the country can be either the full name or the short form, as it appears on the url (For USA it is `www`). For a full list of available countries, please check the `utils.py` module in the `indeedjobs` package in the main directory.

    `db_path` and `log_path` are the file paths to the database and log file respectively.

    `selenium_sleep_sec` represents how long the `Selenium webdriver` will wait for the page to load in seconds.

    `scraper_delay_sec` represents the delay between each subsequent scraping of the website in seconds.

    `bot_delay_sec` represents the delay between each check from the bot in the database for new postings in seconds.

    `ignore_older_than_days` represents the amount of days where posting older than it will be ignored.

- ### .env file
    Create a file called `.env` in the main directory. The internal structure of the file should be the folllowing four lines:

        # .env
        TOKEN=`Discord bot Token`
        CONFIG_CHANNEL=='Configuration Channel ID'
        NOTIFICATIONS_CHANNEL=`Notification Channel ID`

    You will get the `token` and the `channel IDs` in the following two segments.

- ### Discord bot
    Visit the [Discord Developer Portal](https://discord.com/developers/applications) and create a new application. The bot will need to have the following permissions at a minimum: `Read Messages/View Channels`, `Send Messages`, `Manage Messages`, `Read Message History` and `Add Reactions`. The `Message Content Intent` also needs to be enabled. 
    
    After creating the bot, create a `token` and add it in the [.env](#env-file) file. You can now install the bot in your server and manage it's roles/permissions.

- ### Discord channels
    Create two channels in the Discord server, one for `Configuration` and the other for the `Notifications`. Get the `Channel IDs` for both and add them to the [.env](#env-file) file. 
    
    (**Note:** If you have developer mode activated on Discord, you can just right click on the channel and copy the ID. Otherwise, the `Channel ID` is the last part of the url, after the last `/`, when you have the Channel selected in the [Discord Web Service](https://discord.com/app)).

- ### Selenium webdriver and Firefox
    The scraper uses `Selenium` to extract the data from `Indeed`, as it is protected by `Cloudflare` and regular requests won't return the desirable data. In order to use `Selenium` you will need to download a `webdriver`. For this project, I'm only using `FireFox` so the `webdriver` is `Geckodriver`. You can find the latest version from the [Mozilla Geckodriver Github Repository](https://github.com/mozilla/geckodriver/releases).

    After downloading it, make sure to put the executable in the main directory of the application.

    You will also need to have the `Firefox` browser installed, which you can get from [this link](https://www.mozilla.org/en-US/firefox/new/) or from a simple web search.

    There are currently no plans to implement functionality for other `webrivers` and browsers.

## How to run
After all the above requirements have been satisfied, you can start the application by opening a command line window in the main directory and executing the following command:

    python main.py

## Discord bot commands
Here is a list of the available commands for the bot, which you can also get by using the `!help` command in the `Configuration` Channel:

    ### Config Channel:
    !close            : Close application.

    ## Notification Channel:
    - React with ✅ to mark interested, or ❌ to delete message.
    - Reply with the following commands to swap/set the related field in the database for `job id` in the original message:

    !interview {operation} : Increases/decreases interviews by depending on operation: `+`(default) or `-`.
    !applied:              : Swaps value for `applied` boolean.
    !response:             : Swaps value for `response` boolean.
    !rejected:             : Swaps value for `rejected` boolean.
    !offer:                : Swaps value for `job_offer` boolean.

## Thank you and good luck!