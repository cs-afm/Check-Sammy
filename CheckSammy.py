#!/usr/bin/env python3.6
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
import shutil


class SammyGUI(tk.Tk):
    # In this class all the widgets and methods of the GUI.
    def __init__(self):
        super().__init__()

        self.checksummer = CheckSammy()

        self.version = '0.7.4'
        self.title('Check Sammy %s' % self.version)

        if os.name == 'nt':
            self.iconbitmap(os.path.abspath('./media/paw.ico'))

        self.resizable(False,False)

        self.check_this = {'F': [], 'D': []}
        self.checked = {'Ok': [], 'Corrupted': [],
                        'No md5': [], 'Missing file': [], 'New file': []}

        self.button_frame = tk.Frame(self)
        self.button_frame.grid(row=1, column=0, pady=5, padx=5)

        self.recursive_button = tk.Button(
            self.button_frame, text='   All in one folder   ', command=self.add_all_in_directory)
        self.recursive_button.grid(
            row=1, column=0, sticky='N', padx=2, pady=10)

        self.folder_button = tk.Button(
            self.button_frame, text='Single folder', command=self.add_directory)
        self.folder_button.grid(row=2, column=0, sticky='N', padx=2, pady=2)

        self.file_button = tk.Button(
            self.button_frame, text='Single file', command=self.add_file)
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
        self.batch_yscrollbar.grid(row=1, column=3, rowspan=2, sticky='NS')

        self.batch_xscrollbar = tk.Scrollbar(
            self.batch_frame, orient='horizontal')
        self.batch_xscrollbar.grid(row=2, column=0, columnspan=3, sticky='WE')

        self.batch_label = tk.Label(
            self.batch_frame, text='Queue (0)', borderwidth=4, relief='groove', width=100)
        self.batch_label.grid(row=0, column=2, sticky='W', pady=5)

        self.batch_remove_button = tk.Button(
            self.batch_frame, text='Remove', command=self.remove_item)
        self.batch_remove_button.grid(row=0, column=0, sticky='W', pady=5, padx=10)

        self.batch_tranfer_button = tk.Button(
            self.batch_frame, text='Safe transfer', command=self.open_safe_transfer)
        self.batch_tranfer_button.grid(row=0, column=1, sticky='W', pady=5, padx=10)

        self.batch_listbox = tk.Listbox(self.batch_frame, yscrollcommand=self.batch_yscrollbar.set,
                                        xscrollcommand=self.batch_xscrollbar.set, width=180, height=23)
        self.batch_listbox.configure(activestyle='none', highlightthickness=0)

        self.batch_yscrollbar.configure(command=self.batch_listbox.yview)
        self.batch_xscrollbar.configure(command=self.batch_listbox.xview)

        self.batch_listbox.grid(row=1, column=0, columnspan=3)

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

    def open_safe_transfer(self):
        x = self.winfo_x()
        y = self.winfo_y()

        self.transfer_window = tk.Toplevel()
        self.transfer_window.grab_set()
        self.transfer_window.title('Safe Transfer')
        if os.name == 'nt':
            self.transfer_window.iconbitmap(os.path.abspath('./media/paw.ico'))
        self.transfer_window.geometry(f'650x160+{x+145}+{y+80}')
        self.transfer_window.resizable(False, False)

        self.transfer_dst_button = tk.Button(self.transfer_window, text='Select target folder:',command=self.select_target_directory)
        self.transfer_dst_button.place(x=250,y=20,width=150)

        self.transfer_dst_entry = tk.Entry(self.transfer_window,state=DISABLED,width=100)
        self.transfer_dst_entry.place(x=15,y=70,width=620)

        self.transfer_start_button = tk.Button(self.transfer_window, text='Start transfer',command=lambda: threading.Thread(
            target=self.safe_transfer, args=()).start())
        self.transfer_start_button.place(x=275,y=110,width=100)

    def select_target_directory(self):
        dst = filedialog.askdirectory()

        self.transfer_dst_entry.configure(state=NORMAL)
        self.transfer_dst_entry.insert(0,dst)
        self.transfer_dst_entry.configure(state=DISABLED)

    def remove_item(self):
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

    def add_file(self):
        # Opens filedialog window for selecting files to add to the batch.
        files = filedialog.askopenfilenames()
        for file in files:
            if not os.path.abspath(file) in self.check_this['F'] and file != '':
                self.check_this['F'].append(os.path.abspath(file))
        self.update_batch()

    def add_directory(self):
        # Opens filedialog window for selecting a folder to add to the batch.
        # All the files in the folder (and recursively in the subfolders) will
        # be checksummed individually.
        dir = filedialog.askdirectory()
        if not dir in self.check_this['D']:
            if dir != '':
                self.check_this['D'].append(os.path.abspath(dir))
        self.update_batch()

    def add_all_in_directory(self):
        # Opens filedialog window for selecting a folder.
        # Every file and/or folder inside the chosen directory will be added
        # to the batch.
        dir = filedialog.askdirectory()
        if dir != '':
            root, dirs, files = next(os.walk(dir))
            for d in dirs:
                self.check_this['D'].append(
                    os.path.abspath(self.checksummer.join_path(root, d)))
            for f in files:
                if not '.md5' in f:
                    self.check_this['F'].append(
                        os.path.abspath(self.checksummer.join_path(root, f)))
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

    def report(self,transfer=False):
        # Generates the report of the fixity check.
        ok_count = len(self.checked['Ok'])
        corrupted_count = len(self.checked['Corrupted'])
        no_checksum_count = len(self.checked['No md5'])
        missing_count = len(self.checked['Missing file'])
        new_file_count = len(self.checked['New file'])
        total_count = ok_count + corrupted_count + no_checksum_count + missing_count + new_file_count

        self.report_window = tk.Toplevel(self)
        if os.name == 'nt':
            self.report_window.iconbitmap(os.path.abspath('./media/paw.ico'))
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
        operation = 'checked' if transfer == False else 'transferred'
        self.report_text.insert(END, 'Fixity check summary:\n\n---\n%s files/folders %s.\n---\n\nOk: %s.\nCorrupted: %s.\nMissing: %s.\nNew/Unknown: %s.\n---\n\n' %
                                (str(total_count), operation, str(ok_count), str(corrupted_count), str(missing_count), str(new_file_count)))

        if no_checksum_count > 0:
            self.report_text.insert(
                END, "Sammy couldn't find a valid .md5 for %s files/folders.\n------------\n\n\n" % str(no_checksum_count))
        else:
            self.report_text.insert(
                END, 'All the .md5 were found.\n------------\n\n\n')

        if corrupted_count > 0:
            self.report_text.insert(
                END, 'The following files/folders are corrupted:\n\n')
            for obj in self.checked['Corrupted']:
                self.report_text.insert(END, "'" + obj + "'\n")
            self.report_text.insert(END, '---\n\n\n')

        if missing_count > 0:
            self.report_text.insert(
                END, 'The following files/folders are missing:\n\n')
            for obj in self.checked['Missing file']:
                self.report_text.insert(END, "'" + obj + "'\n")
            self.report_text.insert(END, '---\n\n\n')

        if new_file_count > 0:
            self.report_text.insert(
                END, 'The following files/folders are new/unknown:\n\n')
            for obj in self.checked['New file']:
                self.report_text.insert(END, "'" + obj + "'\n")
            self.report_text.insert(END, '---\n\n\n')

        if no_checksum_count > 0:
            self.report_text.insert(
                END, 'The following .md5 files are missing:\n\n')
            for obj in self.checked['No md5']:
                self.report_text.insert(END, "'" + obj + "'\n")
            self.report_text.insert(END, '---\n\n\n')

        if ok_count > 0:
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
                self.create_md5()

            elif self.sel_operation.get() == 2:
                self.compare_checksums()

            else:
                self.status_label.configure(text="Sammy's confused...")

    def create_md5(self,transfer=False,dst=None):
        self.status_label.configure(text='Working...')

        before = datetime.datetime.now()
        workers = mp.Pool(8)

        if transfer == False:
            workers.map(self.checksummer.save_md5, self.check_this['F'])
        else:
            args = []
            for file in self.check_this['F']:
                args.append((file,dst))
            workers.starmap(self.checksummer.transfer_save_md5, args)

        for dir in self.check_this['D']:
            self.hash_dict = {}
            self.hash_dict['PARENT FOLDER'] = os.path.basename(dir)
            for root, folders, files in os.walk(dir):
                a = []
                for file in files:
                    to_hash = self.checksummer.join_path(root, file)
                    a.append((dir, to_hash))

                workers.starmap(self.checksummer.get_hash_dict, a)

            js = json.dumps(self.hash_dict, indent=4)
            if transfer == False:
                with open(dir + '.md5', 'w+') as dot_md5:
                    dot_md5.write(js)
            else:
                path = self.checksummer.join_path(dst,dir.split(os.sep)[-1])
                with open(path + '.md5', 'w+') as dot_md5:
                    dot_md5.write(js)

        workers.close()
        workers.join()

        print('Finished after: ' + str(datetime.datetime.now() - before))
        self.status_label.configure(text='Done')

    def compare_checksums(self, transfer=False, check_transferred=None):
        self.status_label.configure(text='Working...')
        to_check = self.check_this if transfer == False else check_transferred

        workers = mp.Pool(8)

        workers.map(self.checksummer.check_md5, to_check['F'])

        a = []
        for dir in to_check['D']:
            a.append((dir, 1))

        workers.starmap(self.checksummer.check_md5, a)

        workers.close()
        workers.join()

        self.report(transfer)
        self.status_label.configure(text='Done')

    def safe_transfer(self):
        if self.transfer_dst_entry.get() != '':
            dst = self.transfer_dst_entry.get()
            self.transfer_window.destroy()

            try:
                if self.check_this == {'F': [], 'D': []}:
                    self.status_label.configure(text='Batch empty')
                else:
                    check_transferred = {'F': [], 'D': []}
                    print('Calculating checksums...')
                    self.create_md5(True,dst)
                    print('Done\n')
                    print('Transferring files...')

                    for file in self.check_this['F']:
                        new_copy = self.checksummer.join_path(dst,file.split(os.sep)[-1])
                        if not os.path.isfile(self.checksummer.join_path(dst,file.split(os.sep)[-1])):
                            shutil.copy(file,dst)
                        else:
                            raise FileExistsError
                        check_transferred['F'].append(new_copy)
                    print('Done\n')
                    print('Transferring folders...')

                    for dir in self.check_this['D']:
                        new_copy = self.checksummer.join_path(dst,dir.split(os.sep)[-1])
                        shutil.copytree(dir,new_copy)
                        check_transferred['D'].append(new_copy)
                    print('Done\n')
                    print('Comparing difference...')

                    self.compare_checksums(True,check_transferred)
                    print('Done')
                    print('----------')

            except FileExistsError:
                print('The destination directory is not empty')








