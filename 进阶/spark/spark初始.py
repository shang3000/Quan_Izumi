from pyspark import SparkConf, SparkContext

# 创建sparkconf对象
conf = SparkConf().setMaster("local[*]"). \
    setAppName("test_spark_app")
# 基于SparkConf类对象创建SparkContext对象
sc = SparkContext(conf=conf)
print(sc.version)
sc.stop()
