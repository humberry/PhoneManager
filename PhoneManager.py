# coding: utf-8

import datetime, os, ui, shutil, console, sys, clipboard, requests, zipfile, zlib, tarfile, photos, editor, time

def get_dir(path = os.path.expanduser('~')):
    dirs  = [] if path == os.path.expanduser('~') else ['..']
    files = []
    for entry in sorted(os.listdir(path)):
        if os.path.isdir(path + '/' + entry):
            dirs.append(entry)
        else:
            files.append(entry)
    dirs_and_files = []
    for directory in dirs:
        dic = {'accessory_type':'none'}
        dic.setdefault('title', '/' + directory)
        dirs_and_files.append(dic)
    if path != os.path.expanduser('~'):
        for file in files:
            full_pathname = path + '/' + file 
            dic = {'accessory_type':'detail_button'}
            dic.setdefault('title', file)
            dic.setdefault('size', os.path.getsize(full_pathname))
            dic.setdefault('date', datetime.datetime.fromtimestamp(os.path.getmtime(full_pathname)))
            dirs_and_files.append(dic)
    return dirs_and_files

def get_dirs(path = os.path.expanduser('~')):
    dir = [] if path == os.path.expanduser('~') else ['..']
    for entry in sorted(os.listdir(path)):
        if os.path.isdir(path + '/' + entry):
            dir.append(entry)
    dirs = ['/' + directory for directory in dir]
    return dirs

def hex_view(filepath):
    return_value = ''
    try:
        with open(filepath,'rb') as in_file:
            for line in range(0, os.path.getsize(filepath), 16):
                h = s = ''
                for c in in_file.read(16):
                    i = ord(c)
                    h += '{:02X} '.format(i)
                    s += c if 31 < i < 127 else '.'
                return_value += '0x{:08X} | {:48}| {:8}\n'.format(line, h, s)
    except Exception as e:
        return 'Error!\nFile = {}\nError = {}'.format(filepath, e)
    return return_value

class MyImageView(ui.View):
    def __init__(self,x,y,color,img):
        self.color = color
        self.x_off = x
        self.y_off = y
        self.scr_height = None 
        self.scr_width = None 
        self.img = img
        self.img_width, self.img_height = self.img.size
        self.scr_cor = 2.0
        self.ratio = 1.0

    def draw(self):
        self.scr_height = self.height
        self.scr_width = self.width
        path = ui.Path.rect(0, 0, self.scr_width, self.scr_height)
        ui.set_color(self.color)
        path.fill()
        self.img.draw(self.x_off,self.y_off,self.img_width*self.ratio/self.scr_cor,self.img_height*self.ratio/self.scr_cor)

    def touch_began(self, touch):
        self.close()

    def layout(self):
        scr_height_real = self.height * self.scr_cor
        scr_width_real = self.width * self.scr_cor
        y_ratio = scr_height_real / self.img_height
        x_ratio = scr_width_real / self.img_width
        # 1.0 = okay, <1.0 = Image to small, >1.0 = Image to big
        if x_ratio == 1.0 and y_ratio == 1.0:
            self.ratio = 1.0 #perfect size
        elif x_ratio == 1.0 and y_ratio > 1.0:
            self.ratio = 1.0 #perfect width
        elif x_ratio > 1.0 and y_ratio == 1.0:
            self.ratio = 1.0 #perfect height
        elif x_ratio > 1.0 and y_ratio > 1.0:
            self.ratio = 1.0 #show image in original size
        elif x_ratio >= 1.0 and y_ratio < 1.0:
            self.ratio = y_ratio #shrink height
        elif x_ratio < 1.0 and y_ratio >= 1.0:
            self.ratio = x_ratio #shrink width
        elif x_ratio < 1.0 and y_ratio < 1.0:
            if x_ratio < y_ratio: #which side?
                self.ratio = x_ratio
            else:
                self.ratio = y_ratio
        else:
            print 'This should never happen. :('