class CheckSammy():
    # This class is the actual 'checksum' handler.
    def join_path(self,a,b):
        return a + '/' + b

    def calculate_md5(self, file):
        # Calculates the md5 for the selected file.
        h = hashlib.md5()

        with open(file, 'rb') as file_data:
            for chunk in iter(lambda: file_data.read(4096), b''):
                h.update(chunk)

        return(h.hexdigest())

    def check_md5(self, path, switch=0):
        # Calculates a new checksum and confronts it with the one stored in the json.
        if switch == 0:
            try:
                previous_checksum = json.load(open(path + '.md5'))[os.path.basename(path)]
                new_checksum = self.calculate_md5(path)
                if previous_checksum == new_checksum:
                    puppy.checked['Ok'].append(os.path.basename(path))
                else:
                    puppy.checked['Corrupted'].append(os.path.basename(path))
            except FileNotFoundError:
                puppy.checked['No md5'].append(os.path.basename(path) + '.md5')

        elif switch == 1:
            new_dict = {}
            new_dict['PARENT FOLDER'] = os.path.basename(path)
            try:
                previous_dict = json.load(open(path + '.md5'))

                for root, folders, files in os.walk(path):
                    for file in files:
                        to_hash = self.join_path(root, file)
                        new_dict[to_hash.replace(
                            path, '')[1:]] = self.calculate_md5(to_hash)

                for obj in previous_dict:
                    if not obj in new_dict:
                        puppy.checked['Missing file'].append(
                            self.join_path(new_dict['PARENT FOLDER'], obj))

                for obj in new_dict:
                    if not obj in previous_dict:
                        puppy.checked['New file'].append(
                            self.join_path(new_dict['PARENT FOLDER'], obj))
                    else:
                        if new_dict[obj] == previous_dict[obj]:
                            if obj != 'PARENT FOLDER':
                                puppy.checked['Ok'].append(self.join_path(
                                    new_dict['PARENT FOLDER'], obj))
                        else:
                            puppy.checked['Corrupted'].append(
                                self.join_path(new_dict['PARENT FOLDER'], obj))

            except FileNotFoundError:
                puppy.checked['No md5'].append(new_dict['PARENT FOLDER'] + '.md5')

    def save_md5(self, file):
        # Starts the calculate_md5 method and stores the results in a dictionary.
        # Then dumps the dictionary into a json file.
        checksum_data = {}
        checksum_data[os.path.basename(file)] = self.calculate_md5(file)

        js = json.dumps(checksum_data, indent=4)
        with open(file + '.md5', 'w+') as file_data:
            file_data.write(js)

    def transfer_save_md5(self, file, dst):
        # Starts the calculate_md5 method and stores the results in a dictionary.
        # Then dumps the dictionary into a json file in the dst folder.
        checksum_data = {}
        checksum_data[os.path.basename(file)] = self.calculate_md5(file)

        js = json.dumps(checksum_data, indent=4)
        path = self.join_path(dst,file.split(os.sep)[-1])
        with open(path + '.md5', 'w+') as file_data:
            file_data.write(js)

    def get_hash_dict(self, dir, to_hash):
        # Starts the calculate_md5 method and stores the results in a dictionary.
        puppy.hash_dict[to_hash.replace(dir, '')[1:].replace(os.sep,'/')] = self.calculate_md5(to_hash)


puppy = SammyGUI()
puppy.mainloop()
