import scraper
import data_verification
import write_database

ignore_errors = False

if __name__ == "__main__":
    results = scraper.load_all_hero_data()
    all_ok = data_verification.run_tests(results)
    if(ignore_errors == True or all_ok == True):
        write_database.DatabaseWriter(results, ignore_errors)
    else:
        print("\n*** ERRORS DETECTED, NOT WRITING DATABSE! ***")

