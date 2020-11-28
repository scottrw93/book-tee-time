import mechanize
import datetime as dt
import time
import sys
import re

USER_AGENT = "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1"

GOLF_CLUBS = {

}

PLAYERS = {

}


def _wait_for_timesheet(TIME_SHEET_LIVE):
    current_time, imminent = dt.datetime.now().replace(microsecond=0), False
    while current_time < TIME_SHEET_LIVE:
        current_time = dt.datetime.now().replace(microsecond=0)
        if not imminent:
            time.sleep(abs((current_time - TIME_SHEET_LIVE).total_seconds()) - 10.0)
            imminent = True


def book_tee_time(
    gui_number,
    password,
    date_of_comp,
    time_required,
    player_names,
    time_sheet_live=None,
    golf_club="castle",
    dry_run=False,
):
    booking_page = GOLF_CLUBS[golf_club]

    # Sleep until timesheet is live
    if time_sheet_live:
        _wait_for_timesheet(time_sheet_live)

    # Open login page
    mech = mechanize.Browser()
    mech.set_handle_robots(False)
    mech.addheaders = [("User-agent", USER_AGENT)]

    mech.open(booking_page + "/member/login")

    # Login and get page of current competitions
    mech.select_form(nr=0)
    mech["_username"] = gui_number
    mech["_password"] = password
    mech.submit()

    # Parse competitions to find the correct date. Take the first result as even if there is
    # two comps on the same day they will have the same link
    for link in mech.links():
        if date_of_comp in link.url:
            mech.follow_link(link)
            break

    # Find correct tee time to book
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
    "111",
    "111",
    "2021-06-21",
    "18:40",
    ["Scott"]
)
