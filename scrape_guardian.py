############################################################################################################
#                                                                                                          #
#        Run script with command line args:                                                                #
#        python3 Scrape_Guardian.py latest_crossword_number:int /path/to/output/directory:str              #
#                                                                                                          #
############################################################################################################

from urllib.request import urlopen
import re
import html
from unidecode import unidecode
import json
from urllib.error import HTTPError
import sys
import os
from datasets import load_dataset

def clean(str, typestr):
    
    str = re.sub("&quot;", "", str)
    str = re.sub(f"{typestr}:", "", str) 
    str = html.unescape(str)
    str = unidecode(str)
    return str

def separate(ans, sep):

    symbol = sep[1] 
    if symbol==",":
        symbol = " "
         
    loc = eval(sep[3:-1])
    prev = 0
    result = ""

    for i in loc:
        substr = ans[prev:i]
        prev = i
        result = result + substr + symbol
    
    result = result + ans[i:]

    return result

def fix(clue, ans, sep):

    if clue[0:3]=="See":
        return None
    
    enum = re.findall("\(.*?\)", clue)[-1]
    symbol = sep[1]
    enum = re.sub(symbol, " ", enum)
    tot = sum([int(i) for i in enum[1:-1].split()])

    if len(ans)!=tot:
        return None
    elif sep=="{}":
        return clue, ans
    else:
        return clue, separate(ans, sep)
    
def cw_write(html_dec, output_file):
    
    match_results = re.search("data-crossword-data=\".*?\">", html_dec, re.IGNORECASE)
    crossword_data = match_results.group()
    f = open(output_file, "a", encoding="utf-8")

    for match in re.finditer("&quot;clue&quot;.*?&quot;solution&quot;.*?;}", crossword_data):
        clue = re.findall("&quot;clue&quot;:&quot;.*?&quot;", match.group())[0]
        clue = clean(clue, "clue")
        
        sep = re.findall("&quot;separatorLocations&quot;:{.*?},&quot;", match.group())[0]
        sep = clean(sep, "separatorLocations")
        sep = sep[:-1]

        ans = re.findall("&quot;solution&quot;:&quot;.*?&quot;", match.group())[0]
        ans = clean(ans, "solution")
        
        try:
            temp = fix(clue, ans, sep)
        except:
            continue

        if temp is None:
            pass
        else:
            clue, ans = temp
            cw_dict = {"clue":clue, "ans":ans}
            json.dump(cw_dict, f)
            f.write("\n")

    f.close()

def main():
    
    cw_no = int(sys.argv[1])    # latest crossword number
    failures = 0                # counts page not found errors; stops scraping after too many failures 
    time_out_list= []           # saves any crossword numbers whose pages timed out, to retry later

    path = str(sys.argv[2])

    if not os.path.exists(path):
        print("Invalid path")
        sys.exit()

    if path[-1]=='/': 
        output_file = path + 'cryptics.json' 
    else:
        output_file = path + '/cryptics.json'

    while failures < 10000 and cw_no > 0:
        try:
            print(f"Trying crossword no. {cw_no}")
            url = "https://www.theguardian.com/crosswords/cryptic/%d" % (cw_no)  # change cryptic to quiptic for easier 'quiptic' crosswords
            page = urlopen(url, timeout=5)
            html_bytes = page.read()
            html_dec = html_bytes.decode("utf-8")
            cw_write(html_dec, output_file)
            cw_no-=1
            
        except HTTPError:
            print(f"Crossword {cw_no} does not exist.")
            cw_no-=1
            failures+=1

        except TimeoutError:
            print(f"Timeout error for crossword {cw_no}.")  # useful in case of delays due to bad network connection; save no.s to try again later
            cw_no-=1
            time_out_list.append(cw_no)
        
        except KeyboardInterrupt:
            sys.exit()
            
        except Exception as e:
            print(e)
            print(f"Abandoning crossword {cw_no}.")  # to catch any other error
            cw_no-=1
    
    print("Number of crosswords skipped due to timeout: ", len(time_out_list))

    print("Re-scraping timed out crosswords...")

    # Repeat until all timed out crosswords are recovered
    while len(time_out_list)>0:

        time_out_list_2 = []

        for cw_no in time_out_list:
            try:
                print(f"Retrying crossword no. {cw_no}")
                url = "https://www.theguardian.com/crosswords/cryptic/%d" % (cw_no)
                page = urlopen(url, timeout=5)
                html_bytes = page.read()
                html_dec = html_bytes.decode("utf-8")
                cw_write(html_dec, output_file)

            except HTTPError:
                print(f"Crossword {cw_no} does not exist.")

            except TimeoutError:
                print(f"Timeout error for crossword {cw_no}.")
                time_out_list_2.append(cw_no)
            
            except KeyboardInterrupt:
                sys.exit()

            except:
                print(f"Abandoning crossword {cw_no}.")

        time_out_list = time_out_list_2
        print("Number of crosswords left = ", len(time_out_list))

    # Divide into train and test sets, and save
    data_full = load_dataset("json", data_files=output_file, split="train")
    print("No. of clues scraped = ", data_full.shape[0])

    rest_test = data_full.train_test_split(test_size=0.1)
    rest_test["train"].to_json("data_cryptic_train.json")
    rest_test["test"].to_json("data_cryptic_test.json")


if __name__ == "__main__":
    main()