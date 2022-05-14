import json
from random import randrange
from django.http import HttpResponse
from pyecharts.options import AxisOpts
from rest_framework.views import APIView
from pyecharts.charts import Bar
from pyecharts import options as opts
from apps.goods.models import GoodsSKU, GoodsType
from django.db import connection


# Create your views here.
def response_as_json(data):
    json_str = json.dumps(data)
    response = HttpResponse(
        json_str,
        content_type="application/json",
    )
    response["Access-Control-Allow-Origin"] = "*"
    return response


def json_response(data, code=200):
    data = {
        "code": code,
        "msg": "success",
        "data": data,
    }
    return response_as_json(data)


def json_error(error_string="error", code=500, **kwargs):
    data = {
        "code": code,
        "msg": error_string,
        "data": {}
    }
    data.update(kwargs)
    return response_as_json(data)


JsonResponse = json_response
JsonError = json_error


def bar_base() -> Bar:
    skus = GoodsSKU.objects.filter(is_delete=False).order_by('-sales')[:10]
    c = (
        Bar()
        .add_xaxis([sku.spu.name + sku.category for sku in skus])
        .add_yaxis('销量', [sku.sales for sku in skus], bar_width=50)
        .set_global_opts(title_opts=opts.TitleOpts(title="销量前十"),
                         xaxis_opts=AxisOpts(axislabel_opts={'interval':'0', 'rotate':15}))
        .dump_options_with_quotes()
    )
    return c

def pie_base() -> Bar:
    typesales = my_custom_sql('''select type.goods_type,sum(sku.sales) as totalsale
from ec_goods_sku as sku join ec_goods_spu as spu
on sku.spu_id = spu.id
join ec_goods_type as type on spu.type_id = type.id
where sku.is_delete=false and spu.is_delete=false
group by spu.type_id
order by totalsale desc
limit 10;''')
    c = (
        Bar()
        .add_xaxis([typesale[0] for typesale in typesales])
        .add_yaxis('分类销量', [typesale[1] for typesale in typesales], bar_width=50)
        .set_global_opts(title_opts=opts.TitleOpts(title="分类销量"),
                         xaxis_opts=AxisOpts(axislabel_opts={'interval':'0', 'rotate':15}))
        .dump_options_with_quotes()
    )

    return c

class ChartView(APIView):
    def get(self, request, *args, **kwargs):
        return JsonResponse(json.loads(bar_base()))

class PieChartView(APIView):
    def get(self, request, *args, **kwargs):
        return JsonResponse(json.loads(pie_base()))

class IndexView(APIView):
    def get(self, request, *args, **kwargs):
        return HttpResponse(content=open("./templates/charts.html").read())


def my_custom_sql(sql):
    with connection.cursor() as cursor:
        cursor.execute(sql)
        row = cursor.fetchall()
    return row