class PhoneManager(ui.View):
    pos = -1
    searchstr = ''

    def __init__(self):
        self.view = ui.load_view('PhoneManager')
        self.root = os.path.expanduser('~')
        self.rootlen = len(self.root)
        self.path = os.getcwd()
        self.path_po = self.path
        self.view.name = self.path[self.rootlen:]
        self.tableview1 = self.make_tableview1()
        self.lst = self.make_lst()
        self.lst_po = self.lst
        self.filename = ''
        self.set_button_actions()
        self.view.present('full_screen')

    def set_button_actions(self):               # assumes that ALL buttons have an action method 
        for subview in self.view['scrollview1'].subviews:      # with EXACTLY the same name as the button name
            if isinstance(subview, ui.Button):  # `self.view['btn_Help'].action = self.btn_Help`
                subview.action = getattr(self, subview.name)

    def btn_HTMLview(self, sender):
        self.view_po = ui.View()
        self.view_po.name = self.filename
        wv = ui.WebView()
        wv.width = self.view.width
        wv.height = self.view.height
        wv.flex = 'WH'
        self.view_po.add_subview(wv)
        self.view_po.present('full_screen')
        wv.load_url(self.path + '/' + self.filename)

    def btn_Edit(self, sender):
        editor.open_file(self.path + '/' + self.filename)
        self.view.close()

    def btn_PicView(self, sender):
        img = ui.Image.named(self.path + '/' + self.filename)
        self.view_po = MyImageView(0,0,'white',img)
        self.view_po.name = self.filename + '  ' + str(img.size)
        self.view_po.present('full_screen')

    @ui.in_background
    def btn_GetPic(self, sender):
        img = photos.pick_image()
        if not img:
            return
        for i in xrange(sys.maxint):
            filename = '{}/image{}.jpg'.format(self.path, str(i).zfill(3))
            if not os.path.exists(filename):
                img.save(filename, 'JPEG')
                break
        self.make_lst()
        self.view['tableview1'].reload_data()

    def btn_Help(self, sender, message='Use at your own risk. \nNo error handling!', name='Help'):
        self.view['scrollview1'].hidden = True 
        self.view['tableview1'].hidden = True
        self.name = name
        textview = ui.TextView()
        textview.name = 'textview'
        textview.x = 6
        textview.y = 6
        textview.width = self.view.width - 12
        textview.height = 150
        textview.flex = 'WR'
        textview.font = ('Courier', 18)
        textview.text = message
        textview.editable = False 
        self.view.add_subview(textview)
        button = ui.Button()
        button.name = 'button'
        button.x = 6
        button.y = 160
        button.width = self.view.width - 12
        button.height = self.view.height - 160
        button.flex = 'WRH'
        button.border_color = 'blue'
        button.border_width = 0.7
        button.corner_radius = 5
        button.title = 'Cancel'
        button.action = self.btn_Help_Cancel
        self.view.add_subview(button)

    def btn_Help_Cancel(self, sender):
        self.view.remove_subview(self.view['textview'])
        self.view.remove_subview(self.view['button'])
        self.view['scrollview1'].hidden = False 
        self.view['tableview1'].hidden = False 

    def make_view_browse(self):
        self.view['scrollview1'].hidden = True 
        self.view['tableview1'].hidden = True
        self.name = self.path_po[self.rootlen:]
        tableview = ui.TableView()
        tableview.name = 'tableview2'
        tableview.x = 6
        tableview.y = 6
        tableview.width = 308
        tableview.height = 434
        tableview.border_width = 1
        tableview.border_color = 'blue'
        tableview.corner_radius = 5
        tableview.row_height = 40
        tableview.bg_color = 'black'
        tableview.background_color = 'white'
        tableview.allows_selection = True
        self.view.add_subview(tableview)
        button1 = ui.Button()
        button1.name = 'button1'  
        button1.title = 'Okay'
        button1.x = 6
        button1.y = 448
        button1.width = 150
        button1.height = 50
        button1.border_color = 'blue'
        button1.border_width = 0.7
        button1.corner_radius = 5
        button1.action = self.btn_Move_Okay
        self.view.add_subview(button1)
        button2 = ui.Button()
        button2.name = 'button2'
        button2.title = 'Cancel'
        button2.x = 164
        button2.y = 448
        button2.width = 150
        button2.height = 50
        button2.border_color = 'blue'
        button2.border_width = 0.7
        button2.corner_radius = 5
        button2.action = self.close_view_browse
        self.view.add_subview(button2)
        
    def close_view_browse(self, sender):
        self.view.remove_subview(self.view['tableview2'])
        self.view.remove_subview(self.view['button1'])
        self.view.remove_subview(self.view['button2'])
        self.view['scrollview1'].hidden = False 
        self.view['tableview1'].hidden = False 
        
    def btn_Move(self, sender):
        self.make_view_browse()
        self.path_po = self.path
        self.make_lst_po()
        self.view['tableview2'].reload()

    def btn_Move_Okay(self, sender):
        if self.filename == '':
            self.close_view_browse(None)
            self.btn_Help(None,message='No file is selected.',name='Error')
        try:
            if not os.path.isfile(self.path_po + '/' + self.filename):
                shutil.move(self.path + '/' + self.filename,self.path_po + '/' + self.filename)
                self.make_lst()
                self.view['tableview1'].reload_data()
                self.close_view_browse(None)
            else:
                self.close_view_browse(None)
                self.btn_Help(None,message='File already exists in the destination directory.',name='Error')
        except:
            self.close_view_browse(None)
            self.btn_Help(None,message='Your selected file: ' + self.filename + " doesn't exist in the source directory. Please select the file and then directly press the Move-Button.",name='Error')

    def make_lst_po(self):
        dirs = get_dirs(self.path_po)
        lst = ui.ListDataSource(dirs)
        self.view['tableview2'].data_source = lst
        self.view['tableview2'].delegate = lst
        self.view['tableview2'].editing = False
        lst.action = self.table_tapped_po
        lst.delete_enabled = False
        lst.font = ('Courier', 18)
        return lst

    def table_tapped_po(self, sender):
        dirname_tapped = sender.items[sender.selected_row]
        if dirname_tapped[0] == '/':  # we have a directory
            if dirname_tapped == '/..':  # move up one
                self.path_po = self.path_po.rpartition('/')[0]
            else:                         # move down one
                self.path_po = self.path_po + dirname_tapped
            self.view.name = self.path_po[self.rootlen:]
            self.lst_po = self.make_lst_po()
            self.view['tableview2'].reload()

    @ui.in_background
    def btn_OpenIn(self, sender):
        file = self.path + '/' + self.filename
        console.open_in(file)

    def btn_Download(self, sender):
        url = clipboard.get()
        pos = url.find('://') # ftp://, http://, https:// >> 3-5
        if pos < 3 or pos > 5:
            url = 'http://www.'
        self.make_view_po('Download', '', 'Url:', '', url, self.btn_Download_Okay)

    def btn_Download_Okay(self, sender):
        url = self.view['textfield1'].text
        pos = url.find('://') # ftp://, http://, https:// >> 3-5
        if pos > 2 or pos < 6:
            pos = url.rfind('/') + 1
            filename = url[pos:]
            dl = requests.get(url, stream=True)
            with open(self.path + '/' + filename, 'wb') as f:
                for chunk in dl.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
                        f.flush()
            self.make_lst()
            self.view['tableview1'].reload_data()
        self.remove_view_po()

    def make_view_compress(self):
        self.view['scrollview1'].hidden = True 
        self.view['tableview1'].hidden = True
        self.name = self.path_po[self.rootlen:]
        textfield1 = ui.TextField()
        textfield1.name = 'tf_name'
        textfield1.text = 'Archivename'
        textfield1.x = 6
        textfield1.y = 6
        textfield1.width = 308
        textfield1.height = 32
        self.view.add_subview(textfield1)
        segcontr1 = ui.SegmentedControl()
        segcontr1.name = 'sc_compression'
        segcontr1.segments = ['.zip', '.tar', '.tar.gz', '.tar.bz2']
        segcontr1.selected_index = 0
        segcontr1.x = 6
        segcontr1.y = 46
        segcontr1.width = 308
        segcontr1.height = 64
        self.view.add_subview(segcontr1)
        segcontr2 = ui.SegmentedControl()
        segcontr2.name = 'sc_range'
        segcontr2.segments = ['Selected', 'All', '*.py*']
        segcontr2.selected_index = 0
        segcontr2.x = 6
        segcontr2.y = 118
        segcontr2.width = 308
        segcontr2.height = 64
        self.view.add_subview(segcontr2)
        button1 = ui.Button()
        button1.name = 'button1'  
        button1.title = 'Okay'
        button1.x = 6
        button1.y = 190
        button1.width = 150
        button1.height = 50
        button1.border_color = 'blue'
        button1.border_width = 0.7
        button1.corner_radius = 5
        button1.action = self.btn_Compress_Okay
        self.view.add_subview(button1)
        button2 = ui.Button()
        button2.name = 'button2'
        button2.title = 'Cancel'
        button2.x = 164
        button2.y = 190
        button2.width = 150
        button2.height = 50
        button2.border_color = 'blue'
        button2.border_width = 0.7
        button2.corner_radius = 5
        button2.action = self.close_view_compress
        self.view.add_subview(button2)

    def close_view_compress(self, sender):
        self.view.remove_subview(self.view['tf_name'])
        self.view.remove_subview(self.view['sc_compression'])
        self.view.remove_subview(self.view['sc_range'])
        self.view.remove_subview(self.view['button1'])
        self.view.remove_subview(self.view['button2'])
        self.view['scrollview1'].hidden = False 
        self.view['tableview1'].hidden = False 

    def btn_Compress(self, sender):
        self.make_view_compress()

    def btn_Compress_Okay(self, sender):
        def tar_compress(archive_name, compression, filter=False, fn=[]):
            if compression == 'tar':
                archive_name += '.tar'
                mode = 'w'
            elif compression == 'gztar':
                archive_name += '.tar.gz'
                mode = 'w:gz'
            elif compression == 'bztar':
                archive_name += '.tar.bz2'
                mode = 'w:bz2'
            tar = tarfile.open(archive_name, mode)
            if filter:
                for file in fn:
                    tar.add(self.path + '/' + file,arcname=file)
            else:
                tar.add(self.path + '/' + self.filename,arcname=self.filename)
            tar.close()

        comp = self.view['sc_compression'].selected_index
        compression = ''
        mode = ''
        rang = self.view['sc_range'].selected_index
        archive_name = self.path + '/' + self.view['tf_name'].text # no extension
        if comp == 0:
            compression = 'zip'
        elif comp == 1:
            compression = 'tar'
        elif comp == 2:
            compression = 'gztar'
        else:
            compression = 'bztar'
        if rang == 0: # selected file
            if compression == 'zip':
                zf = zipfile.ZipFile(archive_name + '.zip', mode='w')
                zf.write(self.path + '/' + self.filename, os.path.basename(self.path + '/' + self.filename), compress_type=zipfile.ZIP_DEFLATED)
                zf.close()
            else:
                tar_compress(archive_name, compression)
        else:
            if rang == 1: # all files
                files = self.get_files()
            elif rang == 2: # only python files (*.py*)
                files = self.get_files(filter=True )
            if compression == 'zip':
                zf = zipfile.ZipFile(archive_name + '.zip', mode='w')
                for file in files:
                    zf.write(self.path + '/' + file, os.path.basename(self.path + '/' + file), compress_type=zipfile.ZIP_DEFLATED)
                zf.close()
            else:
                tar_compress(archive_name, compression, filter=True, fn=files)
        self.make_lst()
        self.view['tableview1'].reload_data()
        self.close_view_compress(None)

    def get_files(self,filter=False):
        files = []
        for entry in sorted(os.listdir(self.path)):
            if os.path.isfile(self.path + '/' + entry):
                if filter:
                    if entry.find('.py') >= 0: # has to be fixed with re
                        files.append(entry)
                else:
                    files.append(entry)
        return files

    def btn_Extract(self, sender):
        pos = self.filename.rfind('.')
        ext = self.filename[pos+1:]
        dir_name = ''
        if ext == 'zip' or ext == 'tar':
            dir_name = self.filename[:pos]
            os.mkdir(self.path + '/' + dir_name)
            if ext == 'zip':
                file = open(self.path + '/' + self.filename, 'rb')
                z = zipfile.ZipFile(file)
                z.extractall(self.path + '/' + dir_name)
                file.close()
            elif ext == 'tar':
                tar = tarfile.open(self.path + '/' + self.filename)
                tar.extractall(self.path + '/' + dir_name)
                tar.close()
        elif ext == 'gz' or ext == 'bz2':
            dir_name = self.filename[:pos-4]
            os.mkdir(self.path + '/' + dir_name)
            tar = tarfile.open(self.path + '/' + self.filename)
            tar.extractall(self.path + '/' + dir_name)
            tar.close()
        else:
            #unsupported type
            pass
        self.make_lst()
        self.view['tableview1'].reload_data()

    def btn_HexView(self, sender):
        if self.filename != '':
            self.hexview_a_file(self.filename)

    def btn_RemoveDir(self, sender):
        pos = self.path.rfind('/')
        dir = self.path[pos:]
        self.make_view_po('RemoveDir', 'Dir:', '', dir, '', self.btn_RemoveDir_Okay)

    def btn_RemoveDir_Okay(self, sender):
        shutil.rmtree(self.path)
        pos = self.path.rfind('/')
        dir = self.path[:pos]
        self.path = dir
        self.make_lst()
        self.view['tableview1'].reload_data()
        self.remove_view_po()

    def btn_MakeDir(self, sender):
        self.make_view_po('MakeDir', '', 'New Dir:', '', '', self.btn_MakeDir_Okay)

    def btn_MakeDir_Okay(self, sender):
        os.mkdir(self.path + '/' + self.view['textfield1'].text)
        self.make_lst()
        self.view['tableview1'].reload_data()
        self.remove_view_po()

    def btn_Delete(self, sender):
        self.make_view_po('Delete', 'Name:', '', self.filename, '', self.btn_Delete_Okay)

    def btn_Delete_Okay(self, sender):
        os.remove(self.path + '/' + self.filename)
        self.make_lst()
        self.view['tableview1'].reload_data()
        self.remove_view_po()

    def btn_Copy(self, sender):
        self.make_view_po('Copy', 'Name:', 'New Name:', self.filename, self.filename, self.btn_Copy_Okay)

    def btn_Copy_Okay(self, sender):
        if self.filename != self.view['textfield1'].text:
            shutil.copyfile(self.path + '/' + self.filename, self.path + '/' + self.view['textfield1'].text)
            self.make_lst()
            self.view['tableview1'].reload_data()
        self.remove_view_po()

    def btn_Rename(self, sender):
        self.make_view_po('Rename', 'Old Name:', 'New Name:', self.filename, self.filename, self.btn_Rename_Okay)

    def btn_Rename_Okay(self, sender):
        os.rename(self.path + '/' + self.filename, self.path + '/' + self.view['textfield1'].text)
        self.remove_view_po()
        self.make_lst()
        self.view['tableview1'].reload_data()

    def btn_Cancel(self, sender):
        self.remove_view_po()

    def make_view_po(self, hl, l1, l2, l3, tf, action):
        self.view['scrollview1'].hidden = True 
        self.view['tableview1'].hidden = True
        self.name = hl
        label1 = ui.Label()
        label1.name = 'label1'
        label1.text = l1
        label1.x = 6
        label1.y = 6
        label1.width = 308
        label1.height = 32
        self.view.add_subview(label1)
        label2 = ui.Label()
        label2.name = 'label2'
        label2.text = l2
        label2.x = 6
        label2.y = 94
        label2.width = 308
        label2.height = 32
        self.view.add_subview(label2)
        label3 = ui.Label()
        label3.name = 'label3'
        label3.text = ' ' + l3
        label3.x = 6
        label3.y = 46
        label3.width = 308
        label3.height = 32
        label3.border_color = 'lightgrey'
        label3.border_width = 0.5
        label3.corner_radius = 5
        self.view.add_subview(label3)
        textfield1 = ui.TextField()
        textfield1.name = 'textfield1'
        textfield1.text = tf
        textfield1.x = 6
        textfield1.y = 134
        textfield1.width = 308
        textfield1.height = 32
        self.view.add_subview(textfield1)
        button1 = ui.Button()
        button1.name = 'button1'  
        button1.title = 'Okay'
        button1.x = 6
        button1.y = 192
        button1.width = 150
        button1.height = 90
        button1.border_color = 'blue'
        button1.border_width = 0.7
        button1.corner_radius = 5
        button1.action = action
        self.view.add_subview(button1)
        button2 = ui.Button()
        button2.name = 'button2'
        button2.title = 'Cancel'
        button2.x = 164
        button2.y = 192
        button2.width = 150
        button2.height = 90 
        button2.border_color = 'blue'
        button2.border_width = 0.7
        button2.corner_radius = 5
        button2.action = self.btn_Cancel
        self.view.add_subview(button2)

    def remove_view_po(self):
        self.view.remove_subview(self.view['label1'])
        self.view.remove_subview(self.view['label2'])
        self.view.remove_subview(self.view['label3'])
        self.view.remove_subview(self.view['textfield1'])
        self.view.remove_subview(self.view['button1'])
        self.view.remove_subview(self.view['button2'])
        self.view['scrollview1'].hidden = False 
        self.view['tableview1'].hidden = False 

    def make_tableview1(self):
        tableview = ui.TableView()
        tableview.name = 'tableview1'
        tableview.frame = self.frame
        tableview.x = 0
        tableview.y = 50
        tableview.width = 320
        tableview.height = 454
        tableview.border_width = 1
        tableview.border_color = 'blue'
        tableview.corner_radius = 5
        tableview.flex = 'WH'
        tableview.row_height = 40
        tableview.bg_color = 'black'
        tableview.background_color = 'white'
        tableview.allows_selection = True
        self.view.add_subview(tableview)
        return tableview

    def make_lst(self):
        dirs_and_files = get_dir(self.path)
        lst = ui.ListDataSource(dirs_and_files)
        lst.accessory_action = self.fileinfo
        self.tableview1.data_source = lst
        self.tableview1.delegate = lst
        self.tableview1.editing = False
        lst.action = self.table_tapped
        lst.delete_enabled = False
        lst.font = ('Courier', 18)
        return lst

    def table_tapped(self, sender):
        filename_tapped = sender.items[sender.selected_row]['title']
        if filename_tapped[0] == '/':  # we have a directory
            if filename_tapped == '/..':  # move up one
                self.path = self.path.rpartition('/')[0]
            else:                         # move down one
                self.path = self.path + filename_tapped
            self.view.name = self.path[self.rootlen:]
            self.lst = self.make_lst()
            self.tableview1.reload()
        else:
            self.filename = filename_tapped

    def button_action(self, sender):
        tvd = self.view['tv_data']
        tfss = self.view['tf_search']
        if tfss.text != '':
            if tfss.text == PhoneManager.searchstr:
                #next hit
                PhoneManager.pos = tvd.text.find(PhoneManager.searchstr,PhoneManager.pos+1)
            else:
                #new search
                PhoneManager.searchstr = tfss.text
                PhoneManager.pos = tvd.text.find(PhoneManager.searchstr)
            if PhoneManager.pos >= 0:    #hit
                x = tvd.text.find('\n',PhoneManager.pos) - 79        #line start
                y = len(tvd.text) - len(tvd.text) % 80  #last line start
                if PhoneManager.pos < y:
                    sender.title = tvd.text[x:x+10]
                else:
                    sender.title = tvd.text[y:y+10]
                tvd.selected_range = (PhoneManager.pos, PhoneManager.pos+len(PhoneManager.searchstr))  # works only when textview is active!!!
            else:
                sender.title = 'Restart'
                PhoneManager.pos = -1
        else:
            sender.title = 'Search'
            PhoneManager.pos = -1

    def hexview_a_file(self, filename):
        self.view['scrollview1'].hidden = True 
        self.view['tableview1'].hidden = True
        self.name = filename
        textfield1 = ui.TextField()
        textfield1.name = 'tf_search'
        textfield1.text = ''
        textfield1.x = 6
        textfield1.y = 6
        textfield1.width = self.view.width - 118
        textfield1.height = 32
        textfield1.flex = 'WR'
        self.view.add_subview(textfield1)
        button1 = ui.Button()
        button1.name = 'btn_search'
        button1.title = 'Search'
        button1.x = self.view.width - 106
        button1.y = 6
        button1.width = 100
        button1.height = 32
        button1.flex = 'WL'
        button1.border_color = 'blue'
        button1.border_width = 0.7
        button1.corner_radius = 5
        button1.action = self.button_action
        self.view.add_subview(button1)
        full_pathname = self.path + '/' + filename
        textview1 = ui.TextView()
        textview1.name = 'tv_data'
        textview1.text = hex_view(full_pathname)
        textview1.x = 6
        textview1.y = 46
        textview1.width = self.view.width - 12
        textview1.height = 452
        textview1.flex = 'WR'
        textview1.border_color = 'lightgrey'
        textview1.border_width = 0.5
        textview1.corner_radius = 5
        textview1.font = ('Courier', 11)
        textview1.editable = False 
        self.view.add_subview(textview1)

    @ui.in_background
    def fileinfo(self, sender):
        til = sender.items[sender.tapped_accessory_row]['title']
        siz = sender.items[sender.tapped_accessory_row]['size']
        dat = sender.items[sender.tapped_accessory_row]['date']
        title = til
        msg = str(siz) + ' Bytes'
        msg += '\n' + str(dat)
        console.alert(title, msg)

PhoneManager()
