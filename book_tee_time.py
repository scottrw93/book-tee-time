# Author:   Scott Williams
# Date:     01-01-15
# About:    Run with a cronjob time for when comp comes live. This is given on the BRS
#           booking site. Saturdays go live 10am Friday the week before. The Script
#           lacks error checking so be carefull to enter data correctly at the top
#           of script as it is easy to make a mistake and there will be no time to
#           re-run it.
# Requires: Mechanize, BeautifulSoup Version 4


from bs4 import BeautifulSoup
import logging
import mechanize
import datetime as dt
import time
import sys
import re

DEFAULT_URL = 'http://www.brsgolf.com/castle'

PLAYERS = dict()
PLAYERS['Nicholas Armstrong']   = '12'
PLAYERS['Eoghan McKeever']      = '469'
PLAYERS['Peter McKeever']       = '471'
PLAYERS['Ross McKeever']        = '1725'
PLAYERS['Ben Murray']           = '1888'
PLAYERS['Peter Murray']         = '530'
PLAYERS['Ross Murray']          = '1751'
PLAYERS['Harry Scott']          = '683'
PLAYERS['John Williams']        = '764'
PLAYERS['Paul Williams']        = '765'
PLAYERS['Scott Williams']       = '766'
PLAYERS['Stephen Williams']     = '1716'


def _parse_date(link):
    competition_details = dict()
    details = link.split('?')[1].split('&')
    for d in details:
        key, value = d.split('=')
        competition_details[key] = value
    return competition_details['d_date']

def _parse_competitions(soup):
    return map(lambda x: x.find('a')['href'], \
        soup.find_all('table', { "class" : "competition_booking_summary_table" }))

def _parse_available_times(soup):
    tables = soup.find_all('table', { "class" : "table_white_text" })[0]
    times = dict()

    for table in tables.find_all('tr'):
        row = table.find('td', { "class" : "t_h" })
        if row:
            times[row.getText()] = table.find('form')
    return times

def _wait_for_timesheet(TIME_SHEET_LIVE):
    current_time, imminent = dt.datetime.now().replace(microsecond=0), False
    while current_time < TIME_SHEET_LIVE:
        current_time = dt.datetime.now().replace(microsecond=0)
        if not imminent:
            time.sleep(abs((current_time - TIME_SHEET_LIVE).total_seconds()) - 10.0)
            imminent = True

#To find bugs if soemthing goes wrong as it runs using a cronjob.
def book_tee_time(GUI_NUMBER, PASSWORD, DATE_OF_COMP, TIME_REQ, PLAYER_NAMES, TIME_SHEET_LIVE=None, booking_page=DEFAULT_URL, players=PLAYERS):

    # Sleep until timesheet is live
    if TIME_SHEET_LIVE:
        _wait_for_timesheet(TIME_SHEET_LIVE)

    player_ids = map(lambda n: players[n], PLAYER_NAMES)

    #Open login page
    mech = mechanize.Browser()
    mech.set_handle_robots(False)
    mech.open(booking_page+'/members_booking.php?operation=member_info')

    #Login and get page of current competitions
    mech.select_form(nr=0)
    mech['GUILDNUMBER_VALIDATE'] = GUI_NUMBER
    mech['PASSWORD_VALIDATE'] = PASSWORD
    competitions_page = mech.submit()

    #Parse competitions to find the correct date. Take the first result as even if there is
    #two comps on the same day they will have the same link
    soup = BeautifulSoup(competitions_page)
    competitions = _parse_competitions(soup)
    competition_link = filter(lambda x: _parse_date(x) == DATE_OF_COMP, competitions)
    timesheet_page = mech.open(booking_page+'/'+competition_link[0])

    #Parse timesheet to find the desired time and select the form associated with it
    soup = BeautifulSoup(timesheet_page)
    available_times = _parse_available_times(soup)
    form = available_times[TIME_REQ]

    #Submit form with desired time so you can select players
    unique_id = form.find('input', { "name" : "unique_id" })['value']
    d_date = form.find('input', { "name" : "d_date" })['value']

    # First two forms are unrelated to tee times. You don't have to select the form
    # associated with the specific time, any form is sufficent. 
    mech.select_form(nr=2)
    mech.form.set_all_readonly(False)

    mech['course_id'] = '1'
    mech['unique_id'] = unique_id
    mech['d_date'] = d_date
    mech['Booking_Operation'] = 'Book Competition'
    mech['SubmitButton'] = 'Book Now'
    mech.submit()

    #Submit form with selected players
    mech.select_form(nr=0)
    mech.form.set_all_readonly(False)
    
    for i, user_id in enumerate(player_ids):
        mech['Player'+`i+1`+'_uid'] = [user_id]
    mech['Booking_Operation'] = 'Confirm Competition Booking'
    mech['SubmitButton'] = 'Confirm Booking'

    print 'Booked tee-time' if mech.submit() else 'Failed to book tee time'

book_tee_time('xxx', 'xxx', '2016-05-14', '15:40', ['Scott Williams'], TIME_SHEET_LIVE=dt.datetime(2016, 5, 12, 10, 0, 0))



