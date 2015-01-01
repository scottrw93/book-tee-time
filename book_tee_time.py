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
import sys
import re

GUI_NUMBER = '31711862'     #Only need that of the person booking line.
PASSWORD = 'xxxxx'
DATE_OF_COMP = '2015-01-07' # MUST follow this format YEAR-MONTH-DAY
TIME_REQ = '12:20'          # MUST be a time in the competition or it will fail
PLAYERS_IDS = ['766']       # Each member has a unique id. Grep the players.txt file to find them.
                            # To book two players use: PLAYERS_IDS = ('xxx','xxx'), for three you
                            # can use PLAYERS_IDS = ('xxx','xxx', 'xxx') etc

#To find bugs if soemthing goes wrong as it runs using a cronjob.
logging.basicConfig(filename='book_tee_time.log', format='%(asctime)s - %(levelname)s - %(message)s', level=logging.DEBUG)

loginPage = 'http://www.brsgolf.com/castle/members_booking.php?operation=member_info'

mech = mechanize.Browser()
mech.set_handle_robots(False)
mech.open(loginPage)

#Login and get page of current competitions
try:
    mech.select_form(nr=0)
    mech['GUILDNUMBER_VALIDATE'] = GUI_NUMBER
    mech['PASSWORD_VALIDATE'] = PASSWORD
    competitions_page = mech.submit()
except:
    logging.error('Failed to load login page. Exiting...')
    sys.exit(1)

soup = BeautifulSoup(competitions_page)

#Runs through all available competitions
for competition in soup.find_all('table', { "class" : "competition_booking_summary_table" }):
    link = competition.find('a')['href']
    date = link.split('&')[2].split('=')[1] # Date of current comp to compare to date specified
    
    if date == DATE_OF_COMP:
        link = 'http://www.brsgolf.com/castle/'+link

        booking_page = mech.open(link)
        soup = BeautifulSoup(booking_page)
        
        available_times = soup.find_all('table', { "class" : "table_white_text" })[0]
        
        #Looks for the time specified by user
        for avail_time in available_times.find_all('tr'):
            
            time = avail_time.find('td', { "class" : "t_h" })
            
            if time and time.get_text() == TIME_REQ:
                
                form = avail_time.find('form')
                
                if form:
                    unique_id = form.find('input', { "name" : "unique_id" })['value']
                    d_date = form.find('input', { "name" : "d_date" })['value']
                    
                    mech.select_form(nr=1)
                    mech.form.set_all_readonly(False)

                    mech['course_id'] = '1' # Never any 10th tee starts for medals
                    mech['unique_id'] = unique_id
                    mech['d_date'] = d_date
                    mech['Booking_Operation'] = 'Book Competition'
                    mech['SubmitButton'] = 'Book Now'
                        
                    mech.submit()

                    mech.select_form(nr=0)
                    mech.form.set_all_readonly(False)
                    
                    #Specify the players you are booking a line for using their unique ids.
                    player_num = 1
                    for user_id in PLAYERS_IDS:
                        try:
                            mech['Player'+str(player_num)+'_uid'] = [user_id]
                        except:
                            logging.error('Failed to book a tee time. Invalid id "'+str(user_id)+'" used.')
                            sys.exit(1)
                        player_num += 1
            
                    mech['Booking_Operation'] = 'Confirm Competition Booking'
                    mech['SubmitButton'] = 'Confirm Booking'
                    
                    if mech.submit():
                        logging.info('Successfully booked a time.')
                        sys.exit(0)
                            
                    logging.error('Failed to book a tee time. Incorrect player id?')
                    sys.exit(1)
                        
                logging.error('Failed to find from to submit players.')
                sys.exit(1)

logging.error('Failed to book a tee time. Incorrect DATE/TIME.')
sys.exit(1)





