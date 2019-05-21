#!/usr/bin/env python3
'''
Check Sammy is a GUI tool for checksumming stuff (using the md5 algorithm).
It stores the hash values in separate json files (SomePath/InputFileName.md5).
The same files can be used for running integrity checks. In this case Sammy will look
for the json in whatever new path the file has been moved to (SomeOtherPath/InputFileName.md5).
Sammy was born at the Austrian Film Museum in 2019.

"Hoog Sammy, kijk omhoog Sammy
Anders is het vast te laat"
'''

from tkinter import *
from tkinter import filedialog
import multiprocessing.dummy as mp
import tkinter as tk
import os
import hashlib
import json
import threading
import datetime


class SammyGUI(tk.Tk):
    # In this class all the widgets and methods of the GUI.
    def __init__(self):
        super().__init__()

        self.checksummer = CheckSammy()

        self.version = '0.6.3'
        self.title('Check Sammy %s' % self.version)
        self.iconbitmap(os.path.abspath('media/paw.ico'))

        self.check_this = {'F': [], 'D': []}
        self.checked = {'Ok': [], 'Corrupted': [],
                        'No md5': [], 'Missing file': [], 'New file': []}

        self.button_frame = tk.Frame(self)
        self.button_frame.grid(row=1, column=0, pady=5, padx=5)

        self.recursive_button = tk.Button(
            self.button_frame, text='   All in one folder   ', command=self.sel_pathr)
        self.recursive_button.grid(
            row=1, column=0, sticky='N', padx=2, pady=10)

        self.folder_button = tk.Button(
            self.button_frame, text='Single folder', command=self.sel_dir)
        self.folder_button.grid(row=2, column=0, sticky='N', padx=2, pady=2)

        self.file_button = tk.Button(
            self.button_frame, text='Single file', command=self.sel_file)
        self.file_button.grid(row=3, column=0, sticky='N', pady=2)

        self.start_button = tk.Button(self.button_frame, text='Start', command=lambda: threading.Thread(
            target=self.start, args=()).start())
        self.start_button.grid(row=5, sticky='N', pady=2)

        self.status_label = tk.Label(self.button_frame, text='Ready')
        self.status_label.grid(row=6, sticky='N', pady=20)

        self.sammy = tk.PhotoImage(file='media/dog.png')

        self.sammy_frame = tk.Frame(self.button_frame)
        self.sammy_frame.grid(row=4, column=0)

        self.sammy_label = tk.Label(self.sammy_frame, image=self.sammy)
        self.sammy_label.grid(pady=10)

        self.batch_frame = tk.Frame(self, width=1700)
        self.batch_frame.grid(row=0, column=1, rowspan=2)

        self.batch_yscrollbar = tk.Scrollbar(
            self.batch_frame, orient='vertical')
        self.batch_yscrollbar.grid(row=1, column=2, rowspan=2, sticky='NS')

        self.batch_xscrollbar = tk.Scrollbar(
            self.batch_frame, orient='horizontal')
        self.batch_xscrollbar.grid(row=2, column=0, columnspan=2, sticky='WE')

        self.batch_label = tk.Label(
            self.batch_frame, text='Queue (0)', borderwidth=4, relief='groove', width=100)
        self.batch_label.grid(row=0, column=1, sticky='W', pady=5)

        self.batch_button = tk.Button(
            self.batch_frame, text='Delete', command=self.delete_item)
        self.batch_button.grid(row=0, column=0, sticky='W', pady=5, padx=10)

        self.batch_listbox = tk.Listbox(self.batch_frame, yscrollcommand=self.batch_yscrollbar.set,
                                        xscrollcommand=self.batch_xscrollbar.set, width=180, height=23)
        self.batch_listbox.configure(activestyle='none', highlightthickness=0)

        self.batch_yscrollbar.configure(command=self.batch_listbox.yview)
        self.batch_xscrollbar.configure(command=self.batch_listbox.xview)

        self.batch_listbox.grid(row=1, column=0, columnspan=2)

        self.batch_frame.bind(
            '<Leave>', lambda x: self.batch_listbox.selection_clear(0, END))

        self.control_frame = tk.Frame(self)
        self.control_frame.grid(row=0, column=0)

        self.reset_button = tk.Button(
            self.control_frame, text='Reset', command=self.reset)
        self.reset_button.grid(sticky='N', pady=10)

        self.sel_operation = IntVar()
        self.calculate = tk.Radiobutton(self.control_frame, text='Calculate md5', variable=self.sel_operation,
                                        value=1, tristatevalue=4, command=lambda: self.status_label.configure(text='Ready'))
        self.calculate.grid(row=1, column=0, sticky='w')
        self.difference = tk.Radiobutton(self.control_frame, text='Check difference', variable=self.sel_operation,
                                         value=2, tristatevalue=4, command=lambda: self.status_label.configure(text='Ready'))
        self.difference.grid(row=2, column=0, sticky='w')
        self.difference.grid(row=3, column=0, sticky='w')

    def delete_item(self):
        # Deletes the selected item from the batch listbox.
        try:
            item_text = self.batch_listbox.get(
                self.batch_listbox.curselection())
            if item_text[2] == 'F':
                self.check_this['F'].remove(item_text.split('"')[1])
            elif item_text[2] == 'D':
                self.check_this['D'].remove(item_text.split('"')[1])

            self.batch_listbox.delete(self.batch_listbox.curselection())
            self.batch_label.configure(
                text='Queue (%s)' % str(self.batch_listbox.size()))
        except:
            pass

    def sel_file(self):
        # Opens filedialog window for selecting files to add to the batch.
        files = filedialog.askopenfilenames()
        for file in files:
            if not os.path.abspath(file) in self.check_this['F'] and file != '':
                self.check_this['F'].append(os.path.abspath(file))
        self.update_batch()

    def sel_dir(self):
        # Opens filedialog window for selecting a folder to add to the batch.
        # All the files in the folder (and recursively in the subfolders) will
        # be checksummed individually.
        dir = filedialog.askdirectory()
        if not dir in self.check_this['D']:
            if dir != '':
                self.check_this['D'].append(os.path.abspath(dir))
        self.update_batch()

    def sel_pathr(self):
        # Opens filedialog window for selecting a folder.
        # Every file and/or folder inside the chosen directory will be added
        # to the batch.
        dir = filedialog.askdirectory()
        if dir != '':
            root, dirs, files = next(os.walk(dir))
            for d in dirs:
                self.check_this['D'].append(
                    os.path.abspath(os.path.join(root, d)))
            for f in files:
                if not '.md5' in f:
                    self.check_this['F'].append(
                        os.path.abspath(os.path.join(root, f)))
            self.update_batch()

    def update_batch(self):
        # Updates the batch listbox.
        self.batch_listbox.delete(0, END)

        for file in self.check_this['F']:
            self.batch_listbox.insert(END, ' -F - "%s"' % file)

        for folder in self.check_this['D']:
            self.batch_listbox.insert(END, ' -D - "%s"' % folder)

        self.status_label.configure(text='Ready')
        self.batch_label.configure(text='Queue (%s)' %
                                   str(self.batch_listbox.size()))

    def report(self):
        # Generates the report of the fixity check.
        ok = len(self.checked['Ok'])
        corr = len(self.checked['Corrupted'])
        no_cs = len(self.checked['No md5'])
        missing = len(self.checked['Missing file'])
        new = len(self.checked['New file'])
        tot = ok + corr + no_cs + missing + new

        self.report_window = tk.Toplevel(self)
        self.report_window.iconbitmap(os.path.abspath('media/paw.ico'))
        self.report_window.title('Report')

        self.report_yscrollbar = tk.Scrollbar(
            self.report_window, orient='vertical')
        self.report_yscrollbar.grid(row=0, column=1, sticky='NS')

        self.report_text = tk.Text(self.report_window, width=100, height=30,
                                   yscrollcommand=self.report_yscrollbar.set, state=DISABLED, wrap=WORD)
        self.report_text.grid(row=0, column=0)

        self.report_yscrollbar.configure(command=self.report_text.yview)

        self.report_button = tk.Button(
            self.report_window, text='Save report', command=self.save_report)
        self.report_button.grid(row=1, column=0, pady=5)

        self.report_text.configure(state=NORMAL)
        self.report_text.delete(1.0, END)
        self.report_text.insert(END, 'Fixity check summary:\n\n---\n%s files/folders checked.\n---\n\nOk: %s.\nCorrupted: %s.\nMissing: %s.\nNew/Unknown: %s.\n---\n\n' %
                                (str(tot), str(ok), str(corr), str(missing), str(new)))

        if no_cs > 0:
            self.report_text.insert(
                END, "Sammy couldn't find a valid .md5 for %s files/folders.\n------------\n\n\n" % str(no_cs))
        else:
            self.report_text.insert(
                END, 'All the .md5 were found.\n------------\n\n\n')

        if corr > 0:
            self.report_text.insert(
                END, 'The following files/folders are corrupted:\n\n')
            for obj in self.checked['Corrupted']:
                self.report_text.insert(END, "'" + obj + "'\n")
            self.report_text.insert(END, '---\n\n\n')

        if missing > 0:
            self.report_text.insert(
                END, 'The following files/folders are missing:\n\n')
            for obj in self.checked['Missing file']:
                self.report_text.insert(END, "'" + obj + "'\n")
            self.report_text.insert(END, '---\n\n\n')

        if new > 0:
            self.report_text.insert(
                END, 'The following files/folders are new/unknown:\n\n')
            for obj in self.checked['New file']:
                self.report_text.insert(END, "'" + obj + "'\n")
            self.report_text.insert(END, '---\n\n\n')

        if no_cs > 0:
            self.report_text.insert(
                END, 'The following .md5 files are missing:\n\n')
            for obj in self.checked['No md5']:
                self.report_text.insert(END, "'" + obj + "'\n")
            self.report_text.insert(END, '---\n\n\n')

        if ok > 0:
            self.report_text.insert(
                END, 'The following files/folders are ok:\n\n')
            for obj in self.checked['Ok']:
                self.report_text.insert(END, "'" + obj + "'\n")
            self.report_text.insert(END, '---\n\n\n')

        self.report_text.insert(END, 'Report generated by \'Check Sammy %s\' on %s' % (
            self.version, str(datetime.date.today())))

        self.report_text.configure(state=DISABLED)
        self.status_label.configure(text='Ready')
        self.checked = {'Ok': [], 'Corrupted': [],
                        'No md5': [], 'Missing file': [], 'New file': []}

    def save_report(self):
        # Stores report in a .txt file.
        try:
            with open(filedialog.asksaveasfilename(defaultextension='.txt', filetypes=(('Text file', '*.txt'), ('All files', '*.*'))), 'w+', encoding='utf8') as dot_txt:
                dot_txt.write(self.report_text.get(1.0, END))
        except FileNotFoundError:
            pass

    def reset(self):
        # Empties the batch
        self.check_this = {'F': [], 'D': []}
        self.checked = {'Ok': [], 'Corrupted': [],
                        'No md5': [], 'Missing file': [], 'New file': []}
        self.batch_listbox.delete(0, END)
        self.update_batch()
        self.status_label.configure(text='Ready')

    def start(self):
        # This method starts the selected operation (either create checksums or
        # check their difference) for all of the files/folders in the batch listbox.
        if self.check_this == {'F': [], 'D': []}:
            self.status_label.configure(text='Batch empty')
        else:
            if self.sel_operation.get() == 1:
                self.status_label.configure(text='Working...')

                before = datetime.datetime.now()
                workers = mp.Pool(8)

                workers.map(self.checksummer.save_md5, self.check_this['F'])

                for dir in self.check_this['D']:
                    self.hash_dict = {}
                    self.hash_dict['PARENT FOLDER'] = os.path.basename(dir)
                    for root, folders, files in os.walk(dir):
                        a = []
                        for file in files:
                            to_hash = os.path.join(root, file)
                            a.append((dir, to_hash))

                        workers.starmap(self.checksummer.get_hash_dict, a)

                    js = json.dumps(self.hash_dict, indent=4)
                    with open(dir + '.md5', 'w+') as dot_md5:
                        dot_md5.write(js)

                workers.close()
                workers.join()

                print('Finished after: ' + str(datetime.datetime.now() - before))
                self.status_label.configure(text='Done')

            elif self.sel_operation.get() == 2:
                self.status_label.configure(text='Working...')

                workers = mp.Pool(8)

                workers.map(self.checksummer.check_md5, self.check_this['F'])

                a = []
                for dir in self.check_this['D']:
                    a.append((dir, 1))

                workers.starmap(self.checksummer.check_md5, a)

                workers.close()
                workers.join()

                self.report()
                self.status_label.configure(text='Done')

            else:
                self.status_label.configure(text="Sammy's confused...")


