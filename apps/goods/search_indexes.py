# 定义索引类
from haystack import indexes
from apps.goods.models import GoodsSKU  # 导入模型类


# 指定对于某个类的某些数据建立索引
# 索引类名格式：模型类名+Index
class GoodsSPUIndex(indexes.SearchIndex, indexes.Indexable):
    # 索引字段 use_template=True指定表中的哪些字段建立索引文件的说明放在一个文件中
    # templates->search->indexs->goods(跟应用名字一样)->goodssku_text.txt(模型类名字的小写)
    text = indexes.CharField(document=True, use_template=True)

    def get_model(self):
        # 返回你的模型类
        return GoodsSKU

    # 建立索引的数据
    def index_queryset(self, using=None):
        return self.get_model().objects.filter(is_delete=False)
