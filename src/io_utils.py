import numpy as np
import rasterio
from osgeo import gdal
import psutil
from rasterio.windows import Window

def crop_to_same_size(path1, path2, output1, output2):
    with rasterio.open(path1) as ds1, rasterio.open(path2) as ds2:
        # 获取原始尺寸
        width1, height1 = ds1.width, ds1.height
        width2, height2 = ds2.width, ds2.height

        # 取共同最小尺寸
        min_width = min(width1, width2)
        min_height = min(height1, height2)

        # 构造裁剪窗口（从左上角开始）
        window = Window(0, 0, min_width, min_height)

        # 裁剪并保存 path1
        data1 = ds1.read(window=window)
        transform1 = ds1.window_transform(window)
        meta1 = ds1.meta.copy()
        meta1.update({
            "height": min_height,
            "width": min_width,
            "transform": transform1
        })
        with rasterio.open(output1, 'w', **meta1) as out1:
            out1.write(data1)

        # 裁剪并保存 path2
        data2 = ds2.read(window=window)
        transform2 = ds2.window_transform(window)
        meta2 = ds2.meta.copy()
        meta2.update({
            "height": min_height,
            "width": min_width,
            "transform": transform2
        })
        with rasterio.open(output2, 'w', **meta2) as out2:
            out2.write(data2)

    print(f"裁剪完成，输出图像：\n{output1}\n{output2}") # 保存裁剪后的图像

def get_nodata(raster):
    """获取NoData值，并将所有波段的NoData转换为NaN"""
    if raster is None:
        print("无法打开影像文件")
        return None, None  # 返回None，表示影像打开失败

    num_bands = raster.RasterCount  # 影像的波段数
    print(f"影像包含 {num_bands} 个波段")

    nodata_values = []  # 存储每个波段的NoData值
    image_data_list = []  # 存储处理后的数据

    for i in range(1, num_bands + 1):  # 波段索引从1开始
        band = raster.GetRasterBand(i)
        nodata_value = band.GetNoDataValue()
        nodata_values.append(nodata_value)  # 存储NoData值
        print(f"波段 {i} 的 NoData 值是: {nodata_value}")

        # 读取波段数据
        image_data = band.ReadAsArray().astype(np.float32)
        print(image_data.dtype)

        # 读取前检查是否有NaN
        has_nan_before = np.isnan(image_data).any()
        print(f"波段 {i} 处理前是否包含 NaN: {has_nan_before}")
        print(f"波段{i}{image_data}")

        # 替换NoData值为NaN
        # 是不是应该循环整个二维数组？——不需要，np.where会实现
        if nodata_value is not None:
            image_data = np.where(image_data == nodata_value, np.nan, image_data)

        # 替换后检查是否有NaN
        has_nan_after = np.isnan(image_data).any()
        print(f"波段 {i} 处理后是否包含 NaN: {has_nan_after}")
        print(f"波段{i}{image_data}")

        # 存储处理后的影像数据
        image_data_list.append(image_data)

    return nodata_values, image_data_list  # 返回所有波段的NoData值和处理后的数据


def get_geo(image):
    with rasterio.open(image) as src:
        transform = src.transform
        bound = src.bounds
        crs = src.crs
        width = src.width
        height = src.height
    return transform, bound, crs, width, height


def get_optimal_block_size():
    """根据可用内存选择合适的块大小"""
    free_mem = psutil.virtual_memory().available / (1024 ** 3)  # GB
    if free_mem > 16:
        return 512
    elif free_mem > 8:
        return 256
    else:
        return 128  # 低内存情况

def save_image(output_path, image_data, reference_image_path):
    # 读取参考影像
    ref_raster = gdal.Open(reference_image_path)
    driver = gdal.GetDriverByName("GTiff")

    geotransform = ref_raster.GetGeoTransform()
    projection = ref_raster.GetProjection()

    print(image_data.shape)  # 确保 image_data 形状是 (bands, rows, cols)
    print(image_data)
    print("最终影像均值（忽略 NaN）:", np.nanmean(image_data))
    print("最终影像最大值（忽略 NaN）:", np.nanmax(image_data))
    print("最终影像最小值（忽略 NaN）:", np.nanmin(image_data))

    bands, rows, cols = image_data.shape  # 获取波段数、行数、列数

    # 创建输出影像（波段数 = bands）
    output_raster = driver.Create(output_path, cols, rows, bands, gdal.GDT_Float32)
    output_raster.SetGeoTransform(geotransform)
    output_raster.SetProjection(projection)

    # 逐个波段写入数据
    for i in range(bands):
        output_raster.GetRasterBand(i + 1).WriteArray(image_data[i])  # 波段索引从1开始

    # 释放资源
    output_raster = None
    ref_raster = None

    print(f"Image saved to {output_path}")