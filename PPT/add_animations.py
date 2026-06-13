# -*- coding: utf-8 -*-
"""
win32com 动画增强
读取静态 PPT，添加淡入动画 + 页面切换
"""

import win32com.client
import os

# 动画常量
MOTION_FADE_IN = 10       # 淡入
ON_CLICK = 3              # 点击触发
AFTER_PREVIOUS = 2        # 上一个完成后自动播放
PP_FADE = 3849            # 平滑淡出切换


def add_fade_in(slide, shape_index, duration=0.6, delay=0.0, start=AFTER_PREVIOUS):
    """给指定形状添加淡入动画"""
    shape = slide.Shapes(shape_index)
    effect = slide.TimeLine.MainSequence.AddEffect(
        Shape=shape,
        effectId=MOTION_FADE_IN,
    )
    effect.Timing.Duration = duration
    effect.Timing.TriggerType = start
    effect.Timing.TriggerDelayTime = delay
    return effect


def add_slide_transition(slide, effect=PP_FADE, duration=1.0):
    """设置幻灯片切换效果"""
    slide.SlideShowTransition.EntryEffect = effect
    slide.SlideShowTransition.Duration = duration


def process_slide(slide, slide_num, total):
    """处理单页：添加动画"""
    shape_count = slide.Shapes.Count
    print(f'  Slide {slide_num}/{total}: {shape_count} shapes')

    # 页面切换
    add_slide_transition(slide, PP_FADE, 1.0)

    # 给每个形状添加淡入动画
    for i in range(1, shape_count + 1):
        trigger = ON_CLICK if i == 1 else AFTER_PREVIOUS
        delay = 0 if i == 1 else 0.1
        add_fade_in(slide, i, duration=0.5, delay=delay, start=trigger)

    # 验证
    seq = slide.TimeLine.MainSequence
    print(f'    -> {seq.Count} animations added')


def main():
    input_path = 'D:/pycharm/Person-Practice/PPT/Dify_Agent_凡戴克棕.pptx'
    output_path = 'D:/pycharm/Person-Practice/PPT/Dify_Agent_凡戴克棕_动画.pptx'

    print('Starting PowerPoint...')
    app = win32com.client.Dispatch("PowerPoint.Application")
    app.Visible = True

    print(f'Opening: {input_path}')
    pres = app.Presentations.Open(os.path.abspath(input_path))

    slide_count = pres.Slides.Count
    print(f'Total slides: {slide_count}')

    for i in range(1, slide_count + 1):
        process_slide(pres.Slides(i), i, slide_count)

    print(f'Saving: {output_path}')
    pres.SaveAs(os.path.abspath(output_path))
    pres.Close()

    print('Done!')
    print(f'Output: {output_path}')


if __name__ == '__main__':
    main()
