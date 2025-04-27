from io_utils import get_nodata, get_geo, get_optimal_block_size,crop_to_same_size
from projection_utils import reproject_to_utm50, compare_two_projection
from overlap_utils import extract_overlap
from core_algorithm import global_fuse_image
from osgeo import gdal
import numpy as np
import os
import tkinter as tk
from ui import ImageNormalizationUI

# 主函数
def main():
    # 创建 tkinter 主窗体
    root = tk.Tk()
    # root.withdraw()  # 隐藏主窗口

    # 创建并启动 UI
    ui = ImageNormalizationUI(root)
    root.mainloop()   # 等待用户操作
    path1, path2, output_dir, q_low, q_high, q_low_color, q_high_color = ui.submit()  # 获取用户输入数据

    # qlow,high转化为数字类型
    try:
        q_low = float(q_low)
        q_high = float(q_high)
        q_low_color = float(q_low_color)
        q_high_color = float(q_high_color)
    except ValueError as e:
        print(f"错误：无法将 q_low 或 q_high 转换为数字: {e},按默认值计算")
        # 可以设置默认值或退出程序
        q_low = 2.0  # 默认值
        q_high = 98.0  # 默认值
        q_low_color = 10
        q_high_color = 90


    if path1 is None or path2 is None or output_dir is None:
        print("用户取消了操作或输入无效")
        return

    # 判断两个图像的大小，如果不同，调用裁剪函数

    # 示例数据
    # path1 = r"D:\python_project\image-stitching-main\samples\wd\cropped_images_transform\cropped_image_1.tif"
    # path2 = r"D:\python_project\image-stitching-main\samples\wd\cropped_images_transform\cropped_image_2.tif"

    # 打开两个栅格图像
    raster1 = gdal.Open(path1)
    raster2 = gdal.Open(path2)

    # 获取提取公共区域需要的边界和投影
    transform1, bound1, crs1, width1, height1 = get_geo(path1)
    transform2, bound2, crs2, width2, height2 = get_geo(path2)


    # 裁剪
    if (width1 != width2) or (height1 != height2):
        print("图像尺寸不一致，正在裁剪...")

        # 创建输出路径
        clipped1 = os.path.join(output_dir, "clipped_image1.tif")
        clipped2 = os.path.join(output_dir, "clipped_image2.tif")

        # 裁剪两幅图像
        crop_to_same_size(path1, path2, clipped1, clipped2)

        # 更新路径
        path1 = clipped1
        path2 = clipped2

        print("裁剪完成，继续处理...")

    # 判断两个投影，如果不同，则将crs1转到crs2
    if crs1 != crs2:
        path1, raster1, transform1, bound1, crs1 = compare_two_projection(crs1, crs2, path1, output_dir)
    ui.set_progress(5)  # 设置进度

    # 转换nodata值
    no_data1, raster1_new = get_nodata(raster1)
    no_data2, raster2_new = get_nodata(raster2)

    # 转为numpy数组
    raster1_new = np.array(raster1_new)
    raster2_new = np.array(raster2_new)

    overlap1, overlap2 = extract_overlap(raster1_new, transform1, bound1,
                                         raster2_new, transform2, bound2)
    ui.set_progress(10)  # 设置进度

    block_size = get_optimal_block_size()

    #全局
    global_fuse_image(overlap1, overlap2, raster1_new, raster2_new, output_dir, 1024, path1, path2, q_low, q_high,q_low_color, q_high_color,ui=ui)

    ui.set_progress(100)  # 设置进度
    # delete过程文件
    if os.path.exists("temp_norm.dat"):
        os.remove("temp_norm.dat")  # 删除文件
    if os.path.exists("temp_norm1.dat"):
        os.remove("temp_norm1.dat")  # 删除文件

    # #局部
    # denorm_A_to_B, denorm_B_to_A = fuse_images(overlap1, overlap2, raster1_new, raster2_new, output_dir, 1024)


if __name__ == "__main__":
    main()

