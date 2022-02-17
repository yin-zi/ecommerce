# https://docs.celeryproject.org/en/stable/userguide/daemonizing.html#init-script-celerybeat
# 初始化脚本：celerybeat
# 用法 /etc/init.d/celerybeat {start|stop|restart}
# 配置文件 /etc/default/celerybeat 或 /etc/default/celeryd
# Absolute or relative path to the 'celery' command:
CELERY_BIN="/usr/local/bin/celery"
#CELERY_BIN="/virtualenvs/def/bin/celery"

# App instance to use
# comment out this line if you don't use an app
CELERY_APP="proj"
# or fully qualified:
#CELERY_APP="proj.tasks:app"

# Where to chdir at start. 更改为django项目目录
CELERYBEAT_CHDIR="/opt/Myproject/"

# Extra arguments to celerybeat
CELERYBEAT_OPTS="--schedule=/var/run/celery/celerybeat-schedule"