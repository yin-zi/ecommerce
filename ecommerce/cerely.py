import os
from celery import Celery


# 为celery设置默认的Django设置模块
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
app = Celery('ecommerce')

# 在这里使用字符串意味着工作者不必将配置对象序列化给子进程
# namespace='CELERY' 意味着所有与CELERY相关的配置键都应该有一个`CELERY_`前缀
app.config_from_object('django.conf:settings', namespace='CELERY')

# 从所有注册的Django应用程序中加载任务模块
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