class CheckSammy():
    # This class is the actual 'checksum' handler.
    def calc_md5(self, file):
        # Calculates the md5 for the selected file.
        h = hashlib.md5()

        with open(file, 'rb') as tohash:
            for chunk in iter(lambda: tohash.read(4096), b''):
                h.update(chunk)

        return(h.hexdigest())

    def check_md5(self, ff, switch=0):
        # Calculates a new checksum and confronts it with the one stored in the json.
        if switch == 0:
            try:
                old_cs = json.load(open(ff + '.md5'))[os.path.basename(ff)]
                new_cs = self.calc_md5(ff)
                if old_cs == new_cs:
                    puppy.checked['Ok'].append(ff)
                else:
                    puppy.checked['Corrupted'].append(ff)
            except FileNotFoundError:
                puppy.checked['No md5'].append(ff + '.md5')

        elif switch == 1:
            try:
                old_hash_dict = json.load(open(ff + '.md5'))
                new_hash_dict = {}
                for root, folders, files in os.walk(ff):
                    for file in files:
                        to_hash = os.path.join(root, file)
                        new_hash_dict['PARENT FOLDER'] = os.path.basename(ff)
                        new_hash_dict[to_hash.replace(
                            ff, '')[1:]] = self.calc_md5(to_hash)

                for obj in old_hash_dict:
                    if not obj in new_hash_dict:
                        puppy.checked['Missing file'].append(
                            os.path.join(new_hash_dict['PARENT FOLDER'], obj))

                for obj in new_hash_dict:
                    if not obj in old_hash_dict:
                        puppy.checked['New file'].append(
                            os.path.join(new_hash_dict['PARENT FOLDER'], obj))
                    else:
                        if new_hash_dict[obj] == old_hash_dict[obj]:
                            if obj != 'PARENT FOLDER':
                                puppy.checked['Ok'].append(os.path.join(
                                    new_hash_dict['PARENT FOLDER'], obj))
                        else:
                            puppy.checked['Corrupted'].append(
                                os.path.join(new_hash_dict['PARENT FOLDER'], obj))

            except FileNotFoundError:
                puppy.checked['No md5'].append(ff + '.md5')

    def save_md5(self, file):
        # Starts the calc_md5 method and stores the results in a dictionary.
        # Then dumps the dictionary into a json file.
        hash_dict = {}
        hash_dict[os.path.basename(file)] = self.calc_md5(file)

        js = json.dumps(hash_dict, indent=4)
        with open(file + '.md5', 'w+') as dot_md5:
            dot_md5.write(js)

    def get_hash_dict(self, dir, to_hash):
        # Starts the calc_md5 method and stores the results in a dictionary.
        puppy.hash_dict[to_hash.replace(dir, '')[1:]] = self.calc_md5(to_hash)


puppy = SammyGUI()
puppy.mainloop()
