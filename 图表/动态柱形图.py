from pyecharts.charts import Bar, Timeline
from pyecharts.options import LabelOpts

bar1 = Bar()
bar1.add_xaxis(['中国', '美国', '俄罗斯'])
bar1.add_yaxis('GDP', [24, 35, 45], label_opts=LabelOpts(position='right'))
bar1.reversal_axis()

bar2 = Bar()
bar2.add_xaxis(['中国', '美国', '俄罗斯'])
bar2.add_yaxis('GDP', [34, 45, 55], label_opts=LabelOpts(position='right'))
bar2.reversal_axis()

bar3 = Bar()
bar3.add_xaxis(['中国', '美国', '俄罗斯'])
bar3.add_yaxis('GDP', [54, 35, 25], label_opts=LabelOpts(position='right'))
bar3.reversal_axis()

timeline = Timeline()
timeline.add(bar1, '点1')
timeline.add(bar2, '点2')
timeline.add(bar3, '点3')

timeline.add_schema(
    play_interval=1000,
    is_timeline_show=True,
    is_auto_play=True,
    is_loop_play=True
)

timeline.render()
