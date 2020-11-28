import mechanize
import datetime as dt
import time
import sys
import re

USER_AGENT = "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1"

PLAYERS = {
    "Guest": "Guest",
}


def wait_until(time):
    current_time, imminent = dt.datetime.now().replace(microsecond=0), False
    while current_time < time:
        current_time = dt.datetime.now().replace(microsecond=0)
        if not imminent:
            time.sleep(abs((current_time - time).total_seconds()) - 10.0)
            imminent = True


def book_tee_time(
    gui_number,
    password,
    tee_time,
    player_names,
    time_sheet_live=None,
    dry_run=False,
):
    # Sleep until 20 seconds before live, then login
    if time_sheet_live:
        wait_until(time_sheet_live - dt.timedelta(seconds=20))

    # Open login page
    mech = mechanize.Browser()
    mech.set_handle_robots(False)
    mech.addheaders = [("User-agent", USER_AGENT)]

    mech.open("https://www.brsgolf.com/castle/member/login")

    # Login and get page of current competitions
    mech.select_form(nr=0)
    mech["_username"] = gui_number
    mech["_password"] = password
    mech.submit()

    # Wait for timesheet to go live
    if time_sheet_live:
        wait_until(time_sheet_live)

    # Parse competitions to find the correct date. Take the first result as even if there is
    # two comps on the same day they will have the same link
    date_required = "{:%Y-%m-%d}".format(tee_time)
    for link in mech.links():
        if date_required in link.url:
            mech.follow_link(link)
            break

    # Find correct tee time to book
    time_required = "{:%H:%M}".format(tee_time)
    for pos, form in enumerate(mech.forms()):
        for control in form.controls:
            if time_required in str(form):
                mech.form = list(mech.forms())[pos]
                break
    mech.submit()

    mech.select_form(nr=0)

    player_ids = map(lambda name: PLAYERS[name], player_names)
    for index, player_id in enumerate(player_ids, start=1):
        mech["Player{}_uid".format(index)] = [player_id]

    if dry_run:
        print("Would have booked tee-time")
    else:
        print("Booked tee-time" if mech.submit() else "Failed to book tee time")


book_tee_time(
    "xxx",
    "xxx",
    dt.datetime(2021, 6, 21, 18, 40, 0),
    ["Guest"],
    time_sheet_live=dt.datetime(2020, 11, 28, 17, 50, 0),
    dry_run=True,
)
