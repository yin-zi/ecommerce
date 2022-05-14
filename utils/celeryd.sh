# https://docs.celeryproject.org/en/stable/userguide/daemonizing.html#init-script-celeryd
# 初始化脚本：celeryd
# 用法 /etc/init.d/celeryd {start|stop|restart|status}
# 配置文件 /etc/default/celeryd
# Names of nodes to start
#   most people will only start one node:
CELERYD_NODES="worker"
#   but you can also start multiple and configure settings
#   for each in CELERYD_OPTS
#CELERYD_NODES="worker1 worker2 worker3"
#   alternatively, you can specify the number of nodes to start:
#CELERYD_NODES=10

# Absolute or relative path to the 'celery' command:
# CELERY_BIN="/usr/local/bin/celery"
CELERY_BIN="/home/yyy/ecommerce/venv/bin"

# App instance to use
# comment out this line if you don't use an app
CELERY_APP="ecommerce"
# or fully qualified:
#CELERY_APP="proj.tasks:app"

# Where to chdir at start. 更改为django项目目录
CELERYD_CHDIR="/home/yyy/ecommerce"

# Extra command-line arguments to the worker
CELERYD_OPTS="--time-limit=300 --concurrency=8"
# Configure node-specific settings by appending node name to arguments:
#CELERYD_OPTS="--time-limit=300 -c 8 -c:worker2 4 -c:worker3 2 -Ofair:worker1"

# Set logging level to DEBUG
#CELERYD_LOG_LEVEL="DEBUG"

# %n will be replaced with the first part of the nodename.
CELERYD_LOG_FILE="/var/log/celery/%n%I.log"
CELERYD_PID_FILE="/var/run/celery/%n.pid"

# Workers should run as an unprivileged user.
#   You need to create this user manually (or you can choose
#   a user/group combination that already exists (e.g., nobody).
CELERYD_USER="celery"
CELERYD_GROUP="celery"

# If enabled pid and log directories will be created if missing,
# and owned by the userid/group configured.
CELERY_CREATE_DIRS=1