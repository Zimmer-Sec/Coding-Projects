# Intended to be an easy proof of concept for python list creation and web requests. - Kyle Zimmer 7 Oct 2025.

import urllib.request

wordlist_location = 'C:\\Users\\kzimm\\Desktop\\wordlist.txt' # Change to whatever file you want. This list was filled with filenames from my HackTheBox CTF github folder (mixed with random words and capitalization).
file_extensions = {"DIRECTORIES": "/", "MARKDOWN": ".md", "PHP": ".php", "HTML": ".html", "EXE": ".exe", "TXT": ".txt", "Word": "docx", "Libre Office": ".odt", "Excel": ".xlsx", "PDF": ".pdf"}
chosen_extensions = []


def brute(url, wordlist, extensions):
    winners = []
    for ext in extensions: # <- For each file extension, it'll run through the wordlist.
        for i in wordlist:
            tgt = str(url + str(i) + ext)
            try:
                with urllib.request.urlopen(tgt) as response:
                    if response.getcode() == 200:
                        print("WINNER! >>> " + tgt)
                        winners.append(str(tgt))
                    else:
                        print(f"FAILED: {tgt}")
            except Exception as e: # catch errors like connection refused/DNS
                print(f"Error: {str(e)}")
    return winners


with open(wordlist_location, 'r') as wl: # <- create list from the given wordlist file
    words = [line.strip() for line in wl]

print("Zimmer-Sec Proof of Concept Directory Brute Forcing Python Script -- I don't expect anyone to actually run or read this\n\n\n\n\n")
target_protocol = str(input("HTTPS or HTTP? \n\n>>> ").lower())
target_address = str(input("\n\nEnter your target's domain name or IP addr.\n\n>>>> "))
# target_port = str(input("Does your target use a non-standard port? Hit Enter for no: \n>>> ")) <- the : at the end of target_url was monkeying it up if there's wasn't non-standard port... removed due to unlikelyness of https:// or http:// not directing to it.

print("\n\nPlease select which file types you'd like to search for. Type 'continue' to finish.\n\n")
while True:
    for i in file_extensions:
        print(i, end="    ")
    choice = str(input("\n\n>>> "))
    if choice.lower() == "continue":
        break
    elif file_extensions.get(choice):
        chosen_extensions.append(file_extensions.get(choice))
        file_extensions.__delitem__(choice)
        print(chosen_extensions)
    else:
        print("Invalid input. Make sure that it's spelt the exact same as the listed option...")


target_url = target_protocol + "://" + target_address + "/"
start_choice = input(f"\n\n{target_url} with file types: {str(chosen_extensions)} \n FIRE or QUIT ?:\n\n>>> ")
while True:
    if start_choice.lower() == "fire":
        winners = brute(target_url, words, chosen_extensions)
        print("\n\n\n The following locations exist:\n======================================")
        for i in range(len(winners)):
            print(winners[i])
        break
    elif start_choice.lower() == "quit":
        print("goodbye...")
        break
    else:
        print("Invalid choice.")
