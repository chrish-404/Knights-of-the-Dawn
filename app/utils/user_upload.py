# author 风逝
import os
from datetime import datetime
from random import randint


class fileupload:
    # 验证文件大小、扩展名、是不是日期文件夹
    def __init__(self,file, exts=('png','jpg','jpeg'), size=1024 * 1024, is_randomname=False):
        self.file = file
        self.exts = exts
        self.size = size
        self.is_randomname = is_randomname

    def upload(self, dest):
        # 获取文件上传对象
        if not self.check_type():
            return -1

        # 检测文件大小，上传文件的大小不能过大
        if not self.check_size():
            return -2


        if self.is_randomname:
            self.file_name=self.radom_filename()
        else:
            self.file_name=self.file.name

        path =os.path.join(dest,self.file_name)

        self.write_file(path)
        return 1

        # 检测文件类型，必须是指定的几种文件扩展名对应的文件类型


    def check_size(self):
        if self.size <0:
            return False
        return self.file.size<=self.size

    def check_type(self):
        ext = os.path.splitext(self.file.name)
        if len(ext) > 1:
            ext = ext[1].lstrip('.')
            if ext in self.exts:
                return True
        return False


    def radom_filename(self):
        filename=datetime.now().strftime('%Y%m%d%H%M%S')+str(randint(1,10000))
        ext=os.path.splitext(self.file.name)
        ext=ext[1] if len(ext)>1 else ''
        filename+=ext
        return filename

    def get_path(self):
        if self.is_datefolder:
            folder_name = datetime.now().strftime('%Y/%m/%d')
            folder_path = os.path.join(self.path, folder_name)
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)

            file_path = os.path.join(folder_path, self.f_obj.name)
        else:
            file_path = os.path.join(self.path, self.f_obj.name)
        return file_path

    def write_file(self, path):
        with open(path,'wb') as fp:
            if self.file.multiple_chunks():
               for chunk in self.file.multiple_chunks():
                fp.write(chunk)
            else:
                fp.write(self.file.read())
