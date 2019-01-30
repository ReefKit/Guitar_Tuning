import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pprint

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('Guitar Tuning-5cf31322c0b1.json', scope)
client = gspread.authorize(creds)

sheet = client.open('Guitar Tuning').sheet1


pp = pprint.PrettyPrinter()
tunings = sheet.get_all_records()

pp.pprint(tunings)

'''
sheet.update_cells(2,2, "Wee")
result = sheet.cell(2,2)
pp.pprint(result)
'''