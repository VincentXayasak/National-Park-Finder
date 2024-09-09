import tkinter as tk
from tkinter.messagebox import showinfo
import json
import requests
import os
import tkinter.filedialog
import threading
import time
import queue

API_KEY = "jz3Js8BTMlplh65eqZpyxMcKD6dUwaMlYE799poK"

class Window(tk.Tk):
    """Window class"""
    
    def __init__(self):
        super().__init__()

        self.stateParks = {}
        self.queue = queue.Queue()

        with open("states_hash.json", "r") as f:
            states = {value: key for key, value in json.load(f).items()}

        self.title("US NPS")
        self.geometry("800x800+800+100")
        self.resizable(False, False)

        titleLabel = tk.Label(self,text="National Park Finder",font=("Arial", 25, "bold"),fg="black",anchor="center",justify="center",)
        titleLabel.pack(pady=10)

        instructLabel = tk.Label(self,text="Select Up To 5 States",font=("Arial", 15),fg="black",anchor="center",justify="center",)
        instructLabel.pack(pady=10)

        LB = tk.Listbox(self, selectmode="multiple", width=50, height=10)
        LB.insert(tk.END, *states.keys())

        scrollbar = tk.Scrollbar(self)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        LB.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=LB.yview)

        self.choice = True

        def setStates(firstChoice):
            """Callback function from button."""
            if firstChoice:
                if 0 < len(LB.curselection()) < 6:

                    def apiCall(state):
                        """API call and creates data structure."""
                        data = requests.get("https://developer.nps.gov/api/v1/parks?stateCode="+states[state],headers={"X-Api-Key": API_KEY},)

                        self.stateParks[state] = {
                            d["name"]: {
                                "fullname": d["fullName"],
                                "description": d["description"],
                                "activities": ", ".join(
                                    [inner_dict["name"] for inner_dict in d["activities"]]
                                ),
                                "url": d["url"],
                            }
                            for d in data.json()["data"]
                        }
                        total = data.json()["total"]
                        self.queue.put((state, total))

                    def fetchParks():
                        """Fetches park data."""
                        threads = []
                        start = time.time()
                        for index in LB.curselection():
                            state = LB.get(index)
                            t = threading.Thread(target=apiCall, args=(state,))
                            threads.append(t)
                            t.start()

                        for t in threads:
                            t.join()
                        print("Total Time For Requests:", time.time() - start, "Seconds")

                        self.after(0, showParkInfo)

                    def showParkInfo():
                        """Changes instructions."""
                        instructLabel.config(text="Select Parks To Save Park Info To File")
                        button.config(text="Save")

                        LB.delete(0, tk.END)
                        for state in self.stateParks.keys():
                            LB.insert(tk.END,*[state + ": " + park for park in self.stateParks[state].keys()],)

                        self.choice = False

                    threading.Thread(target=fetchParks).start()
                else:
                    showinfo("Error", "Pick 1-5 States!", parent=self)
            else:
                if len(LB.curselection()) > 0:
                    chosenDirectory = tk.filedialog.askdirectory(initialdir=".")

                    if chosenDirectory:
                        parkDict = {}
                        for index in LB.curselection():
                            state = LB.get(index).split(":")[0]
                            park = LB.get(index).split(":")[1].strip()
                            if state not in parkDict:
                                parkDict[state] = [park]
                            else:
                                parkDict[state].append(park)

                        self.writeJSON(chosenDirectory, parkDict)
                        showinfo("Saved","Saved Files: "+ ", ".join([state + ".json" for state in parkDict.keys()]),parent=self,)
                        raise SystemExit()
                    else:
                        LB.selection_clear(0, tk.END)
                else:
                    showinfo("Error", "No Park Chosen", parent=self)

        button = tk.Button(self, text="Submit Choice", command=lambda: setStates(self.choice))
        LB.pack()
        button.pack(pady=10)

        statusLabel = tk.Label(self, text="", font=("Arial", 12), fg="black", anchor="center", justify="center")
        statusLabel.pack(pady=10)

        self.processQueue(statusLabel)

    def processQueue(self, statusLabel):
        """Checks queue."""
        while not self.queue.empty():
            data = self.queue.get()
            self.updateStatus(data, statusLabel)

        self.after(100, self.processQueue, statusLabel)

    resultList = []

    def updateStatus(self, data, statusLabel):
        """Update the status."""
        state, total = data
        self.resultList.append(state + ": " + str(total))
        statusLabel.config(text="Result: " + ", ".join(self.resultList))

    def writeJSON(self, directory, parkDict):
        """Write to JSON file."""
        for state, parks in parkDict.items():
            filePath = os.path.join(directory, state + ".json")
            transportData = []
            for park in parks:
                transportData.append(
                    {
                        park: {
                            "full name": self.stateParks[state][park]["fullname"],
                            "description": self.stateParks[state][park]["description"],
                            "activities": self.stateParks[state][park]["activities"],
                            "url": self.stateParks[state][park]["url"],
                        }
                    }
                )
            with open(filePath, "w") as f:
                json.dump(transportData, f, indent=3)

if __name__ == "__main__":
    Window().mainloop()