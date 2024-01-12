# Google Finance Automation

Tired of going click-click when trying to upload your stock
purchases on Google Finance? This repository aims at reducing
the manual work required to populate the portfolio(s) in Google
Finance UI by reading from CSV/TSV files.

Demo Video:  

https://github.com/Akshayanti/Google-Finance-Automation/assets/14781746/f385ba0f-9acd-42c3-b08c-a3265b155874

## How To Get Started?

1. Fill up the contents of `data/portfolio.csv` file with the
links to the portfolios with their names. Example:

```csv
Group_Name,Group_Link

# Comments are included like this with # in beginning of line
Group1, https://www.google.com/finance/portfolio/<groupUUID1>
Group2, https://www.google.com/finance/portfolio/<groupUUID2>
Group3, https://www.google.com/finance/portfolio/<groupUUID3>
```

2. The value in `Group_Name` you provide in the file does NOT need to be the
same as how the portfolio is called.

3. To find the UUID for the group, navigate to the portfolio in the UI and find
the 32-character long identifier in the address bar when the portfolio is open.

4. Fill up the contents of `data/stonks_*.tsv` file. You can choose to have one file
to contain all your data, or you can define your data across multiple files. All the
data present in the TSV files would be added to your Google Finance Portfolio. Example:

```csv
Symbol	Action	Date	Units	Price/unit	Currency	Group

# Comments are included like this with # in beginning of line
AMZN	BUY	2022-01-01	1.234567	97.76	USD	group1
AMZN	BUY	2023-01-01	2.345678	99.02	USD	group2
AMZN	SELL	2024-01-01	3.456789	95.86	USD	group3
```

5. Note that `Action` can only be either of `BUY`/`SELL`.

6. Note that the values in `Group` column are a subset of `Group_Name` values
we defined in `data/portfolio.csv` file.
   
7. We use venv to install the dependencies as follows:

```commandline
python -m venv venv;
source venv/bin/activate;
pip install -r requirements.txt;
```

8. With the data filled in, run the program as follows:
```commandline
python main.py --email <your_email_here> --password <your_password_here> \
--directory <link_to_data_directory>
```

9. In case MFA is enabled in your account, add `--mfa` switch to your run. It will
insert a 30s wait period which will allow you to finish the MFA for logging in.

10. You can specify if you want to input data only based on the date of transaction:
    1. To only input data after a certain date, use `--start_date` switch
    2. To only input data before a certain date, use `--end_date` switch
    3. To limit input data between a date range, use both switches together

11. You can limit if you want to input data for just one trade symbol.
To do that, specify the symbol using `--symbol` switch.

12. You can also limit if you want to input data for just one portfolio.
To do that, specify the symbol using `--group` switch.

13. You can use all the switches in conjunction with each other to fill
the data as you want.

14. The error messages about the stocks that couldn't be bought would be displayed as
log messages.

15. The script doesn't sell any stocks and will log which stock needs to be sold off.

# Questions?

Open an issue [here](https://github.com/Akshayanti/Google-Finance-Automation/issues).
