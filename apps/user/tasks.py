from django.core.mail import send_mail
from celery import shared_task


@shared_task
def send_register_active_email(to_mail, username, token):
    """发送激活邮件"""
    send_mail(
        subject='天天图书用户激活',
        message='用户激活',
        from_email='<2230979122@qq.com>',
        recipient_list=[to_mail],
        html_message=f"<h1>{username}，欢迎您</h1><br>"
                     f"<a href='http://127.0.0.1:8000/user/active/{token}'>请在一小时内激活您的账户</a>"
    )
