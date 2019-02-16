import numpy
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pprint

def spreadsheet_setup():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('Guitar Tuning-5cf31322c0b1.json', scope)
    client = gspread.authorize(creds)

    sheet = client.open('Guitar Tuning').sheet1
    return(sheet)

def pull_tunings():
    pieces = []
    data = spreadsheet_setup().get_all_records()
    for i in data:
        tuning = []
        for j in range(6):
            tuning.append(i["String " + str(j+1)])
        pieces.append((i["Piece"],i["Author"],tuning))
    return (pieces)


scale = {"A":0, "A#":1, "B":2, "C":3, "C#":4, "D":5, "D#":6, "E":7, "F":8, "F#":9, "G":10, "G#":11}
id_num = 0
id_tunings = {}
length = None
global_strings = []
used_strings = []

def get_tuning_manual(): # formats given tuning into computer-readable notation
    while True:
        try:
            tuning = []
            octave = []
            for i in range(6):

                # tuning
                note = input("String " + str(i + 1) + ": ").upper()


                if len(note) == 2:                  # Consider if note is flat, e.g. "Ab"
                    if note[1] == "B":
                        format_note = (scale[note[:-1]]-1) % 12
                else:
                    format_note = scale[note]
                tuning.append(format_note)

                # octave
                if i == 0:
                    degree = 0
                else:
                    if tuning[-2] >= tuning[-1]:
                        degree+=1

                octave.append(degree)

            break

        except:
            print("Incorrect input format")

    return ((tuning[0],tuning[1],tuning[2],tuning[3],tuning[4],tuning[5]), (octave[0],octave[1],octave[2],octave[3],octave[4],octave[5]))

def get_tuning_auto(in_tuning):
    try:
        tuning = []
        octave = []
        for i in range(6):

            # tuning
            note = in_tuning[i].upper()

            if len(note) == 2:  # Consider if note is flat, e.g. "Ab"
                if note[1] == "B":
                    format_note = (scale[note[:-1]] - 1) % 12
                else:
                    format_note = scale[note]
            else:
                format_note = scale[note]
            tuning.append(format_note)

            # octave
            if i == 0:
                degree = 0
            else:
                if tuning[-2] >= tuning[-1]:
                    degree += 1

            octave.append(degree)
        return ((tuning[0], tuning[1], tuning[2], tuning[3], tuning[4], tuning[5]),
                (octave[0], octave[1], octave[2], octave[3], octave[4], octave[5]))
    except:
        print("Incorrect input format")

def dif(tun1,tun2): # takes difference between each string of two tunings.
    dif_tun = []
    for i in range(6):
        dif_tun.append((tun1[0][i] + tun1[1][i]*12) - (tun2[0][i] + tun2[1][i]*12))
    return dif_tun

# We need to fix the tuning difference by considering different keys.
# Let a(i) be the difference of the ith string.
def dif_fix(dif_tun):  # Want min total difference. i.e. min[(a(1) + n) + (a(2) + n) + ... + (a(6) + n)]
    k_sum = sum(dif_tun)

    k = k_sum % 6       # want min|k|
    if k_sum % 6 >= 3:
        k = k - 6

    n = int((k-k_sum)/6)         # do some algebra from above to get this expression
    dif_numpy = numpy.array(dif_tun)    # this allows a constant to be added to the whole list
    return dif_numpy + n

'''
TO DO!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
'''
def dif_count(dif_tun, count): # Want max of 'count' number of strings to change. So we must find the amount of strings which have the same difference
    if dif_tun.count(max(set(dif_tun), key = dif_tun.count)) >= 6 - count:
        return True
    else:
        return False


'''
def id(tuning):
    global id_num
    global id_tunings
    print(tuning)
    id_tunings[tuning] = id_num
    id_num+=1
'''
def checker(dif_tun, n): # checks if a difference tuning is acceptable, i.e. max variation of n
    bool = True
    for i in dif_tun:
        if (i < -n) or (i > n):
            bool = False
    return bool


def good_set(tunings, n, count): # find 'good_set's, where a 'good_set' is a list of tunings where its not hard to change between them
    #MUST INPUT FORMATED TUNINGS (but not fixed)
    #differences = {}
    good_sets = []
    global length
    length = len(tunings)
    for i in tunings:
        id(i)
    for i in range(length):
        #print(id_tunings)
        good_set = []
        for j in range(length):
            if i != j:              # better program: i>j (imagine a table of i against j to see where repetition occurs, and hence why this is best)!!!!!!!!!!!!!!!!!!!!
                #differences[(i,j)] = dif_fix((i,j))
                diff = dif(tunings[i], tunings[j])
                if checker(dif_fix(diff), n):
                    if dif_count(diff, count):
                        good_set.append(j)
        good_sets.append(good_set)
    return good_sets
def string_start(good_set):
    for main_tuning in range(length):
        string_inf(good_set[main_tuning], [main_tuning])
def string_inf(variations, string):
    total_strings = []
    for var in variations:
        new_string = string
        new_string.append(var)  # extends string to have variation/main tuning i
        if var not in string: # prevents loops
            for collected_string in string_inf(good_sets[var], new_string): # finds all string variations
                total_strings.append(collected_string)
                # repetition occurs as we let the main tunings turn into variations for their main tuning
        else:
            global_strings.append(string)
    if total_strings==[]:
        global_strings.append(string) # stores all strings together
    return total_strings # returns all string variations of i


def display(id):
    tuning = ""
    for i in pull[id][2]:
        tuning += i + ","
    tuning = tuning[:-1]
    return pull[id][0] + " by " + pull[id][1] + " (" + tuning + ")\n"

if "__main__" == __name__:
    #print(good_set((get_tuning(),get_tuning(),get_tuning())))
    tunings = []
    pull = pull_tunings()
    #pprint.PrettyPrinter().pprint(pull)
    for i in pull:
        tunings.append(get_tuning_auto(i[2]))
    #pprint.PrettyPrinter().pprint(
    good_sets = good_set(tunings, 2, 2)
    results = ""
    for i in range(length):
        line = "Main Tuning: " + display(i)
        line+= "Number of variations: " + str(len(good_sets[i])) + "\n"
        line+= "Variations:\n"

        for j in good_sets[i]:
            tuning = ""
            for k in pull[j][2]:
                tuning += k + ","
            tuning = tuning[:-1]
            line += display(j)
        results+= line+"\n"

    results += "\n\n\n"
    results += "Strings:\n"
    count = 0
    print(good_sets)
    string_start(good_sets)
    pprint.pprint(global_strings)
    '''
    for i in global_strings:
        count += 1
        results += "Set " + str(count) + ":\n"
        print(i)
        for j in i:
            print(j)
            results += display(j)
        results+="\n"
    '''
    file = open('Guitar Tunings.txt','w')
    file.write(results)