import argparse

from GoogleFinance import GoogleFinance


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", type=str, help="Directory containing the TSV and CSV files", required=True)
    parser.add_argument("-u", "--email", type=str, help="Email Id for logging in to Google", required=True)
    parser.add_argument("-p", "--password", type=str, help="Password for logging in to Google", required=True)
    parser.add_argument("--start_date", type=str, help="Start date (DD-MM-YYYY) when to start register")
    parser.add_argument("--end_date", type=str, help="End date (DD-MM-YYYY) when to end register")
    parser.add_argument("--symbol", type=str, help="Add data for specific symbol")
    parser.add_argument("--group", type=str, help="Add data for specific group")
    args = parser.parse_args()

    google = GoogleFinance(data_dir=args.directory, start_date=args.start_date, end_date=args.end_date)
    google.login_google(email=args.email, password=args.password, two_fa_enabled=True)
    google.start_transactions(specific_symbol=args.symbol, specific_grp=args.group)


if __name__ == "__main__":
    main()
