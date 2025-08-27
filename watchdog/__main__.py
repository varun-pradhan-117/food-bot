import time
import datetime
from .watchdog import run_sync

# Scheduled times in 24h format
RUN_HOURS = [9, 14, 20]

def main():
    print("[LISTENER] Starting Google Sheets scheduler...")

    # Run immediately at startup
    print("[LISTENER] Initial sync on startup...")
    run_sync()

    while True:
        now = datetime.datetime.now()
        current_hour = now.hour
        current_minute = now.minute

        if current_hour in RUN_HOURS and current_minute == 0:
            print(f"[LISTENER] Scheduled sync triggered at {now.strftime('%H:%M')}...")
            run_sync()
            # sleep a minute to avoid multiple runs within the same hour:minute
            time.sleep(60)

        # Check every 30 seconds
        time.sleep(30)

if __name__ == "__main__":
    main()
