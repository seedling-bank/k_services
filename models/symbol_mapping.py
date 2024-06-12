from peewee import BigIntegerField, TextField, DoubleField, CharField

from base import BaseModel


class SymbolMapping(BaseModel):
    index = BigIntegerField(primary_key=True)
    symbol = TextField()
    tweet_name = TextField()
    twitter_url = TextField()
    keyword1 = TextField()
    keyword2 = TextField()
    source = TextField()
    tag = TextField()
    value = TextField()
    icon = TextField()
    id = TextField()
    name = TextField()
    username = TextField()
    introduce = CharField(max_length=2048)
    introduce_zh = CharField(max_length=2048)
    Category1 = CharField()
    Category2 = CharField()
    Category3 = CharField()
    market_cap = DoubleField()
    launch_time = CharField()

    class Meta:
        table_name = 'symbol_mapping'


class PriceOfData(BaseModel):
    symbol = CharField(null=False)
    eventtime = CharField(null=False)
    start = CharField(null=False)
    end = CharField(null=False)
    interval = CharField(null=False)
    open = CharField(null=False)
    close = CharField(null=False)
    high = CharField(null=False)
    low = CharField(null=False)
    volume = CharField(null=False)

    class Meta:
        table_name = 'price_of_data_tbl'
