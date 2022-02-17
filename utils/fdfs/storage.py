from django.core.files.storage import Storage
from fdfs_client.client import Fdfs_client, get_tracker_conf
from django.conf import settings


class FDFSStorage(Storage):
    """FastDfs文件存储类
    https://docs.djangoproject.com/zh-hans/3.2/howto/custom-file-storage/
    自定义存储系统必须为django.core.files.storage.Storage的一个子类
    Django必须能以无参数实例化你的存储系统,意味着所有配置都应从django.conf.settings配置中获取
    存储类中，除了其他自定义的方法外，还必须实现 _open() 以及 _save() 等其他适合存储类的方法
    """
    def __init__(self, client_conf=None, base_url=None):
        """初始化"""
        self.client_conf = client_conf or settings.FDFS_CLIENT_CONF
        self.base_url = base_url or settings.FDFS_SERVER_URL

    def _open(self, name, mode='rb'):
        """打开文件时使用 方法必须要返回一个文件对象"""
        pass

    def _save(self, name, content):
        """保存文件时使用
        @name: 选择上传的文件名
        @content: 上传文件内容的File对象
        @return: 返回保存的文件名的实际名称
        """
        # 创建一个Fdfs_client对象
        client = Fdfs_client(get_tracker_conf(self.client_conf))
        # 上传文件到FastDFS
        res = client.upload_by_buffer(content.read())
        if res.get('Status') != 'Upload successed.':
            raise Exception('上传文件到FastDFS失败')
        return res.get('Remote file_id').decode()

    def path(self, name):
        """本地文件系统路径，在这里可以使用Python的标准open()打开文件
        对于不能从本地文件系统访问的存储系统，这将引发NotImplementedError
        """
        pass

    def delete(self, name):
        """删除 name 引用的文件。如果目标存储系统不支持删除，这将引发 NotImplementedError"""
        pass

    def exists(self, name):
        """Django判断文件名是否可用,返回False即可用
        如果给定名称所引用的文件已经存在于存储系统中，则返回True
        如果该名称可用于新文件，则返回False
        """
        return False

    def listdir(self, path):
        """列出指定路径的内容，返回一个二元元组列表，第一项是目录，第二项是文件
        对于不能提供这种列表的存储系统，这将引发一个 NotImplementedError
        """
        pass

    def size(self, name):
        """返回 name 引用的文件的总大小，以字节为单位
        对于不能返回文件大小的存储系统，将引发 NotImplementedError
        """
        pass

    def url(self, name):
        """返回可以访问name引用的文件内容的URL
        对于不支持通过URL访问的存储系统，这将引发NotImplementedError
        """
        return self.base_url + name

    def get_accessed_time(self, name):
        """返回文件最后访问时间的datetime
        对于不能返回最后访问时间的存储系统，将引发 NotImplementedError。
        如果USE_TZ为True，则返回一个处理过的datetime，否则返回一个当地时区的未处理的datetime
        """
        pass

    def get_created_time(self, name):
        """返回文件的创建时间的 datetime
        对于不能返回创建时间的存储系统，将引发 NotImplementedError。
        如果USE_TZ为True，则返回一个处理过的datetime，否则返回一个当地时区的未处理的datetime
        """
        pass

    def get_modified_time(self, name):
        """返回文件最后修改时间的datetime
        对于不能返回最后修改时间的存储系统，将引发 NotImplementedError。
        如果USE_TZ为True，则返回一个处理过的datetime，否则返回一个当地时区的未处理的datetime
        """
        pass
